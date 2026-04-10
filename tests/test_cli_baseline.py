from __future__ import annotations

import json
import sys
import tempfile
import unittest

from tools.cli_baseline import collect_dependency_status, doctor_clis, run_cli, smoke_clis


class CliBaselineTests(unittest.TestCase):
    def test_xiaogugit_runs_with_shared_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cli-baseline-test-xg-") as temp_dir:
            result = run_cli("xiaogugit", ["--root-dir", temp_dir, "project", "list"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"projects": []})

    def test_wikimg_smoke_matches_python_baseline(self) -> None:
        result = smoke_clis(["wikimg"])[0]
        expected_status = "skipped" if sys.version_info[:2] < (3, 10) else "passed"

        self.assertEqual(result["status"], expected_status)

    def test_ner_smoke_matches_python_baseline(self) -> None:
        result = smoke_clis(["ner"])[0]
        expected_status = "skipped" if sys.version_info[:2] < (3, 10) else "passed"

        self.assertEqual(result["status"], expected_status)

    def test_aft_smoke_is_skipped_when_python_is_too_old(self) -> None:
        results = smoke_clis(["aft-review", "aft-qa"])
        expected_status = "skipped" if sys.version_info[:2] < (3, 11) else "passed"

        self.assertEqual([result["status"] for result in results], [expected_status, expected_status])

    def test_doctor_reports_defaults_and_dependency_metadata(self) -> None:
        report = doctor_clis(["mm-denoise"], include_help=False, include_smoke=False)[0]

        self.assertEqual(report["cli"], "mm-denoise")
        self.assertTrue(report["defaults"]["config_path"].endswith("preprocess\\config.no_models.yaml"))
        self.assertIn("dependencies", report)
        self.assertIn("optional", report["dependencies"])

    def test_collect_dependency_status_marks_missing_modules(self) -> None:
        report = collect_dependency_status(
            [
                {"module": "json", "package": "json", "optional": False},
                {"module": "module_that_should_not_exist_for_cli_baseline_tests", "package": "missing", "optional": True},
            ]
        )

        self.assertEqual(report["required_missing"], [])
        self.assertEqual(
            report["optional_missing"],
            [{"module": "module_that_should_not_exist_for_cli_baseline_tests", "package": "missing"}],
        )


if __name__ == "__main__":
    unittest.main()
