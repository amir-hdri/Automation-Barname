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


class MapSelectors:
    """انتخابگرهای مربوط به نقشه"""

    CONTAINER_SELECTORS = (
        "#map",
        ".map",
        "#map-container",
        ".map-container",
        "[id*='map']",
        "[class*='map']",
        ".ol-map",
        ".leaflet-container",
        ".gm-style",
    )