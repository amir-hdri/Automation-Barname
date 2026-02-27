"""
انتخابگر مکان با قابلیت جایگزینی: نقشه ← منوی کشویی ← ورودی متنی
"""

import asyncio
from typing import Dict, Any, Optional, List
from playwright.async_api import Page
import logging

from app.automation.map_controller import MapController, GeoCoordinate
from app.core.exceptions import LocationSelectionError
from app.automation.script_loader import script_loader
from app.automation.selectors import LocationSelectors

logger = logging.getLogger(__name__)


class LocationSelector:
    """
    انتخابگر هوشمند مکان که روش‌های مختلف را امتحان می‌کند:
    ۱. انتخاب مبتنی بر نقشه
    ۲. انتخاب آبشاری (استان ← شهر ← منطقه)
    ۳. ورودی متنی با تکمیل خودکار
    """

    def __init__(self, page: Page):
        self.page = page
        self.map_controller = MapController(page)

    async def select_location(
        self,
        location_data: Dict[str, Any],
        origin: bool = True
    ) -> Dict[str, Any]:
        """
        انتخاب مکان با استفاده از بهترین روش موجود

        Args:
            location_data: {
                "province": "تهران",
                "city": "تهران",
                "district": "منطقه ۱",
                "address": "خیابان آزادی",
                "coordinates": {"lat": 35.6892, "lng": 51.3890}
            }
            origin: True برای مبدا، False برای مقصد

        Returns:
            نتیجه انتخاب همراه با روش استفاده شده
        """
        prefix = "Origin" if origin else "Destination"

        # روش ۱: تلاش برای انتخاب با نقشه
        map_result = await self._try_map_selection(location_data, prefix)
        if map_result["success"]:
            return map_result

        # روش ۲: تلاش برای انتخاب با منوی کشویی
        dropdown_result = await self._try_dropdown_selection(location_data, prefix)
        if dropdown_result["success"]:
            return dropdown_result

        # روش ۳: تلاش برای ورودی متنی
        text_result = await self._try_text_input(location_data, prefix)
        if text_result["success"]:
            return text_result

        raise LocationSelectionError(
            f"انتخاب مکان با شکست مواجه شد: {location_data}"
        )

    async def _try_map_selection(
        self,
        location_data: Dict[str, Any],
        prefix: str
    ) -> Dict[str, Any]:
        """تلاش برای انتخاب مکان با استفاده از نقشه"""

        # تشخیص وجود نقشه
        map_type = await self.map_controller.detect_map_type()

        if not map_type:
            return {"success": False, "method": "map", "error": "نقشه‌ای یافت نشد"}

        coordinates = location_data.get("coordinates")
        if not coordinates:
            # ژئوکد کردن آدرس
            coordinates = await self._geocode_address(location_data)

        if not coordinates:
            return {"success": False, "method": "map", "error": "مختصات یافت نشد"}

        # یافتن ورودی‌های مرتبط با نقشه
        search_input = await self._find_map_search_input(prefix)

        try:
            location = GeoCoordinate(
                latitude=coordinates["lat"],
                longitude=coordinates["lng"],
                address=location_data.get("address"),
            )

            selected = await self.map_controller.select_on_map(
                selector=None,
                location=location,
                search_input_selector=search_input,
            )

            if not selected:
                return {
                    "success": False,
                    "method": "map",
                    "error": "انتخاب نقطه روی نقشه انجام نشد",
                }

            await self.map_controller.wait_for_map_idle()

            return {
                "success": True,
                "method": "map",
                "coordinates": {
                    "lat": location.latitude,
                    "lng": location.longitude,
                },
                "map_type": map_type,
            }

        except Exception as e:
            return {"success": False, "method": "map", "error": str(e)}

    async def _try_dropdown_selection(
        self,
        location_data: Dict[str, Any],
        prefix: str
    ) -> Dict[str, Any]:
        """
        تلاش برای انتخاب آبشاری
        استان ← شهر ← منطقه
        """

        try:
            # الگوهای انتخابگر رایج
            selectors = {
                "province": [
                    s.format(prefix=prefix, prefix_lower=prefix.lower())
                    for s in LocationSelectors.PROVINCE_TEMPLATES
                ],
                "city": [
                    s.format(prefix=prefix, prefix_lower=prefix.lower())
                    for s in LocationSelectors.CITY_TEMPLATES
                ],
                "district": [
                    s.format(prefix=prefix, prefix_lower=prefix.lower())
                    for s in LocationSelectors.DISTRICT_TEMPLATES
                ]
            }

            # انتخاب استان
            province_selectors = selectors["province"]
            province_selected = await self._select_from_options(
                province_selectors,
                location_data.get("province", "")
            )

            if not province_selected:
                return {
                    "success": False,
                    "method": "dropdown",
                    "error": "انتخاب استان با شکست مواجه شد"
                }

            await asyncio.sleep(0.5)  # انتظار برای بارگذاری شهرها

            # انتخاب شهر
            city_selectors = selectors["city"]
            city_selected = await self._select_from_options(
                city_selectors,
                location_data.get("city", "")
            )

            if not city_selected:
                return {
                    "success": False,
                    "method": "dropdown",
                    "error": "انتخاب شهر با شکست مواجه شد"
                }

            await asyncio.sleep(0.5)  # انتظار برای بارگذاری مناطق

            # انتخاب منطقه (اختیاری)
            district_selectors = selectors["district"]
            await self._select_from_options(
                district_selectors,
                location_data.get("district", "")
            )

            # پر کردن آدرس متنی اگر وجود داشته باشد
            address_selectors = [
                s.format(prefix=prefix, prefix_lower=prefix.lower())
                for s in LocationSelectors.ADDRESS_TEMPLATES
            ]

            for selector in address_selectors:
                try:
                    await self.page.fill(selector, location_data.get("address", ""))
                    break
                except:
                    continue

            return {
                "success": True,
                "method": "dropdown",
                "province": location_data.get("province"),
                "city": location_data.get("city"),
                "district": location_data.get("district")
            }

        except Exception as e:
            return {"success": False, "method": "dropdown", "error": str(e)}

    async def _try_text_input(
        self,
        location_data: Dict[str, Any],
        prefix: str
    ) -> Dict[str, Any]:
        """تلاش برای ورودی متنی با تکمیل خودکار"""

        try:
            # یافتن ورودی تکمیل خودکار
            input_selectors = [
                s.format(prefix=prefix, prefix_lower=prefix.lower())
                for s in LocationSelectors.INPUT_TEMPLATES
            ]

            search_text = f"{location_data.get('city', '')} {location_data.get('address', '')}"

            for selector in input_selectors:
                try:
                    # پر کردن ورودی
                    await self.page.fill(selector, search_text)
                    await asyncio.sleep(0.5)

                    # انتظار برای تکمیل خودکار
                    await asyncio.sleep(1)

                    # کلیک روی اولین پیشنهاد
                    suggestion_selectors = LocationSelectors.SUGGESTION_SELECTORS

                    for sugg_selector in suggestion_selectors:
                        sugg = await self.page.query_selector(sugg_selector)
                        if sugg:
                            await sugg.click()
                            return {
                                "success": True,
                                "method": "autocomplete",
                                "search": search_text
                            }

                except:
                    continue

            return {
                "success": False,
                "method": "autocomplete",
                "error": "هیچ پیشنهادی یافت نشد"
            }

        except Exception as e:
            return {"success": False, "method": "autocomplete", "error": str(e)}

    async def _select_from_options(
        self,
        selectors: List[str],
        value: str
    ) -> bool:
        """انتخاب گزینه از منوی کشویی بر اساس متن یا مقدار"""

        for selector in selectors:
            try:
                # بررسی وجود عنصر
                element = await self.page.query_selector(selector)
                if not element:
                    continue

                # دریافت تمام گزینه‌ها
                options = await self.page.query_selector_all(f'{selector} option')

                for option in options:
                    option_text = await option.text_content()
                    option_value = await option.get_attribute('value')

                    if value in (option_text or "") or value in (option_value or ""):
                        await self.page.select_option(selector, value=option_value)
                        return True

                # تلاش برای تطابق جزئی
                for option in options:
                    option_text = await option.text_content() or ""
                    if value in option_text or option_text in value:
                        option_value = await option.get_attribute('value')
                        await self.page.select_option(selector, value=option_value)
                        return True

            except Exception as e:
                continue

        return False

    async def _find_map_search_input(self, prefix: str) -> Optional[str]:
        """یافتن انتخابگر ورودی جستجوی نقشه"""

        selectors = [
            s.format(prefix=prefix, prefix_lower=prefix.lower())
            for s in LocationSelectors.MAP_SEARCH_TEMPLATES
        ]

        for selector in selectors:
            element = await self.page.query_selector(selector)
            if element:
                return selector

        return None

    async def _geocode_address(self, location_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        تبدیل آدرس به مختصات با استفاده از سرویس خارجی
        """
        import aiohttp

        address = f"{location_data.get('city', '')}, {location_data.get('address', '')}, Iran"

        try:
            # استفاده از Nominatim (OpenStreetMap)
            async with aiohttp.ClientSession() as session:
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    "q": address,
                    "format": "json",
                    "limit": 1
                }
                headers = {
                    "User-Agent": "UTCMS-Automation/1.0"
                }

                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data:
                            return {
                                "lat": float(data[0]["lat"]),
                                "lng": float(data[0]["lon"])
                            }
        except Exception as e:
            logger.warning(
                "geocoding_failed",
                extra={"extra_fields": {"address": address, "error": str(e)}},
            )

        return None


class RouteCalculator:
    """محاسبه مسیر بین دو نقطه"""

    def __init__(self, page: Page):
        self.page = page

    async def calculate_distance(
        self,
        origin: GeoCoordinate,
        destination: GeoCoordinate
    ) -> Dict[str, Any]:
        """
        محاسبه مسافت و زمان بین دو نقطه

        استفاده از جاوااسکریپت برای محاسبه یا استخراج از صفحه
        """

        script = script_loader.load("calculate_distance")

        try:
            result = await self.page.evaluate(script, {
                "originLat": origin.latitude,
                "originLng": origin.longitude,
                "destLat": destination.latitude,
                "destLng": destination.longitude
            })
            return result or {}
        except:
            # محاسبه با استفاده از پایتون
            return self._calculate_haversine(origin, destination)

    def _calculate_haversine(
        self,
        origin: GeoCoordinate,
        destination: GeoCoordinate
    ) -> Dict[str, Any]:
        """محاسبه فاصله با استفاده از فرمول هاورسین"""
        import math

        R = 6371  # شعاع زمین به کیلومتر

        lat1 = math.radians(origin.latitude)
        lat2 = math.radians(destination.latitude)
        dlat = math.radians(destination.latitude - origin.latitude)
        dlon = math.radians(destination.longitude - origin.longitude)

        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(lat1) * math.cos(lat2) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        # تخمین زمان
        duration_min = (distance / 60) * 60  # فرض ۶۰ کیلومتر بر ساعت

        return {
            "distance": f"{distance:.2f} km",
            "distance_value": distance * 1000,
            "duration": f"{int(duration_min)} mins",
            "duration_value": duration_min * 60,
            "method": "haversine"
        }
