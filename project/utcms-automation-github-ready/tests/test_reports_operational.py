import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.automation.reporting import ReportService
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_operational_report_contains_latency_and_mode_counters():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, future=True
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    service = ReportService()
    with patch("app.automation.reporting.engine", test_engine):
        await service.record_request(mode="safe")
        await service.record_success(mode="safe", latency_ms=120.0)
        await service.record_failure(mode="full", category="auth")
        report = await service.get_operational_report()

    assert "latency_ms" in report
    assert "mode_counters" in report
    assert report["mode_counters"]["safe"]["requests"] >= 1
    assert report["error_categories"]["auth"] >= 1
    await test_engine.dispose()


def test_operational_endpoint_available():
    with patch("app.core.config.utcms_config.API_AUTH_MODE", "off"):
        response = client.get("/reports/operational")
    assert response.status_code == 200
    body = response.json()
    assert "latency_ms" in body
    assert "mode_counters" in body
