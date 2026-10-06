---
title: "Performance of MCP at enterprise scale: the latency budget, the ceiling, and what 2026-07-28 actually bought"
date: 2026-09-21
sources_verified_on: 2026-09-21
status: draft
---

<!-- ABOUTME: Performance pillar. Where wall-clock time goes on an MCP tool call, what a server and a gateway sustain, and what the stateless revision measurably changed. -->
<!-- ABOUTME: Token economics are deliberately absent; they live in bestpractice/mcp-token-economics-and-tool-consolidation.md. This file is about seconds, not tokens. -->

## Sourcing labels

Five labels per the repo convention, plus one addition. `PREPRINT` marks arXiv
work that has not been refereed. It is stronger than `PRACTITIONER` because the
method is written down, and weaker than `PEER-REVIEWED` because nobody checked
it. Two of the agent-side sources are in that category and collapsing them into
either neighboring label would misstate their weight.

| Label | Meaning |
|---|---|
| OFFICIAL | The MCP specification, the maintainers' blog, or an OpenTelemetry repository |
| VENDOR | A company writing about its own product |
| PEER-REVIEWED | Refereed publication |
| PREPRINT | arXiv, method stated, not refereed |
| PRACTITIONER | An independent party publishing a method and a result |
| SECONDHAND | A figure reported without its origin, or reported about someone else |

Every figure below is additionally marked **measured** or **claimed**. Where a
number is claimed by the party that benefits from it and measured by somebody
else, both appear, because the gap between them is a finding.

---

## Scope, and what this deliberately does not re-cover

| Already covered, referenced not repeated | Where |
|---|---|
| Token economics, tool-definition footprint, prompt cache invalidation, tool-count accuracy degradation | `bestpractice/mcp-token-economics-and-tool-consolidation.md` |
| The gateway comparison across 13 projects, and the 3.1 latency table this file supersedes | `bestpractice/mcp-gateway-and-registry-operations.md` |
| Failure modes, timeouts, SLI list, eval harness guidance | `ops/mcp-operations-at-scale-2026-09.md` |
| Statelessness as an architecture change, Kubernetes substrate, multi-tenancy | `scale/mcp-at-scale-architecture-2026-09.md` |
| OTel MCP span names, metric names, attribute requirement levels, transport deduction | `components/supporting-layers.md` 1.1 |
| CVEs, injection, supply chain | `security/mcp-security-failures-2026-09.md` |

Two things this file closes rather than references.

1. `bestpractice/mcp-gateway-and-registry-operations.md` 3.1 carries two vendor
   figures two orders of magnitude apart and says neither is independently
   reproduced. As of 2026-08-24 one of them is, by a third party, with a
   published method. Section 2.2 has the numbers. **One of the two cited figures
   no longer exists at its cited URL** (section 2.6).
2. `components/supporting-layers.md` 1.1 records the OTel MCP conventions
   accurately. It does not say that two of the four metrics measure a construct
   the current protocol deleted, nor that the histogram floor is coarser than
   every measured gateway overhead. Section 6 does.

---

## 1. The latency budget, end to end

### 1.1 The table

A tool call is six segments plus the inference passes around it. Nobody has
published a single instrumented trace with all of them, so this table is
assembled from separate sources and each row says who measured it and how.

| # | Segment | Published figure | Source and method | Label |
|---|---|---|---|---|
| 1 | Client dispatch: serialize JSON-RPC, build the three required headers | **No published figure** | nothing found | gap |
| 2 | Network, client to gateway | **14.1 ms** round trip to TrueFoundry's region; **~100 ms** to Cortx in `us-east-1`, both from one 8-vCPU box | AIMultiple, interleaved paired calls, 2026-08-17 and 2026-08-19 | PRACTITIONER, measured |
| 3a | Gateway, routing only | **840 µs** (Bifrost v1.6.10), **1,134 µs** (Docker MCP Gateway v0.43.3) added per call at concurrency 1 | AIMultiple, median gateway-routed call minus a matched direct call, 2026-08-13 | PRACTITIONER, measured |
| 3b | Gateway, inspecting bodies | **23,058 µs** (IBM ContextForge v1.0.7, detectors enforcing). Turning its four detectors on costs **3,198 µs, an 11.5% increase**. TrueFoundry's two guardrails take it from **55.5 ms to 172.1 ms**, roughly triple | same | PRACTITIONER, measured |
| 4 | Server processing | p95 **8.13 ms** (Quarkus) to **342.41 ms** (Python) across 15 implementations on identical I/O-bound work | TM Dev Lab, k6, 50 VUs, 5 minutes, 2 vCPU per server | PRACTITIONER, measured |
| 5 | Downstream system | folded into row 4 above (Redis plus an HTTP API). A separate cited trace puts an external API call at **50 ms** | TM Dev Lab; bex.co table below | mixed |
| 6 | Model round trips around the call | "hundreds of milliseconds to seconds" per round trip avoided; code execution "eliminates 19+ inference passes" | Anthropic, advanced tool use. Already recorded in `bestpractice/` 3.3 | OFFICIAL, unquantified |

**Read rows 3a and 3b together. That is the architecture decision.** A gateway
that routes on `Mcp-Method` and `Mcp-Name` costs under two milliseconds. A
gateway that opens the body and inspects it costs between 11.5% more and roughly
three times more, depending on what the detector does. Pattern matching for
credentials is the cheap end. Prompt-injection detection is the expensive end,
and it is also the only control in the measured set that caught anything
injection-shaped (`security/` covers why that matters).

The shape recorded in `bestpractice/` 3.1 survives. The magnitudes are now
measured rather than asserted, and the inspecting figure is **lower** than the
vendor claim it replaces: ContextForge's 23 ms and TrueFoundry's 117 ms
increment sit below the 100 to 250 ms that was circulating, except at the top of
TrueFoundry's range.

### 1.2 The one end-to-end budget in circulation, and its provenance problem

The most-quoted MCP latency budget is a five-row p95 table totaling 180 ms:

| Hop | Latency |
|---|---|
| Client to gateway | 5 ms |
| Authentication | 10 ms |
| Connection-manager routing | 25 ms |
| MCP server processing | 90 ms |
| External API call | 50 ms |
| **Total (p95)** | **180 ms** |

Source: Dora Noda, bex.co, 2026-07-30,
<https://bex.co/blog/2026/07/30/mcp-server-concurrency-production-readiness>
(verified 2026-09-21). **[SECONDHAND]**

The post describes it as "a Docker-based MCP deployment on an AWS EC2
`c6i.4xlarge`, measured end to end". **It does not name who measured it.** The
page has a "Sources" heading in its table of contents and no source list under
it as rendered on 2026-09-21. The numbers are plausible and consistent with the
measured rows above, and the origin is not recoverable from the page.

