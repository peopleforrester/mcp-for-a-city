---
title: Registry count verification, three published MCP ecosystem counts
date: 2026-09-19
sources_verified_on: 2026-09-19
status: draft
---

<!-- ABOUTME: Re-measures three published MCP ecosystem counts (official registry, PulseMCP, Glama) and checks what each says it counts. -->
<!-- ABOUTME: Also records the publisher concentration in the official registry, measured by full pagination on 2026-09-19. -->

# Registry count verification

## Why this exists

The keynote opens on this line:

> "Three published counts of the same ecosystem, an order of magnitude apart,
> none of them wrong, and none of them saying which thing they counted."

The vulnerable half is the last clause. If any of the three publishes a clear
definition of what it counts, the line is an accusation that the maintainers in
the room can refute from their own site during the talk. This document checks
each one and re-measures all three.

**Result: the line does not survive. Two of the three publish an explicit
definition, and one of them pre-emptively explains the exact discrepancy the
keynote is built on. The measured spread is also 4x, not an order of magnitude.**

## Today's measurements against the 2026-09-17 figures

All three re-measured 2026-09-19.

| Source | 2026-09-17 (as supplied) | 2026-09-19 (measured) | Method used today |
|---|---|---|---|
| Official MCP Registry, version records | "more than 28,000" | **108,042** | Paged `GET /v0.1/servers?limit=100` to cursor exhaustion, 1,081 pages |
| Official MCP Registry, distinct servers | 2,660 distinct names in first 7,500 records | **33,366** | Paged `GET /v0.1/servers?limit=100&version=latest`, 334 pages, records and distinct names 1:1 |
| PulseMCP | 21,880 | **21,869** | Count rendered on the directory page |
| Glama | 88,809 | **89,255** | Count rendered in the page title |

Sources and verification date for each, all 2026-09-19:

- Registry API: `https://registry.modelcontextprotocol.io/v0.1/servers`
- PulseMCP: https://www.pulsemcp.com/servers
- Glama: https://glama.ai/mcp/servers

The 2026-09-17 PulseMCP and Glama figures are **UNVERIFIED** and not
retroactively checkable. Neither site publishes a historical series, so the only
honest statement is that they are close to today's readings and drifting in
opposite directions.

### One 2026-09-17 figure reproduces, one does not

The "2,660 distinct names in the first 7,500 records" measurement is sound. Run
again today on the same endpoint in the same order, the first 7,500 records
contain **2,642 distinct names**. That is a stable property of the listing order,
not an artefact.

The "more than 28,000 version records" figure does not reproduce. Today the full
paginated total is 108,042. Two days cannot produce that growth, so the 2026-09-17
run was almost certainly truncated before cursor exhaustion and its number is a
floor rather than a total. **Do not use the 28,000 figure on a slide.**

The larger problem is what was inferred from the pair. Reading 2,660 distinct
names out of 7,500 records as evidence that the registry holds only a few
thousand real servers is wrong by an order of magnitude. The registry's listing
order front-loads heavily republished servers, so the early-page ratio is not
representative. Measured to exhaustion, the registry holds **33,366 distinct
servers**, which is more than PulseMCP's 21,869, not a tenth of it.

## 1. PulseMCP: publishes a definition, and pre-explains the gap

**It does.** PulseMCP's statistics page carries a section headed "Total MCP
Servers" whose entire purpose is to say what the count includes.

Verbatim, from https://www.pulsemcp.com/statistics, verified 2026-09-19:

> "Important notes about the 'total MCP servers' count in the data above:
> This count is representative of PulseMCP's scraped database of meaningful MCP
> servers. We intentionally omit low quality implementations that we don't think
> would ever be used by someone besides the creator. This is why our 'total
> count' may be less than that of another server aggregator; we are confident
> that the difference in total numbers can be purely attributed to our decision
> to not catalog the lowest quality implementations."

That last sentence is the problem for the keynote. PulseMCP defines its count,
then names the comparison the talk is about to make and gives its reason for the
difference before anyone asks.

The same page also states its scope for the surrounding metrics:

> "MCP ecosystem-wide metrics derived from data we are scraping from across the
> internet. The statistics on this page are kept dynamically up-to-date by our
> internal data warehouse, updated daily. They are meant to approximate the whole
> MCP ecosystem, and not the metrics of any single particular platform that
> integrates with MCP."

The directory page's own meta description makes the scope claim too: "A
daily-updated directory of all Model Context Protocol (MCP) servers available on
the internet" (https://www.pulsemcp.com/servers, verified 2026-09-19).

**Material caveat on freshness.** PulseMCP's ingestion is currently paused, from
https://www.pulsemcp.com/submit, verified 2026-09-19, page dated "Last updated:
September 3, 2026":

> "We know this is not what you came here to read. We are not accepting new MCP
> server or client submissions right now, and we are not making changes to
> existing listings. [...] Why: our directory pipeline and listing management need
> a bit of an overhaul to ensure listings are accurate and changes are addressed
> more quickly."

and:

> "In the meantime, if you have a server to share, publish it to the Official MCP
> Registry. That is the best first step even when we are not paused, and we will
> pick it up automatically once we are back."

