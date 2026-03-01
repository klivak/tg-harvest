"""Parse page — main parsing interface."""

import asyncio
import csv
import io
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

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

    with st.expander(t("parser.tips_expander"), expanded=False):
        st.markdown(t("parser.tips_body"))

    # Channel input — selectbox from loaded channels, or manual text input
    prefill = st.session_state.pop("prefill_channel", "")
    loaded_channels = st.session_state.get("channels", [])

    if loaded_channels:
        # Build options: "Title (@username)" -> "@username" or "Title (ID: 123)" -> "123"
        channel_options: dict[str, str] = {}
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

        manual_mode = st.checkbox(t("parser.channel_manual_toggle"))

        if manual_mode:
            channel = st.text_input(
                t("parser.channel_manual_label"),
                value=prefill,
                placeholder=t("parser.channel_placeholder"),
            )
        else:
            labels = list(channel_options.keys())
            # If prefilled, find matching index
            default_idx = 0
            if prefill:
                for i, lbl in enumerate(labels):
                    if channel_options[lbl] == prefill:
                        default_idx = i
                        break
            selected_label = st.selectbox(
                t("parser.channel_select_label"),
                labels,
                index=default_idx,
            )
            channel = channel_options[selected_label]
    else:
        channel = st.text_input(
            t("parser.channel_label"),
            value=prefill,
            placeholder=t("parser.channel_placeholder"),
        )
        st.caption(t("parser.channel_load_hint"))

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
        max_media_size = st.slider(t("parser.max_media_size_label"), 1, 200, 50)

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

    # Parse button — show reason if disabled
    if not channel:
        st.info(t("parser.empty_state_info"))
        st.caption(t("parser.empty_state_hint"))
    elif not selected_fields:
        st.warning(t("parser.fields_warning"))

    if st.button(
        t("parser.parse_button"),
        type="primary",
        disabled=not channel or not selected_fields,
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
            channel,
            from_date,
            to_date,
            int(limit),
            export_format,
            output_dir,
            incremental,
            fields,
            options,
        )

    # Show last result
    if "last_parse_result" in st.session_state:
        _show_result(
            st.session_state["last_parse_result"],
            st.session_state.get("last_output_files", []),
        )


def _do_parse(
    settings,
    channel,
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
                result, output_files = asyncio.run(
                    _parse_async(
                        settings,
                        channel,
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
                st.session_state["last_parse_result"] = result.model_dump(mode="json")
                st.session_state["last_output_files"] = output_files
                st.session_state["result_text_only"] = options.text_only

                if limit > 0:
                    progress_placeholder.progress(100, text=t("parser.progress_done"))

                done_label = t("parser.success", count=result.total_messages)
                status.update(label=done_label, state="complete")
                st.toast(t("parser.toast_success", count=result.total_messages), icon="\u2705")

                # Invalidate search/analytics caches so they pick up new data
                _invalidate_data_caches()

            except Exception as e:
                status.update(label=t("parser.status_error"), state="error")
                _show_parse_error(e, channel)
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


async def _parse_async(
    settings,
    channel,
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

    channel_id = int(channel) if channel.lstrip("-").isdigit() else channel

    state = StateManager(settings.state_path)
    min_id = 0

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)

        if incremental:
            info = await parser.get_channel_info(channel_id)
            last_id = state.get_last_id(info.id)
            if last_id:
                min_id = last_id

        status.update(label=t("parser.spinner_parsing"), state="running")

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

        output_files = []
        if export_format in ("json", "all"):
            path = await JsonExporter(fields).export(result, out_path)
            output_files.append(str(path))
        if export_format in ("csv", "all"):
            path = await CsvExporter(fields).export(result, out_path)
            output_files.append(str(path))
        if export_format in ("xlsx", "all"):
            path = await XlsxExporter(fields).export(result, out_path)
            output_files.append(str(path))
        if export_format in ("html", "all"):
            path = await HtmlExporter(fields).export(result, out_path)
            output_files.append(str(path))

        return result, output_files


def _format_size(path: str) -> str:
    try:
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} B"
        return f"{size / 1024:.1f} KB"
    except OSError:
        return ""


def _show_result(result_data: dict, output_files: list[str]):
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
            key="result_text_only",
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
                key="message_detail_select",
            )
            for msg in display_msgs:
                if msg["id"] == selected_msg_id:
                    st.markdown(f"**{t('parser.col_date')}:** {msg.get('date', '')}")
                    st.text_area(
                        t("parser.col_text"),
                        value=msg.get("text") or "",
                        height=200,
                        disabled=True,
                    )
                    if msg.get("media"):
                        st.json(msg["media"])
                    break

    if output_files:
        st.markdown(t("parser.exported_files_label"))
        for f in output_files:
            size = _format_size(f)
            st.code(f"{f}  ({size})" if size else f)

    base_name = result_data["channel"].get("username", result_data["channel"]["id"])

    if text_only:
        txt_data = _build_txt(result_data)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                t("parser.download_txt"),
                data=txt_data,
                file_name=f"{base_name}.txt",
                mime="text/plain",
            )
        with col2:
            csv_data = _build_text_only_csv(result_data)
            st.download_button(
                t("parser.download_csv"),
                data=csv_data,
                file_name=f"{base_name}_text.csv",
                mime="text/csv",
            )
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.download_button(
                t("parser.download_json"),
                data=json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
                file_name=f"{base_name}.json",
                mime="application/json",
            )

        with col2:
            csv_data = _build_csv(result_data)
            st.download_button(
                t("parser.download_csv"),
                data=csv_data,
                file_name=f"{base_name}.csv",
                mime="text/csv",
            )

        with col3:
            xlsx_data = _build_xlsx(result_data)
            if xlsx_data:
                st.download_button(
                    t("parser.download_xlsx"),
                    data=xlsx_data,
                    file_name=f"{base_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        with col4:
            html_data = _build_html(result_data)
            if html_data:
                st.download_button(
                    t("parser.download_html"),
                    data=html_data,
                    file_name=f"{base_name}.html",
                    mime="text/html",
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
