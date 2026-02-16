"""Channels listing page."""

import asyncio

import streamlit as st

from tg_harvest.config import Settings


def render():
    st.header("Channels & Groups")

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    limit = st.sidebar.slider("Max dialogs to scan", 10, 500, 100)

    if st.button("Load channels", type="primary"):
        with st.spinner("Fetching channels..."):
            try:
                channels = asyncio.run(_fetch_channels(settings, limit))
                st.session_state["channels"] = channels
            except Exception as e:
                st.error(f"Failed to fetch channels: {e}")
                return

    if "channels" in st.session_state and st.session_state["channels"]:
        channels = st.session_state["channels"]

        search = st.text_input("Filter channels", placeholder="Type to filter...")
        if search:
            channels = [
                c
                for c in channels
                if search.lower() in c["title"].lower()
                or (c["username"] and search.lower() in c["username"].lower())
            ]

        st.dataframe(
            channels,
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "title": "Title",
                "username": "Username",
                "type": "Type",
                "members": st.column_config.NumberColumn("Members", format="%d"),
                "restricted": "Restricted",
            },
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Total: {len(channels)} channels/groups")


async def _fetch_channels(settings: Settings, limit: int) -> list[dict]:
    from tg_harvest.client.rate_limiter import RateLimiter
    from tg_harvest.client.session import TelegramSession
    from tg_harvest.parsers.channel_parser import ChannelParser

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)
        channel_list = await parser.list_channels(limit=limit)

    return [
        {
            "id": ch.id,
            "title": ch.title,
            "username": ch.username or "",
            "type": "Group" if ch.is_group else "Channel",
            "members": ch.members_count or 0,
            "restricted": "Yes" if ch.restricted else "",
        }
        for ch in channel_list
    ]