Use the table as an illustration of shape. Do not attribute it, and do not put
180 ms on a slide as a measured p95. The honest version is section 1.1.

The post's actual argument is sound and worth carrying: the widely repeated
claim that "MCP servers handle over 10,000 concurrent connections with sub-50ms
response times" conflates held-open idle connections with concurrent work, and
the sub-50 ms figure covers only the routing segment. Both halves are true and
neither describes what an agent waits for.

### 1.3 A published proxy comparison whose units do not survive reading

Tetrate published an MCP proxy benchmark on 2025-12-08 comparing no proxy,
Envoy AI Gateway and Agent Gateway on an M1 MacBook Pro, calling an echo tool.
Source: <https://tetrate.io/blog/envoy-ai-gateway-mcp-performance> (verified
2026-09-21). **[VENDOR, measured]**

The post states that "both implementations add ~160ms-390ms of latency over the
direct calls", then two sentences later that the difference between the two is
"~0.2ms" and that "sub-millisecond latency in MCP tool calls becomes negligible".
Those cannot both be true. The baseline it reports is "~80µs per operation".
The surrounding text only makes sense if the 160 to 390 figures are
microseconds.

**Do not cite either number.** The finding to carry is that a published
vendor-versus-vendor MCP proxy comparison has an internal inconsistency of three
orders of magnitude and has stood uncorrected for nine months.

Two further reasons it does not transfer to the current protocol: the whole
design under test is Envoy AI Gateway's encrypted aggregated `Mcp-Session-Id`,
which exists because MCP was stateful in December 2025, and the overhead it
measures is a key-derivation function, not routing. The Envoy AI Gateway post it
builds on reports that default settings (about 100,000 KDF iterations) add tens
of milliseconds per new session while roughly 100 iterations drops that to 1 to
2 ms. The 2026-07-28 revision deletes the session that was being encrypted.

### 1.4 The segment nobody instruments

Row 1 of the table is empty and row 6 is unquantified. Between them they are
probably the largest terms in a real agent turn. Anthropic's own framing is that
a round trip through the model costs "hundreds of milliseconds to seconds",
which is two to three orders of magnitude more than the entire gateway and
server path measured above.

That ratio is worth carrying into any optimization argument. Tuning a gateway
from 1 ms to 0.5 ms moves a term that is already three orders of magnitude below
the inference pass sitting next to it in the same turn.

---

## 2. Throughput and concurrency

### 2.1 What one MCP server sustains

The only cross-implementation MCP server benchmark found with a published
method. Thiago Mendes, TM Dev Lab, published 2026-02-28, three runs over
2026-02-27 and 2026-02-28, 39.9 million total requests, 0% errors.
Source: <https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html>
(verified 2026-09-21). **[PRACTITIONER, measured]**

Setup: Azure VM, 8 vCPU, 32 GB, Ubuntu 24.04. Each server capped at 2.0 vCPU and
2 GB. Streamable HTTP, stateless request-response. Three tools doing real Redis
and HTTP work in parallel. k6 at 50 concurrent virtual users, 5 minutes
sustained, 60-second warmup discarded.

| Implementation | RPS | Avg latency | p95 | RAM |
|---|---|---|---|---|
| Rust | 4,845 | 5.09 ms | 10.99 ms | 10.9 MB |
| Quarkus | 4,739 | 4.04 ms | 8.13 ms | 194.5 MB |
| Go | 3,616 | 6.87 ms | 17.62 ms | 23.9 MB |
| Java (Spring MVC) | 3,540 | 6.13 ms | 13.71 ms | 368.1 MB |
| Java virtual threads | 3,482 | 9.03 ms | 18.43 ms | 349.7 MB |
| Quarkus native | 3,449 | 10.36 ms | 15.92 ms | 36.1 MB |
| Micronaut | 3,382 | 9.75 ms | 17.00 ms | 216.3 MB |
| Java WebFlux | 3,032 | 8.89 ms | 27.48 ms | 484.6 MB |
| Bun | 876 | 48.46 ms | 98.50 ms | 540.8 MB |
| Node.js | 423 | 123.50 ms | 200.07 ms | 389.2 MB |
| Python | 259 | 251.62 ms | 342.41 ms | 258.6 MB |

Four GraalVM native builds land between 2,161 and 2,447 RPS and are omitted for
space; native compilation cost throughput and p95 in every pairing here.

**The spread is 18.7x between Rust and Python on identical work.** The author is
explicit that this is one workload at one concurrency level and is not a ranking
of languages. It is still the number to size against, because the reference MCP
server most enterprises start from is Python, and Python is the bottom row.

Two caveats that matter for an enterprise reading this as a capacity model.
Several SDKs under test were pre-release in February 2026. And 2 vCPU per server
is a small allocation; the ordering is more durable than the absolute values.

### 2.2 What one gateway sustains

Independent measurement and vendor claim disagree by about two orders of
magnitude, and the disagreement is legible rather than mysterious.

| Gateway | Figure | Source | Label |
|---|---|---|---|
| Bifrost | **11 µs** of gateway overhead at **5,000 RPS**, 100% success, "sub-3ms latency on MCP operations under production load" | Maxim AI, <https://www.getmaxim.ai/articles/fastest-enterprise-mcp-gateway-in-2026/>, published 2026-04-08, modified 2026-07-03 | VENDOR, **claimed**, no method, no hardware, no link to a benchmark |
| Bifrost | **840 µs** added per call at concurrency 1 | AIMultiple, 2026-08-13 | PRACTITIONER, measured |
| TrueFoundry | **7 ms** overhead at 200 to 220 RPS with tracing off, **8 ms** with full tracing; **7 ms and 12 ms** at 350 to 370 RPS, on a single pod with 1 vCPU and 1 GB. "Beyond that point, adding CPU or replicas scales the gateway to tens of thousands of requests per second" | TrueFoundry, <https://www.truefoundry.com/blog/best-mcp-gateway-for-production-ai-systems>, published 2026-07-21 | VENDOR, **claimed**, self-published, method partially stated |
| TrueFoundry hosted | **55.5 ms** added, of which **14.1 ms** is the round trip | AIMultiple, 2026-08-17 | PRACTITIONER, measured over WAN |
| Envoy AI Gateway | "roughly 1 to 3 ms of reported overhead" | TrueFoundry, same post, describing a competitor | SECONDHAND |

AIMultiple's own reading of the Bifrost gap is the careful one and worth
reproducing rather than rewording: "Bifrost's own sub-100-microsecond figure
is a throughput claim at high concurrency. At concurrency 1 it adds roughly ten
times that, and the claim should be tested as a throughput number rather than
treated as refuted here."

That is the general rule for this whole section. A vendor's gateway number is
almost always amortized overhead at saturation. An independent number is almost
always added latency for one call. They are different quantities and both are
useful.

### 2.3 The non-MCP proxy numbers that get quoted as MCP numbers

