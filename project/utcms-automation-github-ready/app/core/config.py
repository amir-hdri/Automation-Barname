import os


class UTCMSConfig:
    WAYBILL_URL = os.getenv(
        "WAYBILL_URL", "https://barname.utcms.ir/Barname/Waybill/Create"
    )
    BASE_URL = os.getenv("BASE_URL", "https://barname.utcms.ir")
    LOGIN_URL = os.getenv("LOGIN_URL", f"{BASE_URL.rstrip('/')}/Login")
    HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

    # Credentials
    UTCMS_USERNAME = os.getenv("UTCMS_USERNAME", "")
    UTCMS_PASSWORD = os.getenv("UTCMS_PASSWORD", "")

    # Captcha
    UTCMS_CAPTCHA_VALUE = os.getenv("UTCMS_CAPTCHA_VALUE", "").strip()
    UTCMS_ENABLE_MANUAL_CAPTCHA = (
        os.getenv("UTCMS_ENABLE_MANUAL_CAPTCHA", "True").lower() == "true"
    )
    UTCMS_MANUAL_CAPTCHA_TIMEOUT_SECONDS = int(
        os.getenv("UTCMS_MANUAL_CAPTCHA_TIMEOUT_SECONDS", "120")
    )
    UTCMS_MANUAL_CAPTCHA_POLL_SECONDS = float(
        os.getenv("UTCMS_MANUAL_CAPTCHA_POLL_SECONDS", "0.7")
    )
    CAPTCHA_MODE = os.getenv("CAPTCHA_MODE", "provider_first").strip().lower()
    CAPTCHA_PROVIDER = os.getenv("CAPTCHA_PROVIDER", "twocaptcha").strip().lower()
    TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "").strip()
    CAPTCHA_TIMEOUT_SECONDS = int(os.getenv("CAPTCHA_TIMEOUT_SECONDS", "120"))
    CAPTCHA_POLL_SECONDS = float(os.getenv("CAPTCHA_POLL_SECONDS", "5"))
    CAPTCHA_MAX_RETRIES = int(os.getenv("CAPTCHA_MAX_RETRIES", "2"))

    # Auth session state
    AUTH_STATE_PATH = os.getenv("AUTH_STATE_PATH", ".auth/utcms_state.json")
    USE_PERSISTENT_AUTH_STATE = (
        os.getenv("USE_PERSISTENT_AUTH_STATE", "True").lower() == "true"
    )

    # API auth for sensitive endpoints
    API_AUTH_MODE = os.getenv("API_AUTH_MODE", "api_key_or_jwt").lower()
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
    API_KEY = os.getenv("API_KEY", "")
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "")
    JWT_ISSUER = os.getenv("JWT_ISSUER", "")
    JWT_LEEWAY_SECONDS = int(os.getenv("JWT_LEEWAY_SECONDS", "10"))

    # Waybill execution mode
    ALLOW_LIVE_SUBMIT = os.getenv("ALLOW_LIVE_SUBMIT", "False").lower() == "true"

    # High-throughput safety controls (compliant pacing)
    WAYBILL_MAX_CONCURRENT = int(os.getenv("WAYBILL_MAX_CONCURRENT", "2"))
    WAYBILL_MIN_GAP_SECONDS = float(os.getenv("WAYBILL_MIN_GAP_SECONDS", "0.8"))
    WAYBILL_JITTER_SECONDS = float(os.getenv("WAYBILL_JITTER_SECONDS", "0.4"))
    WAYBILL_BLOCK_BACKOFF_SECONDS = float(
        os.getenv("WAYBILL_BLOCK_BACKOFF_SECONDS", "15")
    )
    WAYBILL_BLOCK_BACKOFF_MAX_SECONDS = float(
        os.getenv("WAYBILL_BLOCK_BACKOFF_MAX_SECONDS", "180")
    )
    WAYBILL_MAX_RETRIES = int(os.getenv("WAYBILL_MAX_RETRIES", "1"))
    WAYBILL_RETRY_BASE_SECONDS = float(os.getenv("WAYBILL_RETRY_BASE_SECONDS", "1.0"))
    WAYBILL_RETRY_JITTER_SECONDS = float(
        os.getenv("WAYBILL_RETRY_JITTER_SECONDS", "0.5")
    )
    PAGE_GOTO_MAX_RETRIES = int(os.getenv("PAGE_GOTO_MAX_RETRIES", "2"))
    PAGE_GOTO_RETRY_BASE_SECONDS = float(
        os.getenv("PAGE_GOTO_RETRY_BASE_SECONDS", "1.0")
    )
    PAGE_GOTO_RETRY_JITTER_SECONDS = float(
        os.getenv("PAGE_GOTO_RETRY_JITTER_SECONDS", "0.4")
    )

    # Network timeouts (Optimized for potential Iranian internet latency)
    DEFAULT_NAVIGATION_TIMEOUT = int(os.getenv("DEFAULT_NAVIGATION_TIMEOUT", "60000"))
    DEFAULT_ACTION_TIMEOUT = int(os.getenv("DEFAULT_ACTION_TIMEOUT", "30000"))

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot_stats.db")

    # Logging/observability
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LATENCY_SAMPLE_MAX = int(os.getenv("LATENCY_SAMPLE_MAX", "2000"))


utcms_config = UTCMSConfig()
