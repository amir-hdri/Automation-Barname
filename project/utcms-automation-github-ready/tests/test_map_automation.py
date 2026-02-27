import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from app.automation.map_controller import MapController, GeoCoordinate
from app.automation.location_selector import LocationSelector
from app.automation.waybill_enhanced import EnhancedWaybillManager


class TestMapAutomation(unittest.IsolatedAsyncioTestCase):
    async def test_detect_google_map(self):
        page = AsyncMock()
        # Mock evaluate to return true for Google Maps check (first call)
        page.evaluate.side_effect = [True, False, False, False]

        controller = MapController(page)
        map_type = await controller.detect_map_type()
        self.assertEqual(map_type, "google_maps")

    async def test_location_selector_map_fallback(self):
        page = AsyncMock()
        selector = LocationSelector(page)

        # Mock map controller to fail detection
        selector.map_controller.detect_map_type = AsyncMock(return_value=None)

        # Mock dropdown selection to succeed
        # We patch the method on the instance
        selector._try_dropdown_selection = AsyncMock(
            return_value={"success": True, "method": "dropdown"}
        )

        location_data = {"province": "Tehran", "city": "Tehran", "address": "Azadi"}
        result = await selector.select_location(location_data)

        self.assertTrue(result["success"])
        self.assertEqual(result["method"], "dropdown")

    async def test_location_selector_map_found_but_failed(self):
        page = AsyncMock()
        selector = LocationSelector(page)

        # Mock map selection to fail directly (we can mock the internal method _try_map_selection)
        # Note: In real code select_location calls _try_map_selection first.
        selector._try_map_selection = AsyncMock(
            return_value={"success": False, "method": "map", "error": "Fail"}
        )

        # Mock dropdown selection to succeed
        selector._try_dropdown_selection = AsyncMock(
            return_value={"success": True, "method": "dropdown"}
        )

        location_data = {
            "province": "Tehran",
            "city": "Tehran",
            "address": "Azadi",
            "coordinates": {"lat": 35.0, "lng": 51.0},
        }
        result = await selector.select_location(location_data)

        self.assertTrue(result["success"])
        self.assertEqual(result["method"], "dropdown")

    async def test_haversine_calculation(self):
        # We don't need a page for haversine fallback in RouteCalculator
        # but the class requires it in init
        page = AsyncMock()
        from app.automation.location_selector import RouteCalculator

        calculator = RouteCalculator(page)
        # Mock evaluate to fail so it falls back to python
        page.evaluate.side_effect = Exception("JS Error")

        origin = GeoCoordinate(35.6892, 51.3890)
        dest = GeoCoordinate(36.2972, 59.6067)  # Mashhad approx

        result = await calculator.calculate_distance(origin, dest)

        self.assertEqual(result["method"], "haversine")
        self.assertTrue("km" in result["distance"])
        # Expected distance is around 740km
        self.assertTrue(result["distance_value"] > 700000)

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_search_address(self, mock_sleep):
        page = AsyncMock()
        controller = MapController(page)

        # Mock evaluate to return a list of suggestions
        expected_suggestions = [
            {"text": "Place A", "lat": 10.0, "lng": 20.0},
            {"text": "Place B", "lat": 11.0, "lng": 21.0},
        ]
        page.evaluate.return_value = expected_suggestions

        query = "Test Place"
        input_selector = "#search"

        result = await controller.search_address(query, input_selector)

        # Verify page interactions
        page.fill.assert_awaited_with(input_selector, query)
        page.evaluate.assert_awaited_once()

        # Verify result
        self.assertEqual(result, expected_suggestions)
        # Verify sleeps were called (0.5s + 1s)
        self.assertEqual(mock_sleep.await_count, 2)


if __name__ == "__main__":
    unittest.main()
