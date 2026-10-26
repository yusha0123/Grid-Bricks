"""Unit tests for day-ahead forecast selection (no network)."""

from datetime import datetime, timezone

import pytest

from app.services.forecast_service import (
    decision_cutoff_for,
    select_day_ahead_forecasts,
    summarise,
)

UTC = timezone.utc


def dt(hour: int, minute: int = 0, day: int = 14) -> datetime:
    return datetime(2026, 1, day, hour, minute, tzinfo=UTC)


def rec(start, published, generation):
    return {"startTime": start, "publishTime": published, "generation": generation}


CUTOFF = datetime(2026, 1, 14, 11, 0, tzinfo=UTC)  # (D-1) 11:00Z for D = 2026-01-15


def test_decision_cutoff_is_day_before_at_configured_time():
    from datetime import date

    assert decision_cutoff_for(date(2026, 1, 15)) == CUTOFF


def test_selects_latest_forecast_before_cutoff():
    forecasts = [
        rec(dt(10), dt(2, 30), 1000.0),
        rec(dt(10), dt(9, 30), 1200.0),
        rec(dt(10), dt(7, 30), 1100.0),
    ]
    selected = select_day_ahead_forecasts(forecasts, CUTOFF)
    assert set(selected) == {dt(10)}
    assert selected[dt(10)]["generation"] == 1200.0
    assert selected[dt(10)]["publishTime"] == dt(9, 30)


def test_excludes_forecasts_published_after_cutoff():
    forecasts = [
        rec(dt(10), dt(9, 30), 1200.0),
        rec(dt(10), dt(11, 30), 9999.0),  # after cutoff: must not be used
        rec(dt(10), dt(15, 30), 8888.0),
    ]
    selected = select_day_ahead_forecasts(forecasts, CUTOFF)
    assert selected[dt(10)]["generation"] == 1200.0


def test_no_eligible_forecast_yields_unavailable_interval():
    forecasts = [rec(dt(10), dt(15, 30), 500.0)]
    assert select_day_ahead_forecasts(forecasts, CUTOFF) == {}


def test_duplicate_publish_timestamps_resolve_deterministically():
    forecasts = [
        rec(dt(10), dt(9, 30), 1200.0),
        rec(dt(10), dt(9, 30), 1250.0),
        rec(dt(10), dt(9, 30), 1100.0),
    ]
    first = select_day_ahead_forecasts(forecasts, CUTOFF)
    second = select_day_ahead_forecasts(list(reversed(forecasts)), CUTOFF)
    assert first == second
    assert first[dt(10)]["generation"] == 1250.0  # documented tie-break


def test_multiple_intervals_selected_independently():
    forecasts = [
        rec(dt(10), dt(9, 30), 1200.0),
        rec(dt(11), dt(4, 30), 1300.0),
        rec(dt(11), dt(9, 30), 1350.0),
    ]
    selected = select_day_ahead_forecasts(forecasts, CUTOFF)
    assert selected[dt(10)]["generation"] == 1200.0
    assert selected[dt(11)]["generation"] == 1350.0


def test_invalid_records_are_skipped():
    forecasts = [
        {"startTime": dt(10), "publishTime": dt(9, 30)},  # missing generation
        {"startTime": None, "publishTime": dt(9, 30), "generation": 5.0},
        {"publishTime": dt(9, 30), "generation": 5.0},  # missing startTime
        rec(dt(12), dt(9, 30), 1400.0),
    ]
    selected = select_day_ahead_forecasts(forecasts, CUTOFF)
    assert set(selected) == {dt(12)}


def test_naive_datetimes_treated_as_utc():
    from datetime import datetime as naive_dt

    forecasts = [
        {
            "startTime": naive_dt(2026, 1, 15, 10, 0),
            "publishTime": naive_dt(2026, 1, 14, 9, 30),
            "generation": 1200.0,
        }
    ]
    selected = select_day_ahead_forecasts(forecasts, CUTOFF)
    assert len(selected) == 1


def test_summarise_empty_and_populated():
    assert summarise({})["count"] == 0
    assert summarise({})["averageMw"] is None
    summary = summarise(
        {
            dt(10): rec(dt(10), dt(9, 30), 1000.0),
            dt(11): rec(dt(11), dt(7, 30), 3000.0),
        }
    )
    assert summary["count"] == 2
    assert summary["averageMw"] == pytest.approx(2000.0)
    assert summary["maxMw"] == 3000.0
    assert summary["minMw"] == 1000.0
    assert summary["distinctPublishTimes"] == 2
