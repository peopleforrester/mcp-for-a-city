# ABOUTME: Checks that every relative link and image in the repo's Markdown resolves to a file.
# ABOUTME: Standard library only; run with `python3 -m unittest discover -s tests`.

import os
import re
import unittest
from urllib.parse import unquote

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# An inline link or image: [text](target) or ![alt](target), with an optional title.
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`[^`]*`")
EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def markdown_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in sorted(filenames):
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def relative_targets(text):
    """Yield (line number, target) for every relative link outside code."""
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in INLINE_LINK.finditer(CODE_SPAN.sub("", line)):
            target = match.group(1).strip("<>")
            if EXTERNAL.match(target) or target.startswith("#"):
                continue
            yield number, target


def resolve(source, target):
    path = unquote(target.split("#", 1)[0])
    if path.startswith("/"):
        return os.path.join(REPO_ROOT, path.lstrip("/"))
    return os.path.normpath(os.path.join(os.path.dirname(source), path))


class RelativeTargetsTest(unittest.TestCase):
    def test_finds_links_and_images(self):
        text = "See [gates](../04/gates.md) and ![art](art/a%20b.png \"Title\")."
        self.assertEqual(
            list(relative_targets(text)),
            [(1, "../04/gates.md"), (1, "art/a%20b.png")],
        )

    def test_skips_external_anchors_and_code(self):
        text = "\n".join(
            [
                "[site](https://example.com) [mail](mailto:a@b.c) [top](#start)",
                "`[span](missing.md)`",
                "```",
                "[fenced](missing.md)",
                "```",
            ]
        )
        self.assertEqual(list(relative_targets(text)), [])

    def test_resolve_drops_fragment_and_decodes(self):
        source = os.path.join(REPO_ROOT, "docs", "page.md")
        self.assertEqual(
            resolve(source, "../art/a%20b.png#top"),
            os.path.join(REPO_ROOT, "art", "a b.png"),
        )


class RepoLinksTest(unittest.TestCase):
    def test_markdown_files_exist(self):
        self.assertTrue(any(markdown_files()))

    def test_relative_links_resolve(self):
        broken = []
        for source in markdown_files():
            with open(source, encoding="utf-8") as handle:
                text = handle.read()
            for number, target in relative_targets(text):
                if not os.path.exists(resolve(source, target)):
                    rel = os.path.relpath(source, REPO_ROOT)
                    broken.append(f"{rel}:{number}: {target}")
        self.assertEqual(broken, [], "broken relative links:\n" + "\n".join(broken))


if __name__ == "__main__":
    unittest.main()
