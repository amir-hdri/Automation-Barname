from unittest.mock import AsyncMock, patch

import pytest

from app.automation.captcha.twocaptcha import TwoCaptchaProvider


@pytest.mark.asyncio
async def test_twocaptcha_success_flow():
    provider = TwoCaptchaProvider(api_key="key", timeout_seconds=30, poll_seconds=0.1, max_retries=1)

    with patch.object(provider, "_create_task", AsyncMock(return_value="123")), patch.object(
        provider, "_poll_result", AsyncMock(return_value="abcd")
    ):
        result = await provider.solve_text_captcha("ZmFrZQ==")

    assert result.solved is True
    assert result.value == "abcd"
    assert result.provider == "twocaptcha"


@pytest.mark.asyncio
async def test_twocaptcha_failure_when_api_key_missing():
    provider = TwoCaptchaProvider(api_key="")
    result = await provider.solve_text_captcha("ZmFrZQ==")

    assert result.solved is False
    assert result.error == "missing_api_key"
