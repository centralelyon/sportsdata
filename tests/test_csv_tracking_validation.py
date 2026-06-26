import csv
import copy
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.catalogs import load_json
from sportsdata_models.validators.csv_rules import detect_csv_format
from sportsdata_models.validators.files import validate_file, validate_loaded
from sportsdata_models.validators.schema import validate_schema


BASIC_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "basic_tracking.csv"
COMMON_MINIMAL_SAMPLE = ROOT / "samples" / "common" / "valid" / "minimal_tracking.csv"
COMMON_MINIMAL_METADATA = ROOT / "samples" / "common" / "valid" / "minimal_tracking.json"
TABLE_TENNIS_BASIC_SAMPLE = ROOT / "samples" / "table-tennis" / "valid" / "basic_tracking.csv"
TRACKING_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "exemple_annotation_ligne_5_cycles.csv"
SWIMFLOW_SAMPLE = ROOT / "samples" / "swimming" / "valid" / "paris24-men-back-final-100m.csv"
BASIC_RULES = ROOT / "models" / "rules" / "swimming" / "basic-tracking-csv.rules.json"
COMMON_MINIMAL_RULES = ROOT / "models" / "rules" / "common" / "minimal-tracking-csv.rules.json"
TABLE_TENNIS_BASIC_RULES = ROOT / "models" / "rules" / "table-tennis" / "basic-tracking-csv.rules.json"
TRACKING_RULES = ROOT / "models" / "rules" / "swimming" / "tracking-csv.rules.json"
SWIMFLOW_RULES = ROOT / "models" / "rules" / "swimming" / "swimflow-csv.rules.json"
CSV_RULES_SCHEMA = ROOT / "models" / "schemas" / "common" / "csv-rules.schema.json"


