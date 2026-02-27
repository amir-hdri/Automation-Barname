import asyncio
import logging
import os
import uuid
from typing import Dict, Optional, Tuple

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.core.config import utcms_config

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser lifecycle"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._state_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the browser instance"""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=utcms_config.HEADLESS)

    async def create_context(self) -> Tuple[str, BrowserContext]:
        """Create a new browser context with a secure session ID"""
        if not self.browser:
            await self.initialize()

        session_id = str(uuid.uuid4())
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "viewport": {"width": 1280, "height": 720},
        }
        if utcms_config.USE_PERSISTENT_AUTH_STATE:
            auth_state_path = os.path.abspath(utcms_config.AUTH_STATE_PATH)
            if os.path.exists(auth_state_path):
                context_args["storage_state"] = auth_state_path

        context = await self.browser.new_context(**context_args)
        self._contexts[session_id] = context
        return session_id, context

    async def save_auth_state(self, context: BrowserContext):
        """Persist current authenticated state for future sessions."""
        if not utcms_config.USE_PERSISTENT_AUTH_STATE:
            return

        auth_state_path = os.path.abspath(utcms_config.AUTH_STATE_PATH)
        auth_state_dir = os.path.dirname(auth_state_path)
        if auth_state_dir:
            os.makedirs(auth_state_dir, exist_ok=True)

        async with self._state_lock:
            try:
                await context.storage_state(path=auth_state_path)
            except Exception as exc:
                logger.warning(
                    "save_auth_state_failed",
                    extra={"extra_fields": {"error": str(exc), "path": auth_state_path}},
                )

    async def close_context(self, session_id: str):
        """Close a specific browser context"""
        if session_id in self._contexts:
            await self._contexts[session_id].close()
            del self._contexts[session_id]

    async def new_page(self, context: BrowserContext) -> Page:
        """Create a new page in the given context"""
        return await context.new_page()

    async def close(self):
        """Close browser and playwright"""
        for context in self._contexts.values():
            try:
                await context.close()
            except Exception as exc:
                logger.warning(
                    "context_close_failed_on_shutdown",
                    extra={"extra_fields": {"error": str(exc)}},
                )
        self._contexts.clear()

        if self.browser:
            try:
                await self.browser.close()
            except Exception as exc:
                logger.warning(
                    "browser_close_failed_on_shutdown",
                    extra={"extra_fields": {"error": str(exc)}},
                )
            self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as exc:
                logger.warning(
                    "playwright_stop_failed_on_shutdown",
                    extra={"extra_fields": {"error": str(exc)}},
                )
            self.playwright = None


browser_manager = BrowserManager()


class PageInteractor:
    """Helper for safe page interactions"""

    def __init__(self, page: Page):
        self.page = page

    async def safe_click(self, selector: str, wait_for_navigation: bool = False, timeout: int = 5000):
        """Click an element safely"""
        try:
            element = await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            if element:
                if wait_for_navigation:
                    async with self.page.expect_navigation(timeout=timeout):
                        await element.click()
                else:
                    await element.click()
                return True
        except Exception as exc:
            logger.warning(
                "safe_click_failed",
                extra={"extra_fields": {"selector": selector, "error": str(exc)}},
            )
        return False

    async def safe_fill(self, selector: str, value: str, timeout: int = 5000):
        """Fill an input safely"""
        try:
            element = await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            if element:
                await element.fill(value)
                return True
        except Exception as exc:
            logger.warning(
                "safe_fill_failed",
                extra={"extra_fields": {"selector": selector, "error": str(exc)}},
            )
        return False

    async def screenshot(self, name: str):
        """Take a screenshot"""
        try:
            await self.page.screenshot(path=f"{name}.png")
        except Exception as exc:
            logger.warning(
                "screenshot_failed",
                extra={"extra_fields": {"name": name, "error": str(exc)}},
            )