agentgateway publishes "approximately 500k QPS with 512 connections" and "less
than 0.2 ms P99 latency at 30k QPS with 512 concurrent connections".
Source: <https://agentgateway.dev/blog/2026-06-04-designing-agentgateway-unified-gateway/>
(verified 2026-09-21). **[VENDOR, claimed]**

A separate agentgateway run against LiteLLM, dated 2026-06-26, run ID
`20260626-120716`, fortio, 32 connections, 1 KB payloads, 3 seconds, mock
backend:

| Metric | agentgateway | LiteLLM |
|---|---|---|
| Throughput | 36,933.62 QPS | 3,198.48 QPS |
| p50 | 0.831 ms | 7.076 ms |
| p90 | 1.533 ms | 17.986 ms |
| p99 | 1.970 ms | 32.192 ms |
| Avg memory | 22.38 MiB | 11.81 GiB |

Source: <https://agentgateway.dev/blog/2026-06-26-benchmarking-agentgateway-vs-litellm/>
(verified 2026-09-21). **[VENDOR, measured, self-run]**

**Neither of these is an MCP benchmark.** The 500k QPS figure is general proxy
traffic, and the design post contains no MCP-specific measurement at all. The
LiteLLM comparison proxies LLM-shaped requests to a mock. They are legitimate
numbers about a proxy and they are quoted, including by the gateway comparisons
this repo already catalogs, as if they described MCP tool-call throughput.
They do not.

### 2.4 Where the concurrency ceiling actually is

Sizing should be done in concurrent tool calls. A connection count answers a
different question and is the number vendors tend to publish.

- **Cloudflare**: its Code Mode MCP Server "has scaled up to thousands of
  requests per second and served billions of tool calls".
  <https://blog.cloudflare.com/mcp-v2/>, 2026-08-06, Matt Carey.
  **[VENDOR, claimed]**, no method.
- **Pinterest**: **66,000 invocations per month** across **844 active users**,
  saving roughly 7,000 hours per month, reported by InfoQ on 2026-04-01 from
  Pinterest's engineering blog.
  <https://www.infoq.com/news/2026/04/pinterest-mcp-ecosystem/>
  **[SECONDHAND]**, and the period InfoQ attaches to the figures reads "as of
  January 2025", which is fifteen months before publication and is either a typo
  for January 2026 or a genuinely stale measurement. Mark the date UNVERIFIED.
- **Modal, 64 concurrent tool calls per container with ~400 ms cold starts**:
  this figure circulates via bex.co. **Checked against Modal's own
  documentation on 2026-09-21: `modal.concurrent` documents no default for
  `max_inputs` or `target_inputs`, the Servers guide documents no default
  `target_concurrency`, and the number 64 appears in neither.** The figure traces
  to a secondary blog, not to Modal. **[UNVERIFIED]**, do not cite.

The Pinterest number is the one worth internalizing, and not because it is
large. **66,000 calls a month is about 0.025 calls per second on average.** A
flagship, widely cited, genuinely production MCP deployment at a company with
844 active internal users runs about four orders of magnitude below what a
single Python MCP server sustains in the benchmark above (0.025 calls per second
against 259). Whatever the enterprise
problem with MCP is, at that scale it is not throughput.

### 2.5 The interference effect nobody budgets for

AIMultiple measured something that does not appear in any vendor comparison:
"While Docker or ContextForge was serving, calls made straight to the backend ran
about 0.9 milliseconds slower, between 858 and 973 microseconds across the four
timing tasks."

Co-located gateway and backend, so this does not apply to a gateway on its own
host, and AIMultiple reports it separately for that reason. It is worth knowing
because the sidecar deployment mode that several gateways recommend puts them on
the same host by design.

### 2.6 A figure this repo cites that is no longer retrievable

`bestpractice/mcp-gateway-and-registry-operations.md` 3.1 and
`scale/mcp-at-scale-architecture-2026-09.md` 2.1 both cite MintMCP for
"compliance scanning and deep inspection add 100 to 250 ms per request", at
<https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp>.

**Fetched 2026-09-21. HTTP 200, 22,938 characters of extracted text. The string
"250" does not appear. No latency figure of any kind appears.** The page
(published 2026-04-13) discusses deployment timeframes, a 60 to 80% reduction in
authentication setup time, and a 3 to 4 month payback period. It carries no
per-request performance number.

Either the page changed after the earlier research pass or the figure came from
a different MintMCP page. Retire the citation. The measured replacements in
section 1.1 say the same thing with a method attached.

---

## 3. What the 2026-07-28 revision did to performance

### 3.1 Three mechanisms, all real, none measured by their authors

| Mechanism | What it enables | Who states it |
|---|---|---|
| No sessions, no `Mcp-Session-Id` | Any request routes to any instance. Plain round-robin, no sticky routing, no shared session store, no failover that drops a live conversation | MCP maintainers; AWS; Google; Cloudflare |
| `Mcp-Method` and `Mcp-Name` REQUIRED on every POST | Intermediaries "route, throttle, and meter at the HTTP layer alone" without buffering or parsing the body | MCP maintainers; AWS AgentCore |
| `ttlMs` and `cacheScope` REQUIRED on list and read results | Clients and shared proxies know how long a `tools/list` is fresh and whether it can be shared | MCP maintainers; Cloudflare |
| No `initialize` handshake | "A client's first message can be the actual tool call", removing one round trip | AWS, already recorded in `bestpractice/` 3.1 |

Sources, all verified 2026-09-21:
<https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/>
(**[OFFICIAL]**; its structured data dates it 2026-05-21 while the page header
shows the revision name July 28, 2026),
<https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/>
(2026-07-28, Sean Eichenberger and Luca Chang, **[VENDOR]**),
<https://developers.googleblog.com/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/>
(2026-08-05, Kurtis Van Gent and Alan Blount, **[VENDOR]**),
<https://blog.cloudflare.com/mcp-v2/> (2026-08-06, **[VENDOR]**).

**Every one of those posts asserts the performance benefit and none of them
measures it.** That is uniform across the maintainers, AWS, Google and
Cloudflare. Searched specifically for a before-and-after migration benchmark on
2026-09-21 and found none.

### 3.2 The closest thing to a measured effect

GitHub shipped the migration and described what it removed:

> "Removed Redis sessions: Database writes on `initialize` are gone, and database
> reads are gone from every call, which makes things snappier without users
> losing anything."

Source: <https://github.blog/changelog/2026-07-23-github-mcp-server-supports-the-next-mcp-specification/>,
2026-07-23. **[VENDOR, claimed]**.

"Snappier" is the entire quantification. A Redis read removed from every call is
a real saving and its size is not stated.

Google's version names the same mechanism for the same server: GitHub
"completely removed Redis session storage, eliminating database writes and reads
on every single call".

