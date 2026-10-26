"""Day-ahead forecast selection logic (pure, independently testable).

Rule (uniform for every interval of the delivery day D):
1. Consider all valid forecasts for a ``startTime``.
2. Keep only those with ``publishTime <= decision_cutoff(D)`` where
   ``decision_cutoff(D) = (D - 1 day) at DECISION_CUTOFF_TIME_UTC``.
3. Select the eligible forecast with the latest ``publishTime``.
4. Tie-break: if several records share the same ``publishTime`` for the same
   ``startTime``, pick the one with the highest ``generation`` (deterministic;
   duplicates from the API are otherwise identical).
5. If no eligible forecast exists, the interval is reported as unavailable
   (never back-filled with a later forecast).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from app.config import settings


def decision_cutoff_for(delivery: date) -> datetime:
    """Return the purchasing-decision cutoff (aware UTC) for a delivery day."""
    hour, minute = (settings.decision_cutoff_time_utc.split(":") + ["0"])[:2]
    cutoff_time = time(int(hour), int(minute), tzinfo=timezone.utc)
    return datetime.combine(delivery - timedelta(days=1), cutoff_time).astimezone(
        timezone.utc
    )


def select_day_ahead_forecasts(
    forecasts: list[dict[str, Any]], cutoff: datetime
) -> dict[datetime, dict[str, Any]]:
    """Select the latest eligible forecast per ``startTime``.

    Pure function: no I/O, no network. ``forecasts`` items must contain
    ``startTime`` / ``publishTime`` (aware datetimes) / ``generation``.
    Records with naive datetimes are normalised to UTC; records missing any
    field are ignored.
    """
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    best: dict[datetime, dict[str, Any]] = {}
    for record in forecasts:
        start = record.get("startTime")
        published = record.get("publishTime")
        generation = record.get("generation")
        if not isinstance(start, datetime) or not isinstance(published, datetime):
            continue
        if not isinstance(generation, (int, float)):
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published > cutoff:
            continue  # never use information from after the decision
        current = best.get(start)
        if current is None or (published, generation) > (
            current["publishTime"],
            current["generation"],
        ):
            best[start] = {
                "startTime": start,
                "publishTime": published,
                "generation": float(generation),
            }
    return best


def summarise(selected: dict[datetime, dict[str, Any]]) -> dict[str, Any]:
    """Average / max / min of the selected forecast generation series."""
    values = [r["generation"] for r in selected.values()]
    if not values:
        return {
            "count": 0,
            "averageMw": None,
            "maxMw": None,
            "minMw": None,
            "distinctPublishTimes": 0,
            "latestPublishTime": None,
            "earliestPublishTime": None,
        }
    publishes = sorted(r["publishTime"] for r in selected.values())
    return {
        "count": len(values),
        "averageMw": sum(values) / len(values),
        "maxMw": max(values),
        "minMw": min(values),
        "distinctPublishTimes": len(set(publishes)),
        "latestPublishTime": max(publishes),
        "earliestPublishTime": min(publishes),
    }
