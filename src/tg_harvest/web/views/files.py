"""File Manager page — view, delete, re-export parsed files."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from tg_harvest.config import Settings
from tg_harvest.web.i18n import t

logger = logging.getLogger(__name__)


def render():
    st.header(t("files.header"))
    st.caption(t("files.caption"))

    try:
        settings = Settings()
    except Exception as e:
        st.error(f"Settings error: {e}")
        return

    output_dir = settings.output_dir
    if not output_dir.exists():
        st.warning(t("files.no_dir_warning"))
        return

    files = _scan_files(output_dir)

    if not files:
        st.warning(t("files.no_files_warning"))
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(t("files.metric_total_files"), len(files))
    total_size = sum(f["size_bytes"] for f in files)
    col2.metric(t("files.metric_total_size"), _format_size(total_size))
    json_count = sum(1 for f in files if f["ext"] == ".json")
    col3.metric(t("files.metric_json_files"), json_count)

    # File table
    rows = []
    for f in files:
        rows.append(
            {
                t("files.col_name"): f["name"],
                t("files.col_channel"): f.get("channel_title", ""),
                t("files.col_format"): f["ext"].lstrip(".").upper(),
                t("files.col_messages"): f.get("message_count", ""),
                t("files.col_size"): _format_size(f["size_bytes"]),
                t("files.col_date"): f["modified"],
            }
        )

    st.dataframe(rows, width="stretch", hide_index=True)

    # Actions
    st.divider()
    st.subheader(t("files.actions_subheader"))

    file_names = [f["name"] for f in files]
    selected_file = st.selectbox(t("files.select_file_label"), file_names)

    col1, col2 = st.columns(2)

    with col1:
        selected_info = next((f for f in files if f["name"] == selected_file), None)
        if selected_info and selected_info["ext"] == ".json":
            target_format = st.selectbox(
                t("files.reexport_format_label"),
                ["csv", "xlsx", "html"],
            )
            if st.button(t("files.reexport_button"), type="primary"):
                _do_reexport(output_dir / selected_file, target_format)

    with col2:
        if st.button(t("files.delete_button"), type="secondary"):
            _do_delete(output_dir / selected_file)


def _scan_files(output_dir: Path) -> list[dict]:
    """Scan output directory for parsed files."""
    files: list[dict] = []
    for ext in ("*.json", "*.csv", "*.xlsx", "*.html"):
        for f in output_dir.glob(ext):
            stat = f.stat()
            mod_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            info: dict = {
                "name": f.name,
                "ext": f.suffix,
                "size_bytes": stat.st_size,
                "modified": mod_dt.strftime("%Y-%m-%d %H:%M"),
                "channel_title": "",
                "message_count": "",
            }
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    info["channel_title"] = data.get("channel", {}).get("title", "")
                    info["message_count"] = data.get(
                        "total_messages", len(data.get("messages", []))
                    )
                except (json.JSONDecodeError, KeyError, TypeError):
                    logger.debug("Failed to read metadata from %s", f.name, exc_info=True)
            files.append(info)
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


def _do_reexport(json_path: Path, target_format: str):
    """Re-export a JSON file to another format."""
    try:
        from tg_harvest.models.parse_result import ParseResult

        data = json.loads(json_path.read_text(encoding="utf-8"))
        result = ParseResult.model_validate(data)

        async def _run_export():
            if target_format == "csv":
                from tg_harvest.exporters.csv_exporter import CsvExporter

                return await CsvExporter().export(result, json_path.parent)
            elif target_format == "xlsx":
                from tg_harvest.exporters.xlsx_exporter import XlsxExporter

                return await XlsxExporter().export(result, json_path.parent)
            elif target_format == "html":
                from tg_harvest.exporters.html_exporter import HtmlExporter

                return await HtmlExporter().export(result, json_path.parent)
            return None

        out = asyncio.run(_run_export())
        st.success(t("files.reexport_success", path=str(out)))
        st.rerun()
    except Exception as e:
        st.error(t("files.reexport_error", error=e))


def _do_delete(file_path: Path):
    """Delete a file."""
    try:
        file_path.unlink()
        st.success(t("files.delete_success", name=file_path.name))
        st.rerun()
    except Exception as e:
        st.error(t("files.delete_error", error=e))


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
