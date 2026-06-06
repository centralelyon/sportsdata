from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(os.environ.get("SPORTSDATA_REPO_ROOT", Path(__file__).resolve().parents[2]))
MODELS_ROOT = Path(os.environ.get("SPORTSDATA_MODELS_ROOT", REPO_ROOT / "models"))


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def catalog_path(scope: str, name: str) -> Path:
    filename = name if name.endswith(".json") else f"{name}.json"
    return MODELS_ROOT / "catalogs" / scope / filename


def catalog_overrides_path(scope: str, name: str) -> Path:
    filename = name.removesuffix(".json")
    return MODELS_ROOT / "catalogs" / scope / f"{filename}.overrides.json"


def resolve_catalog(catalog: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    if not overrides:
        return catalog

    resolved = dict(catalog)
    values = [dict(item) for item in catalog.get("values", [])]
    positions = {str(item["id"]): index for index, item in enumerate(values)}

    for item in overrides.get("fixes", []):
        value_id = str(item["id"])
        if value_id in positions:
            values[positions[value_id]] = {**values[positions[value_id]], **item}
        else:
            values.append(dict(item))
            positions[value_id] = len(values) - 1

    for item in overrides.get("manualValues", []):
        value_id = str(item["id"])
        if value_id in positions:
            values[positions[value_id]] = {**values[positions[value_id]], **item}
        else:
            values.append(dict(item))
            positions[value_id] = len(values) - 1

    resolved["values"] = values
    resolved["overrides"] = {
        "id": overrides.get("id"),
        "fixes": len(overrides.get("fixes", [])),
        "manualValues": len(overrides.get("manualValues", [])),
    }
    return resolved


def load_catalog(scope: str, name: str, include_overrides: bool = True) -> dict[str, Any]:
    catalog = load_json(catalog_path(scope, name))
    if not include_overrides:
        return catalog

    overrides_path = catalog_overrides_path(scope, name)
    if not overrides_path.exists():
        return catalog
    return resolve_catalog(catalog, load_json(overrides_path))


def catalog_values(scope: str, name: str, include_overrides: bool = True) -> list[dict[str, Any]]:
    values = load_catalog(scope, name, include_overrides=include_overrides).get("values", [])
    if not isinstance(values, list):
        raise ValueError(f"Catalog {scope}/{name} has a non-list values field")
    return values


def catalog_ids(scope: str, name: str, include_overrides: bool = True) -> set[str]:
    return {str(item["id"]) for item in catalog_values(scope, name, include_overrides=include_overrides)}


def catalog_index(scope: str, name: str, include_overrides: bool = True) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in catalog_values(scope, name, include_overrides=include_overrides)}


def catalog_json_value_options(
    scope: str,
    name: str,
    json_value_field: str = "id",
    include_overrides: bool = True,
) -> list[dict[str, str]]:
    options = []
    for item in catalog_values(scope, name, include_overrides=include_overrides):
        json_value = item.get(json_value_field, item["id"])
        options.append(
            {
                "id": str(item["id"]),
                "label": str(item.get("label", item["id"])),
                "jsonValue": str(json_value),
            }
        )
    return options


def assert_unique_catalog_ids(scope: str, name: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in catalog_values(scope, name):
        value_id = str(item.get("id", ""))
        if not value_id:
            raise ValueError(f"Catalog {scope}/{name} has a value without an id")
        if value_id in seen:
            duplicates.append(value_id)
        seen.add(value_id)
    if duplicates:
        values = ", ".join(sorted(set(duplicates)))
        raise ValueError(f"Catalog {scope}/{name} has duplicate ids: {values}")