So PulseMCP's number has been substantially frozen for roughly two weeks. That is
a better and more defensible explanation of why its count sits below the others
than any claim about undeclared methodology.

**API note:** the `v0beta` API used for prior measurements is fully sunset as of
September 2026 and now fails every request by design. The successor at
`/v0.1/servers` requires an `X-API-Key`. Verified 2026-09-19. The 21,869 figure
above therefore comes from the rendered directory page, not the API.

## 2. Glama: publishes a full methodology page

**It does, and it is the most detailed of the three.** Glama's FAQ points to it:

> "See our indexing methodology for the full technical description of how every
> server in the Glama registry is built, introspected, audited, and scored."

(https://glama.ai/mcp/faq, verified 2026-09-19)

The methodology page at https://glama.ai/mcp/methodology, verified 2026-09-19, is
structured around exactly the question the keynote says nobody answers. It
separates the population into two declared classes, "1. Open-source MCP servers"
and "2. Hosted MCP connectors", and describes ingestion for each.

On what the population is and where it comes from:

> "Glama's registry is not a passive directory. Every server – whether
> open-source or a hosted connector – passes through an automated analysis
> pipeline that builds, runs, introspects, audits, and scores it, and then repeats
> that process for as long as the server exists."

On sourcing and freshness:

> "For every listed server, Glama clones and continuously syncs the complete Git
> history from GitHub. The registry reflects the current state of the repository
> within minutes of a push."

And decisively, on the relationship to the other two counts, under a heading
literally named "3. Relationship to the official MCP Registry":

> "Glama operates as a superset of that registry. Glama ingests and re-publishes
> everything in the official registry, and layers its own sandbox-derived data on
> top."

That single sentence is a published explanation of why Glama's number is the
largest of the three. The keynote cannot claim Glama is silent about what it
counted when Glama has a numbered section explaining that it is a superset of the
registry plus hosted connectors.

Glama also labels the population in the page title of the directory itself:
"Open-Source MCP Servers – 89,255 in the Glama Registry"
(https://glama.ai/mcp/servers, verified 2026-09-19).

**What Glama does not publish.** Two real gaps remain, and they are the only
honest criticism available here:

- No stated policy on forks, mirrors, monorepo subdirectories, or abandoned
  repositories. Searched the methodology page and FAQ on 2026-09-19; neither word
  "fork" nor "duplicate" appears.
- No published breakdown of the 89,255 between open-source servers and hosted
  connectors, so the headline number mixes two populations the methodology itself
  takes care to separate.

A listing-criteria detail is also in tension with the headline number. Section 1.1
states: "Before a server is listed, the submitting maintainer authenticates
through GitHub OAuth." That describes an opt-in submission flow, while the FAQ
says "Glama indexes every MCP server in the ecosystem" and section 3 describes
bulk ingestion of the official registry. These cannot all be the operative rule
for 89,255 entries. The reconciliation is **UNVERIFIED**; Glama does not state
which path most listings arrive by.

## 3. Official registry: documents the mechanism, publishes no headline count

Three separate questions, three different answers.

**Does it document that the listing paginates by name and version?** Partly, and
only by demonstration. The aggregator guide shows the cursor format in a worked
example, `"nextCursor": "com.example/my-server:1.0.0"`
(https://github.com/modelcontextprotocol/registry, `docs/modelcontextprotocol-io/registry-aggregators.mdx`,
verified 2026-09-19). The `name:version` shape is visible to anyone who reads the
example, and the live API returns exactly that form. But no page states in prose
that the default listing returns one record per version, so a consumer who counts
rows gets version records and is never told. That is a genuine documentation gap.

**Does it document a way to get a distinct-server count?** Yes, explicitly. From
`docs/reference/api/official-registry-api.md`, verified 2026-09-19:

> "`version` - Filter by version (currently supports `latest` for latest versions
> only)"

and the worked example on the same page:

> "Example: `GET /v0.1/servers?search=filesystem&updated_since=2025-08-01T00:00:00Z&version=latest`"

The same parameter is in the published OpenAPI spec at
`https://registry.modelcontextprotocol.io/openapi.yaml`, verified 2026-09-19:
"Filter by version ('latest' for latest version, or an exact version like
'1.2.3')". Measured today, `version=latest` returns records and distinct names at
exactly 1:1 across all 33,366 rows, so it does deduplicate as documented.

**Does it publish a distinct-server count anywhere?** No. Checked on 2026-09-19:
the landing page at `https://registry.modelcontextprotocol.io/` shows no total;
there is no `/v0.1/stats` or `/v0.1/servers/count` endpoint (both 404); and the
Prometheus endpoint at `/metrics` exposes HTTP request and error counters but no
gauge for registry size. A consumer who wants the number must page the entire API
themselves, which is 334 requests at the maximum page size of 100.

This is the one part of the keynote's charge that stands, and it is narrower than
the line claims. The registry documents the filter that produces the right number
and then never publishes the number.

Worth noting for tone: the registry is labelled preview. From the aggregator doc,
verified 2026-09-19: "The MCP Registry is currently in preview. Breaking changes
or data resets may occur before general availability." Criticising a
preview-labelled service for not publishing a headline statistic will land badly
with its maintainers.

