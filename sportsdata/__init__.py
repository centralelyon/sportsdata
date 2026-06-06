"""Repository-root import shim for the public sportsdata package."""

from pathlib import Path


_IMPLEMENTATION_DIR = Path(__file__).resolve().parents[1] / "python" / "sportsdata"
__path__ = [str(_IMPLEMENTATION_DIR)]

from sportsdata_models import *  # noqa: F401,F403,E402
