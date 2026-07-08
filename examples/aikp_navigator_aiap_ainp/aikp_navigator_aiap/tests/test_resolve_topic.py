#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import resolve_topic


class ResolveTopicTests(unittest.TestCase):
    def test_normalize_topic(self) -> None:
        self.assertEqual(resolve_topic.normalize_topic("Release Evidence!"), "release-evidence")

    def test_empty_topic_fallback(self) -> None:
        self.assertEqual(resolve_topic.normalize_topic("  !!!  "), "untitled")

    def test_build_request(self) -> None:
        request = resolve_topic.build_request("AIKP Sources")
        self.assertEqual(request["protocol_hint"], "AIKP")
        self.assertEqual(request["topic_slug"], "aikp-sources")
        self.assertIn("risks", request["requested_views"])

    def test_cli_json_output(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", os.path.join(ROOT, "tools", "resolve_topic.py"), "Audit Trail"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["topic_slug"], "audit-trail")


if __name__ == "__main__":
    unittest.main()
