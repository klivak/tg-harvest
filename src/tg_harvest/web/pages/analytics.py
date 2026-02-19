"""Analytics page with charts."""

import csv
import io
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.config import Settings
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

    st.divider()

    # Messages per day
    st.subheader(t("analytics.per_day_subheader"))
    per_day = stats.messages_per_day()
    if per_day:
        fig = px.bar(
            x=list(per_day.keys()),
            y=list(per_day.values()),
            labels={"x": t("analytics.per_day_x"), "y": t("analytics.per_day_y")},
            color_discrete_sequence=CHART_COLORS,
        )
        fig.update_layout(height=350, margin=dict(t=10, b=40), **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
        _download_chart_csv(
            per_day,
            t("analytics.per_day_x"),
            t("analytics.per_day_y"),
            "messages_per_day.csv",
            "dl_per_day",
        )

    # Activity by hour
    st.subheader(t("analytics.by_hour_subheader"))
    by_hour = stats.activity_by_hour()
    fig = px.bar(
        x=list(by_hour.keys()),
        y=list(by_hour.values()),
        labels={"x": t("analytics.by_hour_x"), "y": t("analytics.by_hour_y")},
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(height=300, margin=dict(t=10, b=40), **CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t("analytics.by_hour_caption"))

    # Top by views / top by reactions
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("analytics.top_views_subheader"))
        top_views = stats.top_by_views()
        if top_views:
            rows = [
                {
                    t("analytics.col_id"): m.id,
                    t("analytics.col_views"): m.views,
                    t("analytics.col_text"): truncate(m.text),
                    t("analytics.col_date"): m.date.strftime("%Y-%m-%d"),
                }
                for m in top_views
            ]
            st.dataframe(
                rows,
                column_config={
                    t("analytics.col_id"): st.column_config.NumberColumn(
                        t("analytics.col_id"), format="%d"
                    ),
                    t("analytics.col_views"): st.column_config.NumberColumn(
                        t("analytics.col_views"), format="%d"
                    ),
                    t("analytics.col_text"): st.column_config.TextColumn(
                        t("analytics.col_text"), width="large"
                    ),
                    t("analytics.col_date"): t("analytics.col_date"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(t("analytics.top_views_empty"))

    with col2:
        st.subheader(t("analytics.top_reactions_subheader"))
        top_reactions = stats.top_by_reactions()
        if top_reactions:
            rows = [
                {
                    t("analytics.col_id"): m.id,
                    t("analytics.col_reactions"): m.reactions.total,
                    t("analytics.col_text"): truncate(m.text),
                    t("analytics.col_date"): m.date.strftime("%Y-%m-%d"),
                }
                for m in top_reactions
            ]
            st.dataframe(
                rows,
                column_config={
                    t("analytics.col_id"): st.column_config.NumberColumn(
                        t("analytics.col_id"), format="%d"
                    ),
                    t("analytics.col_reactions"): st.column_config.NumberColumn(
                        t("analytics.col_reactions"), format="%d"
                    ),
                    t("analytics.col_text"): st.column_config.TextColumn(
                        t("analytics.col_text"), width="large"
                    ),
                    t("analytics.col_date"): t("analytics.col_date"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(t("analytics.top_reactions_empty"))

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
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(t("analytics.reactions_breakdown_subheader"))
        reactions = stats.reactions_summary()
        if reactions:
            items = list(reactions.items())[:15]
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("analytics.reactions_breakdown_empty"))


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
    st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

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
    st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig, use_container_width=True)
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
