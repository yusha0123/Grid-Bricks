"""Application configuration (environment-based with sane defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _getenv(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # Elexon BMRS API (official docs: https://bmrs.elexon.co.uk/api-documentation)
    elexon_base_url: str = field(
        default_factory=lambda: _getenv(
            "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
        )
    )
    http_timeout_seconds: float = float(_getenv("ELEXON_TIMEOUT_SECONDS", "30"))
    connect_timeout_seconds: float = float(_getenv("ELEXON_CONNECT_TIMEOUT_SECONDS", "10"))

    # Day-ahead purchasing decision cutoff.
    #
    # ASSUMPTION (not an official Elexon/market rule): the purchasing team must
    # use forecast information available at 11:00 UTC on the day *before*
    # delivery (D-1 at 11:00 UTC). This approximates the UK day-ahead auction
    # gate-closure window. The cutoff is applied UNIFORMLY to every delivery
    # interval of the delivery day: only forecasts with
    # publishTime <= (D-1) 11:00 UTC are eligible.
    decision_cutoff_time_utc: str = field(
        default_factory=lambda: _getenv("DECISION_CUTOFF_TIME_UTC", "11:00")
    )

    # Analysis window required by the assignment.
    min_delivery_date: str = field(
        default_factory=lambda: _getenv("MIN_DELIVERY_DATE", "2026-01-01")
    )
    max_delivery_date: str = field(
        default_factory=lambda: _getenv("MAX_DELIVERY_DATE", "2026-01-31")
    )

    # Simple in-memory cache for successful Elexon responses.
    cache_ttl_seconds: int = int(_getenv("CACHE_TTL_SECONDS", "600"))

    # CORS: local frontend origins only (no wildcard).
    allowed_origins: tuple = (
        tuple(o.strip() for o in _getenv("ALLOWED_ORIGINS", "").split(",") if o.strip())
        or ("http://localhost:5173", "http://127.0.0.1:5173")
    )


settings = Settings()
