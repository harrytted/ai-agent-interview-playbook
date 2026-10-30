"""The fictional business timezone is explicitly UTC+08:00."""

from datetime import datetime, timedelta, timezone


def business_date(iso_datetime: str) -> str:
    value = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("a timezone-aware timestamp is required")
    return value.astimezone(timezone(timedelta(hours=8))).date().isoformat()
