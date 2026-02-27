from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_returns_not_ready_when_db_fails():
    class _FailingEngine:
        def connect(self):
            raise Exception("db down")

    with patch("app.api.routes.system.engine", _FailingEngine()), patch(
        "app.api.routes.system.browser_manager.initialize",
        new=AsyncMock(return_value=None),
    ):
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
