"""Channels listing page."""

import asyncio

import streamlit as st

from tg_parser.config import Settings


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
    from telethon.tl import types

    from tg_parser.client.session import TelegramSession

    result = []
    async with TelegramSession(settings) as session:
        async for dialog in session.client.iter_dialogs(limit=limit):
            entity = dialog.entity
            if not isinstance(entity, (types.Channel, types.Chat)):
                continue

            is_channel = isinstance(entity, types.Channel)
            is_group = is_channel and entity.megagroup

            result.append(
                {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, "username", None) or "",
                    "type": "Group" if is_group or isinstance(entity, types.Chat) else "Channel",
                    "members": getattr(entity, "participants_count", None) or 0,
                    "restricted": "Yes" if getattr(entity, "restricted", False) else "",
                }
            )

    return result
