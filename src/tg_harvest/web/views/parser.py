"""Parse page — main parsing interface."""

import asyncio
import csv
import io
import json
import os
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from streamlit_js_eval import get_local_storage, set_local_storage

from tg_harvest.config import Settings
from tg_harvest.config.constants import ALL_EXPORT_FIELDS
from tg_harvest.exporters.base import build_row, filter_fields
from tg_harvest.parsers.parse_options import ParseOptions
from tg_harvest.web.helpers import truncate
from tg_harvest.web.i18n import t


def render():
    st.header(t("parser.header"))
    st.caption(t("parser.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    # Warn if no channels loaded
    loaded_channels = st.session_state.get("channels", [])
    if not loaded_channels:
        st.warning(t("parser.no_channels_warning"))

    with st.expander(t("parser.tips_expander"), expanded=False):
        st.markdown(t("parser.tips_body"))

    # Channel input — multiselect from loaded channels, or manual text area
    prefill = st.session_state.pop("prefill_channel", "")

    if loaded_channels:
        # Build options: "Title (@username)" -> "@username" or "Title (ID: 123)" -> "123"
        channel_options: dict[str, str] = {}
        value_to_label: dict[str, str] = {}
        for c in loaded_channels:
            ch_title = c["title"]
            ch_username = c["username"]
            ch_id = c["id"]
            if ch_username:
                label = f"{ch_title} (@{ch_username})"
                value = f"@{ch_username}"
            else:
                label = f"{ch_title} (ID: {ch_id})"
                value = str(ch_id)
            channel_options[label] = value
            value_to_label[value] = label

        manual_mode = st.checkbox(t("parser.channel_manual_toggle"))

        if manual_mode:
            channels_text = st.text_area(
                t("parser.channel_textarea_label"),
                value=prefill,
                placeholder=t("parser.channel_textarea_placeholder"),
                height=100,
            )
            channels_list = [ch.strip() for ch in channels_text.strip().splitlines() if ch.strip()]
        else:
            labels = list(channel_options.keys())

            # Search filter
            search_query = st.text_input(
                t("parser.channel_search_label"),
                placeholder=t("parser.channel_search_placeholder"),
                key="channel_search",
            )
            if search_query:
                query_lower = search_query.lower()
                labels = [lbl for lbl in labels if query_lower in lbl.lower()]

            # Restore saved selection from localStorage
            ls_key = "tg_harvest_selected_channels"
            if "ls_channels_loaded" not in st.session_state:
                saved_raw = get_local_storage(ls_key)
                if saved_raw:
                    try:
                        saved_values = (
                            json.loads(saved_raw) if isinstance(saved_raw, str) else saved_raw
                        )
                    except (json.JSONDecodeError, TypeError):
                        saved_values = []
                    restored = [value_to_label[v] for v in saved_values if v in value_to_label]
                    if restored:
                        st.session_state["channel_multiselect"] = restored
                st.session_state["ls_channels_loaded"] = True

            # Default selection from prefill
            default_selection = []
            if prefill:
                for lbl in labels:
                    if channel_options[lbl] == prefill:
                        default_selection = [lbl]
                        break

            selected_labels = st.multiselect(
                t("parser.channel_multiselect_label"),
                labels,
                default=default_selection if default_selection else None,
                key="channel_multiselect",
            )
            channels_list = [channel_options[lbl] for lbl in selected_labels]

            # Sync selection to localStorage
            if channels_list:
                set_local_storage(ls_key, json.dumps(channels_list))
            else:
                set_local_storage(ls_key, "")
    else:
        channels_text = st.text_area(
            t("parser.channel_textarea_label"),
            value=prefill,
            placeholder=t("parser.channel_textarea_placeholder"),
            height=100,
        )
        channels_list = [ch.strip() for ch in channels_text.strip().splitlines() if ch.strip()]
        st.caption(t("parser.channel_load_hint"))

    if channels_list:
        st.caption(t("parser.queue_count", count=len(channels_list)))

    # Quick options on one line
    col1, col2 = st.columns(2)
    with col1:
        export_format = st.selectbox(
            t("parser.format_label"), ["json", "csv", "xlsx", "html", "all"]
        )
    with col2:
        incremental = st.checkbox(t("parser.incremental_label"), help=t("parser.incremental_help"))

    if incremental:
        st.caption(t("parser.incremental_caption"))

    # Date range — always visible with quick preset buttons
    st.markdown(t("parser.date_range_label"))

    today = date.today()
    year_start = date(today.year, 1, 1)
    preset_cols = st.columns(9)
    presets = [
        ("parser.preset_100", None, None, 100),
        ("parser.preset_1w", today - timedelta(weeks=1), today, 0),
        ("parser.preset_1m", today - timedelta(days=30), today, 0),
        ("parser.preset_6m", today - timedelta(days=182), today, 0),
        ("parser.preset_ytd", year_start, today, 0),
        ("parser.preset_1y", today - timedelta(days=365), today, 0),
        ("parser.preset_2y", today - timedelta(days=730), today, 0),
        ("parser.preset_3y", today - timedelta(days=1095), today, 0),
        ("parser.preset_all", None, None, 0),
    ]
    active_preset = st.session_state.get("active_preset")
    for i, (label_key, fd, td, lim) in enumerate(presets):
        with preset_cols[i]:
            btn_type = "primary" if active_preset == i else "secondary"
            if st.button(t(label_key), width="stretch", type=btn_type):
                st.session_state["from_date_input"] = fd
                st.session_state["to_date_input"] = td
                st.session_state["limit_input"] = lim
                st.session_state["active_preset"] = i
                st.rerun()

    date_col1, date_col2, date_col3 = st.columns(3)
    with date_col1:
        from_date = st.date_input(
            t("parser.from_date_label"),
            value=st.session_state.get("from_date_input"),
        )
    with date_col2:
        to_date = st.date_input(
            t("parser.to_date_label"),
            value=st.session_state.get("to_date_input"),
        )
    with date_col3:
        limit = st.number_input(
            t("parser.limit_label"),
            min_value=0,
            value=st.session_state.get("limit_input", 0),
            step=100,
        )

    # Extended options
    st.markdown(t("parser.extended_options_label"))
    ext_col1, ext_col2, ext_col3, ext_col4 = st.columns(4)
    with ext_col1:
        parse_text_only = st.checkbox(
            t("parser.parse_text_only_label"),
            help=t("parser.parse_text_only_help"),
        )
    with ext_col2:
        download_media = st.checkbox(
            t("parser.download_media_label"),
            help=t("parser.download_media_help"),
            disabled=parse_text_only,
        )
    with ext_col3:
        fetch_replies = st.checkbox(
            t("parser.fetch_replies_label"),
            help=t("parser.fetch_replies_help"),
            disabled=parse_text_only,
        )
    with ext_col4:
        enrich_senders = st.checkbox(
            t("parser.enrich_senders_label"),
            help=t("parser.enrich_senders_help"),
            disabled=parse_text_only,
        )

    max_media_size = 50
    if download_media:
        no_size_limit = st.checkbox(t("parser.no_media_size_limit"), value=False)
        if no_size_limit:
            max_media_size = 0
        else:
            max_media_size = st.slider(t("parser.max_media_size_label"), 1, 2048, 50)

    # Advanced options in expander
    with st.expander(t("parser.advanced_expander"), expanded=False):
        output_dir = st.text_input(t("parser.output_dir_label"), value=str(settings.output_dir))

        # Field selection
        select_all = st.checkbox(t("parser.fields_select_all"), value=True)
        if select_all:
            selected_fields = list(ALL_EXPORT_FIELDS)
        else:
            cols = st.columns(4)
            selected_fields = []
            for i, field in enumerate(ALL_EXPORT_FIELDS):
                with cols[i % 4]:
                    if st.checkbox(
                        field, value=field in ("id", "date", "text"), key=f"field_{field}"
                    ):
                        selected_fields.append(field)

        if not selected_fields:
            st.warning(t("parser.fields_warning"))

    st.info(t("parser.flood_wait_info"))
    st.info(t("parser.split_info"))

    # Parse button — show reason if disabled
    has_channels = bool(channels_list)
    if not has_channels:
        st.info(t("parser.empty_state_info"))
        st.caption(t("parser.empty_state_hint"))
    elif not selected_fields:
        st.warning(t("parser.fields_warning"))

    if st.button(
        t("parser.parse_button"),
        type="primary",
        disabled=not has_channels or not selected_fields,
        width="stretch",
    ):
        fields = selected_fields if not select_all else None
        options = ParseOptions(
            download_media=download_media and not parse_text_only,
            max_media_size_mb=max_media_size,
            fetch_replies=fetch_replies and not parse_text_only,
            enrich_senders=enrich_senders and not parse_text_only,
            text_only=parse_text_only,
        )
        _do_parse(
            settings,
            channels_list,
            from_date,
            to_date,
            int(limit),
            export_format,
            output_dir,
            incremental,
            fields,
            options,
        )

    # Show last results (multi-channel)
    if "last_parse_results" in st.session_state:
        for idx, res_entry in enumerate(st.session_state["last_parse_results"]):
            _show_result(res_entry["result"], res_entry["files"], suffix=f"_{idx}")
        # Download All section for multi-channel results
        if len(st.session_state["last_parse_results"]) > 1:
            _show_download_all(st.session_state["last_parse_results"])
    elif "last_parse_result" in st.session_state:
        _show_result(
            st.session_state["last_parse_result"],
            st.session_state.get("last_output_files", []),
        )


def _do_parse(
    settings,
    channels: list[str],
    from_date,
    to_date,
    limit,
    export_format,
    output_dir,
    incremental,
    fields,
    options: ParseOptions,
):
    st.session_state["parsing_active"] = True
    multi = len(channels) > 1
    try:
        with st.status(t("parser.status_label"), expanded=True) as status:
            status.update(label=t("parser.spinner_connecting"), state="running")
            progress_placeholder = st.empty()

            def on_progress(count: int) -> None:
                if limit > 0:
                    pct = min(int(count / limit * 100), 99)
                    msg = t("parser.progress_parsed", count=count)
                    progress_placeholder.progress(pct, text=msg)
                else:
                    progress_placeholder.markdown(t("parser.progress_parsed", count=count))

            try:
                all_results, errors = asyncio.run(
                    _parse_queue_async(
                        settings,
                        channels,
                        from_date,
                        to_date,
                        limit,
                        export_format,
                        output_dir,
                        incremental,
                        fields,
                        on_progress,
                        status,
                        options,
                    )
                )

                # Store results
                total_msgs = sum(r["result"]["total_messages"] for r in all_results)

                if multi:
                    st.session_state["last_parse_results"] = all_results
                    st.session_state.pop("last_parse_result", None)
                    st.session_state.pop("last_output_files", None)
                else:
                    if all_results:
                        st.session_state["last_parse_result"] = all_results[0]["result"]
                        st.session_state["last_output_files"] = all_results[0]["files"]
                    st.session_state.pop("last_parse_results", None)

                st.session_state["result_text_only"] = options.text_only

                if limit > 0:
                    progress_placeholder.progress(100, text=t("parser.progress_done"))

                # Show per-channel errors (non-fatal in multi mode)
                for err_channel, err in errors:
                    _show_parse_error(err, err_channel)

                if errors and not all_results:
                    status.update(label=t("parser.status_error"), state="error")
                    st.toast(t("parser.toast_error"), icon="\u274c")
                elif errors:
                    done_label = t(
                        "parser.queue_partial",
                        ok=len(all_results),
                        fail=len(errors),
                        total=total_msgs,
                    )
                    status.update(label=done_label, state="complete")
                    st.toast(t("parser.toast_success", count=total_msgs), icon="\u2705")
                elif multi:
                    done_label = t(
                        "parser.queue_complete", count=len(all_results), total=total_msgs
                    )
                    status.update(label=done_label, state="complete")
                    st.toast(t("parser.toast_success", count=total_msgs), icon="\u2705")
                else:
                    done_label = t("parser.success", count=total_msgs)
                    status.update(label=done_label, state="complete")
                    st.toast(t("parser.toast_success", count=total_msgs), icon="\u2705")

                _invalidate_data_caches()

            except Exception as e:
                status.update(label=t("parser.status_error"), state="error")
                _show_parse_error(e, channels[0] if channels else "?")
                st.toast(t("parser.toast_error"), icon="\u274c")
    finally:
        st.session_state["parsing_active"] = False


def _invalidate_data_caches():
    """Clear search and analytics result caches after a successful parse."""
    from tg_harvest.web.views.analytics import _load_results_cached as analytics_cache
    from tg_harvest.web.views.search import _load_results_cached as search_cache

    search_cache.clear()
    analytics_cache.clear()


def _show_parse_error(e: Exception, channel: str) -> None:
    """Categorize and display a user-friendly parse error."""
    cls_name = type(e).__name__
    err_str = str(e).lower()

    if cls_name == "FloodWaitError":
        seconds = getattr(e, "seconds", "?")
        st.error(t("parser.error_flood", seconds=seconds))
    elif cls_name in ("AuthKeyError", "UserNotParticipantError") or any(
        kw in err_str for kw in ("not authorized", "unauthorized", "session")
    ):
        st.error(t("parser.error_auth"))
    elif cls_name in (
        "UsernameInvalidError",
        "UsernameNotOccupiedError",
        "ChannelPrivateError",
        "ChatIdInvalidError",
    ) or any(kw in err_str for kw in ("no user", "no entity", "not found", "invalid username")):
        st.error(t("parser.error_not_found", channel=channel))
    elif any(kw in err_str for kw in ("connection", "timeout", "network", "socket")):
        st.error(t("parser.error_network"))
    else:
        st.error(t("parser.error_generic", error=e))


async def _parse_queue_async(
    settings,
    channels: list[str],
    from_date,
    to_date,
    limit,
    export_format,
    output_dir,
    incremental,
    fields,
    on_progress,
    status,
    options: ParseOptions,
):
    from tg_harvest.client.rate_limiter import RateLimiter
    from tg_harvest.client.session import TelegramSession
    from tg_harvest.exporters.csv_exporter import CsvExporter
    from tg_harvest.exporters.html_exporter import HtmlExporter
    from tg_harvest.exporters.json_exporter import JsonExporter
    from tg_harvest.exporters.xlsx_exporter import XlsxExporter
    from tg_harvest.parsers.channel_parser import ChannelParser
    from tg_harvest.storage.state import StateManager

    # Reject path traversal
    if ".." in Path(output_dir).parts:
        raise ValueError("Output directory must not contain '..' path components.")
    out_path = Path(output_dir).resolve()

    # Create date-stamped session folder
    session_dir = out_path / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    session_dir.mkdir(parents=True, exist_ok=True)

    fd = (
        datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
        if from_date
        else None
    )
    td = (
        datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc)
        if to_date
        else None
    )

    multi = len(channels) > 1
    state = StateManager(settings.state_path)
    all_results: list[dict] = []
    errors: list[tuple[str, Exception]] = []

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)

        for ch_idx, channel in enumerate(channels, 1):
            try:
                channel_id = int(channel) if channel.lstrip("-").isdigit() else channel
                min_id = 0

                if multi:
                    status.update(
                        label=t(
                            "parser.queue_progress",
                            current=ch_idx,
                            total=len(channels),
                            channel=channel,
                        ),
                        state="running",
                    )
                else:
                    status.update(label=t("parser.spinner_parsing"), state="running")

                if incremental:
                    info = await parser.get_channel_info(channel_id)
                    last_id = state.get_last_id(info.id)
                    if last_id:
                        min_id = last_id

                result = await parser.parse(
                    channel=channel_id,
                    from_date=fd,
                    to_date=td,
                    limit=limit if limit > 0 else 0,
                    min_id=min_id,
                    on_progress=on_progress,
                    options=options,
                )

                if result.messages:
                    max_msg_id = max(m.id for m in result.messages)
                    state.set_last_id(result.channel.id, max_msg_id)

                # Per-channel subfolder when multiple channels
                channel_out = session_dir
                if multi:
                    folder_name = result.channel.username or str(result.channel.id)
                    folder_name = "".join(
                        c if c.isalnum() or c in "-_" else "_" for c in folder_name
                    )
                    channel_out = session_dir / folder_name
                    channel_out.mkdir(parents=True, exist_ok=True)

                output_files = []
                if export_format in ("json", "all"):
                    path = await JsonExporter(fields).export(result, channel_out)
                    output_files.append(str(path))
                if export_format in ("csv", "all"):
                    path = await CsvExporter(fields).export(result, channel_out)
                    output_files.append(str(path))
                if export_format in ("xlsx", "all"):
                    path = await XlsxExporter(fields).export(result, channel_out)
                    output_files.append(str(path))
                if export_format in ("html", "all"):
                    path = await HtmlExporter(fields).export(result, channel_out)
                    output_files.append(str(path))

                all_results.append(
                    {
                        "result": result.model_dump(mode="json"),
                        "files": output_files,
                    }
                )
            except Exception as e:
                errors.append((channel, e))
                if not multi:
                    raise

    return all_results, errors


