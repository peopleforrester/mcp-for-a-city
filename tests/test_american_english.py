# ABOUTME: Checks the opt-in to the American English check: .american-english lists every Markdown file.
# ABOUTME: Also checks AGENTS.md names the run before a push. The run itself is the E2E suite in e2e/.

import os
import re
import unittest

from test_links import REPO_ROOT, markdown_files

OPT_IN = os.path.join(REPO_ROOT, ".american-english")
CHECK_COMMAND = (
    "`python3 ~/repos/workflow/llm-coding-workflow/scripts/check_american_english.py --published`"
)


def opt_in_patterns(text):
    """The globs an opt-in file lists, read as check_american_english.py reads them."""
    patterns = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            patterns.append(line)
    return patterns


def glob_regex(pattern):
    """The checker's glob: * and ? stay in one directory, ** crosses them, no slash means the root."""
    pattern = pattern.removeprefix("./").lstrip("/")
    if pattern.endswith("/"):
        pattern += "**"
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


def unlisted(paths, patterns):
    regexes = [glob_regex(p) for p in patterns]
    return [p for p in paths if not any(rx.fullmatch(p) for rx in regexes)]


class GlobTest(unittest.TestCase):
    def test_bare_name_is_root_only(self):
        self.assertEqual(unlisted(["README.md", "docs/README.md"], ["README.md"]), ["docs/README.md"])

    def test_double_star_crosses_directories(self):
        self.assertEqual(unlisted(["a.md", "x/y/b.md", "c.txt"], ["**/*.md"]), ["c.txt"])

    def test_comments_and_blank_lines_are_ignored(self):
        self.assertEqual(opt_in_patterns("# published\n\nREADME.md  # front door\n"), ["README.md"])


class OptInTest(unittest.TestCase):
    def test_opt_in_file_lists_paths(self):
        self.assertTrue(os.path.isfile(OPT_IN), ".american-english is missing")
        with open(OPT_IN, encoding="utf-8") as handle:
            self.assertNotEqual(opt_in_patterns(handle.read()), [], ".american-english lists no paths")

    def test_every_markdown_file_is_published(self):
        with open(OPT_IN, encoding="utf-8") as handle:
            patterns = opt_in_patterns(handle.read())
        paths = [os.path.relpath(p, REPO_ROOT).replace(os.sep, "/") for p in markdown_files()]
        missing = unlisted(paths, patterns)
        self.assertEqual(missing, [], "Markdown files .american-english does not list:\n" + "\n".join(missing))

    def test_agents_md_runs_the_check_before_a_push(self):
        with open(os.path.join(REPO_ROOT, "AGENTS.md"), encoding="utf-8") as handle:
            self.assertIn(CHECK_COMMAND, handle.read())


if __name__ == "__main__":
    unittest.main()
