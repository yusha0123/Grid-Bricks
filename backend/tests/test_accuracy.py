"""Unit tests for accuracy matching + metrics (no network)."""

from datetime import datetime, timezone

from app.services.accuracy_service import (
    calculate_metrics,
    interpret,
    match_series,
)

UTC = timezone.utc


def dt(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, day, hour, minute, tzinfo=UTC)


def selected(pairs: dict) -> dict:
    return {
        start: {
            "startTime": start,
            "publishTime": dt(14, 9, 30),
            "generation": forecast,
        }
        for start, forecast in pairs.items()
    }


def actuals(pairs: dict) -> list:
    return [
        {"startTime": start, "generation": value} for start, value in pairs.items()
    ]


def test_match_uses_timestamps_not_positions():
    sel = selected({dt(15, 10): 1000.0, dt(15, 11): 2000.0})
    # Actuals in a different order must still match correctly.
    act = actuals({dt(15, 11): 2100.0, dt(15, 10): 900.0})
    rows = match_series(sel, act)
    by_time = {r["startTime"]: r for r in rows}
    assert by_time[dt(15, 10)]["errorMw"] == 100.0
    assert by_time[dt(15, 11)]["errorMw"] == -100.0


def test_unmatched_timestamps_are_excluded():
    sel = selected({dt(15, 10): 1000.0, dt(15, 12): 1300.0})
    act = actuals({dt(15, 10): 900.0, dt(15, 11): 2000.0})
    rows = match_series(sel, act)
    assert [r["startTime"] for r in rows] == [dt(15, 10)]


def test_metrics_mae_rmse_mape():
    sel = selected({dt(15, 10): 1100.0, dt(15, 11): 900.0})
    act = actuals({dt(15, 10): 1000.0, dt(15, 11): 1000.0})
    rows = match_series(sel, act)
    metrics = calculate_metrics(rows)
    assert metrics["matchedCount"] == 2
    assert metrics["maeMw"] == 100.0
    assert metrics["rmseMw"] == 100.0
    # |100/1000| and |-100/1000| -> 10%
    assert metrics["mapePercent"] == 10.0
    assert metrics["mapeCount"] == 2


def test_mape_excludes_zero_actuals():
    sel = selected({dt(15, 10): 100.0, dt(15, 11): 1100.0})
    act = actuals({dt(15, 10): 0.0, dt(15, 11): 1000.0})
    rows = match_series(sel, act)
    assert rows[0]["absolutePercentageError"] is None
    metrics = calculate_metrics(rows)
    assert metrics["maeMw"] == 100.0  # zero-actual row still counts for MAE
    assert metrics["mapePercent"] == 10.0
    assert metrics["mapeCount"] == 1


def test_empty_match_returns_unavailable_metrics():
    metrics = calculate_metrics([])
    assert metrics["matchedCount"] == 0
    assert metrics["maeMw"] is None
    assert metrics["rmseMw"] is None
    assert metrics["mapePercent"] is None
    assert interpret([], metrics) is None


def test_missing_records_handled():
    rows = match_series({}, actuals({dt(15, 10): 900.0}))
    assert rows == []
    rows = match_series(selected({dt(15, 10): 1000.0}), [])
    assert rows == []


def test_interpretation_reflects_bias_direction():
    over_sel = selected({dt(15, 10): 1200.0, dt(15, 11): 1300.0})
    act = actuals({dt(15, 10): 1000.0, dt(15, 11): 1000.0})
    rows = match_series(over_sel, act)
    text = interpret(rows, calculate_metrics(rows))
    assert text is not None and "overestimated" in text

    under_sel = selected({dt(15, 10): 800.0, dt(15, 11): 700.0})
    rows = match_series(under_sel, act)
    text = interpret(rows, calculate_metrics(rows))
    assert text is not None and "underestimated" in text