def _format_size(path: str) -> str:
    try:
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} B"
        return f"{size / 1024:.1f} KB"
    except OSError:
        return ""


def _show_result(result_data: dict, output_files: list[str], suffix: str = ""):
    st.divider()
    st.subheader(t("parser.results_subheader", title=result_data["channel"]["title"]))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("parser.metric_messages"), result_data["total_messages"])
    col2.metric(t("parser.metric_channel_id"), result_data["channel"]["id"])

    username = result_data["channel"].get("username")
    col3.metric(t("parser.metric_username"), f"@{username}" if username else "N/A")
    col4.metric(t("parser.metric_members"), result_data["channel"].get("members_count") or "N/A")

    if result_data["messages"]:
        display_msgs = result_data["messages"][-50:]

        text_only = st.checkbox(
            t("parser.text_only_label"),
            help=t("parser.text_only_help"),
            key=f"result_text_only{suffix}",
        )

        if text_only:
            rows = []
            for msg in display_msgs:
                rows.append({t("parser.col_text"): msg.get("text") or ""})
            st.dataframe(
                rows,
                column_config={
                    t("parser.col_text"): st.column_config.TextColumn(
                        t("parser.col_text"), width="large"
                    ),
                },
                width="stretch",
                hide_index=True,
            )
        else:
            rows = []
            for msg in display_msgs:
                rows.append(
                    {
                        t("parser.col_id"): msg["id"],
                        t("parser.col_date"): msg.get("date", ""),
                        t("parser.col_text"): truncate(msg.get("text"), limit=200),
                        t("parser.col_views"): msg.get("views") or 0,
                        t("parser.col_forwards"): msg.get("forwards") or 0,
                        t("parser.col_reactions"): msg.get("reactions", {}).get("total", 0)
                        if msg.get("reactions")
                        else 0,
                        t("parser.col_media"): msg.get("media", {}).get("type", "")
                        if msg.get("media")
                        else "",
                        t("parser.col_pinned"): msg.get("is_pinned", False),
                    }
                )

            st.dataframe(
                rows,
                column_config={
                    t("parser.col_id"): st.column_config.NumberColumn(
                        t("parser.col_id"), format="%d"
                    ),
                    t("parser.col_date"): t("parser.col_date"),
                    t("parser.col_text"): st.column_config.TextColumn(
                        t("parser.col_text"), width="large"
                    ),
                    t("parser.col_views"): st.column_config.NumberColumn(
                        t("parser.col_views"), format="%d"
                    ),
                    t("parser.col_forwards"): st.column_config.NumberColumn(
                        t("parser.col_forwards"), format="%d"
                    ),
                    t("parser.col_reactions"): st.column_config.NumberColumn(
                        t("parser.col_reactions"), format="%d"
                    ),
                    t("parser.col_media"): t("parser.col_media"),
                    t("parser.col_pinned"): st.column_config.CheckboxColumn(t("parser.col_pinned")),
                },
                width="stretch",
                hide_index=True,
            )

        if len(result_data["messages"]) > 50:
            st.caption(t("parser.table_truncated", shown=50, total=len(result_data["messages"])))

        # Message detail viewer
        with st.expander(t("parser.message_detail_expander")):
            msg_ids = [msg["id"] for msg in display_msgs]
            selected_msg_id = st.selectbox(
                t("parser.message_detail_id_label"),
                msg_ids,
                key=f"message_detail_select{suffix}",
            )
            for msg in display_msgs:
                if msg["id"] == selected_msg_id:
                    st.markdown(f"**{t('parser.col_date')}:** {msg.get('date', '')}")
                    st.text_area(
                        t("parser.col_text"),
                        value=msg.get("text") or "",
                        height=200,
                        disabled=True,
                        key=f"message_detail_text{suffix}",
                    )
                    if msg.get("media"):
                        st.json(msg["media"])
                    break

    if output_files:
        st.markdown(t("parser.exported_files_label"))
        for f in output_files:
            size = _format_size(f)
            st.code(f"{f}  ({size})" if size else f)

    base_name = result_data["channel"].get("username") or str(result_data["channel"]["id"])

    # Split selector — only affects downloads, no re-parsing needed
    split_col1, split_col2 = st.columns([1, 3])
    with split_col1:
        split_parts = st.number_input(
            t("parser.split_parts_label"),
            min_value=1,
            max_value=20,
            value=1,
            help=t("parser.split_parts_help"),
            key=f"download_split_parts{suffix}",
        )

    if split_parts > 1:
        _show_split_downloads(result_data, base_name, int(split_parts), text_only, suffix)
    elif text_only:
        txt_data = _build_txt(result_data)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                t("parser.download_txt"),
                data=txt_data,
                file_name=f"{base_name}.txt",
                mime="text/plain",
                key=f"dl_txt{suffix}",
            )
        with col2:
            csv_data = _build_text_only_csv(result_data)
            st.download_button(
                t("parser.download_csv"),
                data=csv_data,
                file_name=f"{base_name}_text.csv",
                mime="text/csv",
                key=f"dl_csv_text{suffix}",
            )
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.download_button(
                t("parser.download_json"),
                data=json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
                file_name=f"{base_name}.json",
                mime="application/json",
                key=f"dl_json{suffix}",
            )

        with col2:
            csv_data = _build_csv(result_data)
            st.download_button(
                t("parser.download_csv"),
                data=csv_data,
                file_name=f"{base_name}.csv",
                mime="text/csv",
                key=f"dl_csv{suffix}",
            )

        with col3:
            xlsx_data = _build_xlsx(result_data)
            if xlsx_data:
                st.download_button(
                    t("parser.download_xlsx"),
                    data=xlsx_data,
                    file_name=f"{base_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_xlsx{suffix}",
                )

        with col4:
            html_data = _build_html(result_data)
            if html_data:
                st.download_button(
                    t("parser.download_html"),
                    data=html_data,
                    file_name=f"{base_name}.html",
                    mime="text/html",
                    key=f"dl_html{suffix}",
                )


