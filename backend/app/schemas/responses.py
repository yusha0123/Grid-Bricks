"""Pydantic response models (predictable API contracts)."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    elexonBaseUrl: str


class ForecastObservation(BaseModel):
    startTime: str
    forecastMw: float
    publishTime: str
    ageHours: float | None = None


class ForecastSummary(BaseModel):
    count: int
    averageMw: float | None = None
    maxMw: float | None = None
    minMw: float | None = None
    distinctPublishTimes: int
    latestPublishTime: str | None = None
    earliestPublishTime: str | None = None


class ForecastResponse(BaseModel):
    deliveryDate: str
    decisionCutoff: str
    decisionCutoffExplanation: str
    timezone: str
    summary: ForecastSummary
    observations: list[ForecastObservation]
    missingIntervals: list[str]


class ActualObservation(BaseModel):
    startTime: str
    actualMw: float


class ActualsResponse(BaseModel):
    deliveryDate: str
    timezone: str
    count: int
    observations: list[ActualObservation]


class ComparisonRow(BaseModel):
    startTime: str
    forecastMw: float
    actualMw: float
    errorMw: float
    absoluteErrorMw: float
    absolutePercentageError: float | None = None
    publishTime: str


class AccuracyMetrics(BaseModel):
    matchedCount: int
    maeMw: float | None = None
    rmseMw: float | None = None
    mapePercent: float | None = None
    mapeCount: int
    meanErrorMw: float | None = None


class AccuracyResponse(BaseModel):
    deliveryDate: str
    decisionCutoff: str
    timezone: str
    metrics: AccuracyMetrics
    mapeNote: str
    rows: list[ComparisonRow]
    interpretation: str | None = None
