import asyncio
import logging
import random
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.automation.auth import UTCMSAuthenticator
from app.automation.browser import browser_manager
from app.automation.map_controller import MapController
from app.automation.reporting import report_service
from app.automation.traffic_control import waybill_traffic_controller
from app.automation.waybill_enhanced import EnhancedWaybillManager
from app.core.config import utcms_config
from app.core.exceptions import WaybillError
from app.core.network import is_retryable_network_error
from app.schemas.waybill import OperationMode, WaybillMapRequest


logger = logging.getLogger(__name__)


def _retry_delay_seconds(attempt_number: int) -> float:
    base = max(0.1, utcms_config.WAYBILL_RETRY_BASE_SECONDS)
    jitter = random.uniform(0, max(0.0, utcms_config.WAYBILL_RETRY_JITTER_SECONDS))
    return (base * (2 ** max(0, attempt_number - 1))) + jitter


async def _goto_with_retry(page, url: str, wait_until: str = "domcontentloaded") -> None:
    attempts = max(1, utcms_config.PAGE_GOTO_MAX_RETRIES + 1)
    base_delay = max(0.1, utcms_config.PAGE_GOTO_RETRY_BASE_SECONDS)
    jitter = max(0.0, utcms_config.PAGE_GOTO_RETRY_JITTER_SECONDS)
    last_error: Optional[Exception] = None

    for attempt in range(1, attempts + 1):
        try:
            await page.goto(url, wait_until=wait_until)
            return
        except Exception as exc:
            last_error = exc
            if attempt >= attempts or not is_retryable_network_error(exc):
                raise
            delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0, jitter)
            await asyncio.sleep(delay)

    if last_error:
        raise last_error


def _is_retryable_exception(error: Exception) -> bool:
    return is_retryable_network_error(error)


