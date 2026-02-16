"""Date parsing and timezone utilities."""

from datetime import datetime, timezone


def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format to UTC datetime."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime has UTC timezone info."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