Two further asserted effects with no numbers attached. Google states servers can
now "spin down to zero when idle, drastically reducing costs" on Cloud Run and
Cloud Functions. Cloudflare states MCP servers "can now run in just a Worker, no
stateful infrastructure needed", and that it eliminated the `McpAgent` primitive
and the Durable Object that basic MCP hosting previously required. Cloudflare
deleting a stateful primitive from its own product is stronger evidence than a
paragraph of prose, because the change is visible in the product surface.

AWS's honest counterweight is already in `ops/` 2.6 and is the one number in
this area: "A two-node Amazon ElastiCache (`cache.t4g.micro`) session store is
about $23/month." The saving was never the session store bill.

### 3.3 Header routing is being implemented, and the effect size is still unpublished

The argument for header routing, stated well and without numbers, is Tigera's,
2026-08-06, Alister Baroi,
<https://www.tigera.io/blog/the-new-mcp-headers-are-a-gift-to-gateways/>
(verified 2026-09-21) **[VENDOR]**: before the headers, "any middlebox that
wanted to treat a `tools/list` differently from a `tools/call` had to buffer the
request, parse the JSON-RPC envelope, and make its decision from the body,
putting body parsing on the hot path for every request". **No measured figure is
given.**

The mechanism is now landing in code. Kuadrant's `mcp-gateway` PR #1500,
"perf(router): skip prefix-free 2026 request bodies", opened 2026-09-12 and
**still open as of 2026-09-21**, "routes eligible MCP 2026-07-28 requests during
the request-header phase and overrides Envoy's per-request processing mode so
request bodies are not buffered when no prefix rewriting or guardrail inspection
is required". <https://github.com/Kuadrant/mcp-gateway/pull/1500> **[OFFICIAL,
project source]**. The PR carries unit tests and a race check. It carries no
benchmark.

Note the condition in the PR's own wording: the fast path applies only "when no
prefix rewriting or guardrail inspection is required". Header routing does not
remove the inspection tax, it removes the tax on traffic you were not going to
inspect. Sections 1.1 and 5 are about the traffic you were.

### 3.4 The counter-claim, and what it costs per hour

`ops/` 2.5 already records Artemii Amelin's argument and the quotable line: "A
protocol that is cheap per request and expensive per hour benchmarks very well
and behaves differently in production." That claim is not re-argued here. What
this file adds is the mechanism by which the hourly bill accrues, read from the
spec rather than from commentary.

**MRTR turns one request into N independent full requests.** Source:
<https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr>
(verified 2026-09-21) **[OFFICIAL]**.

- Elicitation, sampling and `roots/list` are no longer server-initiated. The
  server returns `InputRequiredResult` and the client **retries the original
  request** with `inputResponses`. "The JSON-RPC `id` **MUST** be different
  between the initial request and the retry, as they are independent requests."
- The spec is explicit that "the requests in each step are completely
  independent: the server processing the retry does not need any information
  beyond what is directly present in the retry request." Every retry therefore
  re-sends the full original parameters plus the `_meta` block plus the state
  blob.
- Server-side context survives only inside `requestState`, "an opaque string
  meaningful only to the server", which the client echoes back verbatim. Any
  work done before the interruption is either redone or serialized into that
  blob and carried over the wire on every leg.
- `requestState` "**MUST** be treated as attacker-controlled input" and, where it
  influences authorization or business logic, servers "**MUST** protect its
  integrity (e.g. HMAC or AEAD) and **MUST** reject state that fails
  verification". Servers **SHOULD** additionally verify the authenticated
  principal, a short expiry, and a digest of the originating request's salient
  parameters. That is a cryptographic verify plus three checks on every leg.
- **There is no cap on the number of round trips.** Servers "**MAY** choose to
  return an `InputRequiredResult` on multiple attempts at the same request".
- MRTR results are explicitly not cacheable (section 4).

So the per-request cost fell and the per-interaction cost, for any tool that
needs user input, rose from one request plus a callback to N requests, each
carrying the full payload and each paying an integrity check. Combined with the
removal of stream resumability already recorded in `spec/` 4.5, the pattern is
consistent: work that used to be held on a connection is now re-sent.

---

## 4. Caching as a performance lever

Prompt cache economics are in `bestpractice/` section 2 and are not repeated.
This section is about what a shared intermediary can cache, what the hit rate
is, and what credential filtering does to both.

### 4.1 What the spec actually lets a shared cache hold

Source: <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching>
(verified 2026-09-21) **[OFFICIAL]**. `bestpractice/` 3.2 covers the two scope
values and the cross-tenant leak. These are the parts it does not carry.

**Six cacheable operations**, on `resultType: "complete"` results only:
`server/discover`, `tools/list`, `prompts/list`, `resources/list`,
`resources/templates/list`, `resources/read`.

**The cache key** is "the request method together with the request parameters
that affect the result". Clients **MUST NOT** serve a cached response for a
request whose method or parameters differ.

**MRTR retries are uncacheable by rule.** "Results produced by retrying a request
through the multi round-trip requests mechanism, that is, requests carrying
`inputResponses` or `requestState`, **MUST NOT** be cached, as they depend on
inputs that are not part of the cache key."

**TTL is a freshness hint, not a polling interval.** "Clients **SHOULD NOT**
treat TTL as a polling interval that triggers automatic background refetches."
Implementations that poll anyway "**MUST** apply jitter and backoff". This is the
line that prevents a fleet of agents from synchronizing a thundering herd against
`tools/list` every `ttlMs`.

**Stale-on-error is permitted.** "Clients **MAY** serve stale responses if errors
occur during re-fetching." Free availability, and worth turning on.

**Pagination is per-page.** Each page carries its own `ttlMs` and its own
freshness clock, servers **MAY** return different TTLs per page, there is no
cross-page consistency guarantee, and a client needing a consistent snapshot
**SHOULD** re-fetch from the beginning without a cursor. An invalid cursor means
discarding every cached page. A large tool catalog paginated into ten pages is
ten independent cache entries with ten independent expiries and no guarantee they
describe the same catalog.

### 4.2 The credential-filtered tool list defeats shared caching, by design

This is the interaction the brief asks about, and the spec answers it directly.
On choosing a scope:

> `"private"` is appropriate for `resources/read` results that depend on the
> authenticated user, **or for filtered list results that vary per user**.

And the security note:

> Servers **MUST** be aware that responses with a `"public"` `cacheScope` may be
> shared between callers even if the Result is coming from an authenticated
> endpoint.

Put together: the moment a gateway filters `tools/list` by the caller's
entitlements, which is the central thing an enterprise MCP gateway exists to do,
the result is per-user and must be marked `private`. A shared intermediary can
then cache it only within one authorization context. **The two headline
enterprise features, per-user tool filtering and shared-proxy caching, are
mutually exclusive on the same list.**

