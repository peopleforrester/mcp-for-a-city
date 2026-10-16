<!--
ABOUTME: Current state of the keynote collateral repo: what is published, what is still draft, what is next.
ABOUTME: Reconcile against git log and the series index at the start of each session.
-->

# Project state

Last reconciled: 2026-10-16.

## Where things stand

- The keynote was delivered at MCP Dev Summit Toronto on 2026-10-06. The deck
  (the 39 slides shown) and the spoken script are published as delivered.
- The approval gates checklist, architecture diagram, research and source
  ledger, sources slide, art, QR code and film links are published.
- Operating MCP at Scale series, per
  [its index](10-operating-mcp-at-scale-series/README.md):

  | Item | Status |
  |---|---|
  | Part 1, operational excellence | draft |
  | Part 2, security | final |
  | Part 3, reliability | draft |
  | Part 4, performance | draft |
  | Part 5, cost | draft |
  | Enterprise checklist | draft, under review |

- Tests: a relative link and image check over every Markdown file
  (`tests/test_links.py`), standard library only.

## Next

- Move parts 1, 3, 4, 5 and the checklist from draft to final as each is
  approved, updating the status in the series index and the part's header.
- When the series leaves draft, update `date-released` and `version` in
  [CITATION.cff](CITATION.cff), as its header says.
