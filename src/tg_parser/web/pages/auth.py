"""Auth status page."""

import asyncio

import streamlit as st

from tg_parser.config import Settings


def render():
    st.header("Authentication Status")

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Failed to load settings: {e}")
        st.info("Make sure `.env` file exists with TG_API_ID, TG_API_HASH, TG_PHONE.")
        return

    session_file = settings.session_path.with_suffix(".session")
    if session_file.exists():
        st.success("Session file found")

        try:
            from tg_parser.client.session import TelegramSession

            async def check():
                session = TelegramSession(settings)
                try:
                    await session.connect()
                    if await session.ensure_authorized():
                        me = await session.client.get_me()
                        return {
                            "name": f"{me.first_name} {me.last_name or ''}".strip(),
                            "username": f"@{me.username}" if me.username else "N/A",
                            "phone": f"+{me.phone}" if me.phone else "N/A",
                            "id": me.id,
                        }
                    return None
                finally:
                    await session.disconnect()

            info = asyncio.run(check())
            if info:
                col1, col2 = st.columns(2)
                col1.metric("Name", info["name"])
                col2.metric("ID", info["id"])
                col1.metric("Username", info["username"])
                col2.metric("Phone", info["phone"])
            else:
                st.warning("Session exists but not authorized.")
                st.code("tg-parser auth login", language="bash")
        except Exception as e:
            st.warning(f"Could not verify session: {e}")
    else:
        st.warning("Not authenticated")
        st.markdown("Run the following command in terminal to authenticate:")
        st.code("tg-parser auth login", language="bash")

    with st.expander("Configuration"):
        st.json(
            {
                "api_id": settings.api_id,
                "phone": settings.phone,
                "session_name": settings.session_name,
                "output_dir": str(settings.output_dir),
                "flood_sleep_threshold": settings.flood_sleep_threshold,
                "request_delay": settings.request_delay,
                "web_port": settings.web_port,
            }
        )
