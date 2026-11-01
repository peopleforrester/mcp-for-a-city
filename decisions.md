<!--
ABOUTME: Settled decisions for this repo, newest first, each with its reason and where it was made.
ABOUTME: Check here before reopening a choice; add an entry when a new one is settled.
-->

# Decisions

## 2026-11-01: The American English check is tested, and the run is the E2E command

`tests/test_american_english.py` checks that `.american-english` exists, lists
paths, and covers every Markdown file, reading its globs the way
`check_american_english.py` does, and that AGENTS.md names the `--published`
run before a push. Running the checker needs the llm-coding-workflow checkout
in `~/repos`, so that run is `e2e/test_american_english.py`, which fails when
the checkout is missing. That makes it the repo's first test that needs
`~/repos`, so AGENTS.md now declares an E2E command, as the 2026-10-16 entry
below allowed once such a test existed. The checker is not copied into the
repo, so its word table cannot drift from the source. Issue #17, from #16.

## 2026-11-01: Every Markdown file is published writing for the American English check

The repo is public collateral under CC BY 4.0, and pushing it publishes it, so
`.american-english` lists `README.md` and `**/*.md`. That includes the working
research in `06-research-and-source-ledger/`. The first run found 216 British
forms there, and they were changed to American spelling with the wording left
as it was. Three stay British behind an inline `lexicon:` marker: a verbatim
quotation from the spec, a quotation from a paper and a URL slug. With no
build step, the managed pre-commit and the
`--published` run before a push are the publish step. Issue #16, from
peopleforrester/llm-coding-workflow#412.

## 2026-10-16: No end-to-end command; the link check is the whole gate

The heavy gate runs an end-to-end command only where a repo has end-to-end,
browser or integration tests against real services. This repo has none: its
only test is the relative link check, which reads local files. AGENTS.md says
so instead of declaring a command that would run nothing new. Issue #15.

## 2026-10-16: The README is for visitors; internal pointers go in AGENTS.md

The README is the repo's public front door. What the repo is, where its working
counterpart (`talks-knowledge`) lives, and how to work here belong in
[AGENTS.md](AGENTS.md), with `CLAUDE.md` as a symlink to it. Issue #13.

## 2026-10-16: The test is a relative link check

The repo holds talk materials with no code, so the test checks that every
relative link and image in its Markdown resolves to a file in the repo, using
the standard library only. Issue #14, commit `8e3f184`.

## 2026-10-06: Numbered, descriptive folders in the order the talk uses them

Every folder is named for what it holds and numbered in talk order, with the
README as the front door and start-here paths by reader. Issues #4, #5, #6,
commit `7b70c17`.

## 2026-10-05: The series is published as drafts and corrected in the open

Each part of Operating MCP at Scale is published as a draft so its sources can
be checked in the open, after four independent reviews (quotations, figures and
links, a hostile qualified reader, prose). Corrections arrive as issues on this
repo. A part is marked final only once approved, as part two was (issue #12).

## 2026-10-03: The gates checklist is generated from the site

`04-approval-gates-checklist/approval-gates.md` is generated from the site's
gate data, `src/data/gates.ts` in `peopleforrester/mcp-city`. Edit the source
and regenerate; do not edit the generated file. Commit `58572bf`.