class WaybillService:
    async def create_waybill_with_map(self, request: WaybillMapRequest) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        mode = request.operation_mode.value if isinstance(request.operation_mode, OperationMode) else str(request.operation_mode)
        dry_run = mode == OperationMode.SAFE.value

        if mode == OperationMode.FULL.value and not utcms_config.ALLOW_LIVE_SUBMIT:
            raise HTTPException(
                status_code=403,
                detail="ارسال واقعی بارنامه غیرفعال است. برای حالت full مقدار ALLOW_LIVE_SUBMIT=true تنظیم شود",
            )

        await report_service.record_request(mode=mode)

        max_attempts = max(1, utcms_config.WAYBILL_MAX_RETRIES + 1)

        for attempt in range(1, max_attempts + 1):
            internal_session_id: Optional[str] = None
            page = None
            started_at = time.perf_counter()

            try:
                async with waybill_traffic_controller.slot(mode=mode):
                    await browser_manager.initialize()
                    internal_session_id, context = await browser_manager.create_context()
                    page = await browser_manager.new_page(context)

                    auth = UTCMSAuthenticator(page, context)

                    if not await auth._is_logged_in():
                        username = utcms_config.UTCMS_USERNAME
                        password = utcms_config.UTCMS_PASSWORD

                        if not username or not password:
                            raise HTTPException(status_code=401, detail="اطلاعات ورود به سیستم تنظیم نشده است")

                        login_success = await auth.login(username, password)
                        if not login_success:
                            detail = "خطا در ورود به سامانه بارنامه"
                            if auth.last_error:
                                detail = f"{detail}: {auth.last_error}"
                            raise HTTPException(status_code=401, detail=detail)

                        await browser_manager.save_auth_state(context)
                    else:
                        await browser_manager.save_auth_state(context)

                    manager = EnhancedWaybillManager(page, context)
                    manager_result = await manager.create_waybill_with_map(
                        self._build_waybill_payload(request),
                        dry_run=dry_run,
                    )

                    latency_ms = (time.perf_counter() - started_at) * 1000
                    await report_service.record_success(mode=mode, latency_ms=latency_ms)

                    if manager_result.get("origin_method") == "map":
                        map_type = (
                            manager_result.get("origin_map_type")
                            or manager_result.get("destination_map_type")
                            or "unknown"
                        )
                        await report_service.record_map_usage(map_type)

                    return self._build_response(
                        request_id=request_id,
                        mode=mode,
                        manager_result=manager_result,
                    )

            except HTTPException as exc:
                is_temporary = exc.status_code in (429, 503)
                if is_temporary and attempt < max_attempts:
                    await waybill_traffic_controller.mark_temporary_block(multiplier=2.0)
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue

                await report_service.record_failure(
                    mode=mode,
                    category=self._categorize_http_exception(exc),
                )
                raise

            except WaybillError as exc:
                retryable = is_retryable_network_error(exc)
                if retryable and attempt < max_attempts:
                    await waybill_traffic_controller.mark_temporary_block(multiplier=1.0)
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue

                await report_service.record_failure(
                    mode=mode,
                    category="network" if retryable else "form",
                )
                if retryable:
                    raise HTTPException(
                        status_code=503,
                        detail="اختلال موقت در ارتباط با سامانه بارنامه. لطفاً مجدداً تلاش کنید",
                    )
                raise HTTPException(status_code=400, detail=str(exc))

            except Exception as exc:
                if _is_retryable_exception(exc) and attempt < max_attempts:
                    await waybill_traffic_controller.mark_temporary_block(multiplier=1.0)
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue

                await report_service.record_failure(
                    mode=mode,
                    category=self._categorize_exception(exc),
                )
                logger.exception(
                    "create_waybill_with_map_failed",
                    extra={
                        "extra_fields": {
                            "request_id": request_id,
                            "mode": mode,
                            "attempt": attempt,
                            "error": str(exc),
                        }
                    },
                )
                raise HTTPException(status_code=500, detail="خطای داخلی سرور در ثبت بارنامه")

            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        logger.warning(
                            "page_close_failed",
                            extra={"extra_fields": {"request_id": request_id}},
                        )

                if internal_session_id:
                    try:
                        await browser_manager.close_context(internal_session_id)
                    except Exception:
                        logger.warning(
                            "context_close_failed",
                            extra={
                                "extra_fields": {
                                    "request_id": request_id,
                                    "session_id": internal_session_id,
                                }
                            },
                        )

        raise HTTPException(status_code=500, detail="خطای داخلی سرور در ثبت بارنامه")

    async def detect_map(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())

        await browser_manager.initialize()

        internal_session_id: Optional[str] = None
        page = None
        try:
            internal_session_id, context = await browser_manager.create_context()
            page = await browser_manager.new_page(context)

            await _goto_with_retry(page, utcms_config.WAYBILL_URL)

            map_controller = MapController(page)
            map_type = await map_controller.detect_map_type()

            if map_type:
                await report_service.record_map_usage(map_type)
            else:
                await report_service.record_map_usage("none")

            return {
                "request_id": request_id,
                "has_map": map_type is not None,
                "map_type": map_type,
                "session_id": session_id,
            }
        except Exception as exc:
            logger.exception(
                "detect_map_failed",
                extra={"extra_fields": {"request_id": request_id, "error": str(exc)}},
            )
            raise HTTPException(status_code=500, detail="خطای داخلی سرور در تشخیص نقشه")
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    logger.warning(
                        "page_close_failed",
                        extra={"extra_fields": {"request_id": request_id}},
                    )
            if internal_session_id:
                try:
                    await browser_manager.close_context(internal_session_id)
                except Exception:
                    logger.warning(
                        "context_close_failed",
                        extra={"extra_fields": {"request_id": request_id}},
                    )

    @staticmethod
    def _build_waybill_payload(request: WaybillMapRequest) -> Dict[str, Any]:
        return {
            "sender": request.sender.model_dump(),
            "receiver": request.receiver.model_dump(),
            "origin": request.origin.model_dump(),
            "destination": request.destination.model_dump(),
            "cargo": request.cargo.model_dump(),
            "vehicle": request.vehicle.model_dump(),
            "financial": request.financial.model_dump(),
        }

    @staticmethod
    def _build_response(request_id: str, mode: str, manager_result: Dict[str, Any]) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "success": bool(manager_result.get("success", True)),
            "request_id": request_id,
            "mode": mode,
            "status": manager_result.get("status", "validated" if mode == "safe" else "submitted"),
        }

        if mode == OperationMode.SAFE.value:
            response["validation_summary"] = manager_result.get("validation_summary", {})
        else:
            response["tracking_code"] = manager_result.get("tracking_code")

        passthrough_keys = (
            "origin_method",
            "destination_method",
            "origin_map_type",
            "destination_map_type",
            "route",
            "url",
        )
        for key in passthrough_keys:
            if key in manager_result:
                response[key] = manager_result[key]

        return response

    @staticmethod
    def _categorize_http_exception(error: HTTPException) -> str:
        if error.status_code in (401, 403):
            return "auth"
        if error.status_code == 429:
            return "network"
        if error.status_code >= 500:
            return "network"
        return "form"

    @staticmethod
    def _categorize_exception(error: Exception) -> str:
        text = str(error).lower()

        if "captcha" in text:
            return "captcha"
        if "login" in text or "credential" in text or "auth" in text:
            return "auth"
        if "map" in text or "location" in text:
            return "map"
        if is_retryable_network_error(text):
            return "network"
        if "field" in text or "validation" in text or "form" in text:
            return "form"

        return "unknown"


waybill_service = WaybillService()
