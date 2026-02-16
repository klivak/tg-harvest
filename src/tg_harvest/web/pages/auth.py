"""Auth status page."""

import asyncio

import streamlit as st

from tg_harvest.config import Settings


def _mask_phone(phone: str) -> str:
    """Mask phone number: +380501234567 → +380***4567."""
    if not phone or len(phone) < 6:
        return phone
    return phone[:4] + "***" + phone[-4:]


def render():
    st.header("Authentication Status")
    st.caption("Step 1 — verify your Telegram session before parsing")

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Failed to load settings: {e}")
        st.info(
            "1. Create a `.env` file with `TG_API_ID`, `TG_API_HASH`, `TG_PHONE`\n"
            "2. Run `tg-harvest auth login` in terminal"
        )
        return

    session_file = settings.session_path.with_suffix(".session")
    if session_file.exists():
        try:
            from tg_harvest.client.session import TelegramSession

            async def check():
                session = TelegramSession(settings)
                try:
                    await session.connect()
                    if await session.ensure_authorized():
                        me = await session.client.get_me()
                        return {
                            "name": f"{me.first_name} {me.last_name or ''}".strip(),
                            "username": f"@{me.username}" if me.username else "N/A",
                            "phone": _mask_phone(f"+{me.phone}") if me.phone else "N/A",
                            "id": me.id,
                        }
                    return None
                finally:
                    await session.disconnect()

            with st.spinner("Verifying session..."):
                info = asyncio.run(check())

            if info:
                st.success(f"Authenticated as **{info['name']}**")
                col1, col2 = st.columns(2)
                col1.metric("Name", info["name"])
                col2.metric("ID", info["id"])
                col1.metric("Username", info["username"])
                col2.metric("Phone", info["phone"])
            else:
                st.warning("Session file exists but is not authorized.")
                st.info("Re-run login to authenticate:")
                st.code("tg-harvest auth login", language="bash")
        except Exception as e:
            st.error(f"Could not connect to Telegram: {e}")
            st.info("Check your internet connection and try again.")
    else:
        st.info("No session found. To authenticate:")
        st.markdown(
            "1. Make sure `.env` file exists with your API credentials\n"
            "2. Run the login command in terminal:"
        )
        st.code("tg-harvest auth login", language="bash")

    with st.expander("Configuration"):
        st.json(
            {
                "api_id": settings.api_id,
                "phone": _mask_phone(settings.phone),
                "session_name": settings.session_name,
                "output_dir": str(settings.output_dir),
                "flood_sleep_threshold": settings.flood_sleep_threshold,
                "request_delay": settings.request_delay,
                "web_port": settings.web_port,
            }
        )
