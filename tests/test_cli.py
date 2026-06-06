import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from sportsdata_models.validators import cli


class CliTests(unittest.TestCase):
    def test_module_runs_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, "-m", "sportsdata.validators.cli", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("--run-tests", result.stdout)

    def test_run_tests_option_dispatches_to_test_runner(self):
        previous_run_tests = cli.run_tests
        cli.run_tests = lambda: 0
        try:
            exit_code = cli.main(["--run-tests"])
        finally:
            cli.run_tests = previous_run_tests

        self.assertEqual(0, exit_code)

    def test_requires_path_without_run_tests(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                cli.main([])

        self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
