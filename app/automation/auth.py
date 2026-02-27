import asyncio
import base64
import inspect
import logging
import random
from typing import Iterable, Optional

from playwright.async_api import BrowserContext, Page

from app.automation.captcha import get_captcha_provider
from app.automation.selectors import AuthSelectors
from app.core.config import utcms_config
from app.core.network import is_retryable_network_error
from app.core.utils import resolve_maybe_awaitable

logger = logging.getLogger(__name__)


class UTCMSAuthenticator:
    """Handles authentication for UTCMS."""

    def __init__(self, page: Page, context: BrowserContext):
        self.page = page
        self.context = context
        self.last_error: Optional[str] = None

    async def _current_url(self) -> str:
        raw_url = getattr(self.page, "url", "")
        try:
            url_value = await resolve_maybe_awaitable(raw_url)
        except Exception:
            return ""

        if url_value is None:
            return ""
        return url_value if isinstance(url_value, str) else str(url_value)

    async def _as_clean_text(self, value) -> str:
        try:
            resolved = await resolve_maybe_awaitable(value)
        except Exception:
            return ""
        if resolved is None:
            return ""
        return (resolved if isinstance(resolved, str) else str(resolved)).strip()

    async def _goto_with_retry(self, url: str, wait_until: str = "domcontentloaded") -> None:
        attempts = max(1, utcms_config.PAGE_GOTO_MAX_RETRIES + 1)
        base_delay = max(0.1, utcms_config.PAGE_GOTO_RETRY_BASE_SECONDS)
        jitter = max(0.0, utcms_config.PAGE_GOTO_RETRY_JITTER_SECONDS)
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                await self.page.goto(url, wait_until=wait_until)
                return
            except Exception as exc:
                last_error = exc
                if attempt >= attempts or not is_retryable_network_error(exc):
                    raise
                delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0, jitter)
                await asyncio.sleep(delay)

        if last_error:
            raise last_error

    def _is_login_url(self, url: str) -> bool:
        lowered = (url or "").lower()
        return any(fragment in lowered for fragment in ("/login", "/account/login", "/signin", "/sign-in"))

    def _candidate_login_urls(self) -> list[str]:
        base_url = utcms_config.BASE_URL.rstrip("/")
        candidates = [utcms_config.LOGIN_URL.strip()]
        candidates.extend(f"{base_url}{path}" for path in AuthSelectors.LOGIN_PATH_CANDIDATES)

        unique_candidates: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in unique_candidates:
                unique_candidates.append(candidate)
        return unique_candidates

    async def _find_selector(
        self,
        selectors: Iterable[str],
        visible: bool = False,
        timeout: int = 1000,
    ) -> Optional[str]:
        for selector in selectors:
            try:
                if visible:
                    element = await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                else:
                    element = await self.page.query_selector(selector)
                if element:
                    return selector
            except Exception:
                continue
        return None

    async def _has_auth_cookie(self) -> bool:
        try:
            cookies = await self.context.cookies()
        except Exception:
            return False

        auth_keywords = (
            "auth",
            "session",
            "sessionid",
            "aspxauth",
            "identity",
            "aspnet.applicationcookie",
            "aspnetcore.identity",
            "jwt",
        )
        for cookie in cookies:
            name = str(cookie.get("name", "")).lower()
            if any(keyword in name for keyword in auth_keywords):
                return True
        return False

    async def _looks_like_login_page(self) -> bool:
        if self._is_login_url(await self._current_url()):
            return True

        username_selector = await self._find_selector(AuthSelectors.USERNAME_SELECTORS)
        password_selector = await self._find_selector(AuthSelectors.PASSWORD_SELECTORS)
        submit_selector = await self._find_selector(AuthSelectors.SUBMIT_SELECTORS)
        return bool(username_selector and password_selector and submit_selector)

    async def _is_logged_in(self) -> bool:
        self.last_error = None
        try:
            await self._goto_with_retry(utcms_config.WAYBILL_URL, wait_until="domcontentloaded")
            await asyncio.sleep(1.0)
        except Exception:
            return False

        current_url = await self._current_url()
        if self._is_login_url(current_url):
            return False
        if await self._find_selector(AuthSelectors.LOGOUT_SELECTORS, visible=True, timeout=500):
            return True

        for selector in AuthSelectors.WAYBILL_FORM_MARKERS:
            try:
                if await self.page.query_selector(selector):
                    return True
            except Exception:
                continue

        if await self._looks_like_login_page():
            return False

        # Some UTCMS builds rename waybill fields; non-login pages after auth are
        # still considered authenticated even when legacy markers are missing.
        await asyncio.sleep(0.4)
        return not self._is_login_url(await self._current_url())

    async def _extract_login_error(self) -> Optional[str]:
        for selector in AuthSelectors.LOGIN_ERROR_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if not element:
                    continue
                text = await self._as_clean_text(await element.text_content())
                if text:
                    return text
            except Exception:
                continue
        return None

    async def _wait_for_login_result(self, timeout_ms: int = 12000) -> bool:
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while asyncio.get_running_loop().time() < deadline:
            if await self._find_selector(AuthSelectors.LOGOUT_SELECTORS, visible=True, timeout=300):
                return True

            if not await self._looks_like_login_page():
                if not self._is_login_url(await self._current_url()):
                    return True

            login_error = await self._extract_login_error()
            if login_error:
                self.last_error = login_error
                return False

            await asyncio.sleep(0.35)

        return (
            not await self._looks_like_login_page()
            and not self._is_login_url(await self._current_url())
        )

    async def _complete_post_login_steps(self) -> bool:
        """
        Handle additional UI steps after credential submission.
        Some UTCMS accounts show a rules acceptance modal on first login.
        """
        try:
            modal_selector = "#ExceptRulesModalReal"
            if await self._find_selector((modal_selector,), visible=True, timeout=1200):
                await self.page.check("#ruleExcepted")
                await self.page.click("#submitRules")

                deadline = asyncio.get_running_loop().time() + 12
                while asyncio.get_running_loop().time() < deadline:
                    if not self._is_login_url(await self._current_url()):
                        return True
                    await asyncio.sleep(0.3)
                return False
        except Exception as error:
            self.last_error = f"تایید قوانین پس از لاگین ناموفق بود: {error}"
            return False

        return True

    async def _wait_for_manual_captcha_input(self, selector: str) -> bool:
        timeout_seconds = max(5, utcms_config.UTCMS_MANUAL_CAPTCHA_TIMEOUT_SECONDS)
        poll_seconds = max(0.2, utcms_config.UTCMS_MANUAL_CAPTCHA_POLL_SECONDS)
        deadline = asyncio.get_running_loop().time() + timeout_seconds

        while asyncio.get_running_loop().time() < deadline:
            try:
                value = await self.page.eval_on_selector(selector, "el => (el.value || '').trim()")
                if value:
                    return True
            except Exception:
                pass
            await asyncio.sleep(poll_seconds)

        return False

    async def _extract_captcha_image_base64(self) -> Optional[str]:
        for selector in AuthSelectors.CAPTCHA_IMAGE_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if not element:
                    continue

                image_bytes = await element.screenshot(type="png")
                if image_bytes:
                    return base64.b64encode(image_bytes).decode("utf-8")
            except Exception:
                continue

        return None

    async def _solve_captcha_with_provider(self) -> Optional[str]:
        provider = get_captcha_provider()
        if not provider:
            return None

        image_base64 = await self._extract_captcha_image_base64()
        if not image_base64:
            logger.warning("captcha_provider_image_not_found")
            return None

        result = await provider.solve_text_captcha(image_base64)
        if result.solved and result.value:
            return result.value

        logger.warning(
            "captcha_provider_failed",
            extra={"extra_fields": {"provider": result.provider, "error": result.error}},
        )
        return None

    def _captcha_mode(self) -> str:
        mode = (utcms_config.CAPTCHA_MODE or "").strip().lower()
        if mode in ("provider_first", "manual_only", "provider_only"):
            return mode
        return "provider_first"

    async def _fill_credentials(
        self,
        username_selector: str,
        password_selector: str,
        username: str,
        password: str,
    ) -> bool:
        try:
            await self.page.fill(username_selector, username)
            await self.page.fill(password_selector, password)
            return True
        except Exception as error:
            self.last_error = f"تکمیل فرم ورود با خطا مواجه شد: {error}"
            return False

    async def _handle_captcha(self, captcha_selector: str) -> bool:
        if not captcha_selector:
            return True

        if utcms_config.UTCMS_CAPTCHA_VALUE:
            try:
                await self.page.fill(captcha_selector, utcms_config.UTCMS_CAPTCHA_VALUE)
                return True
            except Exception:
                self.last_error = "فیلد کپچا یافت شد اما مقداردهی آن انجام نشد."
                return False

        captcha_mode = self._captcha_mode()
        allow_provider = captcha_mode in ("provider_first", "provider_only")
        allow_manual = captcha_mode in ("provider_first", "manual_only") and utcms_config.UTCMS_ENABLE_MANUAL_CAPTCHA

        solved_by_provider = None
        if allow_provider:
            solved_by_provider = await self._solve_captcha_with_provider()

        if solved_by_provider:
            try:
                await self.page.fill(captcha_selector, solved_by_provider)
                return True
            except Exception:
                self.last_error = "حل کپچا موفق بود اما مقداردهی فیلد کپچا انجام نشد."
                return False

        if allow_manual:
            if utcms_config.HEADLESS:
                self.last_error = (
                    "کپچا فعال است ولی مرورگر در حالت HEADLESS اجرا می‌شود. "
                    "برای حل دستی کپچا، `HEADLESS=false` تنظیم شود."
                )
                return False
            solved = await self._wait_for_manual_captcha_input(captcha_selector)
            if not solved:
                self.last_error = (
                    "کپچا در بازه مجاز تکمیل نشد. لطفاً کپچا را دستی وارد کنید و مجدد تلاش کنید."
                )
                return False
            return True

        if captcha_mode == "provider_only":
            self.last_error = (
                "کپچا در حالت provider_only حل نشد. "
                "مقادیر `CAPTCHA_PROVIDER` و `TWOCAPTCHA_API_KEY` را بررسی کنید."
            )
        elif captcha_mode == "manual_only":
            self.last_error = (
                "حالت manual_only فعال است اما حل دستی کپچا غیرفعال است. "
                "`UTCMS_ENABLE_MANUAL_CAPTCHA=true` تنظیم شود."
            )
        else:
            self.last_error = (
                "کپچا در صفحه ورود فعال است. مقدار `UTCMS_CAPTCHA_VALUE` را تنظیم کنید "
                "یا `TWOCAPTCHA_API_KEY`/`UTCMS_ENABLE_MANUAL_CAPTCHA=true` استفاده شود."
            )
        return False

    async def _submit_login(self, submit_selector: str) -> bool:
        clicked = False
        try:
            async with self.page.expect_navigation(timeout=10000, wait_until="domcontentloaded"):
                await self.page.click(submit_selector)
            clicked = True
        except Exception:
            try:
                await self.page.click(submit_selector)
                clicked = True
            except Exception:
                clicked = False

        if not clicked:
            self.last_error = "ارسال فرم ورود انجام نشد."
            return False

        if await self._wait_for_login_result():
            post_login_ok = await self._complete_post_login_steps()
            if not post_login_ok:
                if not self.last_error:
                    self.last_error = "تکمیل مراحل پس از لاگین ناموفق بود."
                return False

            if await self._is_logged_in():
                return True

            if not self.last_error:
                self.last_error = await self._extract_login_error() or "لاگین تکمیل نشد و دسترسی به فرم بارنامه تایید نشد."
            return False

        if not self.last_error:
            self.last_error = await self._extract_login_error() or "لاگین ناموفق بود؛ صفحه در وضعیت ورود باقی ماند."
        return False

    async def login(self, username: str, password: str) -> bool:
        self.last_error = None
        for login_url in self._candidate_login_urls():
            try:
                await self._goto_with_retry(login_url, wait_until="domcontentloaded")
                await asyncio.sleep(1.0)
            except Exception:
                continue

            username_selector = await self._find_selector(AuthSelectors.USERNAME_SELECTORS, visible=True, timeout=4000)
            password_selector = await self._find_selector(AuthSelectors.PASSWORD_SELECTORS, visible=True, timeout=4000)
            submit_selector = await self._find_selector(AuthSelectors.SUBMIT_SELECTORS, visible=True, timeout=4000)

            if not (username_selector and password_selector and submit_selector):
                continue

            if not await self._fill_credentials(username_selector, password_selector, username, password):
                continue

            captcha_selector = await self._find_selector(AuthSelectors.CAPTCHA_SELECTORS)
            if captcha_selector and not await self._handle_captcha(captcha_selector):
                return False

            if await self._submit_login(submit_selector):
                return True

        if not self.last_error:
            self.last_error = "فرم ورود معتبر در URLهای شناخته‌شده پیدا نشد. مقدار `LOGIN_URL` را تنظیم کنید."

        logger.warning("login_failed", extra={"extra_fields": {"reason": self.last_error}})
        return False
