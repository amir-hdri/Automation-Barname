import unittest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from app.automation.location_selector import LocationSelector


class TestLocationSelector(unittest.IsolatedAsyncioTestCase):
    async def test_try_dropdown_selection_success(self):
        # Setup
        page = AsyncMock()
        selector = LocationSelector(page)

        # Mock _select_from_options to always return True
        selector._select_from_options = AsyncMock(return_value=True)

        # Mock page.fill for address
        page.fill = AsyncMock()

        # Mock asyncio.sleep to speed up tests
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            location_data = {
                "province": "Tehran",
                "city": "Tehran City",
                "district": "District 1",
                "address": "Azadi Square",
            }
            prefix = "Origin"

            # Execute
            result = await selector._try_dropdown_selection(location_data, prefix)

            # Verify Result
            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "dropdown")
            self.assertEqual(result["province"], "Tehran")

            # Verify Interactions
            # 1. Province Selection
            self.assertTrue(selector._select_from_options.called)
            # check calls
            calls = selector._select_from_options.call_args_list

            # Province call
            self.assertIn('select[name="OriginProvince"]', calls[0][0][0])
            self.assertEqual(calls[0][0][1], "Tehran")

            # Sleep 0.5s
            mock_sleep.assert_any_call(0.5)

            # City call
            self.assertIn('select[name="OriginCity"]', calls[1][0][0])
            self.assertEqual(calls[1][0][1], "Tehran City")

            # District call
            self.assertIn('select[name="OriginDistrict"]', calls[2][0][0])
            self.assertEqual(calls[2][0][1], "District 1")

            # Address fill
            page.fill.assert_called()
            fill_args = page.fill.call_args[0]
            self.assertIn(
                'textarea[name="OriginAddress"]', fill_args[0] or str(fill_args)
            )
            self.assertEqual(fill_args[1], "Azadi Square")

    async def test_try_dropdown_selection_province_fail(self):
        # Setup
        page = AsyncMock()
        selector = LocationSelector(page)

        # Mock province failure
        selector._select_from_options = AsyncMock(side_effect=[False, True, True])

        location_data = {"province": "Unknown"}
        prefix = "Origin"

        # Execute
        result = await selector._try_dropdown_selection(location_data, prefix)

        # Verify
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "انتخاب استان با شکست مواجه شد")

        # Should only try province
        self.assertEqual(selector._select_from_options.call_count, 1)

    async def test_try_dropdown_selection_city_fail(self):
        # Setup
        page = AsyncMock()
        selector = LocationSelector(page)

        # Mock province success, city failure
        selector._select_from_options = AsyncMock(side_effect=[True, False, True])

        with patch("asyncio.sleep", new_callable=AsyncMock):
            location_data = {"province": "Tehran", "city": "Unknown"}
            prefix = "Origin"

            # Execute
            result = await selector._try_dropdown_selection(location_data, prefix)

            # Verify
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "انتخاب شهر با شکست مواجه شد")

            # Should try province and city
            self.assertEqual(selector._select_from_options.call_count, 2)


if __name__ == "__main__":
    unittest.main()
