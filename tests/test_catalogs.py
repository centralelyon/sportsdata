import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import assert_unique_catalog_ids, catalog_ids
from sportsdata_models.derivations import derive_swimming_events


class CatalogTests(unittest.TestCase):
    def test_catalog_ids_are_unique(self):
        catalogs = [
            ("common", "sports"),
            ("common", "sexes"),
            ("common", "sides"),
            ("common", "media-types"),
            ("common", "reference-corners"),
            ("swimming", "strokes"),
            ("swimming", "distances"),
            ("swimming", "rounds"),
            ("swimming", "pool-presets"),
            ("swimming", "field-presets"),
            ("swimming", "annotation-events"),
            ("table-tennis", "clip-patterns"),
            ("table-tennis", "annotation-events"),
        ]
        for scope, name in catalogs:
            with self.subTest(scope=scope, name=name):
                assert_unique_catalog_ids(scope, name)

    def test_swimming_events_are_derived_from_fixed_catalogs(self):
        events = derive_swimming_events()
        event_ids = {item["id"] for item in events["values"]}

        self.assertIn("freestyle_hommes_100_finaleA", event_ids)
        self.assertGreaterEqual(len(event_ids), len(catalog_ids("swimming", "distances")))


if __name__ == "__main__":
    unittest.main()
