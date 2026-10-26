"""Timestamp parsing / timezone helpers.

All internal datetimes are timezone-aware (UTC). The Elexon API returns ISO
8601 timestamps with explicit offsets (normally ``Z``). For January 2026 the
UK is on GMT, which coincides with UTC; the API/UI therefore display UTC and
document that UTC == UK local time for the analysis window, without hardcoding
a Europe/London assumption into the calculations.
"""

from __future__ import annotations

from datetime import datetime, timezone


def parse_elexon_timestamp(value: object) -> datetime | None:
    """Parse an Elexon timestamp into an aware UTC datetime.

    Returns ``None`` for missing/unparseable values so callers can skip the
    record instead of silently coercing it to a wrong value.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    # Python's fromisoformat does not accept a bare "Z" suffix.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_generation(value: object) -> float | None:
    """Parse a generation value (MW). Returns ``None`` when missing/invalid."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    # NaN / infinities are not usable measurements.
    if number != number or number in (float("inf"), float("-inf")):
        return None
    if number < 0:
        # Negative generation is physically meaningless here; treat as invalid
        # rather than silently clamping to zero.
        return None
    return number


def to_iso_z(dt: datetime) -> str:
    """Format an aware datetime as ISO 8601 with ``Z`` suffix."""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
