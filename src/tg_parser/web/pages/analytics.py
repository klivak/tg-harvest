"""Analytics page with charts."""

import plotly.express as px
import streamlit as st

from tg_parser.analytics.stats import ChannelStats
from tg_parser.config import Settings
from tg_parser.search.engine import SearchEngine


def render():
    st.header("Analytics")

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    engine = SearchEngine()
    results = engine.load_results(settings.output_dir)

    if not results:
        st.warning("No parsed data found. Go to **Parse** page first.")
        return

    # Select dataset
    options = {}
    for r in results:
        label = (
            f"{r.channel.title} ({r.total_messages} msgs, {r.parsed_at.strftime('%Y-%m-%d %H:%M')})"
        )
        options[label] = r

    selected = st.selectbox("Select parsed dataset", list(options.keys()))
    result = options[selected]
    stats = ChannelStats(result)

    # Summary metrics
    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total messages", stats.total)
    col2.metric("Avg views", f"{stats.avg_views():,.0f}")
    col3.metric("Avg reactions", f"{stats.avg_reactions():,.1f}")
    col4.metric("Forwarded", stats.forwarded_count())

    col1, col2 = st.columns(2)
    with col1:
        col1.metric("Edited", stats.edited_count())
    with col2:
        media_dist = stats.media_distribution()
        text_only = media_dist.get("text_only", 0)
        with_media = stats.total - text_only
        col2.metric("With media", with_media)

    st.divider()

    # Messages per day
    st.subheader("Messages per Day")
    per_day = stats.messages_per_day()
    if per_day:
        fig = px.bar(
            x=list(per_day.keys()),
            y=list(per_day.values()),
            labels={"x": "Date", "y": "Messages"},
        )
        fig.update_layout(height=350, margin=dict(t=10, b=40))
        st.plotly_chart(fig, use_container_width=True)

    # Activity by hour
    st.subheader("Activity by Hour of Day")
    by_hour = stats.activity_by_hour()
    fig = px.bar(
        x=list(by_hour.keys()),
        y=list(by_hour.values()),
        labels={"x": "Hour (UTC)", "y": "Messages"},
    )
    fig.update_layout(height=300, margin=dict(t=10, b=40))
    st.plotly_chart(fig, use_container_width=True)

    # Two columns for tops
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top by Views")
        top_views = stats.top_by_views()
        if top_views:
            rows = []
            for m in top_views:
                rows.append(
                    {
                        "ID": m.id,
                        "Views": m.views,
                        "Text": m.text[:60].replace("\n", " ") if m.text else "",
                        "Date": m.date.strftime("%Y-%m-%d"),
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No view data available")

    with col2:
        st.subheader("Top by Reactions")
        top_reactions = stats.top_by_reactions()
        if top_reactions:
            rows = []
            for m in top_reactions:
                rows.append(
                    {
                        "ID": m.id,
                        "Reactions": m.reactions.total,
                        "Text": m.text[:60].replace("\n", " ") if m.text else "",
                        "Date": m.date.strftime("%Y-%m-%d"),
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No reaction data available")

    # Media distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Media Distribution")
        media_dist = stats.media_distribution()
        if media_dist:
            fig = px.pie(
                names=list(media_dist.keys()),
                values=list(media_dist.values()),
            )
            fig.update_layout(height=350, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Reactions Breakdown")
        reactions = stats.reactions_summary()
        if reactions:
            # Show top 15 reactions
            items = list(reactions.items())[:15]
            fig = px.bar(
                x=[r[0] for r in items],
                y=[r[1] for r in items],
                labels={"x": "Reaction", "y": "Total count"},
            )
            fig.update_layout(height=350, margin=dict(t=10, b=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reaction data available")
