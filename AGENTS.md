<!--
ABOUTME: Internal guidance for any session working in this repo: what it is, what it holds, where its working counterpart lives.
ABOUTME: The README is for visitors; internal pointers belong here. CLAUDE.md is a symlink to this file.
-->

# mcp-for-a-city

Test command: `python3 -m unittest discover -s tests -v`

## What this repo is

The public collateral for **Governing MCP for a Workforce the Size of a City**,
the keynote Michael Rishi Forrester gave at MCP Dev Summit Toronto on
2026-10-06, published as `peopleforrester/mcp-for-a-city`. It is a content repo:
slides, script, research, art and an article series. The only code is the link
check in `tests/`.

This repo is the published output, not the workshop. Anything about the talk
that is not a file here (governance, the repo registry, the KRs, working notes)
lives in the working counterpart.

## Working counterpart: talks-knowledge

`talks-knowledge` is the knowledge repo for the talks grouping. It holds
`GOVERNANCE.md`, `REPOS.md` and the KRs that this repo's work is measured
against. Find it with `repo-management whereis talks-knowledge`, and read this
repo's record with `hec context peopleforrester/mcp-for-a-city`.

## What it holds

The README's "What is here" table maps the numbered folders. Some files are
copies of a source that lives elsewhere; edit the source, then carry the result
here:

| File or folder | Source |
|---|---|
| `04-approval-gates-checklist/approval-gates.md` | Generated from `src/data/gates.ts` in `peopleforrester/mcp-city` (the site) |
| `01-keynote-slides/`, `02-spoken-script/` | Exported from the deck as delivered and its speaker notes |
| `03-shadow-play-film/` | Links only; the film's source is `peopleforrester/mcp-city-film` |

`06-research-and-source-ledger/` is the working research; `07-sources-slide/`
is only what appeared on the sources slide.

## Working here

- Keep `README.md` visitor-facing. Internal pointers, process notes and
  agent guidance go in this file.
- Current status is in [PROJECT_STATE.md](PROJECT_STATE.md); settled choices
  are in [decisions.md](decisions.md).
- Public prose and factual claims wait for Michael's review. Corrections from
  readers arrive as issues using `.github/ISSUE_TEMPLATE/correction.md`.
- Specification facts are stated against the 2026-07-28 revision.
