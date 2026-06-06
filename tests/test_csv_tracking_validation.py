import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.files import validate_file
from sportsdata_models.validators.schema import validate_schema


BASIC_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "basic_tracking.csv"
TRACKING_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "exemple_annotation_ligne_5_cycles.csv"
BASIC_RULES = ROOT / "models" / "rules" / "swimming" / "basic-tracking-csv.rules.json"
TRACKING_RULES = ROOT / "models" / "rules" / "swimming" / "tracking-csv.rules.json"
CSV_RULES_SCHEMA = ROOT / "models" / "schemas" / "common" / "csv-rules.schema.json"


class CsvTrackingValidationTests(unittest.TestCase):
    def test_basic_sample_is_valid(self):
        self.assertEqual([], validate_file(BASIC_SAMPLE))

    def test_full_tracking_sample_is_valid(self):
        self.assertEqual([], validate_file(TRACKING_SAMPLE, "swimming-tracking-csv"))

    def test_csv_rule_files_match_schema(self):
        schema = load_json(CSV_RULES_SCHEMA)
        for rules_path in [BASIC_RULES, TRACKING_RULES]:
            with self.subTest(rules_path=rules_path):
                self.assertEqual([], validate_schema(load_json(rules_path), schema))

    def test_missing_required_header_fails(self):
        path = self._basic_csv(
            ["frameId", "swimmerId", "eventId", "distance"],
            [[0, 1, "cycle", 0.0]],
        )

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("missing required column 'time'" in str(issue) for issue in issues))

    def test_non_numeric_frame_id_fails(self):
        path = self._basic_csv(BASIC_HEADERS, [["start", 1, "cycle", 0.0, 0.0]])

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("$[0].frameId: expected integer" in str(issue) for issue in issues))

    def test_empty_required_value_fails(self):
        path = self._basic_csv(BASIC_HEADERS, [[0, 1, "cycle", "", 0.0]])

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("$[0].time: required value is empty" in str(issue) for issue in issues))

    def test_invalid_event_catalog_value_fails(self):
        path = self._tracking_csv_with_edit(0, "eventId", "unknown")

        issues = validate_file(path, "swimming-tracking-csv")

        self.assertTrue(any("$[0].eventId" in str(issue) and "expected one of" in str(issue) for issue in issues))

    def test_out_of_range_coordinate_fails(self):
        path = self._tracking_csv_with_edit(0, "eventX", "51")

        issues = validate_file(path, "swimming-tracking-csv")

        self.assertTrue(any('$[0].eventX: expected value <= 50' in str(issue) for issue in issues))

    def test_basic_event_id_uses_annotation_event_catalog(self):
        path = self._basic_csv(
            BASIC_HEADERS,
            [
                [0, 1, "dive", 0.0, 0.0],
                [30, 1, "invalid", 1.0, 1.0],
            ],
        )

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("$[1].eventId" in str(issue) and "expected one of" in str(issue) for issue in issues))

    def test_decreasing_time_or_distance_fails(self):
        path = self._basic_csv(
            BASIC_HEADERS,
            [
                [0, 1, "cycle", 1.0, 5.0],
                [30, 1, "finish", 0.5, 4.0],
            ],
        )

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("$[1].time" in str(issue) and "increasing" in str(issue) for issue in issues))
        self.assertTrue(any("$[1].distance" in str(issue) and "nondecreasing" in str(issue) for issue in issues))

    def test_derived_metric_mismatch_is_warning(self):
        path = self._tracking_csv_with_edit(1, "frequence (cylce/min)", "99")

        issues = validate_file(path, "swimming-tracking-csv")

        self.assertTrue(any(issue.severity == "warning" and "frequency-derived-from-tempo" in str(issue) for issue in issues))
        self.assertFalse(any(issue.severity == "error" for issue in issues))

    def _basic_csv(self, headers, rows):
        return self._write_csv(headers, rows)

    def _tracking_csv_with_edit(self, row_index, column, value):
        with TRACKING_SAMPLE.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            headers = reader.fieldnames
        rows[row_index][column] = value
        return self._write_csv(headers, ([row[header] for header in headers] for row in rows))

    def _write_csv(self, headers, rows):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        path = Path(handle.name)
        with handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
        self.addCleanup(path.unlink, missing_ok=True)
        return path


BASIC_HEADERS = ["frameId", "swimmerId", "eventId", "time", "distance"]


if __name__ == "__main__":
    unittest.main()
