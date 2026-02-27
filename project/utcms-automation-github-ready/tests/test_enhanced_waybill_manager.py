import unittest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from app.automation.waybill_enhanced import EnhancedWaybillManager
from app.core.exceptions import WaybillError
from app.automation.location_selector import LocationSelector, RouteCalculator
from app.automation.map_controller import MapController, GeoCoordinate
from app.automation.browser import PageInteractor
from app.core.config import utcms_config


class TestEnhancedWaybillManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mocks for Playwright Page and BrowserContext
        self.mock_page = AsyncMock()
        self.mock_context = AsyncMock()

        # Patch classes BEFORE initializing EnhancedWaybillManager
        self.patcher_interactor = patch(
            "app.automation.waybill_enhanced.PageInteractor"
        )
        self.patcher_map_controller = patch(
            "app.automation.waybill_enhanced.MapController"
        )
        self.patcher_location_selector = patch(
            "app.automation.waybill_enhanced.LocationSelector"
        )
        self.patcher_route_calculator = patch(
            "app.automation.waybill_enhanced.RouteCalculator"
        )

        self.MockInteractor = self.patcher_interactor.start()
        self.MockMapController = self.patcher_map_controller.start()
        self.MockLocationSelector = self.patcher_location_selector.start()
        self.MockRouteCalculator = self.patcher_route_calculator.start()

        # Setup mock instances returned by classes
        self.mock_interactor = self.MockInteractor.return_value
        self.mock_map_controller = self.MockMapController.return_value
        self.mock_location_selector = self.MockLocationSelector.return_value
        self.mock_route_calculator = self.MockRouteCalculator.return_value

        # Configure common async methods on mocks
        self.mock_interactor.safe_fill = AsyncMock()
        self.mock_interactor.safe_click = AsyncMock()
        self.mock_interactor.screenshot = AsyncMock()

        self.mock_location_selector.select_location = AsyncMock()
        self.mock_route_calculator.calculate_distance = AsyncMock()

        # Initialize manager
        self.manager = EnhancedWaybillManager(self.mock_page, self.mock_context)

    async def asyncTearDown(self):
        self.patcher_interactor.stop()
        self.patcher_map_controller.stop()
        self.patcher_location_selector.stop()
        self.patcher_route_calculator.stop()

    async def test_initialization(self):
        """Test that the manager initializes its components correctly."""
        self.assertIs(self.manager.page, self.mock_page)
        self.assertIs(self.manager.context, self.mock_context)
        self.assertIs(self.manager.interactor, self.mock_interactor)
        self.assertIs(self.manager.map_controller, self.mock_map_controller)
        self.assertIs(self.manager.location_selector, self.mock_location_selector)
        self.assertIs(self.manager.route_calculator, self.mock_route_calculator)

    async def test_create_waybill_success(self):
        """Test the happy path for creating a waybill."""
        # Setup data
        data = {
            "sender": {"name": "Sender"},
            "receiver": {"name": "Receiver"},
            "origin": {
                "province": "Tehran",
                "coordinates": {"lat": 35.6892, "lng": 51.3890},
            },
            "destination": {
                "province": "Mashhad",
                "coordinates": {"lat": 36.2972, "lng": 59.6067},
            },
            "cargo": {"type": "General", "weight": 1000},
            "vehicle": {"plate": "12A34567"},
            "financial": {"cost": 5000000},
        }

        # Mock location selection
        self.mock_location_selector.select_location.side_effect = [
            {
                "success": True,
                "method": "map",
                "coordinates": data["origin"]["coordinates"],
            },  # Origin
            {
                "success": True,
                "method": "map",
                "coordinates": data["destination"]["coordinates"],
            },  # Destination
        ]

        # Mock route calculation
        route_info = {"distance": "900 km", "duration": "10h"}
        self.mock_route_calculator.calculate_distance.return_value = route_info

        # Mock tracking code extraction (inside _submit_waybill)
        # We need to mock _extract_tracking_code method on the instance or simulate page behavior
        # Since _extract_tracking_code calls page methods, we can mock page.query_selector
        mock_element = AsyncMock()
        mock_element.text_content.return_value = "Code: 123456"
        self.mock_page.query_selector.return_value = mock_element

        # Run
        result = await self.manager.create_waybill_with_map(data)

        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["tracking_code"], "123456")
        self.assertEqual(result["route"], route_info)

        # Verify calls
        self.mock_page.goto.assert_called_with(utcms_config.WAYBILL_URL)
        self.mock_interactor.safe_fill.assert_any_call(
            'input[name="SenderName"]', "Sender"
        )
        self.mock_interactor.safe_fill.assert_any_call(
            'input[name="ReceiverName"]', "Receiver"
        )

        # Verify cargo info
        self.mock_interactor.safe_fill.assert_any_call(
            'input[name="CargoWeight"]', "1000"
        )

        # Verify vehicle info
        self.mock_interactor.safe_fill.assert_any_call(
            'input[name="PlateNumber"]', "12A34567"
        )

        # Check select_location calls
        self.assertEqual(self.mock_location_selector.select_location.call_count, 2)
        self.mock_location_selector.select_location.assert_any_call(
            data["origin"], origin=True
        )
        self.mock_location_selector.select_location.assert_any_call(
            data["destination"], origin=False
        )

        # Check route calculation
        self.mock_route_calculator.calculate_distance.assert_called_once()

    async def test_create_waybill_origin_failure(self):
        """Test failure when origin selection fails."""
        data = {"sender": {}, "receiver": {}, "origin": {}, "destination": {}}

        # Mock origin failure
        self.mock_location_selector.select_location.return_value = {
            "success": False,
            "error": "Map error",
        }

        with self.assertRaises(WaybillError) as context:
            await self.manager.create_waybill_with_map(data)

        self.assertIn("انتخاب مبدا با شکست مواجه شد", str(context.exception))
        self.mock_interactor.screenshot.assert_called_once_with("waybill_map_error")

    async def test_create_waybill_destination_failure(self):
        """Test failure when destination selection fails."""
        data = {"sender": {}, "receiver": {}, "origin": {}, "destination": {}}

        # Mock origin success, destination failure
        self.mock_location_selector.select_location.side_effect = [
            {"success": True, "coordinates": {"lat": 1, "lng": 1}},
            {"success": False, "error": "Map error"},
        ]

        with self.assertRaises(WaybillError) as context:
            await self.manager.create_waybill_with_map(data)

        self.assertIn("انتخاب مقصد با شکست مواجه شد", str(context.exception))
        self.mock_interactor.screenshot.assert_called_once_with("waybill_map_error")

    async def test_route_calculation_logic(self):
        """Test that route calculation is skipped if coordinates are missing."""
        data = {
            "origin": {"province": "Tehran"},  # No coords
            "destination": {"province": "Mashhad"},  # No coords
        }

        # Mock success but no coordinates returned
        self.mock_location_selector.select_location.side_effect = [
            {"success": True, "coordinates": None},
            {"success": True, "coordinates": None},
        ]

        # Mock tracking code extraction to avoid failure later
        mock_element = AsyncMock()
        mock_element.text_content.return_value = "123456"
        self.mock_page.query_selector.return_value = mock_element

        result = await self.manager.create_waybill_with_map(data)

        self.mock_route_calculator.calculate_distance.assert_not_called()
        self.assertIsNone(result.get("route"))

    async def test_fill_financial_info(self):
        """Test financial info filling logic."""
        financial_data = {"cost": 1000, "payment_method": "Cash"}

        # We need to test the private method _fill_financial_info indirectly or call it directly
        # Calling directly for unit testing is acceptable in Python
        await self.manager._fill_financial_info(financial_data)

        self.mock_interactor.safe_fill.assert_called_with(
            'input[name="TransportCost"]', "1000"
        )
        # _select_dropdown calls page.select_option
        self.mock_page.select_option.assert_called()

    async def test_submit_waybill_tracking_extraction(self):
        """Test extraction of tracking code from different sources."""
        # 1. Test extraction from element text
        mock_element = AsyncMock()
        mock_element.text_content.return_value = "شماره رهگیری: 987654"
        self.mock_page.query_selector.return_value = mock_element

        code = await self.manager._extract_tracking_code()
        self.assertEqual(code, "987654")

        # 2. Test extraction from URL fallback
        self.mock_page.query_selector.side_effect = Exception("Not found")
        self.mock_page.url = "http://example.com/waybill/TRACK12345678"

        code = await self.manager._extract_tracking_code()
        self.assertEqual(code, "TRACK12345678")

    async def test_submit_waybill_rejects_click_failure(self):
        """Submit should fail when click action cannot be performed."""
        self.mock_interactor.safe_click = AsyncMock(return_value=False)

        with self.assertRaises(WaybillError) as context:
            await self.manager._submit_waybill()

        self.assertIn("کلیک روی دکمه ثبت ناموفق بود", str(context.exception))
        self.assertEqual(self.mock_interactor.safe_click.await_count, 2)

    async def test_submit_waybill_rejects_unconfirmed_result(self):
        """Submit should fail when no tracking code or success marker exists."""
        self.mock_interactor.safe_click = AsyncMock(return_value=True)
        self.manager._extract_tracking_code = AsyncMock(return_value=None)
        self.manager._is_submission_successful = AsyncMock(return_value=False)
        self.manager._extract_form_errors = AsyncMock(
            return_value="اعتبارسنجی فرم ناموفق بود"
        )

        with self.assertRaises(WaybillError) as context:
            await self.manager._submit_waybill()

        self.assertIn("اعتبارسنجی فرم ناموفق بود", str(context.exception))

    async def test_create_waybill_generic_error(self):
        """Test handling of unexpected exceptions."""
        data = {"sender": {}}
        # Mock page.goto to raise an exception
        self.mock_page.goto.side_effect = Exception("Network Error")

        with self.assertRaises(WaybillError) as context:
            await self.manager.create_waybill_with_map(data)

        self.assertIn(
            "ایجاد بارنامه با شکست مواجه شد: Network Error", str(context.exception)
        )
        self.mock_interactor.screenshot.assert_called_once_with("waybill_map_error")


if __name__ == "__main__":
    unittest.main()
