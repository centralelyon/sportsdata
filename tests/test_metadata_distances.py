import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import sportsdata
from sportsdata.catalogs import resolve_catalog


class DistanceMetadataTests(unittest.TestCase):
    def test_sportsdata_module_imports_distance_metadata(self):
        metadata = sportsdata.load_metadata_field("swimming", "distance")

        self.assertEqual("distance", metadata["jsonKey"])
        self.assertEqual("select", metadata["ui"]["jsonValueControl"])
        self.assertTrue(metadata["manualValuesAllowed"])
        self.assertEqual("centralelyon/sportsdata", metadata["source"]["repository"])

    def test_distance_json_values_come_from_available_catalog_values(self):
        options = sportsdata.metadata_json_value_options("swimming", "distance")
        json_values = [item["jsonValue"] for item in options]

        self.assertEqual(["50", "100", "200", "400", "800", "1500"], json_values)
        self.assertIn({"id": "100", "label": "100 m", "jsonValue": "100"}, options)

    def test_manual_additions_and_fixes_can_be_resolved(self):
        catalog = {
            "id": "swimming.distances",
            "values": [
                {
                    "id": "100",
                    "label": "100 m",
                    "meters": 100,
                }
            ],
        }
        overrides = {
            "fixes": [
                {
                    "id": "100",
                    "label": "100 meters",
                }
            ],
            "manualValues": [
                {
                    "id": "25",
                    "label": "25 m",
                    "meters": 25,
                }
            ],
        }

        resolved = resolve_catalog(catalog, overrides)

        self.assertEqual("100 meters", resolved["values"][0]["label"])
        self.assertEqual("25", resolved["values"][1]["id"])


if __name__ == "__main__":
    unittest.main()
