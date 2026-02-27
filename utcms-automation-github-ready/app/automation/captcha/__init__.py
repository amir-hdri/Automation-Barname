from typing import Optional

from app.automation.captcha.base import CaptchaProvider
from app.automation.captcha.twocaptcha import TwoCaptchaProvider
from app.core.config import utcms_config


def get_captcha_provider() -> Optional[CaptchaProvider]:
    provider = utcms_config.CAPTCHA_PROVIDER
    if provider in ("off", "none", "disabled", ""):
        return None

    if provider == "twocaptcha":
        if not utcms_config.TWOCAPTCHA_API_KEY:
            return None
        return TwoCaptchaProvider(
            api_key=utcms_config.TWOCAPTCHA_API_KEY,
            timeout_seconds=utcms_config.CAPTCHA_TIMEOUT_SECONDS,
            poll_seconds=utcms_config.CAPTCHA_POLL_SECONDS,
            max_retries=utcms_config.CAPTCHA_MAX_RETRIES,
        )

    return None


__all__ = ["CaptchaProvider", "TwoCaptchaProvider", "get_captcha_provider"]
