# ABOUTME: Runs the real check_american_english.py --published over the repo and fails on any British form.
# ABOUTME: The E2E command in AGENTS.md. Fails, never skips, when the ~/repos llm-coding-workflow checkout is not there.

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = Path.home() / "repos" / "workflow" / "llm-coding-workflow" / "scripts" / "check_american_english.py"


def setUpModule():
    if not CHECKER.is_file():
        raise RuntimeError(
            f"{CHECKER} not found: the E2E suite runs the American English checker from a "
            "~/repos checkout of llm-coding-workflow. Run it on a machine that has one."
        )


class PublishedWritingTest(unittest.TestCase):
    def test_published_markdown_has_no_british_forms(self):
        result = subprocess.run(
            [sys.executable, "-I", str(CHECKER), "--published", "--root", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"check_american_english.py --published exited {result.returncode}:\n"
            + result.stdout
            + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
