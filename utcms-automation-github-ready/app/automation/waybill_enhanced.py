"""
مدیریت پیشرفته بارنامه با پشتیبانی از نقشه
"""

import asyncio
import inspect
import logging
import random
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from playwright.async_api import Page, BrowserContext

from app.core.config import utcms_config
from app.core.exceptions import WaybillError
from app.core.network import is_retryable_network_error
from app.automation.browser import PageInteractor
from app.automation.map_controller import MapController, GeoCoordinate
from app.automation.location_selector import LocationSelector, RouteCalculator

logger = logging.getLogger(__name__)


class EnhancedWaybillManager:
    """مدیریت بارنامه با پشتیبانی کامل از نقشه و مکان‌یابی"""

    def __init__(self, page: Page, context: BrowserContext):
        self.page = page
        self.context = context
        self.interactor = PageInteractor(page)
        self.map_controller = MapController(page)
        self.location_selector = LocationSelector(page)
        self.route_calculator = RouteCalculator(page)

    async def _resolve_maybe_awaitable(self, value: Any) -> Any:
        resolved = value
        for _ in range(3):
            if inspect.isawaitable(resolved):
                resolved = await resolved
                continue
            break
        return resolved

    async def _current_url(self) -> str:
        raw_url = getattr(self.page, "url", "")
        try:
            value = await self._resolve_maybe_awaitable(raw_url)
        except Exception:
            return ""
        if value is None:
            return ""
        return value if isinstance(value, str) else str(value)

    async def _safe_page_title(self) -> str:
        try:
            raw_title = await self.page.title()
            value = await self._resolve_maybe_awaitable(raw_title)
        except Exception:
            value = ""
        if value is None:
            return ""
        return (value if isinstance(value, str) else str(value)).strip()

    async def _as_clean_text(self, value: Any) -> str:
        try:
            resolved = await self._resolve_maybe_awaitable(value)
        except Exception:
            return ""
        if resolved is None:
            return ""
        return (resolved if isinstance(resolved, str) else str(resolved)).strip()

    async def _goto_with_retry(self, url: str, wait_until: Optional[str] = None) -> None:
        attempts = max(1, utcms_config.PAGE_GOTO_MAX_RETRIES + 1)
        base_delay = max(0.1, utcms_config.PAGE_GOTO_RETRY_BASE_SECONDS)
        jitter = max(0.0, utcms_config.PAGE_GOTO_RETRY_JITTER_SECONDS)
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                if wait_until:
                    await self.page.goto(url, wait_until=wait_until)
                else:
                    await self.page.goto(url)
                return
            except Exception as exc:
                last_error = exc
                if attempt >= attempts or not is_retryable_network_error(exc):
                    raise
                delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0, jitter)
                await asyncio.sleep(delay)

        if last_error:
            raise last_error

    async def create_waybill_with_map(
        self,
        data: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        ایجاد بارنامه با انتخاب مکان از طریق نقشه یا منوی کشویی

        Args:
            data: {
                "sender": {...},
                "receiver": {...},
                "origin": {
                    "province": "تهران",
                    "city": "تهران",
                    "district": "منطقه ۱",
                    "address": "خیابان آزادی",
                    "coordinates": {"lat": 35.6892, "lng": 51.3890}
                },
                "destination": {
                    "province": "مشهد",
                    "city": "مشهد",
                    "district": "منطقه ۲",
                    "address": "خیابان امام رضا",
                    "coordinates": {"lat": 36.2972, "lng": 59.6067}
                },
                ...
            }
        """
        try:
            # رفتن به صفحه ایجاد بارنامه
            await self._goto_with_retry(utcms_config.WAYBILL_URL)
            await asyncio.sleep(2)
            await self._ensure_waybill_form_page()

            # پر کردن اطلاعات فرستنده
            await self._fill_sender_info(data.get("sender", {}))

            # پر کردن اطلاعات گیرنده
            await self._fill_receiver_info(data.get("receiver", {}))

            # انتخاب مکان مبدا (نقشه ← منوی کشویی ← متن)
            origin_result = await self.location_selector.select_location(
                data.get("origin", {}),
                origin=True
            )

            if not origin_result["success"]:
                raise WaybillError(f"انتخاب مبدا با شکست مواجه شد: {origin_result}")

            # انتخاب مکان مقصد
            dest_result = await self.location_selector.select_location(
                data.get("destination", {}),
                origin=False
            )

            if not dest_result["success"]:
                raise WaybillError(f"انتخاب مقصد با شکست مواجه شد: {dest_result}")

            # محاسبه مسیر در صورت وجود مختصات
            route_info = None
            if (origin_result.get("coordinates") and
                dest_result.get("coordinates")):

                route_info = await self.route_calculator.calculate_distance(
                    GeoCoordinate(
                        latitude=origin_result["coordinates"]["lat"],
                        longitude=origin_result["coordinates"]["lng"]
                    ),
                    GeoCoordinate(
                        latitude=dest_result["coordinates"]["lat"],
                        longitude=dest_result["coordinates"]["lng"]
                    )
                )

            # پر کردن اطلاعات بار
            await self._fill_cargo_info(data.get("cargo", {}))

            # پر کردن اطلاعات ناوگان
            await self._fill_vehicle_info(data.get("vehicle", {}))

            # پر کردن اطلاعات مالی
            await self._fill_financial_info(data.get("financial", {}))

            # حالت ایمن: ارسال نهایی انجام نمی‌شود و فقط آمادگی ثبت ارزیابی می‌شود.
            if dry_run:
                result = {
                    "success": True,
                    "status": "validated",
                    "validation_summary": {
                        "ready_for_submit": True,
                        "route_calculated": route_info is not None,
                    },
                    "url": await self._current_url(),
                }
            else:
                # ثبت و دریافت کد رهگیری
                result = await self._submit_waybill()

            # افزودن اطلاعات مسیر به نتیجه
            if route_info:
                result["route"] = route_info

            result["origin_method"] = origin_result.get("method")
            result["destination_method"] = dest_result.get("method")
            if origin_result.get("map_type"):
                result["origin_map_type"] = origin_result.get("map_type")
            if dest_result.get("map_type"):
                result["destination_map_type"] = dest_result.get("map_type")

            return result

        except Exception as e:
            await self.interactor.screenshot("waybill_map_error")
            raise WaybillError(f"ایجاد بارنامه با شکست مواجه شد: {str(e)}")

    async def _ensure_waybill_form_page(self):
        """
        In some deployments, the configured create URL lands on a not-found shell page.
        Try to discover and open the real "حمل بارنامه" page from the side menu.
        """
        if await self._is_waybill_form_ready():
            return

        current_url = await self._current_url()
        if await self._looks_like_not_found_page():
            try:
                html = await self.page.content()
                with open("waybill_notfound_snapshot.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception:
                pass

            recovery_selectors = (
                "a:has-text('ورود مجدد به سامانه')",
                "button:has-text('ورود مجدد به سامانه')",
                "a:has-text('بازگشت به خانه')",
                "button:has-text('بازگشت به خانه')",
                "a:has-text('بازگشت به صفحه اصلی')",
                "button:has-text('بازگشت به صفحه اصلی')",
            )
            for selector in recovery_selectors:
                try:
                    action = self.page.locator(selector).first
                    if await action.count() == 0:
                        continue

                    href = await action.get_attribute("href")
                    if href:
                        await self._goto_with_retry(urljoin(current_url, href), wait_until="domcontentloaded")
                    else:
                        await action.click()
                        await self.page.wait_for_load_state("domcontentloaded")

                    await asyncio.sleep(1.2)
                    if await self._is_waybill_form_ready():
                        return
                    current_url = await self._current_url()
                except Exception:
                    continue

        try:
            menu_links = await self.page.eval_on_selector_all(
                "a",
                "els => els.map(e => ({text:(e.innerText||'').trim(), href:(e.getAttribute('href')||'').trim()}))",
            )
            interesting = [
                item for item in menu_links
                if ("بارنامه" in item.get("text", "")) or ("Waybill" in item.get("href", ""))
            ]
            logger.info(
                "waybill_menu_links_discovered",
                extra={"extra_fields": {"url": current_url, "links": interesting[:20]}},
            )
            if any("درخواست دسترسی" in item.get("text", "") for item in interesting):
                raise WaybillError("حساب کاربری به ماژول صدور بارنامه دسترسی ندارد")
        except WaybillError:
            raise
        except Exception:
            pass

        menu_selectors = (
            "a:has-text('حمل بارنامه')",
            "a:has-text('صدور بارنامه')",
            "a[href*='Waybill' i]",
        )

        for selector in menu_selectors:
            try:
                link = self.page.locator(selector).first
                if await link.count() == 0:
                    continue

                href = await link.get_attribute("href")
                if href:
                    await self._goto_with_retry(urljoin(current_url, href), wait_until="domcontentloaded")
                else:
                    await link.click()
                    await self.page.wait_for_load_state("domcontentloaded")

                await asyncio.sleep(1.5)
                if await self._is_waybill_form_ready():
                    return
            except Exception:
                continue

        for candidate_url in self._waybill_url_candidates():
            try:
                await self._goto_with_retry(candidate_url, wait_until="domcontentloaded")
                await asyncio.sleep(1.2)
                if await self._is_waybill_form_ready():
                    return
            except Exception:
                continue

        current_url = (await self._current_url()).lower()
        try:
            lacks_access_banner = await self.page.query_selector(
                "text=نامه درخواست دسترسی به سامانه صدور بارنامه شهری"
            )
        except Exception:
            lacks_access_banner = None

        if "/home/infoindex" in current_url or lacks_access_banner:
            raise WaybillError("حساب کاربری به ماژول صدور بارنامه دسترسی ندارد")

        if not await self._is_waybill_form_ready():
            raise WaybillError("فرم بارنامه پس از بازیابی در دسترس نیست")

    def _waybill_url_candidates(self) -> list[str]:
        base_url = utcms_config.BASE_URL.rstrip("/")
        candidates = [
            utcms_config.WAYBILL_URL,
            f"{base_url}/Barname/Waybill/Create",
            f"{base_url}/barname/Document/HagigiHogugi",
            f"{base_url}/Barname/Document/HagigiHogugi",
        ]
        unique: list[str] = []
        for item in candidates:
            if item and item not in unique:
                unique.append(item)
        return unique

    async def _is_waybill_form_ready(self) -> bool:
        markers = (
            'input[name="txtSenderFirstName"]',
            'input[name="SenderName"]',
            'input[name="txtReceiverFirstName"]',
            'input[name="ReceiverName"]',
            '#btnGoLVL2',
            '#GoLVL2',
        )
        for selector in markers:
            try:
                if await self.page.query_selector(selector):
                    return True
            except Exception:
                continue
        return False

    async def _looks_like_not_found_page(self) -> bool:
        title = await self._safe_page_title()
        current_url = (await self._current_url()).strip().lower()

        if "یافت نشد" in title or "خطا در سامانه" in title:
            return True

        # In tests/mocks URL may not be a real HTTP URL; avoid false positives.
        if current_url and not current_url.startswith(("http://", "https://")):
            return False

        error_url_fragments = ("/error", "/exception", "/fault")
        if any(fragment in current_url for fragment in error_url_fragments):
            return True

        not_found_markers = (
            "text=یافت نشد",
            "text=صفحه مورد نظر شما یافت نشد",
            "text=درخواست مجاز نمی باشد",
            "text=خطا در سامانه",
            "text=متاسفانه در هنگام پردازش درخواست شما خطایی رخ داده است",
            "text=ورود مجدد به سامانه",
        )
        for marker in not_found_markers:
            try:
                if await self.page.query_selector(marker):
                    return True
            except Exception:
                continue
        return False

    async def _fill_sender_info(self, sender: Dict[str, str]):
        """پر کردن اطلاعات فرستنده"""
        await self._select_dropdown_with_fallback(
            [
                'select[name="senderSelectType"]',
                'select[id="senderSelectType"]',
            ],
            "حقیقی",
            "نوع فرستنده",
            required=False,
        )

        sender_name = (sender.get("name") or "").strip()
        sender_first = sender_name
        sender_last = sender_name
        if sender_name:
            parts = sender_name.split(maxsplit=1)
            sender_first = parts[0]
            sender_last = parts[1] if len(parts) > 1 else parts[0]

        if sender_name:
            await self.interactor.safe_fill('input[name="SenderName"]', sender_name)

        await self._fill_with_fallback(
            [
                'input[name="txtSenderFirstName"]',
                'input[id="txtSenderFirstName"]',
                'input[name="SenderName"]',
                'input[id="SenderName"]',
                'input[name*="sender" i][name*="name" i]',
                'input[id*="sender" i][id*="name" i]',
                'input[name*="consignor" i]',
            ],
            sender_first,
            "نام فرستنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtSenderLastName"]',
                'input[id="txtSenderLastName"]',
            ],
            sender_last,
            "نام خانوادگی فرستنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtSenderMobile"]',
                'input[id="txtSenderMobile"]',
                'input[name="SenderPhone"]',
                'input[id="SenderPhone"]',
                'input[name*="sender" i][name*="phone" i]',
                'input[id*="sender" i][id*="phone" i]',
            ],
            sender.get("phone", ""),
            "تلفن فرستنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtSenderTell"]',
                'input[id="txtSenderTell"]',
                'textarea[name="SenderAddress"]',
                'input[name="SenderAddress"]',
                'textarea[id="SenderAddress"]',
                'textarea[name*="sender" i][name*="address" i]',
            ],
            sender.get("address", ""),
            "آدرس فرستنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtSenderNationalCode"]',
                'input[id="txtSenderNationalCode"]',
                'input[name="SenderNationalCode"]',
                'input[name="NationalCode"]',
                'input[id="SenderNationalCode"]',
                'input[id="NationalCode"]',
                'input[name*="sender" i][name*="national" i]',
            ],
            sender.get("national_code", ""),
            "کد ملی فرستنده",
        )
        await self.interactor.safe_click(
            '#btnGoLVL2, #GoLVL2, button:has-text("مرحله بعد")',
            wait_for_navigation=False,
            timeout=2500,
        )
        await asyncio.sleep(0.3)

    async def _fill_receiver_info(self, receiver: Dict[str, str]):
        """پر کردن اطلاعات گیرنده"""
        await self._select_dropdown_with_fallback(
            [
                'select[name="receiverSelectType"]',
                'select[id="receiverSelectType"]',
            ],
            "حقیقی",
            "نوع گیرنده",
            required=False,
        )

        receiver_name = (receiver.get("name") or "").strip()
        receiver_first = receiver_name
        receiver_last = receiver_name
        if receiver_name:
            parts = receiver_name.split(maxsplit=1)
            receiver_first = parts[0]
            receiver_last = parts[1] if len(parts) > 1 else parts[0]

        if receiver_name:
            await self.interactor.safe_fill('input[name="ReceiverName"]', receiver_name)

        await self._fill_with_fallback(
            [
                'input[name="txtReceiverFirstName"]',
                'input[id="txtReceiverFirstName"]',
                'input[name="ReceiverName"]',
                'input[id="ReceiverName"]',
                'input[name*="receiver" i][name*="name" i]',
                'input[id*="receiver" i][id*="name" i]',
                'input[name*="consignee" i]',
            ],
            receiver_first,
            "نام گیرنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtReceiverLastName"]',
                'input[id="txtReceiverLastName"]',
            ],
            receiver_last,
            "نام خانوادگی گیرنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtReceiverMobile"]',
                'input[id="txtReceiverMobile"]',
                'input[name="ReceiverPhone"]',
                'input[id="ReceiverPhone"]',
                'input[name*="receiver" i][name*="phone" i]',
                'input[id*="receiver" i][id*="phone" i]',
            ],
            receiver.get("phone", ""),
            "تلفن گیرنده",
        )
        await self._fill_with_fallback(
            [
                'input[name="txtReceiverTell"]',
                'input[id="txtReceiverTell"]',
                'textarea[name="ReceiverAddress"]',
                'input[name="ReceiverAddress"]',
                'textarea[id="ReceiverAddress"]',
                'textarea[name*="receiver" i][name*="address" i]',
            ],
            receiver.get("address", ""),
            "آدرس گیرنده",
        )
        await self.interactor.safe_click(
            '#btnGoLVL3, #GoLVL3, button:has-text("مرحله بعد")',
            wait_for_navigation=False,
            timeout=2500,
        )
        await asyncio.sleep(0.3)

    async def _fill_cargo_info(self, cargo: Dict[str, Any]):
        """پر کردن اطلاعات کالا"""
        # انتخاب نوع کالا
        if cargo.get("type"):
            await self._select_dropdown_with_fallback(
                [
                    'select[name="CargoType"]',
                    'select[id="CargoType"]',
                    'select[name*="cargo" i][name*="type" i]',
                ],
                cargo["type"],
                "نوع کالا",
                required=False,
            )

        await self._fill_with_fallback(
            [
                'input[name="CargoWeight"]',
                'input[id="CargoWeight"]',
                'input[name*="cargo" i][name*="weight" i]',
            ],
            str(cargo.get("weight", "")),
            "وزن کالا",
        )
        await self._fill_with_fallback(
            [
                'input[name="CargoCount"]',
                'input[id="CargoCount"]',
                'input[name*="cargo" i][name*="count" i]',
            ],
            str(cargo.get("count", "1")),
            "تعداد کالا",
        )
        await self._fill_with_fallback(
            [
                'textarea[name="CargoDescription"]',
                'input[name="CargoDescription"]',
                'textarea[id="CargoDescription"]',
                'textarea[name*="cargo" i][name*="description" i]',
            ],
            cargo.get("description", ""),
            "توضیحات کالا",
        )

    async def _fill_vehicle_info(self, vehicle: Dict[str, str]):
        """پر کردن اطلاعات ناوگان"""
        await self._fill_with_fallback(
            [
                'input[name="DriverNationalCode"]',
                'input[id="DriverNationalCode"]',
                'input[name*="driver" i][name*="national" i]',
            ],
            vehicle.get("driver_national_code", ""),
            "کد ملی راننده",
        )
        await self._fill_with_fallback(
            [
                'input[name="DriverPhone"]',
                'input[id="DriverPhone"]',
                'input[name*="driver" i][name*="phone" i]',
            ],
            vehicle.get("driver_phone", ""),
            "تلفن راننده",
        )
        await self._fill_with_fallback(
            [
                'input[name="PlateNumber"]',
                'input[id="PlateNumber"]',
                'input[name*="plate" i]',
            ],
            vehicle.get("plate", ""),
            "پلاک خودرو",
        )

        if vehicle.get("type"):
            await self._select_dropdown_with_fallback(
                [
                    'select[name="VehicleType"]',
                    'select[id="VehicleType"]',
                    'select[name*="vehicle" i][name*="type" i]',
                ],
                vehicle["type"],
                "نوع ناوگان",
                required=False,
            )

    async def _fill_financial_info(self, financial: Dict[str, Any]):
        """پر کردن اطلاعات مالی"""
        if financial.get("cost"):
            await self._fill_with_fallback(
                [
                    'input[name="TransportCost"]',
                    'input[id="TransportCost"]',
                    'input[name*="transport" i][name*="cost" i]',
                    'input[name*="price" i]',
                ],
                str(financial["cost"]),
                "هزینه حمل",
            )

        if financial.get("payment_method"):
            await self._select_dropdown_with_fallback(
                [
                    'select[name="PaymentMethod"]',
                    'select[id="PaymentMethod"]',
                    'select[name*="payment" i][name*="method" i]',
                ],
                financial["payment_method"]
                ,
                "روش پرداخت",
                required=False,
            )

    async def _fill_with_fallback(self, selectors, value: str, field_label: str):
        """تلاش ترتیبی برای پر کردن فیلد با چند selector جایگزین."""
        if not value:
            return

        for selector in selectors:
            fill_success = await self.interactor.safe_fill(selector, value)
            if fill_success:
                await asyncio.sleep(0.2)
                return

        raise WaybillError(f"پر کردن فیلد `{field_label}` ناموفق بود")

    async def _select_dropdown_with_fallback(
        self,
        selectors,
        value: str,
        field_label: str,
        required: bool = True,
    ):
        """تلاش ترتیبی برای انتخاب گزینه از چند selector."""
        if not value:
            return False

        for selector in selectors:
            selected = await self._select_dropdown(selector, value)
            if selected:
                return True

        if required:
            raise WaybillError(f"انتخاب `{field_label}` ناموفق بود")

        logger.warning(
            "optional_dropdown_not_found",
            extra={"extra_fields": {"field": field_label, "value": value}},
        )
        return False

    async def _select_dropdown(self, selector: str, value: str) -> bool:
        """انتخاب از منوی کشویی"""
        try:
            await self.page.select_option(selector, label=value)
            return True
        except:
            try:
                await self.page.select_option(selector, value=value)
                return True
            except:
                return False

    async def _submit_waybill(self) -> Dict[str, Any]:
        """ثبت فرم بارنامه"""
        submit_clicked = await self.interactor.safe_click(
            'button[type="submit"], button:has-text("ثبت"), input[type="submit"]',
            wait_for_navigation=True
        )

        if not submit_clicked:
            submit_clicked = await self.interactor.safe_click(
                'button[type="submit"], button:has-text("ثبت"), input[type="submit"]',
                wait_for_navigation=False
            )

        if not submit_clicked:
            raise WaybillError("ارسال فرم بارنامه انجام نشد (کلیک روی دکمه ثبت ناموفق بود)")

        await asyncio.sleep(2)

        # استخراج کد رهگیری
        tracking_code = await self._extract_tracking_code()
        submission_confirmed = await self._is_submission_successful()

        if not tracking_code and not submission_confirmed:
            form_errors = await self._extract_form_errors()
            if form_errors:
                raise WaybillError(f"ثبت بارنامه با خطا مواجه شد: {form_errors}")
            raise WaybillError(
                "ثبت بارنامه تایید نشد: نه کد رهگیری پیدا شد و نه نشانه موفقیت در صفحه وجود داشت"
            )

        return {
            "success": True,
            "status": "submitted",
            "tracking_code": tracking_code,
            "url": await self._current_url()
        }

    async def _is_submission_successful(self) -> bool:
        """بررسی نشانه‌های موفقیت پس از ثبت."""
        success_selectors = [
            ".alert-success",
            ".toast-success",
            ".success-message",
            "text=با موفقیت ثبت شد",
            "text=بارنامه ثبت شد",
            "text=شماره بارنامه",
            "text=کد رهگیری",
        ]
        for selector in success_selectors:
            try:
                if await self.page.query_selector(selector):
                    return True
            except Exception:
                continue

        current_url = (await self._current_url()).lower()
        success_fragments = (
            "/print",
            "/details",
            "/success",
            "/notification",
            "/receipt",
            "/result",
        )
        if any(fragment in current_url for fragment in success_fragments):
            return True

        if "/create" not in current_url and "/login" not in current_url:
            # در بسیاری از نسخه‌های UTCMS بعد از ثبت، URL به مسیر غیر Create منتقل می‌شود.
            return True

        return False

    async def _extract_form_errors(self) -> Optional[str]:
        """استخراج خطاهای اعتبارسنجی فرم."""
        error_selectors = [
            ".validation-summary-errors li",
            ".validation-summary-errors",
            ".field-validation-error",
            ".alert-danger",
            ".text-danger",
        ]
        for selector in error_selectors:
            try:
                error_elements = await self.page.query_selector_all(selector)
                for element in error_elements:
                    text = await self._as_clean_text(await element.text_content())
                    if text:
                        return text
            except Exception:
                continue
        return None

    async def _extract_tracking_code(self) -> Optional[str]:
        """استخراج کد رهگیری از صفحه"""
        import re

        # تلاش با انتخابگرهای مختلف
        selectors = [
            '.tracking-code',
            '#TrackingCode',
            '[data-tracking]',
            '.waybill-number'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    codes = re.findall(r'\d{6,}', text or "")
                    if codes:
                        return codes[0]
            except:
                continue

        # تلاش با استفاده از URL
        url = await self._current_url()
        codes = re.findall(r'[A-Z0-9]{8,}', url)
        if codes:
            return codes[0]

        return None
