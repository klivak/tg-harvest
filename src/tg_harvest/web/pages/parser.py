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


def render():
    st.header("Parse Channel")
    st.caption("Step 3 — extract messages from a Telegram channel or group")

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    # Channel input
    col1, col2 = st.columns([3, 1])
    with col1:
        channel = st.text_input(
            "Channel",
            placeholder="@channel_name or numeric ID",
        )
    with col2:
        incremental = st.checkbox("Incremental", help="Only fetch new messages since last parse")

    if incremental:
        st.caption("Will fetch only messages newer than the last parse.")

    # Date range
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From date", value=None)
    with col2:
        to_date = st.date_input("To date", value=None)

    # Options
    col1, col2, col3 = st.columns(3)
    with col1:
        limit = st.number_input("Message limit (0 = no limit)", min_value=0, value=0, step=100)
    with col2:
        export_format = st.selectbox("Export format", ["json", "csv", "xlsx", "all"])
    with col3:
        output_dir = st.text_input("Output directory", value=str(settings.output_dir))

    # Field selection
    with st.expander("Field selection (select which fields to export)"):
        select_all = st.checkbox("Select all fields", value=True)
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
            st.warning("Select at least one field.")

    # Parse button
    if not channel:
        st.info("Enter a channel username (@channel) or numeric ID to start parsing.")

    if st.button("Parse", type="primary", disabled=not channel or not selected_fields):
        fields = selected_fields if not select_all else None
        _do_parse(
            settings,
            channel,
            from_date,
            to_date,
            limit,
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
    progress_bar = st.progress(0, text="Connecting...")
    status = st.empty()

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
                progress_bar,
                status,
            )
        )
        st.session_state["last_parse_result"] = result.model_dump(mode="json")
        st.session_state["last_output_files"] = output_files
        progress_bar.progress(100, text="Done!")
        status.success(f"Parsed {result.total_messages} messages")
    except Exception as e:
        progress_bar.empty()
        st.error(f"Parse error: {e}")


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
    progress_bar,
    status,
):
    from tg_harvest.client.rate_limiter import RateLimiter
    from tg_harvest.client.session import TelegramSession
    from tg_harvest.exporters.csv_exporter import CsvExporter
    from tg_harvest.exporters.json_exporter import JsonExporter
    from tg_harvest.exporters.xlsx_exporter import XlsxExporter
    from tg_harvest.parsers.channel_parser import ChannelParser
    from tg_harvest.storage.state import StateManager

    out_path = Path(output_dir)

    # Convert dates
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

    # Resolve channel
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

        status.info("Parsing messages...")

        msg_count = [0]

        def on_progress(count):
            msg_count[0] = count
            if count % 10 == 0:
                progress_bar.progress(min(count % 100, 99), text=f"Parsed {count} messages...")

        result = await parser.parse(
            channel=channel_id,
            from_date=fd,
            to_date=td,
            limit=limit if limit > 0 else 0,
            min_id=min_id,
            on_progress=on_progress,
        )

        # Update state
        if result.messages:
            max_msg_id = max(m.id for m in result.messages)
            state.set_last_id(result.channel.id, max_msg_id)

        # Export
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
    """Format file size for display."""
    try:
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} B"
        return f"{size / 1024:.1f} KB"
    except OSError:
        return ""


def _show_result(result_data: dict, output_files: list[str]):
    st.divider()
    st.subheader(f"Results: {result_data['channel']['title']}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Messages", result_data["total_messages"])
    col2.metric("Channel ID", result_data["channel"]["id"])

    username = result_data["channel"].get("username")
    col3.metric("Username", f"@{username}" if username else "private")
    col4.metric("Members", result_data["channel"].get("members_count") or "N/A")

    # Messages table
    if result_data["messages"]:
        rows = []
        for msg in result_data["messages"]:
            rows.append(
                {
                    "ID": msg["id"],
                    "Date": msg.get("date", ""),
                    "Text": (msg["text"][:100] + "...")
                    if len(msg.get("text", "")) > 100
                    else msg.get("text", ""),
                    "Views": msg.get("views") or 0,
                    "Forwards": msg.get("forwards") or 0,
                    "Reactions": msg.get("reactions", {}).get("total", 0)
                    if msg.get("reactions")
                    else 0,
                    "Media": msg.get("media", {}).get("type", "") if msg.get("media") else "",
                    "Pinned": msg.get("is_pinned", False),
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)

    # Exported files with sizes
    if output_files:
        st.markdown("**Exported files:**")
        for f in output_files:
            size = _format_size(f)
            st.code(f"{f}  ({size})" if size else f)

    # Download buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download JSON",
            data=json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
            file_name=(
                f"{result_data['channel'].get('username', result_data['channel']['id'])}.json"
            ),
            mime="application/json",
        )

    with col2:
        csv_data = _build_csv(result_data)
        st.download_button(
            "Download CSV",
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
                "Download XLSX",
                data=xlsx_data,
                file_name=(
                    f"{result_data['channel'].get('username', result_data['channel']['id'])}.xlsx"
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


def _build_csv(result_data: dict) -> str:
    """Build CSV string from result data for download."""
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
    """Build XLSX bytes from result data for download."""
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
