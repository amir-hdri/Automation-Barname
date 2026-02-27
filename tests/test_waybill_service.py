from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.waybill import (
    CargoModel,
    FinancialModel,
    GeoCoordinateModel,
    LocationModel,
    OperationMode,
    ReceiverModel,
    SenderModel,
    VehicleModel,
    WaybillMapRequest,
)
from app.services.waybill_service import WaybillService


def create_request(operation_mode: OperationMode = OperationMode.SAFE) -> WaybillMapRequest:
    return WaybillMapRequest(
        session_id="svc-test",
        operation_mode=operation_mode,
        sender=SenderModel(name="Sender", phone="0912", address="Addr", national_code="1234567890"),
        receiver=ReceiverModel(name="Receiver", phone="0912", address="Addr"),
        origin=LocationModel(province="A", city="B", address="C", coordinates=GeoCoordinateModel(lat=1.0, lng=1.0)),
        destination=LocationModel(
            province="D", city="E", address="F", coordinates=GeoCoordinateModel(lat=2.0, lng=2.0)
        ),
        cargo=CargoModel(type="General", weight=1000, count=1, description="test"),
        vehicle=VehicleModel(driver_national_code="123", driver_phone="0912", plate="12A34567", type="Truck"),
        financial=FinancialModel(cost=1000, payment_method="Cash"),
    )


@pytest.mark.asyncio
async def test_service_returns_safe_mode_response():
    service = WaybillService()
    request = create_request(OperationMode.SAFE)

    with patch("app.automation.browser.browser_manager.initialize", AsyncMock()), patch(
        "app.automation.browser.browser_manager.create_context", AsyncMock(return_value=("sid", AsyncMock()))
    ), patch("app.automation.browser.browser_manager.new_page", AsyncMock(return_value=AsyncMock())), patch(
        "app.automation.browser.browser_manager.close_context", AsyncMock()
    ), patch("app.services.waybill_service.UTCMSAuthenticator") as auth_cls, patch(
        "app.services.waybill_service.EnhancedWaybillManager"
    ) as manager_cls, patch("app.automation.reporting.report_service.record_request", AsyncMock()), patch(
        "app.automation.reporting.report_service.record_success", AsyncMock()
    ), patch("app.automation.reporting.report_service.record_map_usage", AsyncMock()), patch(
        "app.core.config.utcms_config.UTCMS_USERNAME", "user"
    ), patch("app.core.config.utcms_config.UTCMS_PASSWORD", "pass"):
        auth_instance = auth_cls.return_value
        auth_instance._is_logged_in = AsyncMock(return_value=True)

        manager_instance = manager_cls.return_value
        manager_instance.create_waybill_with_map = AsyncMock(
            return_value={"success": True, "status": "validated", "validation_summary": {"ready_for_submit": True}}
        )

        response = await service.create_waybill_with_map(request)

    assert response["mode"] == "safe"
    assert response["status"] == "validated"
    assert "request_id" in response


@pytest.mark.asyncio
async def test_service_blocks_full_mode_without_env_flag():
    service = WaybillService()
    request = create_request(OperationMode.FULL)

    with patch("app.core.config.utcms_config.ALLOW_LIVE_SUBMIT", False):
        with pytest.raises(HTTPException) as exc:
            await service.create_waybill_with_map(request)

    assert exc.value.status_code == 403
