import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.files import validate_loaded


SAMPLE = ROOT / "samples" / "swimming" / "valid" / "2024-JO_Paris_freestyle_hommes_100_finaleA.json"


class SwimmingEventConfigTests(unittest.TestCase):
    def test_sample_is_valid(self):
        issues = validate_loaded(load_json(SAMPLE), "swimming-event-config")
        self.assertEqual([], issues)

    def test_rejects_unknown_stroke(self):
        data = load_json(SAMPLE)
        data["nage"] = "crawl"

        issues = validate_loaded(data, "swimming-event-config")

        self.assertTrue(any("$.nage" in str(issue) for issue in issues))
        self.assertTrue(any("not generated" in str(issue) for issue in issues))

    def test_rejects_entity_lane_not_declared_in_root_lanes(self):
        data = copy.deepcopy(load_json(SAMPLE))
        data["annotation_simple"]["entities"][0]["lane"] = "ligne9"

        issues = validate_loaded(data, "swimming-event-config")

        self.assertTrue(any("$.annotation_simple.entities[0].lane" in str(issue) for issue in issues))


if __name__ == "__main__":
    unittest.main()
