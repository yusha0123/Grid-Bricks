"""API contract tests with a mocked Elexon client (no network)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

import app.services.elexon_client as elexon_module
from main import app

UTC = timezone.utc


def _forecasts(_delivery):
    return [
        {
            "startTime": datetime(2026, 1, 15, h, 0, tzinfo=UTC),
            "publishTime": datetime(2026, 1, 14, 9, 30, tzinfo=UTC),
            "generation": 1000.0 + h,
        }
        for h in range(24)
    ]


def _actuals(_delivery):
    return [
        {"startTime": datetime(2026, 1, 15, h, 0, tzinfo=UTC), "generation": 990.0 + h}
        for h in range(24)
    ] + [
        # Half-hour actuals exist too but share no forecast startTime.
        {"startTime": datetime(2026, 1, 15, h, 30, tzinfo=UTC), "generation": 995.0 + h}
        for h in range(24)
    ]


def _patch(monkeypatch):
    async def fake_forecasts(self, delivery):
        return _forecasts(delivery)

    async def fake_actuals(self, delivery):
        return _actuals(delivery)

    monkeypatch.setattr(elexon_module.ElexonClient, "fetch_wind_forecasts", fake_forecasts)
    monkeypatch.setattr(elexon_module.ElexonClient, "fetch_wind_actuals", fake_actuals)


def test_health_does_not_need_elexon():
    with TestClient(app) as tc:
        response = tc.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_forecasts_endpoint(monkeypatch):
    _patch(monkeypatch)
    with TestClient(app) as tc:
        response = tc.get("/api/forecasts", params={"date": "2026-01-15"})
    assert response.status_code == 200
    body = response.json()
    assert body["deliveryDate"] == "2026-01-15"
    assert body["summary"]["count"] == 24
    assert len(body["observations"]) == 24
    # 48 half-hour intervals minus 24 hourly forecasts = 24 missing.
    assert len(body["missingIntervals"]) == 24


def test_accuracy_endpoint_matches_on_starttime(monkeypatch):
    _patch(monkeypatch)
    with TestClient(app) as tc:
        response = tc.get("/api/accuracy", params={"date": "2026-01-15"})
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["matchedCount"] == 24
    assert body["metrics"]["maeMw"] == 10.0
    assert body["interpretation"]


def test_rejects_out_of_range_date(monkeypatch):
    _patch(monkeypatch)
    with TestClient(app) as tc:
        response = tc.get("/api/forecasts", params={"date": "2026-02-01"})
    assert response.status_code == 400


def test_rejects_malformed_date(monkeypatch):
    _patch(monkeypatch)
    with TestClient(app) as tc:
        response = tc.get("/api/accuracy", params={"date": "not-a-date"})
    assert response.status_code == 400
