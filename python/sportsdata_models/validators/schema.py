from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


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
    issues: list[ValidationIssue] = []
    expected_type = schema.get("type")

    if expected_type is not None and not _matches_type(instance, expected_type):
        issues.append(ValidationIssue(path, f"expected {_type_label(expected_type)}, got {_json_type(instance)}"))
        return issues

    if "enum" in schema and instance not in schema["enum"]:
        values = ", ".join(repr(value) for value in schema["enum"])
        issues.append(ValidationIssue(path, f"expected one of {values}"))

    if isinstance(instance, dict):
        issues.extend(_validate_object(instance, schema, path))
    elif isinstance(instance, list):
        issues.extend(_validate_array(instance, schema, path))
    elif isinstance(instance, str):
        issues.extend(_validate_string(instance, schema, path))
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        issues.extend(_validate_number(instance, schema, path))

    return issues


def _validate_object(instance: dict[str, Any], schema: dict[str, Any], path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    properties = schema.get("properties", {})

    for required in schema.get("required", []):
        if required not in instance:
            issues.append(ValidationIssue(path, f"missing required property {required!r}"))

    for key, child_schema in properties.items():
        if key in instance:
            issues.extend(validate_schema(instance[key], child_schema, f"{path}.{key}"))

    if schema.get("additionalProperties") is False:
        allowed = set(properties)
        for key in instance:
            if key not in allowed:
                issues.append(ValidationIssue(f"{path}.{key}", "additional property is not allowed"))

    return issues


def _validate_array(instance: list[Any], schema: dict[str, Any], path: str) -> list[ValidationIssue]:
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
            issues.extend(validate_schema(item, item_schema, f"{path}[{index}]"))

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
