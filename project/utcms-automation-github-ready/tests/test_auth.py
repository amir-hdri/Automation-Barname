import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.automation.auth import UTCMSAuthenticator


class _NoopAsyncContext:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


class TestUTCMSAuthenticator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = AsyncMock()
        self.context = AsyncMock()
        self.auth = UTCMSAuthenticator(self.page, self.context)
        self.page.expect_navigation = Mock(return_value=_NoopAsyncContext())

    async def test_login_fails_fast_when_captcha_detected_without_value(self):
        self.auth._candidate_login_urls = lambda: ["https://barname.utcms.ir/Login"]

        async def find_selector(selectors, visible=False, timeout=1000):
            if selectors is self.auth.USERNAME_SELECTORS:
                return "input[name='Username']"
            if selectors is self.auth.PASSWORD_SELECTORS:
                return "input[name='Password']"
            if selectors is self.auth.SUBMIT_SELECTORS:
                return "button[type='submit']"
            if selectors is self.auth.CAPTCHA_SELECTORS:
                return "input[name='DNTCaptchaInputText']"
            return None

        self.auth._find_selector = AsyncMock(side_effect=find_selector)

        with patch("app.automation.auth.utcms_config.UTCMS_CAPTCHA_VALUE", ""), patch(
            "app.automation.auth.utcms_config.UTCMS_ENABLE_MANUAL_CAPTCHA", False
        ):
            success = await self.auth.login("user", "pass")

        self.assertFalse(success)
        self.assertIn("کپچا", self.auth.last_error or "")

    async def test_login_success_with_non_dashboard_redirect(self):
        self.auth._candidate_login_urls = lambda: ["https://barname.utcms.ir/Login"]

        async def find_selector(selectors, visible=False, timeout=1000):
            if selectors is self.auth.USERNAME_SELECTORS:
                return "input[name='Username']"
            if selectors is self.auth.PASSWORD_SELECTORS:
                return "input[name='Password']"
            if selectors is self.auth.SUBMIT_SELECTORS:
                return "button[type='submit']"
            return None

        self.auth._find_selector = AsyncMock(side_effect=find_selector)
        self.auth._wait_for_login_result = AsyncMock(return_value=True)

        with patch("app.automation.auth.utcms_config.UTCMS_CAPTCHA_VALUE", ""):
            success = await self.auth.login("user", "pass")

        self.assertTrue(success)
        self.page.fill.assert_any_await("input[name='Username']", "user")
        self.page.fill.assert_any_await("input[name='Password']", "pass")
        self.page.click.assert_awaited()

    async def test_login_fails_on_headless_manual_captcha(self):
        self.auth._candidate_login_urls = lambda: ["https://barname.utcms.ir/Login"]

        async def find_selector(selectors, visible=False, timeout=1000):
            if selectors is self.auth.USERNAME_SELECTORS:
                return "input[name='Username']"
            if selectors is self.auth.PASSWORD_SELECTORS:
                return "input[name='Password']"
            if selectors is self.auth.SUBMIT_SELECTORS:
                return "button[type='submit']"
            if selectors is self.auth.CAPTCHA_SELECTORS:
                return "input[name='DNTCaptchaInputText']"
            return None

        self.auth._find_selector = AsyncMock(side_effect=find_selector)

        with patch("app.automation.auth.utcms_config.UTCMS_CAPTCHA_VALUE", ""), patch(
            "app.automation.auth.utcms_config.UTCMS_ENABLE_MANUAL_CAPTCHA", True
        ), patch("app.automation.auth.utcms_config.HEADLESS", True):
            success = await self.auth.login("user", "pass")

        self.assertFalse(success)
        self.assertIn("HEADLESS", self.auth.last_error or "")

    async def test_login_provider_only_fails_without_solver_result(self):
        self.auth._candidate_login_urls = lambda: ["https://barname.utcms.ir/Login"]

        async def find_selector(selectors, visible=False, timeout=1000):
            if selectors is self.auth.USERNAME_SELECTORS:
                return "input[name='Username']"
            if selectors is self.auth.PASSWORD_SELECTORS:
                return "input[name='Password']"
            if selectors is self.auth.SUBMIT_SELECTORS:
                return "button[type='submit']"
            if selectors is self.auth.CAPTCHA_SELECTORS:
                return "input[name='DNTCaptchaInputText']"
            return None

        self.auth._find_selector = AsyncMock(side_effect=find_selector)
        self.auth._solve_captcha_with_provider = AsyncMock(return_value=None)

        with patch("app.automation.auth.utcms_config.UTCMS_CAPTCHA_VALUE", ""), patch(
            "app.automation.auth.utcms_config.CAPTCHA_MODE", "provider_only"
        ), patch("app.automation.auth.utcms_config.UTCMS_ENABLE_MANUAL_CAPTCHA", True):
            success = await self.auth.login("user", "pass")

        self.assertFalse(success)
        self.assertIn("provider_only", self.auth.last_error or "")

    async def test_login_manual_only_requires_manual_enabled(self):
        self.auth._candidate_login_urls = lambda: ["https://barname.utcms.ir/Login"]

        async def find_selector(selectors, visible=False, timeout=1000):
            if selectors is self.auth.USERNAME_SELECTORS:
                return "input[name='Username']"
            if selectors is self.auth.PASSWORD_SELECTORS:
                return "input[name='Password']"
            if selectors is self.auth.SUBMIT_SELECTORS:
                return "button[type='submit']"
            if selectors is self.auth.CAPTCHA_SELECTORS:
                return "input[name='DNTCaptchaInputText']"
            return None

        self.auth._find_selector = AsyncMock(side_effect=find_selector)

        with patch("app.automation.auth.utcms_config.UTCMS_CAPTCHA_VALUE", ""), patch(
            "app.automation.auth.utcms_config.CAPTCHA_MODE", "manual_only"
        ), patch("app.automation.auth.utcms_config.UTCMS_ENABLE_MANUAL_CAPTCHA", False):
            success = await self.auth.login("user", "pass")

        self.assertFalse(success)
        self.assertIn("manual_only", self.auth.last_error or "")

    async def test_wait_for_login_result_accepts_non_login_page(self):
        self.page.url = "https://barname.utcms.ir/Barname/Notification"
        self.auth._find_selector = AsyncMock(return_value=None)
        self.auth._looks_like_login_page = AsyncMock(return_value=False)
        self.auth._has_auth_cookie = AsyncMock(return_value=False)
        self.auth._extract_login_error = AsyncMock(return_value=None)

        success = await self.auth._wait_for_login_result(timeout_ms=50)

        self.assertTrue(success)

    async def test_is_logged_in_false_on_login_page(self):
        self.page.url = "https://barname.utcms.ir/Login"
        self.auth._looks_like_login_page = AsyncMock(return_value=True)
        self.auth._find_selector = AsyncMock(return_value=None)
        self.auth._has_auth_cookie = AsyncMock(return_value=False)

        result = await self.auth._is_logged_in()

        self.assertFalse(result)

    async def test_is_logged_in_true_on_waybill_markers(self):
        self.page.url = "https://barname.utcms.ir/Barname/Waybill/Create"
        self.auth._looks_like_login_page = AsyncMock(return_value=False)
        self.auth._find_selector = AsyncMock(return_value=None)
        self.auth._has_auth_cookie = AsyncMock(return_value=False)
        self.page.query_selector = AsyncMock(
            side_effect=[object(), None, None, None, None]
        )

        result = await self.auth._is_logged_in()

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
