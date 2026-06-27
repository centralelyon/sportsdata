import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import sportsdata
from sportsdata_models.validators import cli
from sportsdata_models.version import model_version, sportsdata_version


class CliTests(unittest.TestCase):
    def test_public_api_returns_models_version(self):
        self.assertEqual(model_version(), sportsdata.model_version())

    def test_public_api_returns_sportsdata_version(self):
        self.assertEqual(sportsdata_version(), sportsdata.sportsdata_version())
        self.assertEqual(sportsdata_version(), sportsdata.__version__)

    def test_prints_models_version(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli.main(["--version"])

        self.assertEqual(0, exit_code)
        self.assertEqual(f"{model_version()}\n", output.getvalue())

    def test_prints_sportsdata_version(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli.main(["--sportsdata-version"])

        self.assertEqual(0, exit_code)
        self.assertEqual(f"{sportsdata_version()}\n", output.getvalue())

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
