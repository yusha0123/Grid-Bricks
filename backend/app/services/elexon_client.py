"""Async Elexon BMRS API client with a small TTL in-memory cache.

Endpoint behaviour (verified against the live API):
- ``GET {base}/datasets/WINDFOR`` returns ``{"data": [...]}`` where each item
  has ``dataset`` / ``publishTime`` / ``startTime`` / ``generation``.
  Supported filters include ``publishDateTimeFrom`` / ``publishDateTimeTo``
  and ``startTimeFrom`` / ``startTimeTo``. WINDFOR runs are HOURLY
  (``startTime`` on the hour, ~8 runs/day, ~73 hourly startTimes per run).
- ``GET {base}/datasets/FUELHH`` with ``settlementDateFrom`` /
  ``settlementDateTo`` / ``fuelType=WIND`` returns ``{"data": [...]}`` with
  half-hourly actuals (``settlementDate`` / ``settlementPeriod`` 1..48,
  ``startTime``, ``generation``).
- The ``.../stream`` variants return a bare JSON array instead of the
  ``{"data": ...}`` envelope; this client uses the envelope endpoints.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings
from app.utils.datetime_utils import parse_elexon_timestamp, parse_generation

logger = logging.getLogger(__name__)


class ElexonError(RuntimeError):
    """Raised when Elexon is unreachable or returns unusable data."""


class ElexonClient:
    """Reusable async client. Cache keys include dataset + date range."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                settings.http_timeout_seconds,
                connect=settings.connect_timeout_seconds,
            )
            self._client = httpx.AsyncClient(
                base_url=settings.elexon_base_url, timeout=timeout
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    def _cache_get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        expires_at, payload = entry
        if time.monotonic() > expires_at:
            self._cache.pop(key, None)
            return None
        return payload

    def _cache_set(self, key: str, payload: Any) -> None:
        self._cache[key] = (time.monotonic() + settings.cache_ttl_seconds, payload)

    async def _fetch_dataset(
        self, dataset: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        cache_key = f"{dataset}:{sorted(params.items())}"
        async with self._lock:
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            client = await self._get_client()
            try:
                response = await client.get(f"/datasets/{dataset}", params=params)
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                raise ElexonError(f"Elexon request failed ({dataset}): {exc}") from exc
            except httpx.HTTPError as exc:
                raise ElexonError(f"Elexon request error ({dataset}): {exc}") from exc
            if response.status_code != 200:
                raise ElexonError(
                    f"Elexon returned HTTP {response.status_code} for {dataset}"
                )
            try:
                body = response.json()
            except ValueError as exc:
                raise ElexonError(
                    f"Elexon returned a non-JSON response for {dataset}"
                ) from exc
            # Envelope form {"data": [...]} or bare list (stream form).
            items = body.get("data") if isinstance(body, dict) else body
            if not isinstance(items, list):
                raise ElexonError(
                    f"Elexon returned an unexpected response shape for {dataset}"
                )
            records = [r for r in items if isinstance(r, dict)]
            # Cache only successful responses.
            self._cache_set(cache_key, records)
            return records

    # -- Normalised fetchers -------------------------------------------------

    async def fetch_wind_forecasts(
        self, delivery: date
    ) -> list[dict[str, Any]]:
        """Fetch raw WINDFOR runs relevant to a delivery day.

        Requests every run published in [D-2 00:00Z, cutoff(D)] whose window
        covers the delivery day, so the selection step can apply the decision
        cutoff day-ahead rule. Client-side filtering narrows to the day.
        """
        from app.services.forecast_service import decision_cutoff_for

        cutoff = decision_cutoff_for(delivery)
        publish_from = datetime(
            delivery.year, delivery.month, delivery.day, tzinfo=timezone.utc
        ) - timedelta(days=2)
        params = {
            "publishDateTimeFrom": publish_from.isoformat().replace("+00:00", "Z"),
            "publishDateTimeTo": cutoff.isoformat().replace("+00:00", "Z"),
            "startTimeFrom": datetime(
                delivery.year, delivery.month, delivery.day, tzinfo=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "startTimeTo": (
                datetime(delivery.year, delivery.month, delivery.day, tzinfo=timezone.utc)
                + timedelta(days=1)
            ).isoformat().replace("+00:00", "Z"),
        }
        raw = await self._fetch_dataset("WINDFOR", params)
        day_start = datetime(
            delivery.year, delivery.month, delivery.day, tzinfo=timezone.utc
        )
        day_end = day_start + timedelta(days=1)
        normalised: list[dict[str, Any]] = []
        for item in raw:
            start = parse_elexon_timestamp(item.get("startTime"))
            published = parse_elexon_timestamp(
                item.get("publishTime", item.get("publishDateTime"))
            )
            generation = parse_generation(item.get("generation"))
            if start is None or published is None or generation is None:
                logger.debug("Skipping invalid WINDFOR record: %r", item)
                continue
            if not (day_start <= start < day_end):
                continue  # keep only intervals of the requested delivery day
            normalised.append(
                {"startTime": start, "publishTime": published, "generation": generation}
            )
        return normalised

    async def fetch_wind_actuals(self, delivery: date) -> list[dict[str, Any]]:
        """Fetch normalised half-hourly national WIND actuals (FUELHH)."""
        stamp = delivery.isoformat()
        raw = await self._fetch_dataset(
            "FUELHH",
            {
                "settlementDateFrom": stamp,
                "settlementDateTo": stamp,
                "fuelType": "WIND",
            },
        )
        normalised: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw:
            if str(item.get("fuelType", "WIND")).upper() != "WIND":
                continue
            start = parse_elexon_timestamp(item.get("startTime"))
            generation = parse_generation(item.get("generation"))
            if start is None or generation is None:
                logger.debug("Skipping invalid FUELHH record: %r", item)
                continue
            # Restrict to the requested delivery day (UTC day == UK day in Jan).
            if start.date() != delivery:
                continue
            key = start.isoformat()
            if key in seen:
                continue  # drop exact duplicates deterministically
            seen.add(key)
            normalised.append({"startTime": start, "generation": generation})
        normalised.sort(key=lambda r: r["startTime"])
        return normalised


client = ElexonClient()
