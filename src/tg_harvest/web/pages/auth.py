"""Auth status page."""

import asyncio

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.web.i18n import t


def _mask_phone(phone: str) -> str:
    """Mask phone number: +380501234567 → +380***4567."""
    if not phone or len(phone) < 6:
        return phone
    return phone[:4] + "***" + phone[-4:]


def render():
    st.header(t("auth.header"))
    st.caption(t("auth.caption"))

    with st.expander(t("auth.help_expander"), expanded=False):
        st.markdown(t("auth.help_step1_header"))
        st.markdown(t("auth.help_step1_body"))
        st.markdown(t("auth.help_step2_header"))
        st.markdown(t("auth.help_step2_body"))
        st.code(
            "TG_API_ID=12345678\n"
            "TG_API_HASH=abcdef1234567890abcdef1234567890\n"
            "TG_PHONE=+380501234567",
            language="dotenv",
        )
        st.markdown(t("auth.help_step3_header"))
        st.markdown(t("auth.help_step3_body"))
        st.code("tg-harvest auth login", language="bash")
        st.markdown(t("auth.help_private_header"))
        st.markdown(t("auth.help_private_body"))

    settings = Settings()

    if not settings.api_id or not settings.api_hash or not settings.phone:
        st.warning(t("auth.no_credentials_warning"))
        st.info(t("auth.no_credentials_info"))
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

            with st.spinner(t("auth.spinner_verifying")):
                info = asyncio.run(check())

            if info:
                st.success(t("auth.success", name=info["name"]))
                col1, col2 = st.columns(2)
                col1.metric(t("auth.metric_name"), info["name"])
                col2.metric(t("auth.metric_id"), info["id"])
                col1.metric(t("auth.metric_username"), info["username"])
                col2.metric(t("auth.metric_phone"), info["phone"])
            else:
                st.warning(t("auth.session_not_authorized"))
                st.info(t("auth.session_relogin_info"))
                st.code("tg-harvest auth login", language="bash")
        except Exception as e:
            st.error(t("auth.connect_error", error=e))
            st.info(t("auth.connect_error_info"))
    else:
        st.info(t("auth.no_session_info"))
        st.markdown(t("auth.no_session_steps"))
        st.code("tg-harvest auth login", language="bash")

    with st.expander(t("auth.config_expander")):
        st.json(
            {
                "api_id": settings.api_id,
                "phone": _mask_phone(settings.phone) if settings.phone else "N/A",
                "session_name": settings.session_name,
                "output_dir": str(settings.output_dir),
                "flood_sleep_threshold": settings.flood_sleep_threshold,
                "request_delay": settings.request_delay,
                "web_port": settings.web_port,
            }
        )
