import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.derivations import derive_swimming_events


class DerivationTests(unittest.TestCase):
    def test_generated_swimming_event_shape(self):
        event = next(
            item
            for item in derive_swimming_events()["values"]
            if item["id"] == "freestyle_hommes_100_finaleA"
        )

        self.assertEqual(event["sport"], "swimming")
        self.assertEqual(event["stroke"], "freestyle")
        self.assertEqual(event["sex"], "hommes")
        self.assertEqual(event["distance"], "100")
        self.assertEqual(event["round"], "finaleA")
        self.assertIn("100 m", event["label"])

    def test_static_generated_catalog_matches_recipe(self):
        generated = load_json(ROOT / "models" / "catalogs" / "swimming" / "generated" / "events.json")
        derived = derive_swimming_events()

        self.assertEqual("models/derivations/swimming/events.recipe.json", generated["generatedFrom"])
        self.assertEqual(
            {item["id"] for item in derived["values"]},
            {item["id"] for item in generated["values"]},
        )


if __name__ == "__main__":
    unittest.main()
