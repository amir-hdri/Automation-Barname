import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.api.routes.waybill_map import (
    create_waybill_with_map,
    WaybillMapRequest,
    LocationModel,
    GeoCoordinateModel,
    SenderModel,
    ReceiverModel,
    CargoModel,
    VehicleModel,
    FinancialModel
)

def create_mock_request():
    return WaybillMapRequest(
        session_id="test_session",
        sender=SenderModel(name="Sender", phone="09121234567", address="Addr", national_code="1234567890"),
        receiver=ReceiverModel(name="Receiver", phone="09121234567", address="Addr"),
        origin=LocationModel(province="Test", city="City", address="Addr", coordinates=GeoCoordinateModel(lat=1.0, lng=1.0)),
        destination=LocationModel(province="Test", city="City", address="Addr", coordinates=GeoCoordinateModel(lat=2.0, lng=2.0)),
        cargo=CargoModel(type="Type", weight=1000, count=1, description="Desc"),
        vehicle=VehicleModel(driver_national_code="1234567890", driver_phone="09121234567", plate="12A34567", type="Truck"),
        financial=FinancialModel(cost=1000000, payment_method="Cash")
    )

@pytest.mark.asyncio
async def test_waybill_login_success():
    # Mock dependencies
    mock_request = create_mock_request()

    with patch("app.automation.browser.browser_manager.initialize", new_callable=AsyncMock) as mock_init, \
         patch("app.automation.browser.browser_manager.create_context", new_callable=AsyncMock) as mock_create_context, \
         patch("app.automation.browser.browser_manager.new_page", new_callable=AsyncMock) as mock_new_page, \
         patch("app.automation.browser.browser_manager.close_context", new_callable=AsyncMock) as mock_close_context, \
         patch("app.services.waybill_service.UTCMSAuthenticator") as MockAuth, \
         patch("app.services.waybill_service.EnhancedWaybillManager") as MockManager, \
         patch("app.automation.reporting.report_service.record_request", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_success", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_map_usage", new_callable=AsyncMock) as mock_record_map_usage, \
         patch("app.core.config.utcms_config.UTCMS_USERNAME", "testuser"), \
         patch("app.core.config.utcms_config.UTCMS_PASSWORD", "testpass"):

        # Setup mock page and context
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_new_page.return_value = mock_page
        mock_create_context.return_value = ("session_uuid", mock_context) # Updated to return tuple

        # Setup authenticator mock
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance._is_logged_in = AsyncMock(return_value=False)
        mock_auth_instance.login = AsyncMock(return_value=True)

        # Setup manager mock
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.create_waybill_with_map = AsyncMock(return_value={"origin_method": "map"})

        # Call the function
        result = await create_waybill_with_map(mock_request)

        # Assertions
        mock_auth_instance._is_logged_in.assert_called_once()
        mock_auth_instance.login.assert_called_once_with("testuser", "testpass")
        mock_manager_instance.create_waybill_with_map.assert_called_once()
        mock_record_map_usage.assert_called_once_with("unknown")
        assert result["origin_method"] == "map"

@pytest.mark.asyncio
async def test_waybill_login_failure():
    # Mock dependencies
    mock_request = create_mock_request()

    with patch("app.automation.browser.browser_manager.initialize", new_callable=AsyncMock), \
         patch("app.automation.browser.browser_manager.create_context", new_callable=AsyncMock) as mock_create_context, \
         patch("app.automation.browser.browser_manager.new_page", new_callable=AsyncMock) as mock_new_page, \
         patch("app.automation.browser.browser_manager.close_context", new_callable=AsyncMock), \
         patch("app.services.waybill_service.UTCMSAuthenticator") as MockAuth, \
         patch("app.automation.reporting.report_service.record_request", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_failure", new_callable=AsyncMock), \
         patch("app.core.config.utcms_config.UTCMS_USERNAME", "testuser"), \
         patch("app.core.config.utcms_config.UTCMS_PASSWORD", "testpass"):

        # Setup mock page and context
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_new_page.return_value = mock_page
        mock_create_context.return_value = ("session_uuid", mock_context) # Updated to return tuple

        # Setup authenticator mock to fail login
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance._is_logged_in = AsyncMock(return_value=False)
        mock_auth_instance.login = AsyncMock(return_value=False)

        # Expect HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await create_waybill_with_map(mock_request)

        # In my updated waybill_map.py, I explicitly re-raise HTTPException
        # except HTTPException as e:
        #     await report_service.record_failure()
        #     raise e
        # So it should be 401
        assert excinfo.value.status_code == 401
        assert "خطا در ورود به سامانه بارنامه" in excinfo.value.detail

@pytest.mark.asyncio
async def test_waybill_already_logged_in():
    # Mock dependencies
    mock_request = create_mock_request()

    with patch("app.automation.browser.browser_manager.initialize", new_callable=AsyncMock), \
         patch("app.automation.browser.browser_manager.create_context", new_callable=AsyncMock) as mock_create_context, \
         patch("app.automation.browser.browser_manager.new_page", new_callable=AsyncMock) as mock_new_page, \
         patch("app.automation.browser.browser_manager.close_context", new_callable=AsyncMock), \
         patch("app.services.waybill_service.UTCMSAuthenticator") as MockAuth, \
         patch("app.services.waybill_service.EnhancedWaybillManager") as MockManager, \
         patch("app.automation.reporting.report_service.record_request", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_success", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_map_usage", new_callable=AsyncMock):

        # Setup mock page and context
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_new_page.return_value = mock_page
        mock_create_context.return_value = ("session_uuid", mock_context) # Updated to return tuple

        # Setup authenticator mock to be already logged in
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance._is_logged_in = AsyncMock(return_value=True)

        # Setup manager mock
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.create_waybill_with_map = AsyncMock(return_value={"origin_method": "map"})

        # Call the function
        await create_waybill_with_map(mock_request)

        # Assertions
        mock_auth_instance._is_logged_in.assert_called_once()
        mock_auth_instance.login.assert_not_called()

@pytest.mark.asyncio
async def test_waybill_missing_credentials():
    # Mock dependencies
    mock_request = create_mock_request()

    with patch("app.automation.browser.browser_manager.initialize", new_callable=AsyncMock), \
         patch("app.automation.browser.browser_manager.create_context", new_callable=AsyncMock) as mock_create_context, \
         patch("app.automation.browser.browser_manager.new_page", new_callable=AsyncMock) as mock_new_page, \
         patch("app.automation.browser.browser_manager.close_context", new_callable=AsyncMock), \
         patch("app.services.waybill_service.UTCMSAuthenticator") as MockAuth, \
         patch("app.automation.reporting.report_service.record_request", new_callable=AsyncMock), \
         patch("app.automation.reporting.report_service.record_failure", new_callable=AsyncMock), \
         patch("app.core.config.utcms_config.UTCMS_USERNAME", ""), \
         patch("app.core.config.utcms_config.UTCMS_PASSWORD", ""):

        # Setup mock page and context
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_new_page.return_value = mock_page
        mock_create_context.return_value = ("session_uuid", mock_context) # Updated to return tuple

        # Setup authenticator mock to report not logged in
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance._is_logged_in = AsyncMock(return_value=False)

        # Expect HTTPException due to missing credentials
        with pytest.raises(HTTPException) as excinfo:
            await create_waybill_with_map(mock_request)

        assert excinfo.value.status_code == 401
        assert "اطلاعات ورود به سیستم تنظیم نشده است" in excinfo.value.detail
