"""Search page."""

import csv
import io
from pathlib import Path

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.models.media import MediaType
from tg_harvest.search.engine import SearchEngine, SearchFilters
from tg_harvest.web.helpers import truncate
from tg_harvest.web.i18n import t


def render():
    st.header(t("search.header"))
    st.caption(t("search.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    results = _load_results_cached(str(settings.output_dir))

    if not results:
        st.warning(t("search.no_data_warning"))
        return

    total_msgs = sum(r.total_messages for r in results)

    # Scope caption with refresh button
    col_scope, col_refresh = st.columns([6, 1])
    with col_scope:
        st.caption(t("search.scope_caption", files=len(results), messages=total_msgs))
    with col_refresh:
        if st.button("\U0001f504", help=t("search.refresh_help"), key="search_refresh"):
            _load_results_cached.clear()
            st.rerun()

    with st.expander(t("search.tips_expander"), expanded=False):
        st.markdown(t("search.tips_body"))

    result_limit = st.sidebar.slider(t("search.sidebar_limit_label"), 50, 500, 200)

    # Search form
    query = st.text_input(t("search.query_label"), placeholder=t("search.query_placeholder"))

    # Filters — always visible
    col1, col2, col3 = st.columns(3)
    with col1:
        media_options = [t("search.filter_media_any")] + [
            mt.value for mt in MediaType if mt != MediaType.NONE
        ]
        media_type = st.selectbox(t("search.filter_media_label"), media_options)
        min_views = st.number_input(t("search.filter_min_views"), min_value=0, value=0)
    with col2:
        has_reactions = st.checkbox(t("search.filter_has_reactions"))
        from_date = st.date_input(t("search.filter_from_date"), value=None, key="search_from")
        to_date = st.date_input(t("search.filter_to_date"), value=None, key="search_to")
    with col3:
        # Channel filter — dedup by ID to avoid losing channels with identical names
        unique: dict[int, str] = {}
        for r in results:
            if r.channel.id not in unique:
                label = (
                    f"{r.channel.title} (@{r.channel.username})"
                    if r.channel.username
                    else r.channel.title
                )
                unique[r.channel.id] = label
        name_to_id: dict[str, int] = {v: k for k, v in unique.items()}
        channel_options = [t("search.filter_channel_all")] + list(name_to_id.keys())
        selected_channel = st.selectbox(t("search.filter_channel_label"), channel_options)

    search_clicked = st.button(t("search.search_button"), type="primary")

    if not query and not search_clicked:
        st.info(t("search.empty_state_info"))
        return

    filters = SearchFilters(
        keyword=query,
        media_type=MediaType(media_type) if media_type != t("search.filter_media_any") else None,
        has_reactions=True if has_reactions else None,
        min_views=min_views if min_views > 0 else None,
        date_from=from_date.isoformat() if from_date else None,
        date_to=to_date.isoformat() if to_date else None,
        channel_id=name_to_id.get(selected_channel)
        if selected_channel != t("search.filter_channel_all")
        else None,
    )

    engine = SearchEngine()
    matches = engine.search(results, filters)

    if not matches:
        st.warning(t("search.no_results_warning"))
        return

    st.subheader(t("search.results_subheader", count=len(matches)))

    rows = []
    for match in matches[:result_limit]:
        msg = match.message
        rows.append(
            {
                t("search.col_channel"): match.channel_username or match.channel_title,
                t("search.col_date"): msg.date.strftime("%Y-%m-%d %H:%M"),
                t("search.col_id"): msg.id,
                t("search.col_text"): truncate(msg.text),
                t("search.col_views"): msg.views or 0,
                t("search.col_reactions"): msg.reactions.total if msg.reactions else 0,
                t("search.col_media"): msg.media.type if msg.media else "",
            }
        )

    st.dataframe(
        rows,
        column_config={
            t("search.col_channel"): t("search.col_channel"),
            t("search.col_date"): t("search.col_date"),
            t("search.col_id"): st.column_config.NumberColumn(t("search.col_id"), format="%d"),
            t("search.col_text"): st.column_config.TextColumn(t("search.col_text"), width="large"),
            t("search.col_views"): st.column_config.NumberColumn(
                t("search.col_views"), format="%d"
            ),
            t("search.col_reactions"): st.column_config.NumberColumn(
                t("search.col_reactions"), format="%d"
            ),
            t("search.col_media"): t("search.col_media"),
        },
        width="stretch",
        hide_index=True,
    )

    if len(matches) > result_limit:
        st.caption(t("search.caption_truncated", limit=result_limit, total=len(matches)))

    csv_data = _build_search_csv(matches[:result_limit])
    st.download_button(
        t("search.download_csv"),
        data=csv_data,
        file_name="search_results.csv",
        mime="text/csv",
    )


@st.cache_data(ttl=60)
def _load_results_cached(output_dir_str: str) -> list:
    engine = SearchEngine()
    return engine.load_results(Path(output_dir_str))


def _build_search_csv(matches: list) -> str:
    output = io.StringIO()
    fields = [
        t("search.col_channel"),
        t("search.col_date"),
        t("search.col_id"),
        t("search.col_text"),
        t("search.col_views"),
        t("search.col_reactions"),
        t("search.col_media"),
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for match in matches:
        msg = match.message
        writer.writerow(
            {
                t("search.col_channel"): match.channel_username or match.channel_title,
                t("search.col_date"): msg.date.strftime("%Y-%m-%d %H:%M"),
                t("search.col_id"): msg.id,
                t("search.col_text"): truncate(msg.text, 500),
                t("search.col_views"): msg.views or 0,
                t("search.col_reactions"): msg.reactions.total if msg.reactions else 0,
                t("search.col_media"): msg.media.type if msg.media else "",
            }
        )

    return output.getvalue()
