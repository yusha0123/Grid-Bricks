"""Accuracy evaluation: match forecast vs actuals on startTime and score.

Matching is by normalised (aware UTC) ``startTime`` equality only -- never by
array position. MAPE excludes intervals with zero actual generation and
reports how many observations were used.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any


def match_series(
    selected_forecasts: dict[datetime, dict[str, Any]],
    actuals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Inner-join forecasts and actuals on exact ``startTime`` (sorted)."""
    actual_by_time = {r["startTime"]: r["generation"] for r in actuals}
    rows: list[dict[str, Any]] = []
    for start in sorted(selected_forecasts):
        if start not in actual_by_time:
            continue
        forecast = float(selected_forecasts[start]["generation"])
        actual = float(actual_by_time[start])
        error = forecast - actual
        rows.append(
            {
                "startTime": start,
                "forecastMw": forecast,
                "actualMw": actual,
                "errorMw": error,
                "absoluteErrorMw": abs(error),
                "absolutePercentageError": (
                    abs(error) / actual * 100.0 if actual != 0 else None
                ),
                "publishTime": selected_forecasts[start]["publishTime"],
            }
        )
    return rows


def calculate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """MAE / RMSE / MAPE over matched rows (pure function)."""
    n = len(rows)
    if n == 0:
        return {
            "matchedCount": 0,
            "maeMw": None,
            "rmseMw": None,
            "mapePercent": None,
            "mapeCount": 0,
            "meanErrorMw": None,
        }
    abs_errors = [r["absoluteErrorMw"] for r in rows]
    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(e * e for e in abs_errors) / n)
    ape_values = [r["absolutePercentageError"] for r in rows if r["absolutePercentageError"] is not None]
    mape = sum(ape_values) / len(ape_values) if ape_values else None
    mean_error = sum(r["errorMw"] for r in rows) / n
    return {
        "matchedCount": n,
        "maeMw": mae,
        "rmseMw": rmse,
        "mapePercent": mape,
        "mapeCount": len(ape_values),
        "meanErrorMw": mean_error,
    }


def interpret(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str | None:
    """Small data-driven summary; returns None when there is nothing to say."""
    if not rows or metrics.get("meanErrorMw") is None:
        return None
    mean_error = metrics["meanErrorMw"]
    mae = metrics["maeMw"] or 0.0
    mean_actual = sum(r["actualMw"] for r in rows) / len(rows)
    if mean_actual > 0:
        bias_pct = mean_error / mean_actual * 100.0
        magnitude = f"{abs(bias_pct):.1f}% of mean actual generation"
    else:
        magnitude = f"{abs(mean_error):.0f} MW mean error"
    direction = (
        "overestimated generation"
        if mean_error > 0
        else "underestimated generation"
        if mean_error < 0
        else "matched actual generation on average"
    )
    over = sum(1 for r in rows if r["errorMw"] > 0)
    under = sum(1 for r in rows if r["errorMw"] < 0)
    exact = len(rows) - over - under
    if mean_error == 0:
        return (
            f"The day-ahead forecast matched actual generation on average "
            f"(MAE {mae:.0f} MW across {len(rows)} matched intervals, "
            f"{exact} exact)."
        )
    return (
        f"The day-ahead forecast {direction} overall ({magnitude}; "
        f"MAE {mae:.0f} MW across {len(rows)} matched intervals: "
        f"{over} overestimated, {under} underestimated, {exact} exact)."
    )
