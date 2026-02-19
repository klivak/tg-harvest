"""Custom CSS theme and Plotly color constants for TG Harvest web UI."""

import streamlit as st

# Plotly chart colors — Telegram-inspired palette
CHART_COLORS = [
    "#0088cc",  # Telegram blue
    "#34a853",  # Green
    "#ea4335",  # Red
    "#fbbc05",  # Yellow
    "#4285f4",  # Light blue
    "#ff6d01",  # Orange
    "#46bdc6",  # Teal
    "#7b61ff",  # Purple
    "#e91e63",  # Pink
    "#00bcd4",  # Cyan
]

CHART_LAYOUT = dict(
    font=dict(family="sans-serif"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)


def apply_custom_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown(
        """
        <style>
        /* Sidebar navigation: make radio options look like nav items */
        div[data-testid="stSidebar"] .stRadio > div {
            gap: 0.2rem;
        }
        div[data-testid="stSidebar"] .stRadio > div > label {
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s;
            font-size: 0.95rem;
        }
        div[data-testid="stSidebar"] .stRadio > div > label:hover {
            background-color: rgba(0, 136, 204, 0.1);
        }

        /* Hide radio button circles in sidebar nav */
        div[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
            display: none;
        }

        /* Sidebar status indicators */
        .sidebar-status {
            padding: 0.4rem 0.75rem;
            border-radius: 0.5rem;
            margin-bottom: 0.4rem;
            font-size: 0.85rem;
        }
        .status-ok { background-color: rgba(33, 195, 84, 0.15); }
        .status-warn { background-color: rgba(255, 165, 0, 0.15); }
        .status-error { background-color: rgba(255, 75, 75, 0.15); }

        /* Parse button full width emphasis */
        div[data-testid="stButton"] > button[kind="primary"] {
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
