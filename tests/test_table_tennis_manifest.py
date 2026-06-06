import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.files import validate_loaded


SAMPLE = ROOT / "samples" / "table-tennis" / "valid" / "flat_match.json"


class TableTennisManifestTests(unittest.TestCase):
    def test_sample_is_valid(self):
        issues = validate_loaded(load_json(SAMPLE), "table-tennis-match-manifest")
        self.assertEqual([], issues)

    def test_rejects_non_contiguous_clip_point(self):
        data = copy.deepcopy(load_json(SAMPLE))
        data[0]["game_clips"][1]["name"] = "set_1_point_3"

        issues = validate_loaded(data, "table-tennis-match-manifest")

        self.assertTrue(any("expected point index 1" in str(issue) for issue in issues))

    def test_rejects_wrong_manifest_extension(self):
        data = copy.deepcopy(load_json(SAMPLE))
        data[0]["video_name"] = "match.txt"

        issues = validate_loaded(data, "table-tennis-match-manifest")

        self.assertTrue(any("video_name" in str(issue) for issue in issues))


if __name__ == "__main__":
    unittest.main()
