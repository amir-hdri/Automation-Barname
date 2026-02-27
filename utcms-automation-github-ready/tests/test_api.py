from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock
import pytest

client = TestClient(app)

def test_read_root():
    # If API_AUTH_MODE is default (usually api_key_or_jwt), we expect 503 or 401
    # unless we configure it to "off" or provide credentials.
    # Here we simulate 'off' to keep the simple check, OR we provide credentials.

    # Option 1: Disable auth for this test
    with patch("app.core.config.utcms_config.API_AUTH_MODE", "off"):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "سیستم اتوماسیون UTCMS فعال است"}

def test_traffic_status():
    with patch("app.core.config.utcms_config.API_AUTH_MODE", "off"):
        response = client.get("/waybill/traffic-status")
        assert response.status_code == 200
        body = response.json()
        assert "active_requests" in body
        assert "queued_requests" in body
        assert "next_allowed_in_seconds" in body
        assert "blocked_for_seconds" in body

@patch("app.automation.browser.browser_manager.initialize", new_callable=AsyncMock)
@patch("app.automation.browser.browser_manager.close", new_callable=AsyncMock)
def test_lifespan(mock_close, mock_init):
    with TestClient(app) as c:
        pass
    mock_init.assert_called()
    mock_close.assert_called()
