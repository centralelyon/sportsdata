from __future__ import annotations

from pathlib import Path
from typing import Any

from ..catalogs import MODELS_ROOT, load_json
from .csv_rules import validate_csv_file
from .schema import ValidationIssue, validate_schema
from .semantic import validate_swimming_event_config, validate_table_tennis_match_manifest


def load_format_declaration(format_id: str) -> dict[str, Any] | None:
    """Load a format declaration from models/formats by format ID.
    
    Format IDs map to files as follows:
    - formats.json.table-tennis-game -> models/formats/json/table-tennis-game.format.json
    - formats.csv.swimming-tracking -> models/formats/csv/swimming-tracking.table-schema.json
    """
    parts = format_id.split(".")
    if len(parts) < 2:
        return None
    
    file_type = parts[1]  # json, csv, etc.
    format_name = ".".join(parts[2:])  # remaining parts
    
    format_file = MODELS_ROOT / "formats" / file_type / f"{format_name}.format.json"
    if format_file.exists():
        return load_json(format_file)
    
    # Also try table-schema.json for CSV formats
    if file_type == "csv":
        schema_file = MODELS_ROOT / "formats" / "csv" / f"{format_name}.table-schema.json"
        if schema_file.exists():
            return load_json(schema_file)
    
    return None


def detect_format(data: Any) -> str:
    if isinstance(data, dict) and data.get("annotation_simple", {}).get("sport") == "swimming":
        return "swimming-event-config"
    if isinstance(data, list) and all(isinstance(item, dict) and "game_clips" in item for item in data):
        return "table-tennis-match-manifest"
    if isinstance(data, dict) and "playerA" in data and "playerB" in data and "fps" in data:
        return "table-tennis-game"
    return "unknown"


def validate_loaded(data: Any, format_id: str | None = None) -> list[ValidationIssue]:
    selected_format = format_id or detect_format(data)

    # Try to load format declaration if it starts with "formats."
    if selected_format.startswith("formats."):
        format_decl = load_format_declaration(selected_format)
        if format_decl and "schema" in format_decl:
            schema_path = format_decl["schema"]
            schema = load_json(MODELS_ROOT / schema_path)
            issues = validate_schema(data, schema)
            
            # Apply semantic rules if available
            if "semanticRules" in format_decl:
                for rule_path in format_decl.get("semanticRules", []):
                    if "table-tennis" in rule_path and isinstance(data, list):
                        issues.extend(validate_table_tennis_match_manifest(data))
            
            return issues

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

    if selected_format == "table-tennis-game":
        schema = load_json(MODELS_ROOT / "schemas" / "table-tennis" / "game.schema.json")
        issues = validate_schema(data, schema)
        return issues

    return [ValidationIssue("$", "unknown sports data format")]


def validate_file(path: str | Path, format_id: str | None = None) -> list[ValidationIssue]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        return validate_csv_file(file_path, format_id)
    return validate_loaded(load_json(file_path), format_id)
