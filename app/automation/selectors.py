"""
ثابت‌های انتخابگر برای اتوماسیون
"""

class LocationSelectors:
    """الگوهای انتخابگر مکان برای استفاده در LocationSelector"""

    PROVINCE_TEMPLATES = [
        'select[name="{prefix}Province"]',
        'select[name="{prefix}State"]',
        'select[id="{prefix}Province"]',
        '#{prefix_lower}_province',
        '[name*="province" i][name*="{prefix_lower}" i]',
        'select[name*="Ostan"]',
        'select[name*="استان"]'
    ]

    CITY_TEMPLATES = [
        'select[name="{prefix}City"]',
        'select[id="{prefix}City"]',
        '#{prefix_lower}_city',
        '[name*="city" i][name*="{prefix_lower}" i]',
        'select[name*="Shahr"]',
        'select[name*="شهر"]'
    ]

    DISTRICT_TEMPLATES = [
        'select[name="{prefix}District"]',
        'select[id="{prefix}District"]',
        '#{prefix_lower}_district',
        'select[name*="Mantaghe"]',
        'select[name*="منطقه"]'
    ]

    ADDRESS_TEMPLATES = [
        'textarea[name="{prefix}Address"]',
        'input[name="{prefix}Address"]',
        '[name*="address" i][name*="{prefix_lower}" i]',
        '[name*="آدرس"]'
    ]

    INPUT_TEMPLATES = [
        'input[name="{prefix}Location"]',
        'input[name="{prefix}Address"]',
        'input[placeholder*="{prefix}" i]',
        '[name*="location" i][name*="{prefix_lower}" i]',
        '.location-search',
        '[class*="location-search"]',
        'input[placeholder*="جستجو"]',
        'input[placeholder*="search"]'
    ]

    SUGGESTION_SELECTORS = [
        '.autocomplete-suggestion:first-child',
        '.pac-item:first-child',
        '[class*="suggestion"]:first-child',
        'li:first-child'
    ]

    MAP_SEARCH_TEMPLATES = [
        'input[name="{prefix}Search"]',
        'input[placeholder*="{prefix}" i]',
        '.map-search input',
        '[class*="map-search"] input',
        '#map-search',
        'input[placeholder*="جستجو در نقشه"]',
        'input[placeholder*="Search map"]'
    ]


class AuthSelectors:
    """انتخابگرهای مربوط به احراز هویت"""

    LOGIN_PATH_CANDIDATES = (
        "/Barname/Account/Login",
        "/Account/Login",
        "/Barname/Login",
        "/Login",
    )
    USERNAME_SELECTORS = (
        "input[name='NationalCode']",
        "input[id='NationalCode']",
        "input[name*='national' i][type='text']",
        "input[name='Username']",
        "input[name='username']",
        "input[name='UserName']",
        "input[id='Username']",
        "input[id='username']",
        "input[type='text'][name*='user' i]",
        "input[autocomplete='username']",
    )
    PASSWORD_SELECTORS = (
        "input[name='Password']",
        "input[name='password']",
        "input[id='Password']",
        "input[id='password']",
        "input[type='password']",
    )
    CAPTCHA_SELECTORS = (
        "input[name='CapToken']",
        "input[id='CapToken']",
        "input[name='DNTCaptchaInputText']",
        "input[id='DNTCaptchaInputText']",
        "input[name*='captcha' i][type='text']",
        "input[id*='captcha' i][type='text']",
    )
    CAPTCHA_IMAGE_SELECTORS = (
        "img[id*='captcha' i]",
        "img[src*='captcha' i]",
        ".captcha img",
        "img.captcha",
    )
    SUBMIT_SELECTORS = (
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('ورود')",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
    )
    LOGOUT_SELECTORS = (
        "text=خروج",
        "a[href*='logout' i]",
        "button:has-text('خروج')",
    )
    WAYBILL_FORM_MARKERS = (
        "input[name='SenderName']",
        "input[name='ReceiverName']",
        "textarea[name='SenderAddress']",
        "textarea[name='ReceiverAddress']",
        "input[name='SenderPhone']",
        "input[name='ReceiverPhone']",
    )
    LOGIN_ERROR_SELECTORS = (
        ".validation-summary-errors li",
        ".validation-summary-errors",
        ".field-validation-error",
        ".alert-danger",
        ".text-danger",
        ".toast-message",
        ".toast-body",
        ".swal2-html-container",
    )