The workaround available is to cache the unfiltered upstream `tools/list` as
`public` inside the gateway and apply the filter per request on the way out. That
preserves the upstream round-trip saving and gives up nothing, and it puts the
filter back on the hot path, which is the cost row 3b in section 1.1 measures.
Nobody has published that this is what any gateway does.

### 4.3 The SDK behavior that determines whether any of this fires

The MCP Python SDK ships a client-side response cache on the `Client` class, on
by default, with an `InMemoryResponseCacheStore` and a pluggable interface for a
Redis-backed one. Source: <https://py.sdk.modelcontextprotocol.io/client/caching/>
(verified 2026-09-21) **[OFFICIAL]**.

Two details decide the hit rate:

- **The default is no caching.** Results carrying no hint get
  `CacheConfig.default_ttl_ms`, which defaults to `0`. A server that has not
  been updated to emit a positive `ttlMs` gets zero benefit, silently. Every
  cacheable result is `ttlMs: 0, cacheScope: "private"` out of the box, which is
  "always safe and always conformant" and also always a cache miss.
- **Sharing `public` entries across partitions is opt-in** via `share_public=True`,
  and the partition "must derive from a verified credential, such as a validated
  token's subject. Never derive it from request-supplied data."

So the measured benefit of the caching feature depends on a server author setting
a non-zero TTL, a client operator enabling public sharing, and a tool list that is
not per-user filtered. All three have to hold.

### 4.4 Nobody has published an MCP cache hit rate

Searched 2026-09-21. **No published hit-rate measurement for `tools/list`,
`server/discover` or `resources/read` caching exists, from any vendor, gateway
project or practitioner.** The feature is two months old at the time of writing
and the instrumentation to measure it (section 6) does not name a cache metric.

The nearest published hit-rate dataset measures a different thing entirely and is
worth naming so it is not mistaken for this one. Requesty, April 2026, defining
hit rate as `cached_tokens / input_tokens` across its inference gateway traffic:
Anthropic direct 77.50%, Bedrock 56.90%, DeepSeek 48.30%, Azure 41.00%, OpenAI
36.40%, Vertex (Claude) 23.50%, Vertex (Gemini) 9.60%, Mistral 4.10%.
<https://www.requesty.ai/data/cache-hit-rate-by-provider-april-2026> (verified
2026-09-21) **[VENDOR, measured]**. That is LLM prompt caching at the inference
hop. It says nothing about MCP result caching.

One mechanism links the two and is worth recording because it is new. Cloudflare
states that `ttlMs` and `cacheScope` let "clients reuse them while keeping
upstream prompt caches stable across reconnects". A `tools/list` served from
cache is byte-identical, so the tool-definition prefix of the model's context does
not change, so the prompt cache prefix survives a reconnect. The MCP cache
protects the prompt cache. Effect size unpublished.

---

## 5. Agent-side performance, in wall-clock time

Token effects are in `bestpractice/` section 4. This section reports only what
moved the clock.

### 5.1 The one properly measured wall-clock result: fewer tools is faster

GitHub, 2025-11-19, online A/B test in VS Code, reducing the default built-in
toolset from 40 tools to 13 with the remainder grouped into four expandable
virtual categories.
Source: <https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/>
(verified 2026-09-21) **[VENDOR, measured]**.

Verbatim:

> "users with the shrunken toolset experience an average decrease of 190
> milliseconds in TTFT (Time To First Token), and an average decrease of 400
> milliseconds in TTFT (Time to Final Token, or time to complete model
> response)."

and

> "In online A/B testing, it reduces response latency by an average of 400
> milliseconds."

**The post uses the acronym TTFT for two different quantities in one sentence.**
Quote it exactly or not at all; a paraphrase that says "400 ms off time to first
token" is wrong and is already circulating.

Two further figures from the same post, both measured:

- Offline: a 2 to 5 percentage point **decrease** in resolution rate on
  SWE-Lancer and SWEbench-Verified when the agent had the full built-in toolset,
  with GPT-5 and Sonnet 4.5.
- Online: "only 19% of Stable tool calls were successfully pre-expanded using the
  old method, whereas 72% of Insiders tool calls were pre-expanded thanks to the
  embedding-based matching."

This is the strongest wall-clock evidence in the file, because it is an A/B test
on production traffic rather than a harness. Two mechanisms contribute: fewer
tool-definition tokens to prefill, and fewer exploratory tool-group lookups, each
of which is a round trip that "adds latency and overhead" in GitHub's own words.
The post does not separate the two contributions.

### 5.2 Progressive discovery costs a retrieval hop, and the hop is cheap

Mudunuri, Wan, Qin and Manoharan, "Semantic Tool Discovery for Large Language
Models: A Vector-Based Approach to MCP Tool Selection", arXiv:2603.20313,
submitted 2026-03-19. <https://arxiv.org/abs/2603.20313> **[PREPRINT]**.

140 queries against 121 tools from 5 MCP servers. Hit rate 97.1% at K=3, MRR
0.91, 99.6% reduction in tool-related token consumption. **Retrieval latency
87.1 ms at K=1, 90.2 ms at K=2, 87.8 ms at K=3**, described as sub-100 ms and
flat in K.

Read that against section 1.1: a semantic tool-selection hop costs roughly 100
times what a routing gateway costs and roughly a tenth of a one-second
inference pass.
It is a good trade in wall clock and it is not free, and the flatness in K means
the cost is the embedding pass rather than the search.

Sadani and Kumar, "Tool Attention Is All You Need", arXiv:2604.21816, submitted
2026-04-23 **[PREPRINT]**, reports a FAISS router at "sub-millisecond for N less
than or equal to 10,000 tools" with an encoder pass of "approximately 30 to 60 ms
on CPU (MiniLM-L6)" and under 10 ms on GPU. That decomposition matches: the
vector search is free, the embedding is the bill.

**The same paper's headline latency figures are projections and say so.** Its
p50 4.2 s to 2.0 s and p95 7.9 s to 4.3 s improvements are derived by combining
measured token counts (47.3k to 2.4k per turn) with published provider TTFT
curves, and the authors mark every projected quantity with a dagger. The token
reduction is measured. **The latency reduction is not.** Do not cite the 52%
figure as measured.

### 5.3 Code execution is cheaper in tokens and slower on the clock

The effect sizes for code execution are in `bestpractice/` 4.4 and `ops/` 4.3.
One number there is marked [SECONDHAND, the AIMultiple original was not read
directly]. It has now been read directly and can be upgraded.

Şevval Alper, AIMultiple, updated 2026-08-14.
<https://aimultiple.com/code-execution-with-mcp> (verified 2026-09-21)
**[PRACTITIONER, measured]**. Method: two tasks, 50 runs each per approach,
Bright Data MCP Server in Pro Mode, GPT-4.1, LangGraph ReAct agent, 63 tool
definitions, cache cleared and a fresh MCP connection per run, each query in its
own subprocess.

