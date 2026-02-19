"""Channels listing page."""

import asyncio

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.web.i18n import t


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

    limit = st.sidebar.slider(t("channels.sidebar_slider"), 10, 500, 100)

    if st.button(t("channels.load_button"), type="primary"):
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
            if search.lower() in c[t("channels.col_title")].lower()
            or (
                c[t("channels.col_username")]
                and search.lower() in c[t("channels.col_username")].lower()
            )
        ]

    st.dataframe(
        channels,
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
        use_container_width=True,
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
        ch_title = c[t("channels.col_title")]
        ch_username = c[t("channels.col_username")]
        ch_id = c[t("channels.col_id")]
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
    from tg_harvest.web.i18n import t as _t

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)
        channel_list = await parser.list_channels(limit=limit)

    return [
        {
            _t("channels.col_id"): ch.id,
            _t("channels.col_title"): ch.title,
            _t("channels.col_username"): ch.username or "",
            _t("channels.col_type"): _t("channels.type_group")
            if ch.is_group
            else _t("channels.type_channel"),
            _t("channels.col_members"): ch.members_count or 0,
            _t("channels.col_restricted"): "\U0001f512" if ch.restricted else "",
            _t("channels.col_private"): "\U0001f510" if not ch.username else "",
        }
        for ch in channel_list
    ]