## The stronger finding, which the counting argument was obscuring

Measured to exhaustion on 2026-09-19, the registry's 33,366 distinct servers are
heavily concentrated in a few publishers:

| Publisher namespace | Distinct servers |
|---|---|
| io.github.sadri-dridi | 2,341 |
| io.github.pipeworx-io | 1,589 |
| io.github.mcp-dir | 1,113 |
| io.github.Evozim | 375 |
| io.github.CSOAI-ORG | 354 |

Three accounts account for 5,043 servers, 15.1% of the entire registry. Version
records concentrate the same way: `io.github.brilliantdirectories/brilliant-directories-mcp`
alone carries 1,177 version records and `ai.bowmark/bowmark` carries 874, out of
108,042 total.

The distribution is the point. The **median** server has exactly 1 version, and
21,013 of 33,367 servers (63%) have exactly one. The mean of 3.24 versions per
server is produced almost entirely by a handful of extreme republishers.

This is a governance observation rather than a counting one, and it is both
better evidenced and harder to rebut than the methodology charge. It is also
directly on the keynote's actual subject.

## Verdict

**Unfair, and the line has to change.** Of the three, two publish exactly the
definition the keynote says is missing: PulseMCP's statistics page states that it
counts "meaningful MCP servers" and that it intentionally omits "low quality
implementations that we don't think would ever be used by someone besides the
creator", and goes on to attribute the gap with other aggregators to precisely
that decision; Glama publishes a full indexing methodology whose section 3 states
that "Glama operates as a superset of that registry" and re-publishes everything
in it alongside hosted connectors. Both counts are explained, by their publishers,
in public, before the talk asks the question. The official registry is the only
one that publishes no headline distinct-server figure, and even it documents the
`version=latest` filter that yields one. The quantitative half of the line fails
too: measured consistently on 2026-09-19 the three counts are 33,366, 21,869 and
89,255, a spread of about 4x rather than an order of magnitude, and the apparent
10x gap came from comparing the registry's version records against other people's
server counts. Delivered as written, the line invites a maintainer to open
pulsemcp.com/statistics from the audience and read the rebuttal aloud.

### Proposed replacement

Keep the observation, drop the accusation, and let the registry's own numbers do
the work:

> "Three published counts of the same ecosystem. The official registry answers
> 33,366 servers, or 108,042, depending on whether you ask for distinct names or
> every version record. PulseMCP says 21,869 and tells you it leaves out the
> low-quality ones. Glama says 89,255 and tells you it is a superset of the
> registry plus hosted connectors. All three published what they counted. I still
> could not tell you how many MCP servers my organisation is allowed to run,
> because not one of those numbers is a statement about fitness for anything."

That version is defensible in the room. It cites each source correctly, credits
the two that documented their methods, and lands the governance point the talk
actually needs, which is that an inventory count is not an admissions decision.

If a shorter line is wanted for the opening beat:

> "The official registry will tell you 33,366 or 108,042 for the same question,
> depending on whether you count servers or versions. Neither number tells you
> which of them you should let into your estate."

### If the concentration finding is used instead

> "Fifteen percent of the official registry comes from three GitHub accounts. The
> median server in it has exactly one published version. An inventory that shape
> is not a catalogue you shop from."

All three figures verified by full pagination of the registry API on 2026-09-19
and reproducible with the loop in the Reproduction section below.

## Reproduction

The counting script was working material rather than a tracked artifact. The whole method is the loop
below and can be pasted fresh:

```bash
# distinct servers: add &version=latest. version records: omit it.
BASE="https://registry.modelcontextprotocol.io/v0.1/servers?limit=100&version=latest"
cursor=""; : > names.txt
while :; do
  url="$BASE"; [ -n "$cursor" ] && url="${BASE}&cursor=$(printf '%s' "$cursor" | jq -sRr @uri)"
  body=$(curl -sS --max-time 40 "$url") || break
  printf '%s' "$body" | jq -r '.servers[].server.name' >> names.txt
  cursor=$(printf '%s' "$body" | jq -r '.metadata.nextCursor // empty')
  [ -z "$cursor" ] && break
done
wc -l names.txt; sort -u names.txt | wc -l
```

Measured 2026-09-19: with `version=latest`, 334 pages, 33,366 records and 33,366
distinct names. Without it, 1,081 pages, 108,042 records and 33,367 distinct
names. Each full run takes several minutes. Treat the cursor as opaque, per the
registry's own guidance: "Always treat cursors as opaque strings. Never manually
construct or modify cursor values."

## Status of every claim in this document

Verified against a live source on 2026-09-19: all registry counts, the
distribution figures, the PulseMCP and Glama live totals, and every quotation.

UNVERIFIED: the 2026-09-17 PulseMCP figure of 21,880 and the 2026-09-17 Glama
figure of 88,809, neither of which can be checked retroactively; and the
reconciliation between Glama's maintainer-submission rule and its 89,255 total.

Superseded: the 2026-09-17 registry figure of "more than 28,000 version records",
which today's full pagination shows to be a truncated run rather than a total.
