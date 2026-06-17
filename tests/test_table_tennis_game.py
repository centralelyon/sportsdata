import sys
import unittest
import copy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.files import validate_loaded


BASIC_GAME = ROOT / "samples" / "table-tennis" / "valid" / "basic_game.json"


class TableTennisGameTests(unittest.TestCase):
    def test_basic_game_metadata_is_valid(self):
        issues = validate_loaded(load_json(BASIC_GAME), "table-tennis-game")
        self.assertEqual([], issues)

    def test_accepts_common_camera_model(self):
        data = copy.deepcopy(load_json(BASIC_GAME))
        data["camera"] = {
            "fov": 55,
            "aspect": 1.777778,
            "near": 0.01,
            "far": 1000,
            "position": [25, 17, -25],
            "target": [25, 0, 10],
            "up": [0, 1, 0],
            "roll": 0,
        }

        issues = validate_loaded(data, "table-tennis-game")

        self.assertEqual([], issues)

    def test_rejects_invalid_common_camera_model(self):
        data = copy.deepcopy(load_json(BASIC_GAME))
        data["camera"] = {
            "fov": 55,
            "aspect": 1.777778,
            "near": 0.01,
            "far": 1000,
            "position": [25, 17, -25],
            "target": [25, 0, 10],
            "up": [0, 1, 0],
        }

        issues = validate_loaded(data, "table-tennis-game")

        self.assertTrue(any("$.camera" in str(issue) and "roll" in str(issue) for issue in issues))


if __name__ == "__main__":
    unittest.main()
