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

    st.sidebar.title("TG Harvest")
    page = st.sidebar.radio(
        "Navigation",
        ["Auth Status", "Channels", "Parse", "Search", "Analytics"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("Auth \u2192 Channels \u2192 Parse \u2192 Search \u2192 Analytics")
    st.sidebar.caption(f"v{__version__}")

    if page == "Auth Status":
        from tg_harvest.web.pages.auth import render

        render()
    elif page == "Channels":
        from tg_harvest.web.pages.channels import render

        render()
    elif page == "Parse":
        from tg_harvest.web.pages.parser import render

        render()
    elif page == "Search":
        from tg_harvest.web.pages.search import render

        render()
    elif page == "Analytics":
        from tg_harvest.web.pages.analytics import render

        render()
