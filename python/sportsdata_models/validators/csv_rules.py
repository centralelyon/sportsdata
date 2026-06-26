from __future__ import annotations

import ast
import csv
import math
import operator
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from ..catalogs import MODELS_ROOT, catalog_ids, load_json
from .schema import ValidationIssue


BASIC_TRACKING_COLUMNS = ["frameId", "swimmerId", "eventId", "time", "distance"]
COMMON_MINIMAL_TRACKING_COLUMNS = ["t", "x", "y"]
TABLE_TENNIS_BASIC_TRACKING_COLUMNS = ["frameId", "playerId", "eventId", "time", "x", "y", "z"]
SWIMMING_TRACKING_COLUMNS = [
    "frameId",
    "swimmerId",
    "swimmerName",
    "lane",
    "cumul",
    "eventId",
    "eventX",
    "eventY",
    "event",
    "TempsVideo (s)",
    "Temps (s)",
    "distance (m)",
    "tempo (s)",
    "frequence (cylce/min)",
    "amplitude (m)",
    "vitesse (m/s)",
]
SWIMFLOW_DETECTION_COLUMNS = [
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

CSV_FORMAT_RULES = {
    "common-minimal-tracking-csv": MODELS_ROOT / "rules" / "common" / "minimal-tracking-csv.rules.json",
    "formats.csv.common-minimal-tracking": MODELS_ROOT / "rules" / "common" / "minimal-tracking-csv.rules.json",
    "swimflow-csv": MODELS_ROOT / "rules" / "swimming" / "swimflow-csv.rules.json",
    "swimming-swimflow-csv": MODELS_ROOT / "rules" / "swimming" / "swimflow-csv.rules.json",
    "formats.csv.swimflow": MODELS_ROOT / "rules" / "swimming" / "swimflow-csv.rules.json",
    "swimming-basic-tracking-csv": MODELS_ROOT / "rules" / "swimming" / "basic-tracking-csv.rules.json",
    "formats.csv.swimming-basic-tracking": MODELS_ROOT / "rules" / "swimming" / "basic-tracking-csv.rules.json",
    "swimming-tracking-csv": MODELS_ROOT / "rules" / "swimming" / "tracking-csv.rules.json",
    "formats.csv.swimming-tracking": MODELS_ROOT / "rules" / "swimming" / "tracking-csv.rules.json",
    "table-tennis-basic-tracking-csv": MODELS_ROOT / "rules" / "table-tennis" / "basic-tracking-csv.rules.json",
    "formats.csv.table-tennis-basic-tracking": MODELS_ROOT / "rules" / "table-tennis" / "basic-tracking-csv.rules.json",
}

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INTEGER = re.compile(r"^[+-]?[0-9]+$")


@dataclass
class CsvRow:
    index: int
    values: dict[str, Any]


def detect_csv_format(path: str | Path) -> str:
    headers = _read_headers(path)
    if _has_columns(headers, SWIMFLOW_DETECTION_COLUMNS):
        return "swimflow-csv"
    if _has_columns(headers, COMMON_MINIMAL_TRACKING_COLUMNS):
        return "common-minimal-tracking-csv"
    if _has_columns(headers, SWIMMING_TRACKING_COLUMNS):
        return "swimming-tracking-csv"
    if _has_columns(headers, BASIC_TRACKING_COLUMNS):
        return "swimming-basic-tracking-csv"
    if _has_columns(headers, TABLE_TENNIS_BASIC_TRACKING_COLUMNS):
        return "table-tennis-basic-tracking-csv"
    return "unknown"


def validate_csv_file(path: str | Path, format_id: str | None = None) -> list[ValidationIssue]:
    selected_format = format_id or detect_csv_format(path)
    rules_path = _rules_path_for_format(selected_format)
    if rules_path is None:
        return [ValidationIssue("$", "unknown sports data format")]
    return validate_csv_with_rules(path, load_json(rules_path))


def validate_csv_with_rules(path: str | Path, rules: dict[str, Any]) -> list[ValidationIssue]:
    delimiter = str(rules.get("delimiter", ","))
    issues: list[ValidationIssue] = []
    typed_rows: list[CsvRow] = []

    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        headers = reader.fieldnames or []
        issues.extend(_validate_headers(headers, rules))

        for row_index, row in enumerate(reader):
            if None in row:
                issues.append(ValidationIssue(f"$[{row_index}]", "row has more cells than declared headers"))
            typed_rows.append(CsvRow(row_index, _coerce_row(row_index, row, rules, issues)))

    issues.extend(_validate_row_rules(typed_rows, rules))
    issues.extend(_validate_group_rules(typed_rows, rules))
    return issues


def _read_headers(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def _has_columns(headers: Sequence[str], required: Sequence[str]) -> bool:
    header_set = set(headers)
    return all(column in header_set for column in required)


def _rules_path_for_format(format_id: str) -> Path | None:
    if format_id in CSV_FORMAT_RULES:
        return CSV_FORMAT_RULES[format_id]

    if format_id.startswith("formats.csv."):
        format_name = format_id.removeprefix("formats.csv.")
        declaration_path = MODELS_ROOT / "formats" / "csv" / f"{format_name}.table-schema.json"
        if declaration_path.exists():
            declaration = load_json(declaration_path)
            rules_ref = declaration.get("rules")
            if isinstance(rules_ref, str):
                return _resolve_models_ref(rules_ref)

    return None


def _resolve_models_ref(reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "models":
        return MODELS_ROOT.parent / path
    return MODELS_ROOT / path


def _validate_headers(headers: list[str], rules: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column_rules = _column_rules(rules)

    duplicates = sorted(header for header, count in Counter(headers).items() if count > 1)
    for header in duplicates:
        issues.append(ValidationIssue("$", f"duplicate header {header!r}"))

    for column in rules.get("columns", []):
        name = column.get("name")
        if column.get("required", False) and name not in headers:
            issues.append(ValidationIssue("$", f"missing required column {name!r}"))

    if rules.get("allowExtraColumns", True) is False:
        for header in headers:
            if header not in column_rules:
                issues.append(ValidationIssue("$", f"unknown column {header!r}"))

    return issues


def _column_rules(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(column["name"]): column for column in rules.get("columns", []) if "name" in column}


def _coerce_row(
    row_index: int,
    row: dict[str | None, str | None],
    rules: dict[str, Any],
    issues: list[ValidationIssue],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in rules.get("columns", []):
        name = str(column.get("name", ""))
        if name not in row:
            continue
        values[name] = _coerce_cell(row_index, name, row.get(name), column, issues)
    return values


def _coerce_cell(
    row_index: int,
    name: str,
    raw_value: str | None,
    column: dict[str, Any],
    issues: list[ValidationIssue],
) -> Any:
    path = _cell_path(row_index, name)
    text = "" if raw_value is None else raw_value.strip()

    if text == "":
        if column.get("required", False):
            issues.append(ValidationIssue(path, "required value is empty"))
        elif column.get("nullable", False):
            return None
        else:
            issues.append(ValidationIssue(path, "empty value is not allowed"))
        return None

    column_type = column.get("type")
    if column_type == "integer":
        value = _coerce_integer(text, path, issues)
    elif column_type == "number":
        value = _coerce_number(text, path, issues)
    elif column_type == "string":
        value = text
    elif column_type == "boolean":
        value = _coerce_boolean(text, path, issues)
    elif column_type in {"date", "timecode"}:
        value = text
    else:
        issues.append(ValidationIssue(path, f"unsupported column type {column_type!r}"))
        return None

    if value is None:
        return None

    _validate_cell_constraints(row_index, name, value, column, issues)
    return value


def _coerce_integer(text: str, path: str, issues: list[ValidationIssue]) -> int | None:
    if _INTEGER.match(text) is None:
        issues.append(ValidationIssue(path, "expected integer"))
        return None
    return int(text)


def _coerce_number(text: str, path: str, issues: list[ValidationIssue]) -> float | None:
    try:
        value = float(text)
    except ValueError:
        issues.append(ValidationIssue(path, "expected number"))
        return None
    if not math.isfinite(value):
        issues.append(ValidationIssue(path, "expected finite number"))
        return None
    return value


def _coerce_boolean(text: str, path: str, issues: list[ValidationIssue]) -> bool | None:
    if text.lower() in {"true", "1"}:
        return True
    if text.lower() in {"false", "0"}:
        return False
    issues.append(ValidationIssue(path, "expected boolean"))
    return None


def _validate_cell_constraints(
    row_index: int,
    name: str,
    value: Any,
    column: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    path = _cell_path(row_index, name)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = column.get("min")
        maximum = column.get("max")
        exclusive_minimum = column.get("exclusiveMin")
        exclusive_maximum = column.get("exclusiveMax")
        if minimum is not None and value < minimum:
            issues.append(ValidationIssue(path, f"expected value >= {minimum}"))
        if maximum is not None and value > maximum:
            issues.append(ValidationIssue(path, f"expected value <= {maximum}"))
        if exclusive_minimum is not None and value <= exclusive_minimum:
            issues.append(ValidationIssue(path, f"expected value > {exclusive_minimum}"))
        if exclusive_maximum is not None and value >= exclusive_maximum:
            issues.append(ValidationIssue(path, f"expected value < {exclusive_maximum}"))

    if isinstance(value, str):
        min_length = column.get("minLength")
        pattern = column.get("pattern")
        if min_length is not None and len(value) < min_length:
            issues.append(ValidationIssue(path, f"expected at least {min_length} characters"))
        if pattern is not None and re.search(str(pattern), value) is None:
            issues.append(ValidationIssue(path, f"does not match pattern {pattern!r}"))

    if "enum" in column and value not in column["enum"]:
        values = ", ".join(repr(item) for item in column["enum"])
        issues.append(ValidationIssue(path, f"expected one of {values}"))

    catalog = column.get("catalog")
    if isinstance(catalog, str):
        allowed = _catalog_ids(catalog)
        if str(value) not in allowed:
            values = ", ".join(sorted(allowed))
            issues.append(ValidationIssue(path, f"expected one of: {values}"))


def _catalog_ids(catalog: str) -> set[str]:
    scope, name = catalog.rsplit(".", 1)
    return catalog_ids(scope, name)


def _validate_row_rules(rows: list[CsvRow], rules: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rule in rules.get("rowRules", []):
        if rule.get("check") == "comparison":
            for row in rows:
                issue = _validate_comparison(row, rule)
                if issue is not None:
                    issues.append(issue)
    return issues


def _validate_comparison(row: CsvRow, rule: dict[str, Any]) -> ValidationIssue | None:
    left_name = str(rule.get("left"))
    right_ref = rule.get("right")
    left = row.values.get(left_name)
    right = row.values.get(right_ref) if isinstance(right_ref, str) and right_ref in row.values else right_ref
    if left is None or right is None:
        return None

    operator_name = str(rule.get("operator"))
    comparisons = {
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }
    compare = comparisons.get(operator_name)
    if compare is None or compare(left, right):
        return None

    right_label = right_ref if isinstance(right_ref, str) else repr(right)
    return ValidationIssue(
        _cell_path(row.index, left_name),
        f"expected {left_name!r} {operator_name} {right_label!r}",
        str(rule.get("severity", "error")),
    )


def _validate_group_rules(rows: list[CsvRow], rules: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for group_rows in _groups(rows, rules).values():
        for rule in rules.get("groupRules", []):
            check = rule.get("check")
            if check == "contiguousInteger":
                issues.extend(_validate_contiguous_integer(group_rows, rule))
            elif check == "monotonic":
                issues.extend(_validate_monotonic(group_rows, rule))
            elif check == "deltaEquals":
                issues.extend(_validate_delta_equals(group_rows, rule))
            elif check == "deltaFormula":
                issues.extend(_validate_delta_formula(group_rows, rule))
            elif check == "formula":
                issues.extend(_validate_formula(group_rows, rule))
    return issues


def _groups(rows: list[CsvRow], rules: dict[str, Any]) -> dict[tuple[Any, ...], list[CsvRow]]:
    group_by = [str(column) for column in rules.get("groupBy", [])]
    if not group_by:
        return {(): rows}

    grouped: dict[tuple[Any, ...], list[CsvRow]] = defaultdict(list)
    for row in rows:
        key = tuple(row.values.get(column) for column in group_by)
        if any(value is None for value in key):
            continue
        grouped[key].append(row)
    return grouped


def _validate_contiguous_integer(rows: list[CsvRow], rule: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column = str(rule.get("column"))
    expected = int(rule.get("start", 0))
    severity = str(rule.get("severity", "error"))

    for row in rows:
        value = row.values.get(column)
        if value is None:
            continue
        if value != expected:
            issues.append(ValidationIssue(_cell_path(row.index, column), f"expected contiguous value {expected}, got {value}", severity))
            expected = value + 1
        else:
            expected += 1
    return issues


def _validate_monotonic(rows: list[CsvRow], rule: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column = str(rule.get("column"))
    direction = str(rule.get("direction", "increasing"))
    severity = str(rule.get("severity", "error"))
    previous: Any = None

    for row in rows:
        value = row.values.get(column)
        if value is None:
            continue
        if previous is not None:
            if direction == "increasing":
                valid = value > previous
            elif direction == "nondecreasing":
                valid = value >= previous
            elif direction == "decreasing":
                valid = value < previous
            elif direction == "nonincreasing":
                valid = value <= previous
            else:
                valid = True
            if not valid:
                issues.append(ValidationIssue(_cell_path(row.index, column), f"expected {direction} values within group", severity))
        previous = value

    return issues


def _validate_delta_equals(rows: list[CsvRow], rule: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column = str(rule.get("column"))
    source = str(rule.get("source"))
    tolerance = float(rule.get("tolerance", 0))
    severity = str(rule.get("severity", "error"))
    previous: float | int | None = None

    for row in rows:
        source_value = row.values.get(source)
        target = row.values.get(column)
        if previous is None:
            previous = source_value
            continue
        if source_value is None:
            previous = source_value
            continue
        if target is None and rule.get("skipWhenEmpty", False):
            previous = source_value
            continue
        if target is None:
            issues.append(ValidationIssue(_cell_path(row.index, column), "expected derived value", severity))
            previous = source_value
            continue

        expected = source_value - previous
        _append_formula_issue(issues, row, column, target, expected, tolerance, rule, severity)
        previous = source_value

    return issues


def _validate_delta_formula(rows: list[CsvRow], rule: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column = str(rule.get("column"))
    source = str(rule.get("source"))
    formula = str(rule.get("formula", "delta"))
    tolerance = float(rule.get("tolerance", 0))
    severity = str(rule.get("severity", "error"))
    previous: float | int | None = None

    for row in rows:
        source_value = row.values.get(source)
        target = row.values.get(column)
        if previous is None:
            previous = source_value
            continue
        if source_value is None:
            previous = source_value
            continue
        if target is None and rule.get("skipWhenEmpty", False):
            previous = source_value
            continue
        if target is None:
            issues.append(ValidationIssue(_cell_path(row.index, column), "expected derived value", severity))
            previous = source_value
            continue

        expected = _eval_formula(formula, {"delta": source_value - previous})
        if expected is not None:
            _append_formula_issue(issues, row, column, target, expected, tolerance, rule, severity)
        previous = source_value

    return issues


def _validate_formula(rows: list[CsvRow], rule: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    column = str(rule.get("column"))
    formula = str(rule.get("formula", ""))
    inputs = {str(name): str(source) for name, source in rule.get("inputs", {}).items()}
    tolerance = float(rule.get("tolerance", 0))
    severity = str(rule.get("severity", "error"))

    for row in rows:
        target = row.values.get(column)
        variables = {name: row.values.get(source) for name, source in inputs.items()}
        has_empty_input = any(value is None for value in variables.values())
        if rule.get("skipWhenEmpty", False) and (target is None or has_empty_input):
            continue
        if target is None:
            issues.append(ValidationIssue(_cell_path(row.index, column), "expected derived value", severity))
            continue
        if has_empty_input:
            continue

        expected = _eval_formula(formula, variables)
        if expected is not None:
            _append_formula_issue(issues, row, column, target, expected, tolerance, rule, severity)

    return issues


def _append_formula_issue(
    issues: list[ValidationIssue],
    row: CsvRow,
    column: str,
    actual: float,
    expected: float,
    tolerance: float,
    rule: dict[str, Any],
    severity: str,
) -> None:
    if abs(actual - expected) <= tolerance:
        return
    issues.append(
        ValidationIssue(
            _cell_path(row.index, column),
            f"expected {column!r} ~= {_format_number(expected)}, got {_format_number(actual)} ({rule.get('id')})",
            severity,
        )
    )


def _eval_formula(formula: str, variables: dict[str, Any]) -> float | None:
    try:
        tree = ast.parse(formula, mode="eval")
        return float(_eval_node(tree.body, variables))
    except (ArithmeticError, KeyError, TypeError, ValueError, SyntaxError):
        return None


def _eval_node(node: ast.AST, variables: dict[str, Any]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        value = variables[node.id]
        if value is None:
            raise ValueError(node.id)
        return float(value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand, variables)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
        return _eval_node(node.operand, variables)
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(ast.dump(node))


def _cell_path(row_index: int, column: str) -> str:
    if _IDENTIFIER.match(column):
        return f"$[{row_index}].{column}"
    escaped = column.replace("\\", "\\\\").replace('"', '\\"')
    return f'$[{row_index}]."{escaped}"'


def _format_number(value: float) -> str:
    return f"{value:.6g}"
