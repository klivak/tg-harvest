"""Search page."""

import streamlit as st

from tg_parser.config import Settings
from tg_parser.models.media import MediaType
from tg_parser.search.engine import SearchEngine, SearchFilters


def render():
    st.header("Search Messages")

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

    total_msgs = sum(r.total_messages for r in results)
    st.caption(f"Searching across {len(results)} files, {total_msgs} messages")

    # Search form
    query = st.text_input("Search query", placeholder="Type keywords...")

    # Filters
    with st.expander("Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            media_options = ["Any"] + [mt.value for mt in MediaType if mt != MediaType.NONE]
            media_type = st.selectbox("Media type", media_options)
            min_views = st.number_input("Minimum views", min_value=0, value=0)
        with col2:
            has_reactions = st.checkbox("Has reactions")
            from_date = st.date_input("From date", value=None, key="search_from")
            to_date = st.date_input("To date", value=None, key="search_to")

        # Channel filter
        channel_names = [
            f"{r.channel.title} (@{r.channel.username})" if r.channel.username else r.channel.title
            for r in results
        ]
        channel_ids = [r.channel.id for r in results]
        unique = {}
        for name, cid in zip(channel_names, channel_ids):
            unique[name] = cid
        channel_options = ["All channels"] + list(unique.keys())
        selected_channel = st.selectbox("Channel", channel_options)

    if st.button("Search", type="primary") or query:
        filters = SearchFilters(
            keyword=query,
            media_type=MediaType(media_type) if media_type != "Any" else None,
            has_reactions=True if has_reactions else None,
            min_views=min_views if min_views > 0 else None,
            date_from=from_date.isoformat() if from_date else None,
            date_to=to_date.isoformat() if to_date else None,
            channel_id=unique.get(selected_channel) if selected_channel != "All channels" else None,
        )

        matches = engine.search(results, filters)

        if not matches:
            st.info("No messages found matching your criteria.")
            return

        st.success(f"Found {len(matches)} messages")

        rows = []
        for match in matches[:200]:
            msg = match.message
            text = msg.text[:120].replace("\n", " ") if msg.text else ""
            rows.append(
                {
                    "Channel": match.channel_username or match.channel_title,
                    "Date": msg.date.strftime("%Y-%m-%d %H:%M"),
                    "ID": msg.id,
                    "Text": text,
                    "Views": msg.views or 0,
                    "Reactions": msg.reactions.total if msg.reactions else 0,
                    "Media": msg.media.type if msg.media else "",
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)

        if len(matches) > 200:
            st.caption(f"Showing 200 of {len(matches)} results")
