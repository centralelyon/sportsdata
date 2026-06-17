import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.files import validate_loaded
from sportsdata_models.validators.schema import validate_schema


SAMPLE = ROOT / "samples" / "swimming" / "valid" / "2024-JO_Paris_freestyle_hommes_100_finaleA.json"
NO_VIDEO_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "basic_tracking.json"
CAMERA_SCHEMA = ROOT / "models" / "schemas" / "common" / "camera.schema.json"

VALID_CAMERA = {
    "fov": 55,
    "aspect": 1.777778,
    "near": 0.01,
    "far": 1000,
    "position": [25, 17, -25],
    "target": [25, 0, 10],
    "up": [0, 1, 0],
    "roll": 0,
}


class SwimmingEventConfigTests(unittest.TestCase):
    def test_sample_is_valid(self):
        issues = validate_loaded(load_json(SAMPLE), "swimming-event-config")
        self.assertEqual([], issues)

    def test_basic_tracking_sample_without_video_is_valid(self):
        issues = validate_loaded(load_json(NO_VIDEO_SAMPLE), "swimming-event-config")
        self.assertEqual([], issues)

    def test_common_camera_schema_accepts_valid_camera(self):
        issues = validate_schema(VALID_CAMERA, load_json(CAMERA_SCHEMA))
        self.assertEqual([], issues)

    def test_rejects_invalid_camera_vector(self):
        data = copy.deepcopy(load_json(NO_VIDEO_SAMPLE))
        data["camera"]["position"] = [25, 17]

        issues = validate_loaded(data, "swimming-event-config")

        self.assertTrue(any("$.camera.position" in str(issue) for issue in issues))

    def test_rejects_unknown_camera_property(self):
        data = copy.deepcopy(load_json(NO_VIDEO_SAMPLE))
        data["camera"]["zoom"] = 1

        issues = validate_loaded(data, "swimming-event-config")

        self.assertTrue(any("$.camera.zoom" in str(issue) for issue in issues))

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