| Metric | Regular MCP | Code execution | Difference |
|---|---|---|---|
| Success rate | 100% | 100% | same |
| **Avg latency** | **9.66 s** | **10.37 s** | **+7%** |
| Avg input tokens | 15,417 | 3,310 | -78.5% |
| Avg output tokens | 87 | 192 | +120% |
| Total tokens | 775,197 | 175,081 | -77.4% |

**Code execution is 7% slower in wall clock while being 77% cheaper in tokens.**
Both directions are real and they point opposite ways. The reason is in the
output-token row: the model writes code, code is output tokens, and output
tokens are generated serially.

Set against Anthropic's own claim that code execution "eliminates 19+ inference
passes" at "hundreds of milliseconds to seconds" each, the two are not in
conflict. They describe different task shapes. A task with one tool call pays the
code-writing cost and saves no round trips. A task chaining twenty calls saves
nineteen round trips and pays the code-writing cost once. **The crossover point
is unpublished**, and it is the number an enterprise would actually need.

### 5.4 The agent-side segment with no published number at all

Tool-selection time inside the model, as distinct from retrieval time in front of
it, is not measured anywhere found. The accuracy degradation past roughly 30
tools is well established (`bestpractice/` 3.2). Whether a 100-tool context also
takes the model longer to decide, independent of the prefill cost of the extra
tokens, has not been isolated by anyone. GitHub's 190 ms is the closest proxy and
it confounds prefill, selection and exploratory calls.

---

## 6. Measurement: what to instrument, and where the conventions fall short

`components/supporting-layers.md` 1.1 has the span names, the four metrics, the
attribute requirement levels and the transport table, all read from the source.
Not repeated. Three performance-specific findings sit on top of it, all verified
2026-09-21 against `open-telemetry/semantic-conventions-genai`.

### 6.1 The histogram floor is coarser than every measured gateway overhead

Both operation-duration metrics specify `ExplicitBucketBoundaries` of
`[0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]` seconds.

**The lowest boundary is 10 ms.** Bifrost's measured 840 µs and Docker's 1,134 µs
both fall in the first bucket, as does ContextForge's 3,198 µs inspection
increment, as does the entire 8.13 ms p95 of the fastest server in section 2.1.
A conformant implementation using the recommended boundaries cannot distinguish a
gateway that adds 100 µs from one that adds 9 ms.

The boundaries are sensible for the metric's stated purpose, which is
agent-visible operation duration where the top bucket is 300 seconds. They are
unusable for the gateway-overhead question. Anyone wanting to answer that has to
override the advisory boundaries, and doing so takes the metric out of the
convention.

### 6.2 Two of the four metrics measure something the protocol deleted

`mcp.client.session.duration` and `mcp.server.session.duration` are both defined
as "the duration of the MCP session". `mcp.session.id` is a Recommended attribute
on both spans and its description links to
`modelcontextprotocol.io/specification/2025-06-18/basic/transports#session-management`.
The `mcp.method.name` enum still contains `initialize`,
`notifications/initialized`, `ping`, `logging/setLevel` and
`notifications/roots/list_changed`, all removed in 2026-07-28. Grepped the file
on 2026-09-21: `server/discover`, `subscriptions/listen`, `tasks/get` and
`tasks/update` appear **zero times**. The `mcp.protocol.version` example value is
`2025-06-18`.

The gap is known and tracked. Issue #437, "MCP: align
semantic conventions with protocol 2026-07-28 and expose peer server
implementation metadata", **open**, created 2026-08-05, last updated 2026-09-20.
<https://github.com/open-telemetry/semantic-conventions-genai/issues/437>
**[OFFICIAL]**. Its own audit of the current state matches the grep above.

### 6.3 How stale, precisely

| Fact | Value, checked 2026-09-21 via the GitHub API |
|---|---|
| Last commit touching `docs/gen-ai/mcp.md` | 2026-08-05, "Keep upstream doc links pinned to the version in `model/manifest.yaml` (#435)". A link-pinning change, not a content change |
| Releases in `semantic-conventions-genai` | **0** |
| Tags in `semantic-conventions-genai` | **0** |
| Stability of every MCP span, metric and attribute | Development |

`scale/` 7.2 already records that the repo has no releases and that pinning a
schema URL is awkward. The API check confirms it is still true seven weeks after
that note, and adds that the MCP document itself has had no substantive edit
since the alignment issue was filed.

### 6.4 The minimum set for answering "is MCP slow here"

`ops/` section 5 has the operational SLI list and it stands. These are the
additions that specifically attribute latency rather than detect failure.

1. **`mcp.client.operation.duration` minus `mcp.server.operation.duration`, per
   call.** The conventions define both, on the sender and the receiver. Their
   difference is everything between them: network, gateway, and queueing. Nobody
   documents taking the difference, and it is the only way to separate a slow
   server from a slow path without adding a third instrument.
2. **A gateway-local histogram with sub-millisecond boundaries**, because 6.1
   means the standard one cannot see the gateway.
3. **Inspection on and off, as a labeled dimension.** Section 1.1's whole point
   is that this is the dominant gateway term. If the guardrail state is not a
   label, the p99 moves when someone enables a detector and nothing says why.
4. **Round trips per completed task**, not calls per second. MRTR (3.4) and
   tool-group expansion (5.1) both multiply round trips invisibly to a
   per-request metric.
5. **Cache outcome on every cacheable operation**, as hit, miss, stale-served or
   uncacheable-by-scope. No OTel metric covers this and section 4.4 is why it
   matters: without it, nobody can tell whether the 2026-07-28 caching feature is
   doing anything.
6. **Protocol version distribution**, already in `scale/` 7.3 and free now that
   `MCP-Protocol-Version` is required on every POST.

Trace context propagation through `_meta` (`traceparent`, `tracestate`,
`baggage`, SEP-414) is what makes items 1 and 4 joinable across the agent,
gateway, server and downstream API. It is already recorded in `spec/` 5.9 and
`scale/` 7.1. Worth stating once more that it is the only protocol-level
performance affordance in the revision, and it is a MAY-when-present convention
rather than a requirement.

---

## 7. The honest ceiling

### 7.1 Where MCP is structurally slower than a direct API call

Four costs are inherent rather than implementation defects.

1. **A hop that a direct call does not have.** Section 1.1 row 3a, 840 µs to
   1,134 µs for routing alone, before any policy. Unavoidable if there is a
   gateway, and the gateway is the entire enterprise governance story.
2. **The model decides, so the decision is a serial LLM step.** A direct API call
   is dispatched by code that already knows which endpoint to hit. An MCP call is
   dispatched after an inference pass that costs "hundreds of milliseconds to
   seconds". This term dwarfs every other row in the budget and no protocol
   revision can remove it.
