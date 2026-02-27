import unittest
import sys
import os
from pathlib import Path

# Add repo root to path
sys.path.append(os.getcwd())

from app.automation.script_loader import script_loader

class TestScriptLoading(unittest.TestCase):
    def test_load_all_scripts(self):
        scripts = [
            "google_maps_select",
            "openlayers_select",
            "leaflet_select",
            "mapbox_select",
            "extract_route_info_google",
            "extract_route_info_generic",
            "extract_suggestions",
            "get_map_center",
            "calculate_distance"
        ]

        for script in scripts:
            content = script_loader.load(script)
            self.assertTrue(content, f"Script {script} is empty")
            self.assertIsInstance(content, str)

    def test_load_non_existent(self):
        with self.assertRaises(FileNotFoundError):
            script_loader.load("non_existent_script")

    def test_caching(self):
        # Load once
        content1 = script_loader.load("google_maps_select")
        # Load again
        content2 = script_loader.load("google_maps_select")

        # Should be same object (str is immutable but caching returns same object ideally)
        self.assertIs(content1, content2)

if __name__ == '__main__':
    unittest.main()
