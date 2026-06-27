"""Shared model assets and validators for sports data files."""

from .catalogs import (
    REPO_ROOT,
    catalog_ids,
    catalog_json_value_options,
    catalog_values,
    load_catalog,
    load_json,
    resolve_catalog,
)
from .metadata import load_metadata_field, metadata_json_value_options
from .version import model_version, sportsdata_version

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
