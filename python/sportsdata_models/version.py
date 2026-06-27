from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version

from .catalogs import MODELS_ROOT, REPO_ROOT, load_json


def model_version() -> str:
    data = load_json(MODELS_ROOT / "version.json")
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version:
        raise ValueError("models/version.json must contain a non-empty string version")
    return version


def sportsdata_version() -> str:
    pyproject_path = REPO_ROOT / "pyproject.toml"
    if pyproject_path.exists():
        match = re.search(
            r'(?m)^version = "([^"]+)"$',
            pyproject_path.read_text(encoding="utf-8"),
        )
        if match is None:
            raise ValueError("pyproject.toml must contain a project version")
        return match.group(1)

    try:
        return version("sportsdata")
    except PackageNotFoundError as error:
        raise RuntimeError("sportsdata package version is unavailable") from error
