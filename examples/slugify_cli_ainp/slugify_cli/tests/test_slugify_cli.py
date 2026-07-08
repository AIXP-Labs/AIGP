#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from slugify_cli import slugify  # noqa: E402


class SlugifyCliTests(unittest.TestCase):
    def test_slugify_normalizes_text(self) -> None:
        self.assertEqual(slugify("Hello, AINP World!"), "hello-ainp-world")
        self.assertEqual(slugify("Crème brûlée"), "creme-brulee")

    def test_slugify_has_fallback_and_length_limit(self) -> None:
        self.assertEqual(slugify("!!!"), "untitled")
        self.assertEqual(slugify("Alpha Beta Gamma", max_length=10), "alpha-beta")

    def test_cli_reads_arguments(self) -> None:
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "slugify_cli.py"), "AINP Program Example"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(proc.stdout.strip(), "ainp-program-example")

    def test_cli_reads_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "slugify_cli.py")],
            input="Generated Content\n",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(proc.stdout.strip(), "generated-content")


if __name__ == "__main__":
    unittest.main()
