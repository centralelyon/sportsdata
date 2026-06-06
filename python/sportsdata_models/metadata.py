from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalogs import MODELS_ROOT, catalog_json_value_options, load_json


def metadata_path(sport: str, field: str) -> Path:
    return MODELS_ROOT / "metadata" / sport / f"{field}.json"


def load_metadata_field(sport: str, field: str) -> dict[str, Any]:
    return load_json(metadata_path(sport, field))


def metadata_json_value_options(sport: str, field: str) -> list[dict[str, str]]:
    metadata = load_metadata_field(sport, field)
    catalog = metadata["valueCatalog"]
    return catalog_json_value_options(
        catalog["scope"],
        catalog["name"],
        json_value_field=metadata.get("jsonValueField", "id"),
    )
