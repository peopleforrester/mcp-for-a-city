<!--
ABOUTME: Settled decisions for this repo, newest first, each with its reason and where it was made.
ABOUTME: Check here before reopening a choice; add an entry when a new one is settled.
-->

# Decisions

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
