from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sensitive_endpoint_rejects_without_auth():
    with patch("app.core.config.utcms_config.API_AUTH_MODE", "api_key"), patch(
        "app.core.config.utcms_config.API_KEY", "test-key"
    ), patch("app.core.config.utcms_config.API_KEY_HEADER", "X-API-Key"):
        response = client.get("/waybill/traffic-status")
        assert response.status_code == 401


def test_sensitive_endpoint_accepts_with_api_key():
    with patch("app.core.config.utcms_config.API_AUTH_MODE", "api_key"), patch(
        "app.core.config.utcms_config.API_KEY", "test-key"
    ), patch("app.core.config.utcms_config.API_KEY_HEADER", "X-API-Key"):
        response = client.get(
            "/waybill/traffic-status",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200
        assert "active_requests" in response.json()