class CsvTrackingValidationTests(unittest.TestCase):
    def test_basic_sample_is_valid(self):
        self.assertEqual([], validate_file(BASIC_SAMPLE))

    def test_common_minimal_tracking_sample_is_detected_and_valid(self):
        self.assertEqual("common-minimal-tracking-csv", detect_csv_format(COMMON_MINIMAL_SAMPLE))
        self.assertEqual([], validate_file(COMMON_MINIMAL_SAMPLE))
        self.assertEqual([], validate_file(COMMON_MINIMAL_SAMPLE, "formats.csv.common-minimal-tracking"))

    def test_common_minimal_tracking_metadata_is_valid(self):
        self.assertEqual([], validate_file(COMMON_MINIMAL_METADATA))
        self.assertEqual([], validate_file(COMMON_MINIMAL_METADATA, "formats.json.common-minimal-tracking-metadata"))

    def test_common_minimal_tracking_metadata_uses_sports_catalog(self):
        data = copy.deepcopy(load_json(COMMON_MINIMAL_METADATA))
        data["applicableSports"] = ["unknown-sport"]

        issues = validate_loaded(data, "common-minimal-tracking-metadata")

        self.assertTrue(any("$.applicableSports[0]" in str(issue) and "expected one of" in str(issue) for issue in issues))

    def test_table_tennis_basic_sample_is_valid(self):
        self.assertEqual([], validate_file(TABLE_TENNIS_BASIC_SAMPLE))

    def test_full_tracking_sample_is_valid(self):
        self.assertEqual([], validate_file(TRACKING_SAMPLE, "swimming-tracking-csv"))

    def test_swimflow_sample_is_detected_and_valid(self):
        self.assertEqual("swimflow-csv", detect_csv_format(SWIMFLOW_SAMPLE))
        self.assertEqual([], validate_file(SWIMFLOW_SAMPLE))

    def test_swimflow_format_declaration_id_is_valid(self):
        self.assertEqual([], validate_file(SWIMFLOW_SAMPLE, "formats.csv.swimflow"))

    def test_swimflow_50m_variant_with_timecode_personal_is_valid(self):
        path = self._write_csv(
            SWIMFLOW_50M_HEADERS,
            [
                [
                    100,
                    50.5,
                    49.5,
                    50.0,
                    "reaction",
                    0,
                    0,
                    0.0,
                    49.0,
                    2.0,
                    49.0,
                    2.0,
                    49.0,
                    2.0,
                    49.0,
                    2.0,
                    24.0,
                    "SWE",
                    "SJOSTROM Sarah",
                    30,
                    "00:23.71",
                    "00:23.61",
                    23.61,
                    "00:23.66",
                    23.66,
                    "00:23.91",
                    23.91,
                    "",
                    0.0,
                    23.71,
                    23.71,
                    0.1,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    50.0,
                    0.0,
                    24.0,
                    -1,
                    0,
                    0.6,
                    5.2,
                    "advance",
                    0,
                ],
                [
                    101,
                    49.5,
                    48.5,
                    49.0,
                    "finish",
                    0,
                    1,
                    2.0,
                    48.0,
                    2.0,
                    48.0,
                    2.0,
                    48.0,
                    2.0,
                    48.0,
                    2.0,
                    24.0,
                    "SWE",
                    "SJOSTROM Sarah",
                    30,
                    "00:23.71",
                    "00:23.61",
                    23.61,
                    "00:23.66",
                    23.66,
                    "00:23.91",
                    23.91,
                    "",
                    0.0,
                    23.71,
                    23.71,
                    0.2,
                    0.0,
                    0.0,
                    0.0,
                    52.0,
                    -2.0,
                    "",
                    -0.1,
                    " ",
                    " ",
                    0.6,
                    5.2,
                    "return",
                    "",
                ],
            ],
        )

        self.assertEqual("swimflow-csv", detect_csv_format(path))
        self.assertEqual([], validate_file(path))

    def test_csv_rule_files_match_schema(self):
        schema = load_json(CSV_RULES_SCHEMA)
        for rules_path in [BASIC_RULES, COMMON_MINIMAL_RULES, TABLE_TENNIS_BASIC_RULES, TRACKING_RULES, SWIMFLOW_RULES]:
            with self.subTest(rules_path=rules_path):
                self.assertEqual([], validate_schema(load_json(rules_path), schema))

    def test_missing_required_header_fails(self):
        path = self._basic_csv(
            ["frameId", "swimmerId", "eventId", "distance"],
            [[0, 1, "cycle", 0.0]],
        )

        issues = validate_file(path, "swimming-basic-tracking-csv")

        self.assertTrue(any("missing required column 'time'" in str(issue) for issue in issues))

    def test_common_minimal_tracking_requires_ordered_time(self):
        path = self._basic_csv(
            ["t", "x", "y"],
            [
                [0, 10, 20],
                [2, 15, 40],
                [1, 30, 60],
            ],
        )

        issues = validate_file(path, "common-minimal-tracking-csv")

        self.assertTrue(any("$[2].t" in str(issue) and "increasing" in str(issue) for issue in issues))

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
SWIMFLOW_50M_HEADERS = [
    "frameId",
    "xa_above",
    "xb_above",
    "x_middle",
    "event",
    "swimmerId",
    "strokeCount",
    "strokeDistance",
    "x_world",
    "speed_world",
    "x_olympic",
    "speed_olympic",
    "x_personal",
    "speed_personal",
    "x_national",
    "speed_national",
    "resultS",
    "nationality",
    "name",
    "age",
    "result",
    "world",
    "world50",
    "olympic",
    "olympic50",
    "personal",
    "personal50",
    "national",
    "national50",
    "currentLap50",
    "averageLap",
    "elapsed",
    "speed",
    "acceleration",
    "averageSpeed",
    "distanceSwam",
    "distanceRemaining",
    "distanceToLeader",
    "estimatedCompletionTime",
    "nextPassing",
    "winner",
    "reaction",
    "diving",
    "direction",
    "currentLeader",
]


if __name__ == "__main__":
    unittest.main()