3. **Tool definitions are prefill on every turn they survive.** Covered as a
   token cost in `bestpractice/`. It is also a wall-clock cost, and GitHub's
   190 ms is the measured size of removing 27 tools' worth of it.
4. **Work that used to live on a connection is now re-sent.** MRTR (3.4) and the
   removal of stream resumability (`spec/` 4.5) both convert held state into
   repeated transmission. A dropped stream means the client re-issues from zero.

### 7.2 The circulating comparison figures do not agree with each other

Searched 2026-09-21 for a measured MCP-versus-direct-API latency comparison.
There is no credible one. What exists is a set of mutually incompatible numbers
in SEO-shaped comparison content, none with a method:

| Claim | Source |
|---|---|
| MCP adds "50-150ms of latency per call"; direct API "can hit 20-50ms" | Nylas CLI guide, Qasim Muhammad, updated 2026-06-09, presented as an estimate |
| MCP adds "300-800ms baseline latency" from "JSON-RPC protocol negotiation and session management" | circulating comparison content |
| Direct API is "5-15ms lower latency than MCP" | circulating comparison content |

The three differ by a factor of 50. The middle one attributes the overhead to
session management, which the current revision removed. **State plainly that no
methodologically sound MCP-versus-direct-API latency comparison has been
published, and do not quote any of these.**

One concrete claim in this space deserves specific handling because it is
striking and gets repeated. The Nylas guide states that a 500-item batch job
takes "~50 seconds" via direct API and "~25 minutes" via MCP, a 30x gap, and
attributes it to "a measured benchmark from Toolradar 2026". Toolradar is a
comparison blog, published 2026-03-24 and updated 2026-09-20; its latency content
as fetched on 2026-09-21 is illustrative arithmetic ("HTTP round-trip ~100-300ms",
"AI reads tool descriptions and decides which tool to call ~0.5-1s"), not a
measurement. **A Staff SRE's post cites an aggregator as a measured benchmark and
the aggregator is doing arithmetic.** Mark the 30x figure UNVERIFIED.

### 7.3 When the trade is worth it anyway

The defensible version, built only from figures verified above.

**MCP's overhead is negligible when a model is in the loop.** Gateway routing is
under 2 ms. Server processing on a competent runtime is under 20 ms at p95. One
inference pass is hundreds of milliseconds to seconds. The protocol and the
governance layer together are a rounding error against the thing they govern.
Tetrate's framing of this is correct even though its numbers are not usable:
"Large Language Model reasoning usually takes several seconds, so sub-millisecond
latency in MCP tool calls becomes negligible in real world use cases."

**MCP's overhead is the whole cost when no model is in the loop.** A batch job, a
scheduled reconciliation, a data pipeline moving 500 rows: every one of those
pays the per-call hop and the per-call inference and gets nothing for either,
because the endpoint was never in doubt. The 30x claim in 7.2 is unverified and
its direction is not in question.

**The inspection tax is a separate decision from the MCP decision.** Row 3b is
between 11.5% and roughly 200% on top of row 3a, and it is the only measured
configuration in AIMultiple's set that stopped an injected instruction. That is a
security purchase priced in milliseconds. Present it with the price attached.

**The population that actually needs throughput is small.** Section 2.4:
Pinterest's production fleet averages about 0.025 calls per second. The
capacity question for most enterprises is not requests per second, it is how
many concurrent tool calls one instance holds, which is where Modal's and
Supabase's cited ceilings sit in the tens to low hundreds. Both of those figures
are unverified (2.4). The unit is still the right one to size against.

---

## 8. Levers ranked by measured effect size

Ranked by the size of the wall-clock effect that somebody actually measured.
Anything with only a claimed effect is below the line.

| # | Lever | Measured wall-clock effect | Source quality | Cost |
|---|---|---|---|---|
| 1 | **Cut the tool count the model sees** | **-400 ms** response latency, **-190 ms** to first token, online A/B, 40 tools to 13 | VENDOR, measured on production traffic | Engineering work on grouping and routing. Also improves accuracy by 2 to 5 points |
| 2 | **Do not inspect bodies you do not need to inspect** | Avoids **+11.5%** (ContextForge) to **+210%** (TrueFoundry, 55.5 ms to 172.1 ms) | PRACTITIONER, measured, one box | Gives up injection detection on the traffic you skip |
| 3 | **Choose the server runtime deliberately** | **18.7x** RPS spread and **42x** p95 spread on identical I/O-bound work (Python 342.41 ms p95, Quarkus 8.13 ms) | PRACTITIONER, measured, 39.9M requests | A rewrite. Only pays where throughput is the constraint, which section 2.4 says is rare |
| 4 | **Put the gateway near the client, or near the server, but do not cross a region** | Cortx's 211 ms is **~200 ms of network**; TrueFoundry's 55.5 ms includes 14.1 ms | PRACTITIONER, measured | Deployment topology, no code |
| 5 | **Semantic tool retrieval in front of the model** | Costs **~90 ms** flat in K, buys the section-1 token and selection effects | PREPRINT | An embedding index to build and keep fresh |
| 6 | **Code execution instead of direct tool calls** | **+7% latency** (9.66 s to 10.37 s) and **-77% tokens** | PRACTITIONER, measured, 100 runs | A sandbox. Slower unless the task chains many calls; crossover unpublished |

Below the line, mechanisms with no measured effect size:

| Lever | Claimed effect | Who claims it |
|---|---|---|
| Header routing instead of body parsing | Removes body buffering and parsing from the hot path | Maintainers, AWS, Google, Cloudflare, Tigera. Implemented in Kuadrant PR #1500, unmerged |
| Statelessness, round-robin instead of sticky | Any instance serves any request; no session store; scale to zero | Maintainers, AWS, Google, Cloudflare |
| Removing the `initialize` handshake | One round trip saved; "a client's first message can be the actual tool call" | AWS |
| Removing the Redis session store | "Database writes on `initialize` are gone, and database reads are gone from every call, which makes things snappier" | GitHub |
| `ttlMs` and `cacheScope` | A `tools/list` round trip skipped per TTL window, and prompt-cache prefix stability across reconnects | Maintainers, Cloudflare |

**The whole of the 2026-07-28 performance story is below the line.** Every
mechanism is real, specified and implemented. Not one of the four organizations
that shipped it has published a before-and-after measurement.

---

## 9. Open gaps

Ordered by what a wrong answer would cost.

1. **No before-and-after measurement of the stateless migration exists.** The
   largest revision of the protocol since launch was justified on scaling and
   latency grounds by its maintainers, AWS, Google and Cloudflare, and none of
   them published a number. GitHub migrated a high-traffic production server,
   removed a Redis read from every call, and described the result as "snappier".
2. **No MCP cache hit rate has been published.** The caching feature is
   mandatory, two months old, and its benefit is entirely unmeasured. Section 4.2
   argues that the enterprise case (per-user filtered tool lists) forces
   `private` scope and defeats shared caching, which would make the measured hit
   rate at a gateway low. Nobody has checked.
