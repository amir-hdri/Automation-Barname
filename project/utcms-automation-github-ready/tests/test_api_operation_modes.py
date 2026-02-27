from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def base_payload():
    return {
        "session_id": "api-mode",
        "sender": {
            "name": "x",
            "phone": "1",
            "address": "a",
            "national_code": "1234567890",
        },
        "receiver": {"name": "y", "phone": "2", "address": "b"},
        "origin": {
            "province": "p",
            "city": "c",
            "address": "a",
            "coordinates": {"lat": 1, "lng": 1},
        },
        "destination": {
            "province": "p2",
            "city": "c2",
            "address": "a2",
            "coordinates": {"lat": 2, "lng": 2},
        },
        "cargo": {"weight": 1000},
        "vehicle": {},
        "financial": {},
    }


def test_api_defaults_to_safe_mode():
    async def fake_handler(request):
        return {
            "success": True,
            "mode": request.operation_mode.value,
            "status": "validated",
            "request_id": "rid",
        }

    with patch("app.core.config.utcms_config.API_AUTH_MODE", "off"), patch(
        "app.services.waybill_service.waybill_service.create_waybill_with_map",
        new=AsyncMock(side_effect=fake_handler),
    ):
        response = client.post("/waybill/create-with-map", json=base_payload())

    assert response.status_code == 200
    assert response.json()["mode"] == "safe"


def test_api_accepts_full_mode_payload():
    payload = base_payload()
    payload["operation_mode"] = "full"

    async def fake_handler(request):
        return {
            "success": True,
            "mode": request.operation_mode.value,
            "status": "submitted",
            "request_id": "rid",
            "tracking_code": "123456",
        }

    with patch("app.core.config.utcms_config.API_AUTH_MODE", "off"), patch(
        "app.services.waybill_service.waybill_service.create_waybill_with_map",
        new=AsyncMock(side_effect=fake_handler),
    ):
        response = client.post("/waybill/create-with-map", json=payload)

    assert response.status_code == 200
    assert response.json()["mode"] == "full"
    assert response.json()["tracking_code"] == "123456"
