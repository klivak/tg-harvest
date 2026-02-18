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
        ],
        check=False,
    )


if __name__ == "__main__" or st.runtime.exists():
    st.set_page_config(
        page_title="TG Harvest",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    from tg_harvest import __version__
    from tg_harvest.web.i18n import LANGUAGES, t

    # Language selector — must be first so all subsequent t() calls use the correct lang
    lang_label = st.sidebar.selectbox(
        t("app.lang_selector_label"),
        list(LANGUAGES.keys()),
        key="lang_label",
    )
    st.session_state["lang"] = LANGUAGES[lang_label]

    st.sidebar.title("TG Harvest")

    page = st.sidebar.radio(
        t("app.nav_label"),
        [
            t("app.page_auth"),
            t("app.page_channels"),
            t("app.page_parse"),
            t("app.page_search"),
            t("app.page_analytics"),
        ],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption(t("app.workflow_caption"))
    st.sidebar.caption(f"v{__version__}")

    if page == t("app.page_auth"):
        from tg_harvest.web.pages.auth import render

        render()
    elif page == t("app.page_channels"):
        from tg_harvest.web.pages.channels import render

        render()
    elif page == t("app.page_parse"):
        from tg_harvest.web.pages.parser import render

        render()
    elif page == t("app.page_search"):
        from tg_harvest.web.pages.search import render

        render()
    elif page == t("app.page_analytics"):
        from tg_harvest.web.pages.analytics import render

        render()
