import unittest
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from app.automation.selectors import LocationSelectors

class TestLocationSelectors(unittest.TestCase):
    def test_selector_formatting(self):
        """Test that all selector templates can be formatted correctly"""
        prefix = "Origin"
        prefix_lower = prefix.lower()

        # Groups to test
        selector_groups = [
            LocationSelectors.PROVINCE_TEMPLATES,
            LocationSelectors.CITY_TEMPLATES,
            LocationSelectors.DISTRICT_TEMPLATES,
            LocationSelectors.ADDRESS_TEMPLATES,
            LocationSelectors.INPUT_TEMPLATES,
            LocationSelectors.MAP_SEARCH_TEMPLATES
        ]

        for group in selector_groups:
            self.assertIsInstance(group, list)
            for template in group:
                self.assertIsInstance(template, str)
                # This should not raise KeyError
                formatted = template.format(prefix=prefix, prefix_lower=prefix_lower)
                self.assertIsInstance(formatted, str)
                # Check that no placeholders remain
                self.assertNotIn("{prefix}", formatted)
                self.assertNotIn("{prefix_lower}", formatted)

    def test_specific_values(self):
        """Test specific selector values match expectations"""
        prefix = "Destination"
        prefix_lower = "destination"

        # Test Province
        provinces = [s.format(prefix=prefix, prefix_lower=prefix_lower)
                    for s in LocationSelectors.PROVINCE_TEMPLATES]

        self.assertIn('select[name="DestinationProvince"]', provinces)
        self.assertIn('#destination_province', provinces)

        # Test Input
        inputs = [s.format(prefix=prefix, prefix_lower=prefix_lower)
                 for s in LocationSelectors.INPUT_TEMPLATES]

        self.assertIn('input[name="DestinationLocation"]', inputs)
        self.assertIn('.location-search', inputs) # Static selector should remain unchanged

    def test_suggestion_selectors(self):
        """Test suggestion selectors are just strings"""
        for selector in LocationSelectors.SUGGESTION_SELECTORS:
            self.assertIsInstance(selector, str)
            # Should not contain formatting placeholders
            self.assertNotIn("{", selector)
            self.assertNotIn("}", selector)

if __name__ == '__main__':
    unittest.main()
