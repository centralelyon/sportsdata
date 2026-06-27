"""Repository-root import shim for sportsdata_models."""

from pathlib import Path


_IMPLEMENTATION_DIR = Path(__file__).resolve().parents[1] / "python" / "sportsdata_models"
__path__ = [str(_IMPLEMENTATION_DIR)]

from .catalogs import (  # noqa: E402
    REPO_ROOT,
    catalog_ids,
    catalog_json_value_options,
    catalog_values,
    load_catalog,
    load_json,
    resolve_catalog,
)
from .metadata import load_metadata_field, metadata_json_value_options  # noqa: E402
from .version import model_version, sportsdata_version  # noqa: E402

__all__ = [
    "REPO_ROOT",
    "catalog_ids",
    "catalog_json_value_options",
    "catalog_values",
    "load_metadata_field",
    "load_catalog",
    "load_json",
    "metadata_json_value_options",
    "model_version",
    "resolve_catalog",
    "sportsdata_version",
]
