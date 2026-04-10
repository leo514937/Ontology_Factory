from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.cli_baseline import run_cli


class MmDenoiseCliTests(unittest.TestCase):
    def test_help_no_longer_requires_optional_dependencies(self) -> None:
        result = run_cli("mm-denoise", ["--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout.lower())

    def test_stdout_json_reports_generated_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mm-denoise-cli-test-") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.txt"
            output_dir = temp_path / "outputs"
            input_path.write_text("ESP8266 连接 OneNet。\n\n重复标题\n重复标题\n", encoding="utf-8")

            result = run_cli(
                "mm-denoise",
                [
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_dir),
                    "--stdout-json",
                ],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["results"]), 1)
            artifact = payload["results"][0]
            self.assertTrue(Path(artifact["clean_text_path"]).exists())
            self.assertTrue(Path(artifact["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
