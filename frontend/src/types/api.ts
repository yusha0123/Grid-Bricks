/** Typed contracts matching the FastAPI Pydantic response models. */

export interface ForecastObservation {
  startTime: string;
  forecastMw: number;
  publishTime: string;
  ageHours: number | null;
}

export interface ForecastSummary {
  count: number;
  averageMw: number | null;
  maxMw: number | null;
  minMw: number | null;
  distinctPublishTimes: number;
  latestPublishTime: string | null;
  earliestPublishTime: string | null;
}

export interface ForecastResponse {
  deliveryDate: string;
  decisionCutoff: string;
  decisionCutoffExplanation: string;
  timezone: string;
  summary: ForecastSummary;
  observations: ForecastObservation[];
  missingIntervals: string[];
}

export interface ActualObservation {
  startTime: string;
  actualMw: number;
}

export interface ActualsResponse {
  deliveryDate: string;
  timezone: string;
  count: number;
  observations: ActualObservation[];
}

export interface ComparisonRow {
  startTime: string;
  forecastMw: number;
  actualMw: number;
  errorMw: number;
  absoluteErrorMw: number;
  absolutePercentageError: number | null;
  publishTime: string;
}

export interface AccuracyMetrics {
  matchedCount: number;
  maeMw: number | null;
  rmseMw: number | null;
  mapePercent: number | null;
  mapeCount: number;
  meanErrorMw: number | null;
}

export interface AccuracyResponse {
  deliveryDate: string;
  decisionCutoff: string;
  timezone: string;
  metrics: AccuracyMetrics;
  mapeNote: string;
  rows: ComparisonRow[];
  interpretation: string | null;
}

export type Section = "forecast" | "accuracy";