def _split_messages(messages: list[dict], parts: int) -> list[list[dict]]:
    """Split message dicts into roughly-equal chunks (mirrors splitter.split_messages)."""
    if parts <= 1 or not messages:
        return [messages]
    total = len(messages)
    chunk_size, remainder = divmod(total, parts)
    chunks: list[list[dict]] = []
    offset = 0
    for i in range(parts):
        size = chunk_size + (1 if i < remainder else 0)
        chunk = messages[offset : offset + size]
        if chunk:
            chunks.append(chunk)
        offset += size
    return chunks


def _show_split_downloads(
    result_data: dict, base_name: str, split_parts: int, text_only: bool, suffix: str = ""
):
    """Build zip downloads with split parts."""
    messages = result_data.get("messages", [])
    chunks = _split_messages(messages, split_parts)
    total_parts = len(chunks)

    def _make_part_data(chunk: list[dict]) -> dict:
        return {**result_data, "messages": chunk}

    def _build_format_zip(ext: str, builder) -> bytes | None:
        buf = io.BytesIO()
        has_content = False
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, chunk in enumerate(chunks, 1):
                part_data = _make_part_data(chunk)
                content = builder(part_data)
                if content is None:
                    continue
                fname = f"{base_name}_part{idx}of{total_parts}.{ext}"
                if isinstance(content, bytes):
                    zf.writestr(fname, content)
                else:
                    zf.writestr(fname, content)
                has_content = True
        return buf.getvalue() if has_content else None

    if text_only:
        col1, col2 = st.columns(2)
        with col1:
            zip_data = _build_format_zip("txt", _build_txt)
            if zip_data:
                st.download_button(
                    t("parser.download_txt_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_txt.zip",
                    mime="application/zip",
                    key=f"dl_txt_zip{suffix}",
                )
        with col2:
            zip_data = _build_format_zip("csv", _build_text_only_csv)
            if zip_data:
                st.download_button(
                    t("parser.download_csv_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_csv.zip",
                    mime="application/zip",
                    key=f"dl_csv_txt_zip{suffix}",
                )
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            zip_data = _build_format_zip(
                "json",
                lambda d: json.dumps(d, ensure_ascii=False, indent=2, default=str),
            )
            if zip_data:
                st.download_button(
                    t("parser.download_json_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_json.zip",
                    mime="application/zip",
                    key=f"dl_json_zip{suffix}",
                )
        with col2:
            zip_data = _build_format_zip("csv", _build_csv)
            if zip_data:
                st.download_button(
                    t("parser.download_csv_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_csv.zip",
                    mime="application/zip",
                    key=f"dl_csv_zip{suffix}",
                )
        with col3:
            zip_data = _build_format_zip("xlsx", _build_xlsx)
            if zip_data:
                st.download_button(
                    t("parser.download_xlsx_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_xlsx.zip",
                    mime="application/zip",
                    key=f"dl_xlsx_zip{suffix}",
                )
        with col4:
            zip_data = _build_format_zip("html", _build_html)
            if zip_data:
                st.download_button(
                    t("parser.download_html_zip"),
                    data=zip_data,
                    file_name=f"{base_name}_html.zip",
                    mime="application/zip",
                    key=f"dl_html_zip{suffix}",
                )


def _show_download_all(all_results: list[dict]):
    """Show a unified 'Download All' section for multi-channel results."""
    st.divider()
    st.subheader(t("parser.download_all_header"))

    split_col1, split_col2 = st.columns([1, 3])
    with split_col1:
        split_parts = st.number_input(
            t("parser.split_parts_label"),
            min_value=1,
            max_value=20,
            value=1,
            help=t("parser.download_all_split_help"),
            key="download_all_split_parts",
        )

    fmt_col1, fmt_col2, fmt_col3, fmt_col4 = st.columns(4)

    def _build_all_zip(ext: str, builder) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in all_results:
                result_data = entry["result"]
                ch_name = result_data["channel"].get("username") or str(
                    result_data["channel"]["id"]
                )
                folder = "".join(c if c.isalnum() or c in "-_" else "_" for c in ch_name)
                messages = result_data.get("messages", [])
                chunks = _split_messages(messages, int(split_parts))
                total_parts = len(chunks)
                for idx, chunk in enumerate(chunks, 1):
                    part_data = {**result_data, "messages": chunk}
                    content = builder(part_data)
                    if content is None:
                        continue
                    if total_parts > 1:
                        fname = f"{folder}/{folder}_part{idx}of{total_parts}.{ext}"
                    else:
                        fname = f"{folder}/{folder}.{ext}"
                    if isinstance(content, bytes):
                        zf.writestr(fname, content)
                    else:
                        zf.writestr(fname, content)
        return buf.getvalue()

    with fmt_col1:
        zip_data = _build_all_zip("txt", _build_txt)
        st.download_button(
            t("parser.download_all_txt"),
            data=zip_data,
            file_name="all_channels_txt.zip",
            mime="application/zip",
            key="dl_all_txt",
        )

    with fmt_col2:
        zip_data = _build_all_zip(
            "json",
            lambda d: json.dumps(d, ensure_ascii=False, indent=2, default=str),
        )
        st.download_button(
            t("parser.download_all_json"),
            data=zip_data,
            file_name="all_channels_json.zip",
            mime="application/zip",
            key="dl_all_json",
        )

    with fmt_col3:
        zip_data = _build_all_zip("csv", _build_csv)
        st.download_button(
            t("parser.download_all_csv"),
            data=zip_data,
            file_name="all_channels_csv.zip",
            mime="application/zip",
            key="dl_all_csv",
        )

    with fmt_col4:
        zip_data = _build_all_zip("xlsx", _build_xlsx)
        if zip_data:
            st.download_button(
                t("parser.download_all_xlsx"),
                data=zip_data,
                file_name="all_channels_xlsx.zip",
                mime="application/zip",
                key="dl_all_xlsx",
            )


def _build_txt(result_data: dict) -> str:
    lines = []
    for msg_data in result_data.get("messages", []):
        text = msg_data.get("text") or ""
        if text.strip():
            lines.append(text.strip())
    return "\n".join(lines)


def _build_text_only_csv(result_data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["text"])
    for msg_data in result_data.get("messages", []):
        text = msg_data.get("text") or ""
        if text.strip():
            writer.writerow([text.strip()])
    return output.getvalue()


def _build_csv(result_data: dict) -> str:
    from tg_harvest.models.message import ParsedMessage

    output = io.StringIO()
    fields = list(ALL_EXPORT_FIELDS)
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for msg_data in result_data.get("messages", []):
        try:
            msg = ParsedMessage.model_validate(msg_data)
            row = filter_fields(build_row(msg), fields)
            writer.writerow(row)
        except (ValueError, KeyError, TypeError):
            continue

    return output.getvalue()


def _build_xlsx(result_data: dict) -> bytes | None:
    try:
        from openpyxl import Workbook

        from tg_harvest.models.message import ParsedMessage

        wb = Workbook()
        ws = wb.active
        ws.title = "Messages"

        fields = list(ALL_EXPORT_FIELDS)
        ws.append(fields)

        for msg_data in result_data.get("messages", []):
            try:
                msg = ParsedMessage.model_validate(msg_data)
                row = filter_fields(build_row(msg), fields)
                ws.append([row.get(f, "") for f in fields])
            except (ValueError, KeyError, TypeError):
                continue

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    except ImportError:
        return None


def _build_html(result_data: dict) -> str | None:
    try:
        from tg_harvest.exporters.html_exporter import HtmlExporter
        from tg_harvest.models.parse_result import ParseResult

        result = ParseResult.model_validate(result_data)
        exporter = HtmlExporter()
        return exporter._render(result)
    except (ValueError, ImportError):
        return None
