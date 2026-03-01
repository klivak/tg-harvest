"""Streamlit web application — main entry point."""

import streamlit as st


def main():
    """Entry point for tg-harvest-web script."""
    import subprocess
    import sys

    from tg_harvest.config import Settings

    settings = Settings()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            __file__,
            "--server.port",
            str(settings.web_port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
            "--theme.primaryColor",
            "#0088cc",
            "--theme.backgroundColor",
            "#ffffff",
            "--theme.secondaryBackgroundColor",
            "#f0f2f6",
            "--theme.textColor",
            "#262730",
        ],
        check=True,
    )


def _show_sidebar_status():
    """Show auth + data status indicators in sidebar."""
    from tg_harvest.config import Settings
    from tg_harvest.web.i18n import t

    try:
        settings = Settings()
    except Exception:
        return

    session_file = settings.session_path.with_suffix(".session")
    if session_file.exists():
        st.sidebar.markdown(
            f'<div class="sidebar-status status-ok">'
            f"\u2705 {t('sidebar.status_authenticated')}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f'<div class="sidebar-status status-error">'
            f"\u274c {t('sidebar.status_not_authenticated')}</div>",
            unsafe_allow_html=True,
        )

    output_dir = settings.output_dir
    json_count = len(list(output_dir.glob("*.json"))) if output_dir.exists() else 0
    if json_count > 0:
        st.sidebar.markdown(
            f'<div class="sidebar-status status-ok">'
            f"\U0001f4c4 {t('sidebar.status_data_count', count=json_count)}"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f'<div class="sidebar-status status-warn">'
            f"\U0001f4c4 {t('sidebar.status_no_data')}</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__" or st.runtime.exists():
    st.set_page_config(
        page_title="TG Harvest",
        page_icon="\U0001f4e1",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    from tg_harvest import __version__
    from tg_harvest.web.i18n import LANGUAGES, t
    from tg_harvest.web.theme import apply_custom_css

    apply_custom_css()

    # Language selector — must be first so all subsequent t() calls use correct lang
    lang_label = st.sidebar.selectbox(
        t("app.lang_selector_label"),
        list(LANGUAGES.keys()),
        key="lang_label",
    )
    st.session_state["lang"] = LANGUAGES[lang_label]

    st.sidebar.title("TG Harvest")

    # Build page list
    nav_pages = [
        t("app.page_auth"),
        t("app.page_channels"),
        t("app.page_parse"),
        t("app.page_search"),
        t("app.page_analytics"),
        t("app.page_files"),
    ]

    # Support programmatic navigation from other pages
    nav_key = "nav_radio"
    if "nav_page" in st.session_state:
        st.session_state[nav_key] = st.session_state.pop("nav_page")

    page = st.sidebar.radio(
        t("app.nav_label"),
        nav_pages,
        key=nav_key,
    )

    # Sidebar status indicators
    st.sidebar.divider()
    _show_sidebar_status()

    st.sidebar.caption(t("app.workflow_caption"))
    st.sidebar.caption(f"v{__version__}")

    # Guard: warn if navigating away from parser while parsing is active
    parse_page = t("app.page_parse")
    if st.session_state.get("parsing_active") and page != parse_page:

        @st.dialog(t("app.nav_guard_title"))
        def _nav_guard():
            st.warning(t("app.nav_guard_warning"))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(t("app.nav_guard_stay"), type="primary", use_container_width=True):
                    st.session_state[nav_key] = parse_page
                    st.rerun()
            with col2:
                if st.button(t("app.nav_guard_leave"), use_container_width=True):
                    st.session_state["parsing_active"] = False
                    st.rerun()

        _nav_guard()
        st.stop()

    if page == t("app.page_auth"):
        from tg_harvest.web.views.auth import render

        render()
    elif page == t("app.page_channels"):
        from tg_harvest.web.views.channels import render

        render()
    elif page == t("app.page_parse"):
        from tg_harvest.web.views.parser import render

        render()
    elif page == t("app.page_search"):
        from tg_harvest.web.views.search import render

        render()
    elif page == t("app.page_analytics"):
        from tg_harvest.web.views.analytics import render

        render()
    elif page == t("app.page_files"):
        from tg_harvest.web.views.files import render

        render()
