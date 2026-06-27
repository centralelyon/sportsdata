from __future__ import annotations

import argparse
import sys
import unittest

from ..catalogs import REPO_ROOT
from ..version import model_version, sportsdata_version

from .files import validate_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate sports data files.")
    parser.add_argument("paths", nargs="*", help="Sports data files to validate")
    parser.add_argument("--format", dest="format_id", help="Force a known format id")
    parser.add_argument("--run-tests", action="store_true", help="Run the repository test suite")
    parser.add_argument("--version", action="store_true", help="Print the models version and exit")
    parser.add_argument(
        "--sportsdata-version",
        action="store_true",
        help="Print the sportsdata package version and exit",
    )
    args = parser.parse_args(argv)

    if args.sportsdata_version:
        print(sportsdata_version())
        return 0

    if args.version:
        print(model_version())
        return 0

    if args.run_tests:
        return run_tests()

    if not args.paths:
        parser.error("provide at least one path to validate, or use --run-tests")

    total_errors = 0
    for path in args.paths:
        issues = validate_file(path, args.format_id)
        if issues:
            print(f"{path}: {len(issues)} issue(s)")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"{path}: ok")
        total_errors += sum(1 for issue in issues if issue.severity == "error")

    return 1 if total_errors else 0


def run_tests() -> int:
    tests_dir = REPO_ROOT / "tests"
    if not tests_dir.exists():
        print(f"{tests_dir}: tests directory not found", file=sys.stderr)
        return 1

    suite = unittest.defaultTestLoader.discover(str(tests_dir), top_level_dir=str(REPO_ROOT))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
