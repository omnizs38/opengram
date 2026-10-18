#!/usr/bin/env python3
"""Regression checks for concise CI failure diagnostics."""
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from show_failure import report


class FailureOutput(unittest.TestCase):
    def run_report(self, text, env=None):
        with tempfile.TemporaryDirectory(prefix="opengram log test ") as tmp:
            path = Path(tmp) / "build.log"
            path.write_text(text, encoding="utf-8")
            output = io.StringIO()
            with patch.dict(os.environ, env or {}, clear=True), redirect_stdout(output):
                self.assertEqual(report(path), 0)
            return output.getvalue(), path.read_text(encoding="utf-8")

    def test_large_log_is_bounded_and_keeps_early_error(self):
        text = "fatal error C1060: compiler heap exhausted\n" + "progress\n" * 25000
        output, saved = self.run_report(text)
        self.assertIn("fatal error C1060", output)
        self.assertLess(len(output.splitlines()), 60)
        self.assertEqual(saved, text)

    def test_long_lines_are_truncated_and_workflow_commands_are_prefixed(self):
        output, _ = self.run_report("::warning::" + "x" * 30000 + "\n")
        self.assertLess(len(output), 1000)
        self.assertFalse(any(line.startswith("::warning::") for line in output.splitlines()))

    def test_secrets_are_removed_from_console_and_artifact(self):
        output, saved = self.run_report("error: abc123abc 123\n", {"API_HASH": "abc123abc", "API_ID": "123"})
        for value in ("abc123abc", "123"):
            self.assertNotIn(value, output)
            self.assertNotIn(value, saved)

    def test_error_storm_is_bounded(self):
        output, _ = self.run_report("error: build failed\n" * 25000)
        self.assertLess(len(output.splitlines()), 60)

    def test_empty_log(self):
        output, saved = self.run_report("")
        self.assertIn("No explicit error line", output)
        self.assertEqual(saved, "")

    def test_missing_log(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            self.assertEqual(report(Path(tmp) / "missing.log"), 1)


if __name__ == "__main__":
    unittest.main()
