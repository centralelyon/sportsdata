from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

from .catalogs import MODELS_ROOT, REPO_ROOT, catalog_values, load_json


def _dimension_values(dimension: dict[str, Any]) -> list[dict[str, Any]]:
    field = dimension["field"]
    values = []
    for item in catalog_values(dimension["scope"], dimension["catalog"]):
        value = dict(item)
        value["field"] = field
        values.append(value)
    return values


def _passes_filters(row: dict[str, str], filters: list[dict[str, Any]]) -> bool:
    for rule in filters:
        field = rule["field"]
        allowed = set(rule.get("allow", []))
        denied = set(rule.get("deny", []))
        value = row.get(field)
        if allowed and value not in allowed:
            return False
        if denied and value in denied:
            return False
    return True


def derive_catalog(recipe: dict[str, Any], generated_from: str | None = None) -> dict[str, Any]:
    dimensions = recipe.get("dimensions", [])
    filters = recipe.get("filters", [])
    id_template = recipe["idTemplate"]
    label_template = recipe["labelTemplate"]
    values = []

    for combination in itertools.product(*[_dimension_values(d) for d in dimensions]):
        row: dict[str, Any] = {}
        labels: dict[str, str] = {}
        for item in combination:
            field = item["field"]
            row[field] = str(item["id"])
            labels[f"{field}_label"] = str(item.get("label", item["id"]))

        if not _passes_filters(row, filters):
            continue

        context = {**row, **labels}
        values.append(
            {
                "id": id_template.format(**context),
                "sport": "swimming",
                **row,
                "label": label_template.format(**context),
            }
        )

    return {
        "id": f"{recipe['id']}.generated",
        "title": recipe.get("title", recipe["id"]),
        "generatedFrom": generated_from or recipe.get("id"),
        "values": values,
    }


def derive_swimming_events() -> dict[str, Any]:
    recipe_path = MODELS_ROOT / "derivations" / "swimming" / "events.recipe.json"
    recipe = load_json(recipe_path)
    return derive_catalog(recipe, generated_from=str(recipe_path.relative_to(REPO_ROOT)))


def write_swimming_events(output: str | Path | None = None) -> Path:
    recipe_path = MODELS_ROOT / "derivations" / "swimming" / "events.recipe.json"
    recipe = load_json(recipe_path)
    target = Path(output) if output is not None else REPO_ROOT / recipe["output"]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(
            derive_catalog(recipe, generated_from=str(recipe_path.relative_to(REPO_ROOT))),
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")
    return target


def main() -> int:
    target = write_swimming_events()
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
