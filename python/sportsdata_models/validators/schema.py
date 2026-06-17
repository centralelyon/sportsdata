from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(os.environ.get("SPORTSDATA_REPO_ROOT", Path(__file__).resolve().parents[3]))


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        if self.severity != "error":
            return f"{self.path}: [{self.severity}] {self.message}"
        return f"{self.path}: {self.message}"


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[ValidationIssue]:
    return _validate_schema(instance, schema, path, schema)


def _validate_schema(
    instance: Any,
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "$ref" in schema:
        referenced_schema, referenced_root = _resolve_ref(schema["$ref"], schema, root_schema)
        issues.extend(_validate_schema(instance, referenced_schema, path, referenced_root))

        sibling_schema = {
            key: value
            for key, value in schema.items()
            if key not in {"$ref", "$schema", "$id", "title", "description"}
        }
        if sibling_schema:
            issues.extend(_validate_schema(instance, sibling_schema, path, root_schema))
        return issues

    expected_type = schema.get("type")

    if expected_type is not None and not _matches_type(instance, expected_type):
        issues.append(ValidationIssue(path, f"expected {_type_label(expected_type)}, got {_json_type(instance)}"))
        return issues

    if "enum" in schema and instance not in schema["enum"]:
        values = ", ".join(repr(value) for value in schema["enum"])
        issues.append(ValidationIssue(path, f"expected one of {values}"))

    if isinstance(instance, dict):
        issues.extend(_validate_object(instance, schema, path, root_schema))
    elif isinstance(instance, list):
        issues.extend(_validate_array(instance, schema, path, root_schema))
    elif isinstance(instance, str):
        issues.extend(_validate_string(instance, schema, path))
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        issues.extend(_validate_number(instance, schema, path))

    return issues


def _resolve_ref(
    ref: str,
    current_schema: dict[str, Any],
    root_schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ref_path, _, fragment = ref.partition("#")
    if not ref_path:
        return _resolve_json_pointer(root_schema, fragment), root_schema

    schema_path = _resolve_ref_path(ref_path, current_schema)
    referenced_root = _load_schema(schema_path)
    referenced_schema = _resolve_json_pointer(referenced_root, fragment)
    return referenced_schema, referenced_root


def _resolve_ref_path(ref_path: str, current_schema: dict[str, Any]) -> Path:
    path = Path(ref_path)
    if path.is_absolute():
        return path
    if ref_path.startswith("models/"):
        return REPO_ROOT / ref_path

    schema_id = current_schema.get("$id")
    if isinstance(schema_id, str) and schema_id.startswith("models/"):
        return (REPO_ROOT / schema_id).parent / ref_path
    return REPO_ROOT / ref_path


@lru_cache(maxsize=128)
def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Referenced schema {path} is not an object")
    return loaded


def _resolve_json_pointer(schema: dict[str, Any], fragment: str) -> dict[str, Any]:
    if fragment == "":
        return schema
    if not fragment.startswith("/"):
        raise ValueError(f"Unsupported schema reference fragment: #{fragment}")

    target: Any = schema
    for raw_part in fragment.removeprefix("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(target, dict):
            target = target[part]
        elif isinstance(target, list):
            target = target[int(part)]
        else:
            raise ValueError(f"Schema reference fragment does not resolve to an object: #{fragment}")
    if not isinstance(target, dict):
        raise ValueError(f"Schema reference fragment does not resolve to an object: #{fragment}")
    return target


def _validate_object(
    instance: dict[str, Any],
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    properties = schema.get("properties", {})

    for required in schema.get("required", []):
        if required not in instance:
            issues.append(ValidationIssue(path, f"missing required property {required!r}"))

    for key, child_schema in properties.items():
        if key in instance:
            issues.extend(_validate_schema(instance[key], child_schema, f"{path}.{key}", root_schema))

    if schema.get("additionalProperties") is False:
        allowed = set(properties)
        for key in instance:
            if key not in allowed:
                issues.append(ValidationIssue(f"{path}.{key}", "additional property is not allowed"))

    return issues


def _validate_array(
    instance: list[Any],
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")

    if min_items is not None and len(instance) < min_items:
        issues.append(ValidationIssue(path, f"expected at least {min_items} items"))
    if max_items is not None and len(instance) > max_items:
        issues.append(ValidationIssue(path, f"expected at most {max_items} items"))

    item_schema = schema.get("items")
    if item_schema:
        for index, item in enumerate(instance):
            issues.extend(_validate_schema(item, item_schema, f"{path}[{index}]", root_schema))

    return issues


def _validate_string(instance: str, schema: dict[str, Any], path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    min_length = schema.get("minLength")
    pattern = schema.get("pattern")

    if min_length is not None and len(instance) < min_length:
        issues.append(ValidationIssue(path, f"expected at least {min_length} characters"))
    if pattern is not None and re.search(pattern, instance) is None:
        issues.append(ValidationIssue(path, f"does not match pattern {pattern!r}"))

    return issues


def _validate_number(instance: int | float, schema: dict[str, Any], path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_minimum = schema.get("exclusiveMinimum")
    exclusive_maximum = schema.get("exclusiveMaximum")

    if minimum is not None and instance < minimum:
        issues.append(ValidationIssue(path, f"expected value >= {minimum}"))
    if maximum is not None and instance > maximum:
        issues.append(ValidationIssue(path, f"expected value <= {maximum}"))
    if exclusive_minimum is not None and instance <= exclusive_minimum:
        issues.append(ValidationIssue(path, f"expected value > {exclusive_minimum}"))
    if exclusive_maximum is not None and instance >= exclusive_maximum:
        issues.append(ValidationIssue(path, f"expected value < {exclusive_maximum}"))

    return issues


def _matches_type(instance: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(instance, item) for item in expected_type)
    if expected_type == "object":
        return isinstance(instance, dict)
    if expected_type == "array":
        return isinstance(instance, list)
    if expected_type == "string":
        return isinstance(instance, str)
    if expected_type == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected_type == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected_type == "boolean":
        return isinstance(instance, bool)
    if expected_type == "null":
        return instance is None
    raise ValueError(f"Unsupported JSON schema type: {expected_type}")


def _type_label(expected_type: str | list[str]) -> str:
    if isinstance(expected_type, list):
        return " or ".join(expected_type)
    return expected_type


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__
