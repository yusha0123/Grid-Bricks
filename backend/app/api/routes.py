"""HTTP endpoints: validation, orchestration, serialisation."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas.responses import (
    AccuracyResponse,
    ActualsResponse,
    ForecastResponse,
    HealthResponse,
)
from app.services import accuracy_service, forecast_service
from app.services.elexon_client import ElexonError, client
from app.utils.datetime_utils import to_iso_z

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

TIMEZONE_LABEL = "UTC (UK was on GMT in January 2026, so UTC equals UK local time)"
CUTOFF_EXPLANATION = (
    "Assumption for this analysis (not an official Elexon/market rule): the "
    "day-ahead purchasing decision uses the latest forecast published on or "
    "before 11:00 UTC on the day before delivery. The cutoff applies uniformly "
    "to every delivery interval of the day and is configurable via "
    "DECISION_CUTOFF_TIME_UTC."
)
MAPE_NOTE = (
    "MAPE excludes intervals with zero actual generation (division by zero); "
    "mapeCount reports how many matched intervals were used."
)


def _parse_delivery_date(raw: str) -> date:
    try:
        delivery = date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid date '{raw}'. Use YYYY-MM-DD."
        )
    if not (settings.min_delivery_date <= raw <= settings.max_delivery_date):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Date {raw} is outside the supported range "
                f"{settings.min_delivery_date}..{settings.max_delivery_date}."
            ),
        )
    return delivery


def _expected_day_starts(delivery: date) -> list[datetime]:
    """Half-hourly delivery-interval starts for the day (48, UTC)."""
    midnight = datetime(delivery.year, delivery.month, delivery.day, tzinfo=timezone.utc)
    return [midnight + timedelta(minutes=30 * i) for i in range(48)]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # Independent of Elexon availability by design.
    return HealthResponse(status="healthy", elexonBaseUrl=settings.elexon_base_url)


@router.get("/forecasts", response_model=ForecastResponse)
async def get_forecasts(
    date: str = Query(..., description="Delivery date YYYY-MM-DD (January 2026)"),
) -> ForecastResponse:
    delivery = _parse_delivery_date(date)
    cutoff = forecast_service.decision_cutoff_for(delivery)
    try:
        records = await client.fetch_wind_forecasts(delivery)
    except ElexonError as exc:
        logger.exception("WINDFOR fetch failed for %s", date)
        raise HTTPException(status_code=502, detail=str(exc))
    selected = forecast_service.select_day_ahead_forecasts(records, cutoff)
    summary = forecast_service.summarise(selected)

    observations = [
        {
            "startTime": to_iso_z(rec["startTime"]),
            "forecastMw": rec["generation"],
            "publishTime": to_iso_z(rec["publishTime"]),
            "ageHours": (cutoff - rec["publishTime"]).total_seconds() / 3600.0,
        }
        for _, rec in sorted(selected.items())
    ]
    missing = [
        to_iso_z(start)
        for start in _expected_day_starts(delivery)
        if start not in selected
    ]
    return ForecastResponse(
        deliveryDate=delivery.isoformat(),
        decisionCutoff=to_iso_z(cutoff),
        decisionCutoffExplanation=CUTOFF_EXPLANATION,
        timezone=TIMEZONE_LABEL,
        summary={
            **summary,
            "latestPublishTime": to_iso_z(summary["latestPublishTime"])
            if summary["latestPublishTime"]
            else None,
            "earliestPublishTime": to_iso_z(summary["earliestPublishTime"])
            if summary["earliestPublishTime"]
            else None,
        },
        observations=observations,
        missingIntervals=missing,
    )


@router.get("/actuals", response_model=ActualsResponse)
async def get_actuals(
    date: str = Query(..., description="Delivery date YYYY-MM-DD (January 2026)"),
) -> ActualsResponse:
    delivery = _parse_delivery_date(date)
    try:
        records = await client.fetch_wind_actuals(delivery)
    except ElexonError as exc:
        logger.exception("FUELHH fetch failed for %s", date)
        raise HTTPException(status_code=502, detail=str(exc))
    return ActualsResponse(
        deliveryDate=delivery.isoformat(),
        timezone=TIMEZONE_LABEL,
        count=len(records),
        observations=[
            {"startTime": to_iso_z(r["startTime"]), "actualMw": r["generation"]}
            for r in records
        ],
    )


@router.get("/accuracy", response_model=AccuracyResponse)
async def get_accuracy(
    date: str = Query(..., description="Delivery date YYYY-MM-DD (January 2026)"),
) -> AccuracyResponse:
    delivery = _parse_delivery_date(date)
    cutoff = forecast_service.decision_cutoff_for(delivery)
    try:
        forecasts = await client.fetch_wind_forecasts(delivery)
        actuals = await client.fetch_wind_actuals(delivery)
    except ElexonError as exc:
        logger.exception("Accuracy fetch failed for %s", date)
        raise HTTPException(status_code=502, detail=str(exc))
    selected = forecast_service.select_day_ahead_forecasts(forecasts, cutoff)
    rows = accuracy_service.match_series(selected, actuals)
    metrics = accuracy_service.calculate_metrics(rows)
    return AccuracyResponse(
        deliveryDate=delivery.isoformat(),
        decisionCutoff=to_iso_z(cutoff),
        timezone=TIMEZONE_LABEL,
        metrics=metrics,
        mapeNote=MAPE_NOTE,
        rows=[
            {
                "startTime": to_iso_z(r["startTime"]),
                "forecastMw": r["forecastMw"],
                "actualMw": r["actualMw"],
                "errorMw": r["errorMw"],
                "absoluteErrorMw": r["absoluteErrorMw"],
                "absolutePercentageError": r["absolutePercentageError"],
                "publishTime": to_iso_z(r["publishTime"]),
            }
            for r in rows
        ],
        interpretation=accuracy_service.interpret(rows, metrics),
    )