3. **No methodologically sound MCP-versus-direct-API comparison exists**, and the
   figures in circulation differ by a factor of 50 (7.2).
4. **The code-execution crossover point is unpublished.** Code execution costs 7%
   wall clock and saves 77% tokens; it saves round trips only on multi-call
   tasks. How many calls a task needs before it is faster as well as cheaper is
   the number that would make it a decision rather than a preference.
5. **The OTel MCP conventions describe the previous protocol** (6.2), have no
   releases or tags (6.3), and cannot resolve gateway overhead with their
   recommended histogram boundaries (6.1). An enterprise standardizing on them
   today is standardizing on a pre-stateless model with a known open alignment
   issue.
6. **No published operational latency target.** `ops/` 8.5 already records that
   nobody has published what a good p99 for an MCP tool call is. Nothing found in
   this pass changes that. The only numeric hint in any official artifact is the
   OTel histogram's top bucket at 300 seconds, which is a statement about what
   the convention authors expect to be possible, not a target.
7. **Model-internal tool-selection time has never been isolated** from prefill
   cost or from exploratory tool calls (5.4).
8. **The MRTR round-trip budget is unbounded and unmeasured** (3.4). The spec
   caps nothing. No implementation reports a distribution of round trips per
   completed request.
9. **Two figures this repo previously carried should be retired**: the MintMCP
   100 to 250 ms inspection figure, which is not at its cited URL (2.6), and any
   use of Tetrate's 160 to 390 ms, whose units are internally contradictory
   (1.3).
10. **Three widely repeated figures are unverified against their supposed
    sources**: Modal's 64 concurrent tool calls per container (absent from
    Modal's documentation), the Nylas 30x batch claim (traces to arithmetic on a
    comparison blog), and the date on Pinterest's 66,000 invocations.

---

## Appendix: source index

Every URL below was fetched on 2026-09-21 unless a different verification date
is stated inline.

**Specification and OpenTelemetry (OFFICIAL)**
- Caching utility: <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching>
- Multi Round-Trip Requests: <https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr>
- Release candidate post: <https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/>
- MCP semantic conventions: <https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md>
- Alignment issue #437: <https://github.com/open-telemetry/semantic-conventions-genai/issues/437>
- Kuadrant mcp-gateway PR #1500: <https://github.com/Kuadrant/mcp-gateway/pull/1500>
- MCP Python SDK caching hints: <https://py.sdk.modelcontextprotocol.io/client/caching/>

**Independent measurement (PRACTITIONER)**
- Berk Kalelioğlu, "MCP Gateway Benchmark: Latency & Security of 6 Gateways", AIMultiple, published 2026-08-24, data updated 2026-09-19: <https://aimultiple.com/mcp-gateway>. Disclosure on the page: "This research does not mention any subscribers of AIMultiple's benchmarking services."
- Şevval Alper, "Code Execution with MCP", AIMultiple, updated 2026-08-14: <https://aimultiple.com/code-execution-with-mcp>
- Thiago Mendes, "MCP Server Performance Benchmark v2", TM Dev Lab, 2026-02-28: <https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html>

**Preprints (PREPRINT)**
- arXiv:2603.20313, Semantic Tool Discovery for MCP Tool Selection, 2026-03-19: <https://arxiv.org/abs/2603.20313>
- arXiv:2604.21816, Tool Attention Is All You Need, 2026-04-23: <https://arxiv.org/html/2604.21816v1>

**Vendor (VENDOR)**
- GitHub, "How we're making GitHub Copilot smarter with fewer tools", 2025-11-19: <https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/>
- GitHub changelog, MCP Server stateless support, 2026-07-23: <https://github.blog/changelog/2026-07-23-github-mcp-server-supports-the-next-mcp-specification/>
- AWS AgentCore Gateway and the 2026-07-28 spec, 2026-07-28: <https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/>
- Google, Scaling AI agent infrastructure with the MCP stateless updates, 2026-08-05: <https://developers.googleblog.com/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/>
- Cloudflare, "The next generation of MCP", 2026-08-06: <https://blog.cloudflare.com/mcp-v2/>
- Tigera, "The New MCP Headers Are a Gift to Gateways", 2026-08-06: <https://www.tigera.io/blog/the-new-mcp-headers-are-a-gift-to-gateways/>
- TrueFoundry, "Best MCP Gateway for Production AI Systems in 2026", 2026-07-21: <https://www.truefoundry.com/blog/best-mcp-gateway-for-production-ai-systems>
- TrueFoundry, Enterprise MCP Governance, 2026-09-11: <https://www.truefoundry.com/blog/enterprise-mcp-governance-control-audit-secure-mcp-server-access>
- Maxim AI, "Fastest Enterprise MCP Gateway in 2026", 2026-04-08, modified 2026-07-03: <https://www.getmaxim.ai/articles/fastest-enterprise-mcp-gateway-in-2026/>
- agentgateway design post: <https://agentgateway.dev/blog/2026-06-04-designing-agentgateway-unified-gateway/>
- agentgateway vs LiteLLM, 2026-06-26: <https://agentgateway.dev/blog/2026-06-26-benchmarking-agentgateway-vs-litellm/>
- Tetrate, Envoy AI Gateway MCP Performance, Ignasi Barrera, 2025-12-08: <https://tetrate.io/blog/envoy-ai-gateway-mcp-performance>
- Envoy AI Gateway, MCP traffic routing performance: <https://aigateway.envoyproxy.io/blog/mcp-in-envoy-ai-gateway/>
- Requesty prompt-cache hit rate by provider, April 2026: <https://www.requesty.ai/data/cache-hit-rate-by-provider-april-2026>
- MintMCP, enterprise AI infrastructure, 2026-04-13: <https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp> (cited here only to record that the figure this repo attributes to it is absent)

**Secondhand (SECONDHAND)**
- Dora Noda, bex.co, 2026-07-30: <https://bex.co/blog/2026/07/30/mcp-server-concurrency-production-readiness>
- InfoQ on Pinterest's MCP ecosystem, 2026-04-01: <https://www.infoq.com/news/2026/04/pinterest-mcp-ecosystem/>
- Nylas CLI, MCP vs API for AI agents, Qasim Muhammad, updated 2026-06-09: <https://cli.nylas.com/guides/mcp-vs-api-ai-agents>
- Toolradar, MCP vs API, published 2026-03-24, updated 2026-09-20: <https://toolradar.com/blog/mcp-vs-api>

**Checked and found to contain nothing usable**
- Modal Servers guide: <https://modal.com/docs/guide/servers> and `modal.concurrent` reference: <https://modal.com/docs/reference/modal.concurrent>. Neither documents a default concurrency, and neither contains the number 64.
