#!/usr/bin/env python3
"""Run with python3 scripts/rove-launcher-test.py; no network or processes."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("rove_launcher", Path(__file__).with_name("rove-launcher.py"))
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTest(unittest.TestCase):
    def test_target_selection_and_explicit_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            (prefix / "hosts.json").write_text(json.dumps(["user@example.test"]))
            server = "--server=~/.local/opt/rove-mosh/bin/mosh-server"
            self.assertIn(server, launcher.command(prefix, ["--ssh=ssh -p 2223", "-p", "60000:60010", "user@example.test"]))
            self.assertIn(server, launcher.command(prefix, ["--ssh", "ssh -p 2223", "--", "user@example.test"]))
            self.assertNotIn(server, launcher.command(prefix, ["other@example.test", "echo", "user@example.test"]))
            override = launcher.command(prefix, ["--server=/custom/server", "user@example.test"])
            self.assertLess(override.index(server), override.index("--server=/custom/server"))
            self.assertNotIn(server, launcher.command(prefix, ["--version"]))


if __name__ == "__main__":
    unittest.main()
