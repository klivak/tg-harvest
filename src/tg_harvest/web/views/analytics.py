"""Analytics page with charts."""

import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.config import Settings
from tg_harvest.config.constants import MIN_WORD_LENGTH, TOP_REACTIONS_DISPLAY, TOP_WORDS_COUNT
from tg_harvest.search.engine import SearchEngine
from tg_harvest.web.helpers import truncate
from tg_harvest.web.i18n import t
from tg_harvest.web.theme import CHART_COLORS, CHART_LAYOUT


def render():
    st.header(t("analytics.header"))
    st.caption(t("analytics.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    # Header with refresh button
    col_header, col_refresh = st.columns([6, 1])
    with col_refresh:
        if st.button("\U0001f504", help=t("analytics.refresh_help"), key="analytics_refresh"):
            _load_results_cached.clear()
            st.rerun()

    results = _load_results_cached(str(settings.output_dir))

    if not results:
        st.warning(t("analytics.no_data_warning"))
        return

    with st.expander(t("analytics.tips_expander"), expanded=False):
        st.markdown(t("analytics.tips_body"))

    # Build options map
    options: dict[str, object] = {}
    for r in results:
        label = (
            f"{r.channel.title} ({r.total_messages} msgs, {r.parsed_at.strftime('%Y-%m-%d %H:%M')})"
        )
        options[label] = r

    # Tabs: single channel / compare
    tab_single, tab_compare = st.tabs([t("analytics.tab_single"), t("analytics.tab_compare")])

    with tab_single:
        _render_single(options)

    with tab_compare:
        _render_compare(options)


def _render_single(options: dict):
    """Render single-channel analytics."""
    selected = st.selectbox(t("analytics.dataset_label"), list(options.keys()))
    result = options[selected]
    stats = ChannelStats(result)

    # Summary metrics — 3+3 layout
    st.subheader(t("analytics.summary_subheader"))
    col1, col2, col3 = st.columns(3)
    col1.metric(t("analytics.metric_total"), stats.total)
    col2.metric(t("analytics.metric_avg_views"), f"{stats.avg_views():,.0f}")
    col3.metric(t("analytics.metric_avg_reactions"), f"{stats.avg_reactions():,.1f}")

    col4, col5, col6 = st.columns(3)
    col4.metric(t("analytics.metric_forwarded"), stats.forwarded_count())
    col5.metric(t("analytics.metric_edited"), stats.edited_count())
    media_dist = stats.media_distribution()
    with_media = stats.total - media_dist.get("text_only", 0)
    col6.metric(t("analytics.metric_with_media"), with_media)

    col7, col8, col9 = st.columns(3)
    col7.metric(t("analytics.metric_engagement_rate"), f"{stats.engagement_rate():.2%}")
    col8.metric(t("analytics.metric_avg_msg_length"), f"{stats.avg_message_length():,.0f}")
    top_fwd = stats.top_by_forwards(1)
    col9.metric(t("analytics.metric_max_forwards"), top_fwd[0].forwards if top_fwd else 0)

    # Download section: split + JSON
    result_data = result.model_dump(mode="json")
    base_name = result.channel.username or str(result.channel.id)

    split_col1, split_col2 = st.columns([1, 3])
    with split_col1:
        split_parts = st.number_input(
            t("parser.split_parts_label"),
            min_value=1,
            max_value=20,
            value=1,
            help=t("parser.split_parts_help"),
            key="analytics_split_parts",
        )

    if split_parts > 1:
        zip_data = _build_split_json_zip(result_data, base_name, int(split_parts))
        if zip_data:
            st.download_button(
                t("analytics.download_json_zip"),
                data=zip_data,
                file_name=f"{base_name}_json.zip",
                mime="application/zip",
                key="dl_messages_json_zip",
            )
    else:
        st.download_button(
            t("analytics.download_json"),
            data=json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
            file_name=f"{base_name}.json",
            mime="application/json",
            key="dl_messages_json",
        )

    st.divider()

    # Messages over time — with aggregation toggle
    st.subheader(t("analytics.activity_subheader"))
    time_modes = {
        t("analytics.time_mode_day"): "day",
        t("analytics.time_mode_week"): "week",
        t("analytics.time_mode_month"): "month",
    }
    time_mode_label = st.radio(
        t("analytics.time_mode_label"),
        list(time_modes.keys()),
        horizontal=True,
        key="time_mode",
    )
    time_mode = time_modes[time_mode_label]

    if time_mode == "day":
        activity_data = stats.messages_per_day()
    elif time_mode == "week":
        activity_data = stats.messages_per_week()
    else:
        activity_data = stats.messages_per_month()

    if activity_data:
        fig = px.bar(
            x=list(activity_data.keys()),
            y=list(activity_data.values()),
            labels={"x": t("analytics.per_day_x"), "y": t("analytics.per_day_y")},
            color_discrete_sequence=CHART_COLORS,
        )
        fig.update_layout(height=350, margin=dict(t=10, b=40), **CHART_LAYOUT)
        st.plotly_chart(fig, width="stretch")
        _download_chart_csv(
            activity_data,
            t("analytics.per_day_x"),
            t("analytics.per_day_y"),
            f"messages_per_{time_mode}.csv",
            "dl_per_time",
        )

    # Activity by hour
    st.subheader(t("analytics.by_hour_subheader"))
    by_hour = stats.activity_by_hour()
    if by_hour:
        fig = px.bar(
            x=list(by_hour.keys()),
            y=list(by_hour.values()),
            labels={"x": t("analytics.by_hour_x"), "y": t("analytics.by_hour_y")},
            color_discrete_sequence=CHART_COLORS,
        )
        fig.update_layout(height=300, margin=dict(t=10, b=40), **CHART_LAYOUT)
        st.plotly_chart(fig, width="stretch")
        st.caption(t("analytics.by_hour_caption"))
        _download_chart_csv(
            by_hour,
            t("analytics.by_hour_x"),
            t("analytics.by_hour_y"),
            "activity_by_hour.csv",
            "dl_by_hour",
        )

    # Top by views / top by reactions / top by forwards
    col1, col2, col3 = st.columns(3)

    with col1:
        _render_top_table(
            stats.top_by_views(),
            "analytics.top_views_subheader",
            "analytics.col_views",
            lambda m: m.views,
            "analytics.top_views_empty",
        )

    with col2:
        _render_top_table(
            stats.top_by_reactions(),
            "analytics.top_reactions_subheader",
            "analytics.col_reactions",
            lambda m: m.reactions.total,
            "analytics.top_reactions_empty",
        )

    with col3:
        _render_top_table(
            stats.top_by_forwards(),
            "analytics.top_forwards_subheader",
            "analytics.col_forwards",
            lambda m: m.forwards,
            "analytics.top_forwards_empty",
        )

    # Reply threads
    thread_data = stats.thread_stats()
    if thread_data["total_threads"] > 0:
        st.subheader(t("analytics.threads_subheader"))
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric(t("analytics.metric_total_threads"), thread_data["total_threads"])
        tc2.metric(
            t("analytics.metric_avg_replies"),
            f"{thread_data['avg_replies']:.1f}",
        )
        tc3.metric(t("analytics.metric_max_replies"), thread_data["max_replies"])

        top_threads_data = stats.top_threads()
        if top_threads_data:
            # Build rows: find the original message text for each thread
            msg_map = {m.id: m for m in result.messages}
            thread_rows = []
            for top_id, count in top_threads_data:
                orig = msg_map.get(top_id)
                thread_rows.append(
                    {
                        t("analytics.col_id"): top_id,
                        t("analytics.col_replies"): count,
                        t("analytics.col_text"): truncate(orig.text if orig else "", limit=100),
                    }
                )
            st.dataframe(thread_rows, width="stretch", hide_index=True)

    # Media distribution / reactions breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("analytics.media_dist_subheader"))
        if media_dist:
            fig = px.pie(
                names=list(media_dist.keys()),
                values=list(media_dist.values()),
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(height=350, margin=dict(t=10, b=10), **CHART_LAYOUT)
            st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader(t("analytics.reactions_breakdown_subheader"))
        reactions = stats.reactions_summary()
        if reactions:
            items = list(reactions.items())[:TOP_REACTIONS_DISPLAY]
            fig = px.bar(
                x=[r[0] for r in items],
                y=[r[1] for r in items],
                labels={
                    "x": t("analytics.reactions_breakdown_x"),
                    "y": t("analytics.reactions_breakdown_y"),
                },
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(height=350, margin=dict(t=10, b=40), **CHART_LAYOUT)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info(t("analytics.reactions_breakdown_empty"))

    # Word frequency
    _render_word_frequency(result.messages)


def _render_top_table(
    messages: list,
    header_key: str,
    metric_key: str,
    metric_getter,
    empty_key: str,
) -> None:
    """Render a 'top by X' table (views, reactions, forwards)."""
    st.subheader(t(header_key))
    if not messages:
        st.info(t(empty_key))
        return
    rows = [
        {
            t("analytics.col_id"): m.id,
            t(metric_key): metric_getter(m),
            t("analytics.col_text"): truncate(m.text),
            t("analytics.col_date"): m.date.strftime("%Y-%m-%d"),
        }
        for m in messages
    ]
    st.dataframe(
        rows,
        column_config={
            t("analytics.col_id"): st.column_config.NumberColumn(
                t("analytics.col_id"), format="%d"
            ),
            t(metric_key): st.column_config.NumberColumn(t(metric_key), format="%d"),
            t("analytics.col_text"): st.column_config.TextColumn(
                t("analytics.col_text"), width="large"
            ),
            t("analytics.col_date"): t("analytics.col_date"),
        },
        width="stretch",
        hide_index=True,
    )


def _render_word_frequency(messages: list) -> None:
    """Render word frequency chart from message texts."""
    st.subheader(t("analytics.word_freq_subheader"))
    words: Counter[str] = Counter()
    for msg in messages:
        if msg.text:
            tokens = msg.text.lower().split()
            tokens = [w for w in tokens if len(w) >= MIN_WORD_LENGTH]
            words.update(tokens)
    top_words = words.most_common(TOP_WORDS_COUNT)
    if top_words:
        fig = px.bar(
            x=[w[0] for w in top_words],
            y=[w[1] for w in top_words],
            labels={
                "x": t("analytics.word_freq_x"),
                "y": t("analytics.word_freq_y"),
            },
            color_discrete_sequence=CHART_COLORS,
        )
        fig.update_layout(height=350, margin=dict(t=10, b=40), **CHART_LAYOUT)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info(t("analytics.word_freq_empty"))


def _build_split_json_zip(result_data: dict, base_name: str, parts: int) -> bytes | None:
    """Split messages into N parts and pack as JSON files in a ZIP."""
    messages = result_data.get("messages", [])
    if not messages:
        return None
    total = len(messages)
    chunk_size, remainder = divmod(total, parts)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        offset = 0
        part_num = 0
        for i in range(parts):
            size = chunk_size + (1 if i < remainder else 0)
            chunk = messages[offset : offset + size]
            if not chunk:
                break
            offset += size
            part_num += 1
            part_data = {**result_data, "messages": chunk}
            content = json.dumps(part_data, ensure_ascii=False, indent=2, default=str)
            fname = f"{base_name}_part{part_num}of{parts}.json"
            zf.writestr(fname, content)
    return buf.getvalue() if part_num > 0 else None


def _render_compare(options: dict):
    """Render channel comparison view."""
    if len(options) < 2:
        st.info(t("analytics.compare_hint"))
        return

    selected_datasets = st.multiselect(
        t("analytics.compare_select_label"),
        list(options.keys()),
        max_selections=5,
    )

    if len(selected_datasets) < 2:
        st.info(t("analytics.compare_hint"))
        return

    # Comparison metrics table
    comparison_rows = []
    for label in selected_datasets:
        r = options[label]
        s = ChannelStats(r)
        comparison_rows.append(
            {
                t("analytics.col_channel"): r.channel.title,
                t("analytics.metric_total"): s.total,
                t("analytics.metric_avg_views"): f"{s.avg_views():,.0f}",
                t("analytics.metric_avg_reactions"): f"{s.avg_reactions():,.1f}",
                t("analytics.metric_forwarded"): s.forwarded_count(),
                t("analytics.metric_edited"): s.edited_count(),
            }
        )
    st.dataframe(comparison_rows, width="stretch", hide_index=True)

    # Overlay messages per day
    st.subheader(t("analytics.per_day_subheader"))
    fig = go.Figure()
    for i, label in enumerate(selected_datasets):
        r = options[label]
        s = ChannelStats(r)
        per_day = s.messages_per_day()
        fig.add_trace(
            go.Bar(
                x=list(per_day.keys()),
                y=list(per_day.values()),
                name=r.channel.title,
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            )
        )
    fig.update_layout(barmode="group", height=400, **CHART_LAYOUT)
    st.plotly_chart(fig, width="stretch")

    # Overlay activity by hour
    st.subheader(t("analytics.by_hour_subheader"))
    fig = go.Figure()
    for i, label in enumerate(selected_datasets):
        r = options[label]
        s = ChannelStats(r)
        by_hour = s.activity_by_hour()
        fig.add_trace(
            go.Bar(
                x=list(by_hour.keys()),
                y=list(by_hour.values()),
                name=r.channel.title,
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            )
        )
    fig.update_layout(barmode="group", height=350, **CHART_LAYOUT)
    st.plotly_chart(fig, width="stretch")
    st.caption(t("analytics.by_hour_caption"))


def _download_chart_csv(data: dict, x_label: str, y_label: str, filename: str, key: str):
    """Render a download button for chart data as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([x_label, y_label])
    for k, v in data.items():
        writer.writerow([k, v])
    st.download_button(
        t("analytics.download_chart_data"),
        data=buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


@st.cache_data(ttl=60)
def _load_results_cached(output_dir_str: str) -> list:
    engine = SearchEngine()
    return engine.load_results(Path(output_dir_str))
