"""Streamlit web application — main entry point."""

import streamlit as st


def main():
    """Entry point for tg-parser-web script."""
    import subprocess
    import sys

    from tg_parser.config import Settings

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
        page_title="Telegram Parser",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("Telegram Parser")
    page = st.sidebar.radio(
        "Navigation",
        ["Auth Status", "Channels", "Parse", "Search", "Analytics"],
        label_visibility="collapsed",
    )

    if page == "Auth Status":
        from tg_parser.web.pages.auth import render

        render()
    elif page == "Channels":
        from tg_parser.web.pages.channels import render

        render()
    elif page == "Parse":
        from tg_parser.web.pages.parser import render

        render()
    elif page == "Search":
        from tg_parser.web.pages.search import render

        render()
    elif page == "Analytics":
        from tg_parser.web.pages.analytics import render

        render()
