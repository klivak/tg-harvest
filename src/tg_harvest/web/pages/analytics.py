"""Analytics page with charts."""

from pathlib import Path

import plotly.express as px
import streamlit as st

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.config import Settings
from tg_harvest.search.engine import SearchEngine
from tg_harvest.web.i18n import t


def _truncate(text: str | None, limit: int = 100) -> str:
    if not text:
        return ""
    return (text[:limit] + "...") if len(text) > limit else text


def render():
    st.header(t("analytics.header"))
    st.caption(t("analytics.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    results = _load_results_cached(str(settings.output_dir))

    if not results:
        st.warning(t("analytics.no_data_warning"))
        return

    with st.expander(t("analytics.tips_expander"), expanded=False):
        st.markdown(t("analytics.tips_body"))

    # Select dataset
    options = {}
    for r in results:
        label = (
            f"{r.channel.title} ({r.total_messages} msgs, {r.parsed_at.strftime('%Y-%m-%d %H:%M')})"
        )
        options[label] = r

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
        )
        fig.update_layout(height=350, margin=dict(t=10, b=40))
        st.plotly_chart(fig, use_container_width=True)

    # Activity by hour
    st.subheader(t("analytics.by_hour_subheader"))
    by_hour = stats.activity_by_hour()
    fig = px.bar(
        x=list(by_hour.keys()),
        y=list(by_hour.values()),
        labels={"x": t("analytics.by_hour_x"), "y": t("analytics.by_hour_y")},
    )
    fig.update_layout(height=300, margin=dict(t=10, b=40))
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
                    t("analytics.col_text"): _truncate(m.text),
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
                    t("analytics.col_text"): _truncate(m.text),
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
            )
            fig.update_layout(height=350, margin=dict(t=10, b=10))
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
            )
            fig.update_layout(height=350, margin=dict(t=10, b=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("analytics.reactions_breakdown_empty"))


@st.cache_data(ttl=60)
def _load_results_cached(output_dir_str: str) -> list:
    engine = SearchEngine()
    return engine.load_results(Path(output_dir_str))
