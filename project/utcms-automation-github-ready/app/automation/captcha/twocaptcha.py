import asyncio
import logging
from typing import Optional

import aiohttp

from app.automation.captcha.base import CaptchaProvider, CaptchaResult

logger = logging.getLogger(__name__)


class TwoCaptchaProvider(CaptchaProvider):
    IN_URL = "https://2captcha.com/in.php"
    RES_URL = "https://2captcha.com/res.php"

    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 120,
        poll_seconds: float = 5.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key.strip()
        self.timeout_seconds = max(30, int(timeout_seconds))
        self.poll_seconds = max(2.0, float(poll_seconds))
        self.max_retries = max(1, int(max_retries))

    async def solve_text_captcha(self, image_base64: str) -> CaptchaResult:
        if not self.api_key:
            return CaptchaResult(
                solved=False, provider="twocaptcha", error="missing_api_key"
            )
        if not image_base64:
            return CaptchaResult(
                solved=False, provider="twocaptcha", error="missing_image"
            )

        for attempt in range(1, self.max_retries + 1):
            try:
                task_id = await self._create_task(image_base64)
                if not task_id:
                    continue

                solved_value = await self._poll_result(task_id)
                if solved_value:
                    return CaptchaResult(
                        solved=True, provider="twocaptcha", value=solved_value
                    )
            except Exception:
                logger.exception(
                    "twocaptcha_solve_failed",
                    extra={"extra_fields": {"attempt": attempt}},
                )

        return CaptchaResult(solved=False, provider="twocaptcha", error="solve_failed")

    async def _create_task(self, image_base64: str) -> Optional[str]:
        data = {
            "key": self.api_key,
            "method": "base64",
            "body": image_base64,
            "json": 1,
        }
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.IN_URL, data=data) as resp:
                payload = await resp.json(content_type=None)

        if str(payload.get("status")) == "1":
            return str(payload.get("request"))

        logger.warning(
            "twocaptcha_task_create_rejected",
            extra={"extra_fields": {"response": payload}},
        )
        return None

    async def _poll_result(self, task_id: str) -> Optional[str]:
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds

        while asyncio.get_running_loop().time() < deadline:
            params = {
                "key": self.api_key,
                "action": "get",
                "id": task_id,
                "json": 1,
            }
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.RES_URL, params=params) as resp:
                    payload = await resp.json(content_type=None)

            if str(payload.get("status")) == "1":
                value = str(payload.get("request", "")).strip()
                return value or None

            request_value = str(payload.get("request", ""))
            if request_value != "CAPCHA_NOT_READY":
                logger.warning(
                    "twocaptcha_task_failed",
                    extra={"extra_fields": {"task_id": task_id, "response": payload}},
                )
                return None

            await asyncio.sleep(self.poll_seconds)

        logger.warning(
            "twocaptcha_timeout",
            extra={
                "extra_fields": {
                    "task_id": task_id,
                    "timeout_seconds": self.timeout_seconds,
                }
            },
        )
        return None
