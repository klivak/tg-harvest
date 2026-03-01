"""Channels listing page."""

import asyncio

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.web.i18n import t

# Stable internal keys for channel data (language-independent)
_K_ID = "id"
_K_TITLE = "title"
_K_USERNAME = "username"
_K_TYPE = "type"
_K_MEMBERS = "members"
_K_RESTRICTED = "restricted"
_K_PRIVATE = "private"


def render():
    st.header(t("channels.header"))
    st.caption(t("channels.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    with st.expander(t("channels.tips_expander"), expanded=False):
        st.markdown(t("channels.tips_body"))

    col_btn, col_limit = st.columns([2, 3])
    with col_limit:
        limit = st.slider(t("channels.sidebar_slider"), 10, 500, 25)
    with col_btn:
        load_clicked = st.button(t("channels.load_button"), type="primary", width="stretch")

    if load_clicked:
        with st.spinner(t("channels.spinner_fetching")):
            try:
                channels = _fetch_channels_cached(
                    settings.api_id or 0, settings.session_name, limit
                )
                st.session_state["channels"] = channels
                st.toast(t("channels.toast_loaded", count=len(channels)), icon="\U0001f4cb")
            except Exception as e:
                err = str(e).lower()
                if "auth" in err or "not authorized" in err or "session" in err:
                    st.error(t("channels.error_auth"))
                else:
                    st.error(t("channels.error_fetch", error=e))
                return

    if "channels" not in st.session_state:
        st.info(t("channels.empty_state_info"))
        st.caption(t("channels.empty_go_parse_hint"))
        return

    channels = st.session_state["channels"]
    if not channels:
        st.warning(t("channels.no_channels_warning"))
        return

    total = len(channels)
    search = st.text_input(t("channels.filter_label"), placeholder=t("channels.filter_placeholder"))
    if search:
        channels = [
            c
            for c in channels
            if search.lower() in c[_K_TITLE].lower()
            or (c[_K_USERNAME] and search.lower() in c[_K_USERNAME].lower())
        ]

    # Build display rows with translated column names
    type_map = {
        "bot": t("channels.type_bot"),
        "group": t("channels.type_group"),
        "channel": t("channels.type_channel"),
        "user": t("channels.type_user"),
    }
    display_rows = []
    for c in channels:
        display_rows.append(
            {
                t("channels.col_id"): c[_K_ID],
                t("channels.col_title"): c[_K_TITLE],
                t("channels.col_username"): c[_K_USERNAME],
                t("channels.col_type"): type_map.get(c[_K_TYPE], c[_K_TYPE]),
                t("channels.col_members"): c[_K_MEMBERS],
                t("channels.col_restricted"): c[_K_RESTRICTED],
                t("channels.col_private"): c[_K_PRIVATE],
            }
        )

    st.dataframe(
        display_rows,
        column_config={
            t("channels.col_id"): st.column_config.NumberColumn(t("channels.col_id"), format="%d"),
            t("channels.col_title"): t("channels.col_title"),
            t("channels.col_username"): t("channels.col_username"),
            t("channels.col_type"): t("channels.col_type"),
            t("channels.col_members"): st.column_config.NumberColumn(
                t("channels.col_members"), format="%d"
            ),
            t("channels.col_restricted"): t("channels.col_restricted"),
            t("channels.col_private"): t("channels.col_private"),
        },
        width="stretch",
        hide_index=True,
    )

    if search:
        st.caption(t("channels.caption_filtered", count=len(channels), total=total))
    else:
        st.caption(t("channels.caption_total", total=total))

    # --- Quick Actions: select channel and go to Parse ---
    st.divider()
    st.subheader(t("channels.actions_subheader"))

    channel_options: dict[str, str] = {}
    for c in channels:
        ch_title = c[_K_TITLE]
        ch_username = c[_K_USERNAME]
        ch_id = c[_K_ID]
        if ch_username:
            label = f"{ch_title} (@{ch_username})"
            value = f"@{ch_username}"
        else:
            label = f"{ch_title} (ID: {ch_id})"
            value = str(ch_id)
        channel_options[label] = value

    selected = st.selectbox(
        t("channels.select_to_parse_label"),
        list(channel_options.keys()),
        key="channel_to_parse_select",
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button(t("channels.parse_button"), type="primary"):
            st.session_state["prefill_channel"] = channel_options[selected]
            st.session_state["nav_page"] = t("app.page_parse")
            st.rerun()
    with col2:
        st.code(channel_options[selected], language=None)


@st.cache_data(ttl=300)
def _fetch_channels_cached(api_id: int, session_name: str, limit: int) -> list[dict]:
    """Cache-safe synchronous wrapper around async channel fetch."""
    settings = Settings()
    return asyncio.run(_fetch_channels(settings, limit))


async def _fetch_channels(settings: Settings, limit: int) -> list[dict]:
    from tg_harvest.client.rate_limiter import RateLimiter
    from tg_harvest.client.session import TelegramSession
    from tg_harvest.parsers.channel_parser import ChannelParser

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)
        channel_list = await parser.list_channels(limit=limit)

    rows = []
    for ch in channel_list:
        if ch.is_bot:
            ch_type = "bot"
        elif ch.is_group:
            ch_type = "group"
        elif ch.is_channel:
            ch_type = "channel"
        else:
            ch_type = "user"
        rows.append(
            {
                _K_ID: ch.id,
                _K_TITLE: ch.title,
                _K_USERNAME: ch.username or "",
                _K_TYPE: ch_type,
                _K_MEMBERS: ch.members_count or 0,
                _K_RESTRICTED: "\U0001f512" if ch.restricted else "",
                _K_PRIVATE: "\U0001f510" if not ch.username else "",
            }
        )
    return rows
