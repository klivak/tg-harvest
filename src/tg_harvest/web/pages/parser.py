"""Parse page — main parsing interface."""

import asyncio
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.config.constants import ALL_EXPORT_FIELDS
from tg_harvest.exporters.base import build_row, filter_fields
from tg_harvest.web.i18n import t


def _truncate(text: str | None, limit: int = 100) -> str:
    if not text:
        return ""
    return (text[:limit] + "...") if len(text) > limit else text


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

    # Channel input
    col1, col2 = st.columns([3, 1])
    with col1:
        channel = st.text_input(
            t("parser.channel_label"),
            placeholder=t("parser.channel_placeholder"),
        )
    with col2:
        incremental = st.checkbox(t("parser.incremental_label"), help=t("parser.incremental_help"))

    if incremental:
        st.caption(t("parser.incremental_caption"))

    # Date range
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input(t("parser.from_date_label"), value=None)
    with col2:
        to_date = st.date_input(t("parser.to_date_label"), value=None)

    # Options
    col1, col2, col3 = st.columns(3)
    with col1:
        limit = st.number_input(t("parser.limit_label"), min_value=0, value=0, step=100)
    with col2:
        export_format = st.selectbox(t("parser.format_label"), ["json", "csv", "xlsx", "all"])
    with col3:
        output_dir = st.text_input(t("parser.output_dir_label"), value=str(settings.output_dir))

    # Field selection
    with st.expander(t("parser.fields_expander")):
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

    # Parse button
    if not channel:
        st.info(t("parser.empty_state_info"))
        st.caption(t("parser.empty_state_hint"))

    if st.button(
        t("parser.parse_button"), type="primary", disabled=not channel or not selected_fields
    ):
        fields = selected_fields if not select_all else None
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
        )

    # Show last result
    if "last_parse_result" in st.session_state:
        _show_result(
            st.session_state["last_parse_result"],
            st.session_state.get("last_output_files", []),
        )


def _do_parse(
    settings, channel, from_date, to_date, limit, export_format, output_dir, incremental, fields
):
    # Two-path progress: real bar if limit known, counter text if unlimited
    if limit > 0:
        progress_bar = st.progress(0, text=t("parser.spinner_connecting"))
        status = st.empty()
    else:
        progress_bar = None
        status = st.empty()
        status.info(t("parser.spinner_connecting"))

    def on_progress(count: int) -> None:
        if limit > 0:
            pct = min(int(count / limit * 100), 99)
            progress_bar.progress(pct, text=t("parser.progress_parsed", count=count))
        else:
            if count % 10 == 0:
                status.info(t("parser.progress_parsed", count=count))

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
            )
        )
        st.session_state["last_parse_result"] = result.model_dump(mode="json")
        st.session_state["last_output_files"] = output_files
        if progress_bar is not None:
            progress_bar.progress(100, text=t("parser.progress_done"))
        status.success(t("parser.success", count=result.total_messages))
    except Exception as e:
        if progress_bar is not None:
            progress_bar.empty()
        status.empty()
        _show_parse_error(e, channel)


def _show_parse_error(e: Exception, channel: str) -> None:
    """Categorize and display a user-friendly parse error."""
    # Check for flood wait via class name (avoids direct Telethon import in web layer)
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
):
    from tg_harvest.client.rate_limiter import RateLimiter
    from tg_harvest.client.session import TelegramSession
    from tg_harvest.exporters.csv_exporter import CsvExporter
    from tg_harvest.exporters.json_exporter import JsonExporter
    from tg_harvest.exporters.xlsx_exporter import XlsxExporter
    from tg_harvest.parsers.channel_parser import ChannelParser
    from tg_harvest.storage.state import StateManager

    out_path = Path(output_dir).resolve()
    if ".." in Path(output_dir).parts:
        raise ValueError("Output directory must not contain '..' path components.")

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

        status.info(t("parser.spinner_parsing"))

        result = await parser.parse(
            channel=channel_id,
            from_date=fd,
            to_date=td,
            limit=limit if limit > 0 else 0,
            min_id=min_id,
            on_progress=on_progress,
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
    col3.metric(t("parser.metric_username"), f"@{username}" if username else t("parser.col_id"))
    col4.metric(t("parser.metric_members"), result_data["channel"].get("members_count") or "N/A")

    if result_data["messages"]:
        rows = []
        for msg in result_data["messages"]:
            rows.append(
                {
                    t("parser.col_id"): msg["id"],
                    t("parser.col_date"): msg.get("date", ""),
                    t("parser.col_text"): _truncate(msg.get("text")),
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
                t("parser.col_id"): st.column_config.NumberColumn(t("parser.col_id"), format="%d"),
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
            use_container_width=True,
            hide_index=True,
        )

    if output_files:
        st.markdown(t("parser.exported_files_label"))
        for f in output_files:
            size = _format_size(f)
            st.code(f"{f}  ({size})" if size else f)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            t("parser.download_json"),
            data=json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
            file_name=(
                f"{result_data['channel'].get('username', result_data['channel']['id'])}.json"
            ),
            mime="application/json",
        )

    with col2:
        csv_data = _build_csv(result_data)
        st.download_button(
            t("parser.download_csv"),
            data=csv_data,
            file_name=(
                f"{result_data['channel'].get('username', result_data['channel']['id'])}.csv"
            ),
            mime="text/csv",
        )

    with col3:
        xlsx_data = _build_xlsx(result_data)
        if xlsx_data:
            st.download_button(
                t("parser.download_xlsx"),
                data=xlsx_data,
                file_name=(
                    f"{result_data['channel'].get('username', result_data['channel']['id'])}.xlsx"
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


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
        except Exception:
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
            except Exception:
                continue

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    except ImportError:
        return None
