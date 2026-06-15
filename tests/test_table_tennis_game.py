import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
