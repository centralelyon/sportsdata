from __future__ import annotations

from pathlib import Path
from typing import Any

from ..catalogs import MODELS_ROOT, load_json
from .csv_rules import validate_csv_file
from .schema import ValidationIssue, validate_schema
from .semantic import validate_swimming_event_config, validate_table_tennis_match_manifest


def detect_format(data: Any) -> str:
    if isinstance(data, dict) and data.get("annotation_simple", {}).get("sport") == "swimming":
        return "swimming-event-config"
    if isinstance(data, list) and all(isinstance(item, dict) and "game_clips" in item for item in data):
        return "table-tennis-match-manifest"
    return "unknown"


def validate_loaded(data: Any, format_id: str | None = None) -> list[ValidationIssue]:
    selected_format = format_id or detect_format(data)

    if selected_format == "swimming-event-config":
        schema = load_json(MODELS_ROOT / "schemas" / "swimming" / "event-config.schema.json")
        annotation_schema = load_json(MODELS_ROOT / "schemas" / "swimming" / "annotation-simple.schema.json")
        issues = validate_schema(data, schema)
        if isinstance(data, dict) and isinstance(data.get("annotation_simple"), dict):
            issues.extend(validate_schema(data["annotation_simple"], annotation_schema, "$.annotation_simple"))
            issues.extend(validate_swimming_event_config(data))
        return issues

    if selected_format == "table-tennis-match-manifest":
        schema = load_json(MODELS_ROOT / "schemas" / "table-tennis" / "match-manifest.schema.json")
        issues = validate_schema(data, schema)
        if isinstance(data, list):
            issues.extend(validate_table_tennis_match_manifest(data))
        return issues

    return [ValidationIssue("$", "unknown sports data format")]


def validate_file(path: str | Path, format_id: str | None = None) -> list[ValidationIssue]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        return validate_csv_file(file_path, format_id)
    return validate_loaded(load_json(file_path), format_id)
