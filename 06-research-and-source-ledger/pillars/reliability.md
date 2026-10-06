---
title: "Reliability of MCP at enterprise scale"
date: 2026-09-21
sources_verified_on: 2026-09-21
status: draft
---

<!-- ABOUTME: The reliability pillar. HA topology, capacity, failure isolation, degradation, SLOs, health checking, version skew. -->
<!-- ABOUTME: Fills the thinnest area of the corpus. References the existing files rather than repeating them. -->

## How to read the sourcing

Every claim carries a source URL and the date it was read. Labels:

| Label | Meaning |
|---|---|
| **[OFFICIAL]** | modelcontextprotocol.io, the specification repository, or an AAIF working-group charter |
| **[VENDOR]** | A company publishing about its own product or platform |
| **[PEER-REVIEWED]** | Published through peer review |
| **[PRACTITIONER]** | A named engineer publishing an account or a measurement, not selling the thing measured |
| **[MEASURED]** | A number produced by running something, with the method stated. Can co-occur with the labels above |
| **[SECONDHAND]** | Reported by someone other than the party who observed it |
| **[UNVERIFIED]** | Stated here because it is load-bearing, and not confirmed. Never put on a slide in this state |

Where a number is a recommendation rather than a measurement, this file says so in the same sentence.

## What this file does not re-cover

The corpus already carries the following, and this file references rather than repeats it.

| Already covered | Where |
|---|---|
| Failure modes F1 to F20, including the tool-definition context tax, retry storms, `isError` on HTTP 200, and layered idle timeouts | `06-research-and-source-ledger/ops/mcp-operations-at-scale-2026-09.md` §1 |
| The stateless dissent (Amelin), the WorkOS resumability account, the AWS well-architected post, pgEdge transport failure modes | `06-research-and-source-ledger/ops/` §2.5 to §2.7 |
| Statelessness removing sticky routing; Kubernetes as substrate; ToolHive and ContextForge deployment shapes | `06-research-and-source-ledger/scale/mcp-at-scale-architecture-2026-09.md` §6 |
| Whether the gateway is a single point of failure, and the Enterprise IG's acknowledgement of the gap | `06-research-and-source-ledger/bestpractice/mcp-gateway-and-registry-operations.md` §3.6 |
| Connection handling after sessions were removed, keep-alives, `X-Accel-Buffering` | `bestpractice/mcp-gateway-and-registry-operations.md` §3.4 |
| Idempotency after resumability was removed; dual-era sticky routing; the `resultType` compatibility branch | `bestpractice/mcp-server-deployment-and-migration.md` §3.1 to §3.3 |
| Error semantics, the two-mechanism model, the explicit-handle pattern | `bestpractice/mcp-server-deployment-and-migration.md` §5.4 to §5.6 |
| The era compatibility matrix and gateway era caching | `bestpractice/mcp-gateway-and-registry-operations.md` §8.3 |
| Registry counts, self-reported metadata, the Registry WG out-of-scope statement | `ecosystem/registry-count-verification.md`, `bestpractice/VERIFIED-transport-and-quote-audit.md` |

Everything below is new.

---

## 1. The single most consequential finding: MCP no longer has a liveness primitive

`ping` was removed in `2026-07-28`. Verbatim from the changelog, major change 5:

> Remove `ping`, `logging/setLevel`, and `notifications/roots/list_changed`. Log
> level is now set per-request via `io.modelcontextprotocol/logLevel` in `_meta`;
> servers **MUST NOT** emit `notifications/message` for requests that did not
> include this field ([SEP-2575]).

Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog (read
2026-09-21). **[OFFICIAL]**

The corpus records the removals of sessions, the handshake and resumability. It
does not record this one, and for reliability it matters more than any of them,
because `ping` was the only protocol-level way to ask a peer whether it was
alive without performing work.

**The replacement exists and is stronger, but it is a different shape.** Major
change 3, verbatim:

> Add `server/discover`: servers **MUST** implement this RPC to advertise their
> supported protocol versions, capabilities, and identity. Clients **MAY** call
> it before any other request for up-front version selection, or use it as a
> backward-compatibility probe on STDIO ([SEP-2575]).

Same source, same date. **[OFFICIAL]**

So the correct probe changed from a no-op round trip to a capability read. That
is better for readiness (it tells you the peer is alive *and* what era it
speaks) and worse for cheap high-frequency liveness (it returns a payload that
is itself cacheable, and `server/discover` results carry `ttlMs` and
`cacheScope` under SEP-2549, so an intermediary may answer a health probe from
cache without the backend being involved at all).

### The failure this has already caused, dated and specific

Issue #567 on `MikkoParkkola/mcp-gateway`, opened and closed 2026-09-18:

> **Backend answering -32601 to the ping health probe is auto-disabled after 30s**

The gateway "sends MCP `ping` every 10s". A backend that answers `-32601`
(method not found), described in the issue as "a complete answer, proof the peer
is alive and speaking MCP", is "counted as unserved". Three consecutive such
answers trip the breaker and the backend loses all traffic.

Source: https://github.com/MikkoParkkola/mcp-gateway/issues/567 (read
2026-09-21). **[PRACTITIONER]**, project issue tracker.

A `2026-07-28`-compliant server is *supposed* to answer `-32601` to `ping`,
because `ping` no longer exists. So the gateway's health check removes exactly
the servers that upgraded correctly, thirty seconds after they upgrade, with no
error anywhere except a traffic graph going to zero.

This is the cleanest available example of three things at once: a removed
primitive nobody budgeted for, version skew presenting as an outage, and a
health check that measures the wrong thing. It is worth putting on a slide, and
it is three days old at the time of writing.

---

## 2. Failure-mode table

New modes, numbered R to keep them distinct from the F-series in `06-research-and-source-ledger/ops/`.
Ordered by how hard the mode is to detect before it hurts.

| # | Failure mode | What it looks like | Evidence | Label |
|---|---|---|---|---|
| **R1** | **Health probe uses a removed method** | Gateway probes with `ping`, compliant server answers `-32601`, breaker trips, all traffic to a healthy backend stops after three probes. Observed at a 10s probe interval, so 30 seconds from upgrade to outage | mcp-gateway #567, 2026-09-18 | [PRACTITIONER] |
| **R2** | **Client fails silently at startup and proceeds without tools** | The handshake does not complete inside the host's startup window, the connection is abandoned with "no error message, no warning", and the agent runs to completion with a smaller tool set and no indication anything is missing | claude-code #25751, 2026-02-14 | [PRACTITIONER] |
| **R3** | **Discovery traffic trips provider rate limits before any tool call** | 90 session startups produced 2,021 downstream connects (about 22.5 per session) and 69 HTTP 429s from one provider serving zero tools. All of it `tools/list` and connect traffic | toolport #874, 2026-09-14 | [MEASURED] |
| **R4** | **The handshake itself exceeds the server's rate limit** | AWS Knowledge MCP throttles about one request per 15s per IP. `initialize` returns 200, the immediate `tools/list` returns 429, and "the client treats this as a connection failure and marks the server as unavailable" | awslabs/mcp #2949, 2026-04-10 | [MEASURED] |
| **R5** | **Registry entry points at nothing** | 9.7% of remote endpoints listed in the official registry answered 404 to an anonymous `initialize`; 4.2% failed DNS; 1.0% failed TLS | The Ops Log scan of 10,716 endpoints, 2026-07-30 | [MEASURED] |
| **R6** | **A stalled tool call hangs the agent with no timeout and no cancellation** | "does not raise, does not time out, and does not produce a degraded answer. The invocation simply never completes." Cancel was called at 25s and the agent was still stuck 65 seconds later | strands-agents #4403, 2026-09-19 | [PRACTITIONER] |
| **R7** | **An oversized tool result removes the server, not just the request** | Responses to about 27.8 KB served repeatably; 56 KB "reliably kills the server"; 77 KB delivered about 1.4 KB then stalled, "server gone afterwards" | stack-chan #712, 2026-09-17 | [MEASURED] |
| **R8** | **Retry amplification across a chain** | A 3-retry policy over 5 dependent steps produces up to 3^5 = 243 attempts. One measured conversation burned about $2 of tokens in a 30-second window on retries alone | TianPan, 2026-04-10 | [MEASURED] + modeled, see §5 |
| **R9** | **Connection pool defaults collapse under agent concurrency** | Default pool (about 50 connections) produced total failure at 50 concurrent users; raising it to 1,000 restored 4,739 RPS. Go's `http.DefaultClient` (2 idle conns per host) pushed P95 from 17.6 ms to 61 ms | TM Dev Lab benchmark v2, 2026-02-28 | [MEASURED] |
| **R10** | **A cached era assumption survives an in-place upgrade** | Clients SHOULD cache era per server process or origin. A backend upgraded behind a shared hostname keeps being addressed under the stale era, and one wrong-answer mode is "process an era-ambiguous method under legacy semantics", which is a silent wrong answer rather than an error | Versioning page, via `bestpractice/` §8.3 | [OFFICIAL] |
| **R11** | **Health checks answered from cache** | `server/discover` results carry `ttlMs` and `cacheScope` under SEP-2549. An intermediary may serve a probe from cache, so a green health check can mean "the cache is up" | Changelog minor change 5 | [OFFICIAL], consequence is this file's inference, see §7 |
| **R12** | **Duplicate side effects in the task-creation window** | The Tasks extension makes work durable *after* the handle is returned. The interval between the client sending `tools/call` and receiving `CreateTaskResult` has no deduplication, and the extension specifies none | ext-tasks overview, read 2026-09-21 | [OFFICIAL], absence finding |

Sources, in order: https://github.com/MikkoParkkola/mcp-gateway/issues/567 ,
https://github.com/anthropics/claude-code/issues/25751 ,
https://github.com/btsouth/toolport/issues/874 ,
https://github.com/awslabs/mcp/issues/2949 ,
https://dev.to/theopslog/i-checked-every-mcp-server-in-the-official-registry-about-1-in-10-is-broken-1ehj ,
https://github.com/strands-agents/harness-sdk/issues/4403 ,
https://github.com/stack-chan/stack-chan/issues/712 ,
https://tianpan.co/blog/2026/04/10/retry-storm-agentic-systems-cascading-failure ,
https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html ,
https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning ,
https://modelcontextprotocol.io/specification/2026-07-28/changelog ,
https://modelcontextprotocol.io/extensions/tasks/overview . All read 2026-09-21
except where the corpus already dates them.

---

## 3. High availability topology

### 3.1 What the stateless revision actually changed, stated as an availability property

The corpus covers the mechanics. The availability consequence is worth stating
separately, because it is the one thing in this whole area that got
unambiguously better.

Before `2026-07-28`, losing a server instance destroyed every session on it. A
session was created by `initialize` and lived in that process. Sticky routing
was therefore mandatory, which meant the load balancer could not shed load away
from a hot instance, and a rolling deploy was a user-visible event.

After `2026-07-28`, no request depends on any prior request. Dora Noda states
the operational form of this plainly:

> "any replica can serve any request now, so a 502 from one instance is
> retryable against the pool without re-handshaking"

Source: https://bex.co/blog/2026/09/09/mcp-stateless-deploy-from-chat (read
2026-09-21). **[PRACTITIONER]**

That is the reliability win, and it is larger than the cost saving. AWS priced
the deleted session store at "about $23/month" for a two-node ElastiCache
(recorded in `06-research-and-source-ledger/ops/` §2.6). Twenty three dollars is not why anyone did
this. Retryability against a pool is.

**Two carve-outs, both already in the corpus and both load-bearing here.** A
dual-era server still mints `Mcp-Session-Id` for legacy clients and holds that
record in a plain in-process dict with no distributed store
(`bestpractice/mcp-server-deployment-and-migration.md` §3.2), so the migration
window has neither the old guarantee nor the new benefit. And
`subscriptions/listen` is still one long-lived stream, so the instance holding
it is still a thing that can be lost.

### 3.2 Running the server tier

Nothing about MCP makes this exotic once sessions are gone. It is an HTTP POST
service. Three replicas across three availability zones behind a round-robin
balancer with no affinity is the whole answer for the modern-era path.

The one MCP-specific configuration item on the major clouds is turning affinity
off, because the platforms default it on. On Azure App Service the setting is
`clientAffinityEnabled: false`; ARR affinity cookies "restrict scaling because
they send requests only to servers associated with the cookie". Source:
https://learn.microsoft.com/en-us/azure/app-service/manage-automatic-scaling
(read 2026-09-21). **[VENDOR]**

The dated warning: guidance written before 2026-07-28 tells you the opposite. A
July 2026 practitioner walkthrough of MCP on Azure Container Apps lists the "SSE
gotcha" as needing "session affinity ('sticky' sessions), server-side keepalive
pings (~15-second intervals), and raised idle timeouts". Published 2026-07-29,
one day after the revision. Source:
https://dev.to/kirandeepjassalcrypto/mcp-deep-dive-part-13-hosting-mcp-on-azure-at-real-scale-container-apps-autoscaling-and-the-182b
(article date confirmed 2026-07-29T18:32:02Z via the dev.to API, read
2026-09-21). **[PRACTITIONER]**

Two of those three are now wrong for the modern era and one is still right. Keep
the keepalive, because `subscriptions/listen` still needs it and the spec only
makes it a SHOULD on the server. Drop the affinity. Keep the raised idle
timeouts for the same one method.

### 3.3 Running the gateway tier, and the question nobody has answered in public

`bestpractice/mcp-gateway-and-registry-operations.md` §3.6 establishes that no
primary source describes an MCP gateway's behavior during its own outage, that
no gateway publishes an SLO, and that the Enterprise IG's "Gateway Deployment
Patterns Document" is the artifact that would fix this.

**Re-verified 2026-09-21.** The charter still lists it as:

| Item | Status | Target Date | Champion |
| --- | --- | --- | --- |
| Gateway Deployment Patterns Document | Planned | Q3 2026 | TBD |

Source: https://modelcontextprotocol.io/community/interest-groups/enterprise
(read 2026-09-21). **[OFFICIAL]** Q3 2026 ends nine days after this file is
written, the champion is still TBD, and the charter's only changelog entry is
still "2026-04-13 Initial charter filed". The document does not exist. The
charter also still routes gateway questions to a "Gateways IG" that has no
published charter page, which §3.6 already measured.

So the following is reasoning from first principles against a documented
absence rather than a summary of published guidance, and it is labeled as such.

**The fail-open versus fail-closed decision.** When the gateway is down, an
agent has exactly two options, and the protocol does not choose for you.

*Fail closed* means the agent loses every tool. This is the safe default and it
is what most deployments get by accident, because the gateway is configured as
the single MCP endpoint in the client config and there is nothing else to try.
The agent then behaves like a model with no tools, which is a degradation the
user sees as wrong answers rather than as an outage. R2 is the client-side
version of the same shape.

*Fail open* means the client routes around the gateway to the servers directly.
This is what the bypass problem in `bestpractice/` §1.5 describes as a security
failure, and it is the same mechanism. A deployment cannot have a gateway that
is both the mandatory policy enforcement point and an optional availability
component. Whichever you choose, the other property is gone.

**The honest framing:** the gateway is a single point of failure by design,
because that is what an enforcement point is. Making it redundant is ordinary
work (stateless replicas, no shared state, health-checked pool). Making it
*optional* is not available, and should not be.

**What does exist in published form for peer failure**, and it is thin:
ContextForge documents "Health checking with configurable intervals (60s
default) and failure thresholds" for gateway-to-gateway federation only
(recorded in `bestpractice/` §3.6). agentgateway has **passive health checks
only** as of 2026-09-21. From the open PR adding active ones:

> "Passive health only learns that a provider is down by failing a real request.
> With an active check, a provider that fails `unhealthyThreshold` probes in a
> row is evicted and stays evicted for as long as it keeps failing."

Source: https://github.com/agentgateway/agentgateway/pull/3352 , opened
2026-09-06, last updated 2026-09-19, **still open** when read 2026-09-21.
**[PRACTITIONER]**, project PR. That PR is scoped to LLM provider endpoints
rather than MCP backends.

### 3.4 The registry is not a runtime dependency, and the project says so

The brief asks what happens when the registry is unreachable at agent start. The
official answer is that this should not be a question anyone has to ask, because
an agent should not be calling the official registry at start.

Verbatim from the registry's own documentation:

> "The MCP Registry is not intended to be directly consumed by host
> applications. Instead, host applications should consume other MCP registries,
> such as downstream marketplaces, via a REST API conforming to the official MCP
> Registry's OpenAPI spec."

And on the expected access pattern:

> "We expect that downstream aggregators will use the MCP Registry API to pull
> new metadata on a regular but infrequent basis (for example, once per hour)."

And on its maturity:

> "The MCP Registry is currently in preview. Breaking changes or data resets may
> occur before general availability."

Source: https://modelcontextprotocol.io/registry/about (read 2026-09-21).
**[OFFICIAL]**

Three reliability consequences follow directly, and together they are the
strongest available support for the delegation-chain argument.

1. **The correct architecture is a pull-through mirror, not a lookup.** An
   enterprise registry ingests hourly and serves locally. Upstream being down
   then costs you freshness, not availability. This is the same shape as an
   artifact proxy, and it is what the federation design in
   `bestpractice/` §6.5 is for.
2. **There is no published availability target for the official registry at
   all.** No SLA, no SLO, no uptime page was found on
   https://registry.modelcontextprotocol.io/docs or
   https://modelcontextprotocol.io/registry/about (both read 2026-09-21).
   Combined with "data resets may occur", treating it as a synchronous
   dependency is not a supported use. **[MEASURED]** absence.
3. **Availability of the catalog is not availability of what it points at.** The
   Ops Log probed 10,716 unique remote endpoints listed in the official registry
   with a single anonymous `initialize` over HTTP and a 10-second timeout, and
   classified the answers:

   > "Completed an anonymous MCP handshake: 5,346 (49.9%). Auth-gated
   > (401/403): 2,643 (24.7%). Not found (404): 1,044 (9.7%). DNS failure: 446
   > (4.2%). Server error (5xx): 236 (2.2%). Timeout: 160 (1.5%). TLS failure:
   > 107 (1.0%)."

   Source:
   https://dev.to/theopslog/i-checked-every-mcp-server-in-the-official-registry-about-1-in-10-is-broken-1ehj ,
   published 2026-07-30, corrected 2026-08-24, read via extraction 2026-09-21.
   **[MEASURED]**, **[PRACTITIONER]**.

   The five hard-failure classes sum to 1,993 endpoints, which is **18.6% of the
   10,716 probed**. Auth-gated is not a failure and is excluded from that figure.
   The quoted classes sum to 9,982, so 734 endpoints fell into classes
   not quoted in the extract read here; the 18.6% is therefore a floor on
   hard failures, and anyone using this number on a slide should re-read the
   original article for the full classification. **[UNVERIFIED]**: the
   composition of the remaining 734.

   Local and stdio packages were excluded, because they have no endpoint to
   probe remotely. So this measures the remote half of the catalog only.

---

## 4. Scaling and capacity

### 4.1 What is actually published, and what is not

This is the thinnest evidence base in the whole reliability area, and the
shortage is itself the finding.

**Published and genuinely measured:** one independent multi-implementation
benchmark (TM Dev Lab, below). **Published as a framework with the numbers
explicitly disclaimed:** a C# Corner article on benchmarking stateless MCP
behind load balancers, which proposes a 1/2/3/5-instance NGINX matrix and then
states of its own figures, verbatim, "Those numbers are only an example of how
results might be reported. They should not be presented as actual benchmark
results unless they came from a real test run." Source:
https://www.c-sharpcorner.com/article/benchmarking-stateless-mcp-servers-behind-load-balancers/ ,
Aarav Patel, 2026-08-11, read 2026-09-21. **[PRACTITIONER]** Cite it for the
method, never for a number.

**Published as a harness with no results:** Microsoft's Locust and Azure Load
Testing walkthrough and its companion repository. The repository describes
itself as "Locust load tests for hosted MCP servers" against GitHub MCP,
Microsoft Learn MCP, Context7 and Azure DevOps Remote MCP, and models "bursty
agent-shaped traffic" through think-time parameters. It publishes no virtual
user counts, request counts, RPS, latency percentiles or dates in the
repository documentation. Source:
https://github.com/kroy92/azure-load-test-mcp-server (read 2026-09-21).
**[VENDOR-adjacent]**. The accompanying Microsoft Tech Community post at
https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/load-testing-hosted-mcp-servers-with-locust-and-azure-load-testing/4522691
could not be retrieved in full on 2026-09-21 across two attempts; search
snippets describe "a 15-minute run against four production servers" producing
"2,293 requests with three failures" and a demo run on 2026-07-12 with 16
virtual users. **[UNVERIFIED]**: every number in that sentence. Do not use it
until the post is read directly. At 2,293 requests over 15 minutes it is
approximately 2.5 requests per second, which is a functional smoke test rather
than a capacity measurement, and the harness authors say as much.

**Not published anywhere found:** a capacity number for any MCP *gateway*, a
published SLO for any MCP server or gateway operated by its vendor, and any
load test of the `2026-07-28` MRTR or `subscriptions/listen` paths.

### 4.2 The one real benchmark

TM Dev Lab, Thiago Mendes, published 2026-02-28. Read 2026-09-21 at
https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html
**[PRACTITIONER]**, **[MEASURED]**.

Method: Azure VM, 8 vCPU / 32 GB, each MCP server confined to 2.0 vCPU and 2 GB,
Docker bridge networking, Streamable HTTP in stateless mode, 50 concurrent
virtual users, I/O-bound workload (Redis reads and external HTTP calls), three
independent runs totaling 39.9 million requests, 0% error rate across all 15
implementations.

| Implementation | RPS | Avg latency | P95 |
|---|---|---|---|
| Rust | 4,845 | 5.09 ms | 10.99 ms |
| Quarkus (JVM) | 4,739 | 4.04 ms | 8.13 ms |
| Go | 3,616 | 6.87 ms | 17.62 ms |
| Java Spring MVC | 3,540 | 6.13 ms | 13.71 ms |
| Java virtual threads | 3,482 | 9.03 ms | 18.43 ms |
| Quarkus native | 3,449 | 10.36 ms | 15.92 ms |
| Bun | 876 | 48.46 ms | 98.50 ms |
| Node.js | 423 | 123.50 ms | 200.07 ms |
| Python | 259 | 251.62 ms | 342.41 ms |

Caveats that matter more than the ranking. This is 2 vCPU per server and 50 VUs,
so it is a per-core efficiency measurement, not a fleet capacity number. The
workload is I/O-bound against local Redis and an external stub, so it measures
protocol and framework overhead rather than anything a real tool does. And it is
one researcher's rig, not a reproduced result.

**The two findings that transfer regardless of language.**

*Connection pool defaults are the first thing to saturate, and they fail hard
rather than degrading.* Quarkus with its default pool of about 50 connections
produced "catastrophic failure (0 RPS)" at 50 virtual users; raising
`connection-pool-size` to 1000 restored 4,739 RPS, and the article calls this
"the only configuration change that prevented catastrophic failure." Go's
`http.DefaultClient`, with two idle connections per host, created TCP churn that
pushed P95 to 61 ms until `MaxIdleConnsPerHost` was raised to 100, after which
P95 was 17.62 ms.

*Stateless MCP has a per-request instantiation floor in some SDKs.*
Per-request `McpServer` instantiation in the JavaScript SDK is described as "the
intentional design for stateless MCP servers", creating "a fixed 5-10 ms
overhead floor that no framework optimization can eliminate." That is a direct
cost of the statelessness that bought the HA property in §3.1, and it is not in
the corpus anywhere.

### 4.3 What saturates first

The brief asks whether the server, the gateway, the model endpoint or the
downstream system saturates first. There is no published measurement that
answers this for a real deployment. The ordering below is reasoning from the
evidence that does exist, labeled as inference.

1. **The downstream system the tool calls, or its rate limiter.** R3 and R4 are
   both this, and both trip before a single tool call is made. The toolport
   measurement is the sharpest: 90 session startups, 2,021 downstream connects
   (about 22.5 per session), 69 HTTP 429s from a provider "that currently serves
   0 tools", so "these 429s come entirely from session-start connects and
   tool-list loads, not tool calls." Source:
   https://github.com/btsouth/toolport/issues/874 (read 2026-09-21).
   **[MEASURED]**
2. **Connection pools and file descriptors on the server.** R9, measured.
3. **The model endpoint.** Agent workloads are token-bound far more often than
   request-bound, and `06-research-and-source-ledger/bestpractice/mcp-token-economics-and-tool-consolidation.md`
   covers that whole axis. A tool call costs a few milliseconds of MCP and a few
   thousand tokens of inference.
4. **The MCP server's own compute.** Only for CPU-bound tools, and Python is the
   case where the runtime itself is the ceiling: the benchmark attributes the
   259 RPS figure to "the CPython GIL in FastMCP session processing", noting
   that "the ASGI server layer is not the bottleneck."
5. **The gateway.** No published number exists. An L7 proxy doing header-based
   routing is not usually the constraint, and `2026-07-28` made this
   specifically cheaper by mandating `Mcp-Method` and `Mcp-Name` so a gateway
   can route without parsing the body (see `VERIFIED-transport-and-quote-audit.md`).

**[INFERENCE]** on the ordering. **[MEASURED]** on items 1, 2 and 4.

### 4.4 Autoscaling signals

Concurrent in-flight requests per replica is the right signal, not CPU. A tool
call is mostly waiting on something else, so CPU stays low while the request
queue grows, and a CPU-based rule scales too late.

The one published MCP-specific configuration found uses exactly this: a KEDA
HTTP scale rule on `concurrentRequests: '100'`, `minReplicas: 2`,
`maxReplicas: 30`, with scale-to-zero only for non-production. The author
reports about 3,200 RPS at peak, 2 replicas overnight scaling toward 30, and a
read-tool P95 of 120 ms held across the range. Source:
https://dev.to/kirandeepjassalcrypto/mcp-deep-dive-part-13-hosting-mcp-on-azure-at-real-scale-container-apps-autoscaling-and-the-182b ,
published 2026-07-29, read 2026-09-21. **[PRACTITIONER]**. The article states no
measurement methodology for those three figures, so treat them as reported
operating experience rather than a benchmark. Its affinity and keepalive advice
is pre-`2026-07-28`, per §3.2.

Two MCP-specific additions to an otherwise ordinary autoscaling setup:

- **`minReplicas` of at least 2, and never 0 in production.** R2 and R4 both
  show a client abandoning a server whose first request is slow. A cold start
  inside the host's startup window is an agent that silently runs without those
  tools for the rest of the session. Scale-to-zero is a reasonable
  non-production saving and a production outage generator.
- **Scale `subscriptions/listen` separately if you serve it at all.** It is the
  only long-lived connection left, its concurrency is bounded by connection
  count rather than by request rate, and mixing it into a request-rate scaling
  rule makes both wrong.

### 4.5 Connection handling now that sessions are gone

Covered mechanically in `bestpractice/` §3.4. The capacity consequence is not:
**the modern era is a request-per-connection HTTP workload, so keep-alive reuse
and pool sizing are now the dominant tuning surface**, and the defaults shipped
by HTTP clients are set for a different shape of traffic. R9 is that, measured
twice in the same benchmark, in two different languages, with two different
symptoms. An agent fleet opens far more short connections than the same number
of human users would, because discovery fans out (R3) and because each request
now stands alone.

---

## 5. Failure isolation

### 5.1 Chained servers, and the amplification arithmetic

The modeled worst case is clean and worth stating precisely, with its label
intact. TianPan, 2026-04-10:

> "3-retry policy and you have 5 dependent steps, a failure at step 1 can
> theoretically produce 3^5 = 243 total retry attempts"

That is arithmetic, not a measurement, and the word "theoretically" is the
author's own. The same article carries one measured figure:

> "uncontrolled retries consumed roughly $2 in tokens over a 30-second window"

reduced to "$0.01" with circuit breaking, described as "a 200x cost reduction".
And the per-call form: a single tool call with an 8,000-token context under a
naive 3-retry policy is "32,000 input tokens consumed to achieve nothing."

Source: https://tianpan.co/blog/2026/04/10/retry-storm-agentic-systems-cascading-failure
(read 2026-09-21). **[PRACTITIONER]**. The $2 and $0.01 are presented as
measured from one conversation with no methodology given, so they are a worked
example rather than a benchmark. Say "one engineer measured" if this reaches a
slide, not "retry storms cost 200x".

The principle in that article is the one worth keeping, and it is stated better
than anything else found:

> "An agent system should never consume more resources trying to recover from a
> failure than it would have consumed succeeding on the first attempt."

`06-research-and-source-ledger/ops/` F11 already carries pgEdge on retry storms from the transport
side. The new part is that with an agent the amplification is multiplicative
across a chain, and that the budget it consumes is the token budget rather than
the connection pool.

### 5.2 Timeouts for long-running tool calls

The spec gives cancellation semantics and no timeout guidance. Verbatim, already
recorded in `bestpractice/` §5.4: closing the SSE response stream "MUST be
treated by the server as cancellation of that request."

What is new here is that **a timeout is now the only thing standing between a
stalled tool and a permanently stuck agent, and at least one production SDK does
not have one**. R6, verbatim from the issue:

> "A stalled MCP tool call hangs the agent forever; ConcurrentToolExecutor never
> consults the cancel signal"

with the measured behavior that `agent.cancel()` at 25 seconds left the agent
unresponsive for a further 65 seconds, and the root cause that the stalled event
stream "never yields again, never raises, and never closes". Source:
https://github.com/strands-agents/harness-sdk/issues/4403 , opened 2026-09-19,
**open** when read 2026-09-21. **[PRACTITIONER]**

pgEdge's numbers remain the only published starting point, already in
`06-research-and-source-ledger/ops/` §2.7: connection timeout around 600 s, idle session timeout
300 s, hard request timeout 30 s, offered explicitly as a Postgres-backed
starting point rather than a universal. Nothing better has been published since.

The structural guidance that follows from R6 and from the layered-idle-timeout
mode (F10): **every tier needs a timeout, and the innermost one must be the
shortest.** Load balancer, gateway, MCP client, and the tool's own downstream
call. If the client's timeout is longer than the gateway's, the client waits for
a connection that is already gone. If no tier has one, R6 is the result.

### 5.3 Idempotency is the caller's problem and no convention exists

`bestpractice/` §3.1 establishes the mechanism: resumability was removed, a
dropped stream is indistinguishable from a cancellation, and clients MUST
re-issue with a new request ID, so a side effect that already happened happens
twice. It also records that the words "idempotency" and "deduplication" do not
appear in the transports, tools or basic pages of `2026-07-28`, and marks as
**[UNVERIFIED]** whether the Tasks extension supplies them.

**That is now verified, and the answer is no.**

Read 2026-09-21 at https://modelcontextprotocol.io/extensions/tasks/overview .
**[OFFICIAL]** The extension is `io.modelcontextprotocol/tasks`, opt-in by both
sides. It gives genuine durability, and the overview is explicit about what it
is for:

> "**Crash resilience.** A task ID is a durable handle. If the client
> disconnects or restarts, it can resume polling with the same ID."

> "The task is durably created before the response is sent."

The gap is the ordering. Durability begins *when the handle is returned*. The
window between the client sending `tools/call` and receiving the
`CreateTaskResult` carries the same exposure as an ordinary call: if the stream
breaks in that window, the client has no task ID to poll, must re-issue, and the
server has no way to recognize the second request as the same request. Nothing
in the overview, the lifecycle table, the client implementation steps or the
server implementation steps mentions an idempotency key, a client-supplied
request identifier that survives a retry, or deduplication of any kind.

Cancellation is also explicitly weak: "Cancellation is cooperative, the server
acknowledges the intent but is not obligated to stop the work."

So the position as of 2026-09-21 is:

- Core protocol: no idempotency mechanism, none proposed.
- Tasks extension: durable after handle creation, nothing before it, opt-in on
  both sides, and per
  https://modelcontextprotocol.io/extensions/client-matrix client support
  varies. **[UNVERIFIED]**: the current client-matrix contents, not read for
  this file.
- Convention: none. No SEP, no working-group deliverable, and no de facto
  pattern found across the sources read here.

The nearest thing to a convention anyone has written down is an application-level
one, from a practitioner running deploys over MCP: make "mutating calls
idempotency-keyed so a retried `deploy` cannot double-provision", and "Give
every long operation a job ID, not a session", with "`deploy` should return
`{ "job_id": ... }` on the first call." Source:
https://bex.co/blog/2026/09/09/mcp-stateless-deploy-from-chat , Dora Noda,
2026-09-09, read 2026-09-21. **[PRACTITIONER]**

That is the explicit-handle pattern from the spec's own non-normative tool
design guidance (`bestpractice/` §5.6), used for reliability rather than for
state. It works. It is also a per-server invention with no shared shape, which
means a gateway cannot enforce it, a registry cannot describe it, and a client
cannot rely on it. **That is a concrete, fixable protocol gap and this audience
owns it.**

### 5.4 Poison-pill tool calls

Three distinct shapes, only one of which is well covered in the corpus.

**Oversized results that kill the process rather than the request.** R7 is the
measured example: about 27.8 KB served repeatably, 56 KB "reliably kills the
server", 77 KB delivered about 1.4 KB then stalled. The reporter's framing is
the reusable part:

> "one oversized response removes the MCP endpoint until someone restarts the
> robot, and it would be much easier to live with if an oversized response
> failed the request and left the listener running."

Source: https://github.com/stack-chan/stack-chan/issues/712 , opened 2026-09-17,
open when read 2026-09-21. **[MEASURED]**, **[PRACTITIONER]**. Scope caveat
worth stating if used: this is an embedded MCP server on constrained hardware,
so the specific KB thresholds are about that device. The failure *shape*, one
request taking down the listener for everyone, is general, and it is the shape
that matters.

**Unbounded results that exhaust the caller instead.** The same class from the
other end: a tool returning a payload large enough to blow the context window
kills the agent run rather than the server. This is F1 and the token economics
research from a reliability angle rather than a cost one, and the spec's own
mitigation is output truncation and pagination
(`bestpractice/mcp-token-economics-and-tool-consolidation.md` §4.5).

**Calls that never terminate.** R6. Neither a large response nor an error, and
therefore invisible to both a size guard and an error-rate SLI.

The bulkhead that addresses all three is the same one: a per-call response size
cap and a hard per-call deadline, both enforced at the gateway, both returning a
tool execution error rather than a transport failure so the model can
self-correct. No MCP gateway examined publishes this as a documented feature.
**[MEASURED]** absence across the gateway documentation read for
`bestpractice/` §2 and re-checked 2026-09-21.

---

## 6. Graceful degradation

### 6.1 What the ecosystem actually implements, which is less than you would expect

This is where the evidence is most surprising and most useful to this room.

**ContextForge, the most comprehensively documented open-source MCP gateway,
declined both halves of the standard resilience kit.**

| Issue | Ask | State |
|---|---|---|
| #258 | "Universal client retry mechanisms with exponential backoff and jitter" across httpx, SSE, StreamableHTTP and WebSocket | **Closed as not planned** |
| #301 | "Full circuit breakers for unstable MCP server backends", three-state Closed/Open/Half-Open | **Closed as not planned** |

Sources: https://github.com/IBM/mcp-context-forge/issues/258 and
https://github.com/IBM/mcp-context-forge/issues/301 , both opened 2025-07-06,
both read 2026-09-21. **[PRACTITIONER]**, project issue tracker.

What #258 says exists instead, verbatim: the codebase has "no retry logic,
leading to immediate failures during temporary network issues."

What #301 says exists instead: a "Two-state system: enabled/disabled +
reachable/unreachable", with deactivation after a threshold, logged as
"Gateway {gateway.name} failed {GW_FAILURE_THRESHOLD} times. Deactivating...".
The issue enumerates what that lacks: "No Fast Failure Protection", "No
Half-Open Trial Requests", no timeout-based automatic recovery, and no
request-level protection beyond health checks.

A two-state disable with no half-open probe is not a circuit breaker. It is a
kill switch. Once a backend is deactivated it does not come back on its own,
which converts a transient dependency failure into a manual-intervention
incident. And it is precisely the mechanism that made R1 an outage on a
different gateway: three bad probes, deactivate, no recovery path.

**agentgateway has passive health checks only**, with active checks for LLM
providers still an open PR as of 2026-09-21 (§3.3).

**So the published position across the two most visible open-source gateways is:
no retry with backoff, no half-open recovery, and health checking that is either
passive or a threshold-and-disable.** That is not a criticism of either project,
both of which ship fast and are solving the discovery and policy problems first.
It is a measurement of where the ecosystem is, and it is the answer to "why does
this need a working group."

### 6.2 What the client best practices page does and does not say

The official client best practices page was read in full on 2026-09-21 at
https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices .
**[OFFICIAL]**

It is a substantial document covering progressive discovery, search strategies,
dynamic server management, caching, prompt-cache interaction, programmatic tool
calling, sandbox selection and sandbox security.

**It contains no guidance on timeouts, retries, backoff, circuit breaking,
health checking, or what a client should do when a server is unavailable.** The
only text adjacent to failure is the Error Handling paragraph under programmatic
tool calling, and it is about converting `isError` into a thrown exception
inside a sandbox. Verbatim:

> "MCP tool errors arrive as a successful response with `isError: true` rather
> than a transport failure. Generated wrappers should convert this into a thrown
> exception so model-authored code can use `try`/`catch`. If an uncaught error
> terminates the script, surface it as the script's result so the model can
> self-correct; **the model is responsible for reporting any partial side
> effects already committed.**"

The emphasis is added. That last clause is the single most quotable sentence in
the specification for this pillar. The official guidance for a partially
completed multi-tool script is that the *model* reports what it already did.
Read alongside §5.3, the position is coherent and worth stating plainly rather
than as an attack: the protocol removed the transport guarantee, provided no
application-level replacement, and assigned the residual accounting to a
non-deterministic component.

Two degradation-adjacent statements the page does make, both useful:

> "treat a cached list as stale once a `list_changed` notification arrives, even
> before its TTL expires"

> "Treat server disconnection as a conversation-boundary operation rather than a
> per-turn one."

The second is a real degradation policy, stated for a cost reason (prompt cache
invalidation) rather than a reliability one, and it happens to be the right
reliability answer too. Do not remove a failing server's tools mid-conversation.
Let the conversation finish, then rebuild.

### 6.3 Partial tool availability: what should happen, and what happens

**What should happen.** A tool the agent expected is gone. The agent should be
told, in the model's own channel, that the capability is unavailable and why, so
it can choose an alternative or tell the user it cannot proceed. The spec's own
two-mechanism error model supports exactly this: a tool execution error with
`isError: true` is the channel the model reads and can act on, and the spec says
clients "SHOULD provide tool execution errors to language models to enable
self-correction" (`bestpractice/` §5.5).

So the correct gateway behavior when a backend is out is **not** to remove the
tool from `tools/list`. Removing it changes the tool array, which invalidates
the prompt cache (F6) and silently narrows what the model believes it can do.
The correct behavior is to keep advertising the tool and to answer calls to it
with a tool execution error that says the backend is unavailable and whether
retrying will help. That is a bulkhead: the failure is contained to the calls
that touch the failing dependency, and everything else proceeds.

**[INFERENCE]**, derived from the spec's error model and the prompt-cache
behavior. No source states this recommendation directly, which is itself worth
noting given how obvious it is once assembled.

**What happens today.** R2: the host abandons the connection during startup with
"no error message, no warning" and "Claude proceeds as if MCP servers don't
exist." The proposed fixes on that issue are the ones this section argues for,
including "Defer MCP server connection to first tool invocation rather than
extension startup" and "Show MCP server connection status in the status bar".
Source: https://github.com/anthropics/claude-code/issues/25751 , opened
2026-02-14, closed as duplicate, read 2026-09-21. **[PRACTITIONER]**

A related report describes a host showing "No servers configured" for
slow-starting stdio servers that were in fact connected and functional, with a
window reload as the workaround. Source:
https://github.com/anthropics/claude-code/issues/29033 (title and summary read
via search 2026-09-21; the issue body was not read directly). **[UNVERIFIED]**
beyond the title. Included because the shape matches R2 and it should be read
before use.

The pattern across both: **degradation is silent on the side that can least
afford it.** A human sees a missing tool and asks. A model sees a smaller tool
list and confabulates a way around it.

### 6.4 Backpressure

Nothing MCP-specific is published. The transferable points:

- **Rate limiting at the gateway is the backpressure mechanism**, and it must
  return something the model can act on. A 429 with no `Retry-After` is what
  turned R4 into a client marking a healthy server permanently unavailable; the
  issue's own second proposed fix is "return a `Retry-After` header with the 429
  response so clients can implement proper backoff."
- **Budget the conversation, not just the request.** TianPan's concrete form:
  "Max tool calls per turn: Cap at 5-10 calls per agent turn", and "Pass a
  remaining-time budget through the agent chain. Sub-agents inherit a shrinking
  deadline." **[PRACTITIONER]**, recommendations not measurements.
- **Discovery needs its own budget.** R3 is 2,021 connects and 69 429s generated
  entirely by session start across "multiple concurrent gateway processes, each
  with independent backoff state." Per-process backoff does not compose. A
  shared token bucket across an agent fleet's discovery traffic is the fix, and
  no MCP gateway documents one.

---

## 7. Health checking, and the error semantics trap

### 7.1 The trap, stated once

Already in the corpus as F13 and `bestpractice/` §5.5, so briefly: a tool
execution error is a JSON-RPC *result* carried on HTTP 200. Monitoring that
alerts on 5xx reports a healthy server while every call fails.

### 7.2 What correct health checking looks like

The corpus states that status-code monitoring is wrong. It does not say what
right looks like. This is that.

**Four signals, and you need all four, because each one is blind to the others.**

| Layer | Probe | What it proves | What it cannot see |
|---|---|---|---|
| **Process liveness** | Out-of-band HTTP `GET /health/live` on a separate port or path, not the MCP endpoint | The process has not crashed | Everything about MCP |
| **Protocol readiness** | `server/discover` over the real MCP endpoint | The peer is alive, speaks MCP, and which era it speaks | Whether tools work |
| **Dependency readiness** | The server's own check of what its tools call, exposed at `GET /health/ready` | The tools can do their job | Whether the results are right |
| **Functional health** | Rate of results carrying `isError: true`, per tool, from real traffic | Tools are actually succeeding | Nothing, and this is the one nobody instruments |

The liveness and readiness split matters operationally and is the standard
Kubernetes distinction applied here: liveness failing restarts the container,
readiness failing "removes the instance from the load balancer pool without
restarting it." Source:
https://agentcat.com/guides/building-health-check-endpoint-mcp-server/ , Kashish
Hora, AgentCat, no publication date stated on the page, read 2026-09-21.
**[VENDOR]**. It recommends separate HTTP endpoints distinct from the MCP
protocol, and offers `HEALTH_CHECK_TIMEOUT = 5000`, dependency checks every
30 s, a 2 s database timeout, load balancer checks "every 5-10 seconds" and a
60 s max startup. Those are recommendations, not measurements, and the guide does
not state which protocol revision its examples assume. **[UNVERIFIED]**:
publication date, which means it cannot be dated relative to the `ping` removal.

**Five rules that follow from the evidence in this file.**

1. **Never probe with `ping`.** It was removed in `2026-07-28` (§1). A compliant
   server answers `-32601`, and R1 is what happens when a gateway counts that as
   a failure. If you must support both eras, treat `-32601` on `ping` as
   *healthy and modern*, not as a failure. That is exactly the acceptance
   criterion issue #567 landed on.
2. **Use `server/discover` as the protocol-level probe**, because servers MUST
   implement it and it returns the era, which makes the probe and the version
   check the same call.
3. **Bypass the cache when probing.** `server/discover` results carry `ttlMs`
   and `cacheScope` (R11). A probe answered from an intermediary's cache proves
   the intermediary is up. This is a direct consequence of SEP-2549 and it is not
   documented anywhere found. **[INFERENCE]** from the changelog and the caching
   utility page, read 2026-09-21.
4. **Alert on `isError` rate, not on status codes.** This is the only signal that
   sees a server whose dependency is down and whose handler is dutifully
   catching its own exception. It requires application instrumentation, which is
   the same instrumentation the Logging deprecation already pushed onto
   OpenTelemetry. Those two facts belong on one slide.
5. **Verify side effects out of band for tools that have them.** A handler that
   returns "OK" after its transaction rolled back is a success in every signal
   above. The only check that catches it observes the downstream effect.

On rule 5, the clearest published statement of the failure is a vendor's, and it
is worth quoting because it names the shape precisely:

> "Silent-success failures. A tool that returns 'OK' when it actually failed to
> perform the operation, the database transaction rolled back, the email queued
> but never sent, the webhook fired but to a stale URL, registers as success in
> the SLI and as failure in the user's reality."

Source: https://www.digitalapplied.com/blog/mcp-server-reliability-metrics-slo-design-framework-2026 ,
Digital Applied, 2026-05-15, read 2026-09-21. **[VENDOR]**, and see §8 for why
this source's numbers should not be used.

---

## 8. SLOs for tool calls

### 8.1 What is published, and how much of it to trust

One framework was found that addresses MCP SLOs directly, and it is content
marketing for a consulting practice. Source:
https://www.digitalapplied.com/blog/mcp-server-reliability-metrics-slo-design-framework-2026 ,
Digital Applied, 2026-05-15, read 2026-09-21. **[VENDOR]**

Its proposed targets are 99.5% monthly availability, P50 180 ms, P95 620 ms, P99
1.8 s, tool-call success rate at or above 99%, schema validation failures below
0.1%, MTTR under 30 minutes. **Every one of these is a recommendation.** The
page attributes its latency distribution to "Digital Applied production MCP
observability, Q2 2026" and publishes no underlying data, so the figures are not
verifiable and should not be repeated as though they were measured. Do not put
these numbers on a slide.

**It also gets a borrowed number wrong.** It presents burn-rate alerting as
14.4x paging and 6x ticketing. Google's own table, verbatim source
https://sre.google/workbook/alerting-on-slos/ (read 2026-09-21,
**[PEER-REVIEWED]**-adjacent, the SRE Workbook), Table 5-8 for a 99.9% SLO:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|---|---|---|---|---|
| Page | 1 hour | 5 minutes | 14.4 | 2% |
| Page | 6 hours | 30 minutes | 6 | 5% |
| Ticket | 3 days | 6 hours | 1 | 10% |

6x is a page in the original, not a ticket. Cite Google directly.

**No operator of an MCP server or gateway publishes an SLO.** Checked across the
gateway and registry documentation surveyed for `bestpractice/` §2 and §5, and
re-checked 2026-09-21 for the official registry (§3.4). **[MEASURED]** absence.

### 8.2 What a sensible objective looks like

Assembled from the evidence in this file. Labeled as construction, not as
published guidance.

**Define the SLI at the MCP boundary, not end to end.** The one genuinely useful
structural point in the vendor framework: build the SLO around "MCP round-trip
plus handler, not end-to-end, otherwise you are committing to a number partially
owned by Anthropic or OpenAI's backbone." An MCP server cannot be accountable
for inference latency it does not control.

**Three SLIs, and the third is the one that is usually missing.**

1. **Availability.** Fraction of `server/discover` probes that return a valid
   result inside a deadline, from at least two locations. Not HTTP 200 rate.
2. **Latency.** P95 of `tools/call` measured from request receipt to result
   emission, per tool. Per tool matters because a server-wide aggregate is
   dominated by whichever tool is called most, and that is rarely the one that
   breaks.
3. **Functional success.** Fraction of `tools/call` results with
   `isError` absent or false, per tool. **A server can hold 100% on SLI 1 and 2
   while SLI 3 is zero.** That is the trap in §7 expressed as a measurement, and
   it is the reason a two-SLI setup is worse than useless here: it reports green
   during a total functional outage.

**Tail latency is the number that matters, and more than usual.** The reason is
specific to this caller. An agent makes many sequential tool calls per task, so
tail latency compounds along the trajectory rather than affecting one request in
twenty. The vendor framework's phrasing of this is correct: "Agents make
hundreds of tool calls per session, a P99 in the seconds is a session in the
minutes." This is the same observation Amelin makes about cost from the other
direction, already in `06-research-and-source-ledger/ops/` §2.5: "A protocol that is cheap per request
and expensive per hour benchmarks very well and behaves differently in
production." Latency and cost have the same per-trajectory accounting problem.

### 8.3 How a non-deterministic caller changes error budget thinking

This is the genuinely new part of SLO design for tool calls, and four things
change.

**1. The caller manufactures its own load from your errors.** A human who gets
an error stops. An agent that gets a retryable-looking error retries, "often
three to five times" per the vendor framework, so one user request becomes five
tool calls of which four are failures. The error budget is consumed faster than
the underlying fault rate would suggest, and the burn-rate alert fires sooner,
which is arguably correct because the cost is real. But it means **your measured
error rate is a function of your callers' retry policies, which you do not
control and cannot see.** No published SLO methodology addresses this.

**2. The error budget is denominated in two currencies.** A failed tool call
spends availability budget and token budget at the same time (§5.1: 32,000
tokens to achieve nothing). Two different teams own those budgets and they are
rarely in the same conversation. An error budget policy that only governs
deployment risk is measuring half the spend.

**3. Error messages are an interface to the caller, and therefore part of the
SLO.** The spec is explicit that tool execution errors "contain actionable
feedback that language models can use to self-correct and retry with adjusted
parameters" (`bestpractice/` §5.5). So an error message that tells the model the
input was malformed converts a failure into a successful second attempt, and one
that says "an error occurred" converts it into a retry storm. **The quality of
the error string is a reliability control.** That is not true of an HTTP API
consumed by code, and it is why `06-research-and-source-ledger/ops/` §4.8 lists error messages as
prompts under mitigations. Restated here as an SLO input rather than a token
optimization.

**4. Partial success is normal and unmeasured.** A trajectory where 8 of 10 tool
calls succeed and the task completes is a success by every per-call SLI and may
be a failure to the user, or the reverse. No published methodology found
measures MCP reliability per trajectory rather than per call. **[MEASURED]**
absence. This is the single largest open question in the pillar, and it is the
one the Enterprise IG's problem-statement mandate is shaped to collect.

---

## 9. Version skew as a reliability problem

`bestpractice/` §8.3 treats version skew as a compatibility matrix and a
migration concern. The reframe this file adds is that **in a mixed fleet, skew
is an availability problem with no protocol-level detection**, and it has
already produced at least one outage shape.

**The mechanism.** R1 is skew presenting as a health check failure: a gateway
built against the old protocol probes with a method the new protocol removed,
and disables every server that upgraded. Nothing in that chain is broken. The
gateway is correct for its era, the server is correct for its era, and the
composition is an outage. Thirty seconds, at a 10-second probe interval, with a
threshold of three.

**Why it is hard to see coming.** Three properties compound:

1. **The wrong-answer mode is silent.** The Modern-to-Legacy row of the
   compatibility matrix includes "process an era-ambiguous method under legacy
   semantics", which is a wrong answer rather than an error
   (`bestpractice/` §8.3, **[OFFICIAL]**).
2. **Era is cached per origin.** Clients SHOULD cache era for the lifetime of
   the server process or origin and MAY persist across restarts. A backend
   upgraded in place behind a shared hostname keeps being addressed under the
   stale assumption until something fails (R10).
3. **Deprecated features keep working.** Roots, Sampling and Logging remain
   "fully functional during the deprecation window", under a policy with a
   minimum twelve-month window. Source:
   https://modelcontextprotocol.io/specification/2026-07-28/changelog , read
   2026-09-21, **[OFFICIAL]**. So nothing surfaces the clock, which
   `bestpractice/` §3.6 already names.

**The live example in gateway documentation.** `bestpractice/` §8.3 records
Agent Router documenting "Last-Event-ID support for SSE streams" and
"persistent connections per June 2025 MCP spec" as of 2026-09-18, which are
mechanics the current revision removed. R1 is that same divergence, in a
different project, actually firing.

**What to do about it, since nothing in the protocol helps.**

- **Make the era an explicit, monitored attribute of every backend.** The
  `MCP-Protocol-Version` header and the `server/discover` response both carry
  it. Emit it as a metric dimension. A fleet whose era distribution is not on a
  dashboard cannot tell an upgrade from an outage.
- **Re-probe on error rather than trusting the cache.** The versioning page's
  own escape hatch, "re-probing if the cached assumption later fails"
  (**[OFFICIAL]**), is the mitigation for R10 and a gateway must implement it.
- **Never let a health check classify an unknown method as unhealthy.** The
  generalization of the R1 fix. A peer that answers *anything* well-formed is
  alive.
- **Treat the era rollout as a deployment with a rollback plan.**
  Because §3.2 of the deployment research establishes that the dual-era window
  has neither the old guarantees nor the new benefit, the window is the risky
  period and it should be as short as the client fleet allows.

---

## 10. Open gaps

Stated as gaps because an absence of published evidence is a finding. Each is
something this room could close.

1. **No gateway deployment patterns document.** Enterprise IG deliverable,
   Planned, Q3 2026, champion TBD, unpublished as of 2026-09-21 with nine days
   of Q3 remaining. **[OFFICIAL]**, re-verified.
2. **No Gateways IG charter.** Two chartered groups route gateway questions to
   it. `/community/interest-groups/gateways` returned 404 on 2026-09-18 per
   `bestpractice/` §3.6 and the charter list is unchanged on 2026-09-21.
3. **No idempotency convention anywhere.** Core has none, the Tasks extension
   protects only after handle creation, and the only pattern in the wild is a
   per-server `job_id` invention that no gateway can enforce and no registry can
   describe (§5.3). This is the most consequential gap in the file.
4. **No published SLO from any MCP operator.** Not from the official registry,
   not from any gateway project, not from any hosted server. The only SLO
   framework found is vendor content marketing whose numbers are unverifiable
   (§8.1).
5. **No capacity number for any MCP gateway.** One independent server benchmark
   exists (§4.2). Nothing for the gateway tier, nothing for MRTR, nothing for
   `subscriptions/listen`.
6. **No reliability measurement per trajectory.** Everything published measures
   per call. The unit of work an agent performs is a trajectory, and a
   per-call SLI cannot express partial success (§8.3).
7. **Circuit breaking is absent from the two most visible open-source
   gateways**, one by explicit decision (#301 closed as not planned) and one
   still in review (§6.1, §3.3).
8. **No guidance on timeouts, retries or unavailability in the official client
   best practices page.** Read in full 2026-09-21 (§6.2). The page is excellent
   on token economics and silent on failure.
9. **The `ping` removal has no published migration note for operators.** The
   changelog records it as one clause of major change 5. No page found explains
   what to probe with instead, and R1 is the cost of that (§1, §7.2).
10. **Gateway capacity for discovery traffic is unbudgeted.** R3 shows
    session-start fan-out tripping provider limits with per-process backoff that
    does not compose. No gateway documents a shared discovery budget (§6.4).

---

## 11. Verification ledger

Everything below was read on 2026-09-21 unless a different date is given.

| Claim | Source | Label | Status |
|---|---|---|---|
| `ping`, `logging/setLevel`, `notifications/roots/list_changed` removed in 2026-07-28 | modelcontextprotocol.io/specification/2026-07-28/changelog | OFFICIAL | Verified verbatim |
| Servers MUST implement `server/discover` | same changelog, major change 3 | OFFICIAL | Verified verbatim |
| `ttlMs` and `cacheScope` required on `server/discover` and list results | same changelog, minor change 5 | OFFICIAL | Verified verbatim |
| Gateway disabling compliant backends over `ping` `-32601` | MikkoParkkola/mcp-gateway#567, 2026-09-18 | PRACTITIONER | Verified, closed |
| ContextForge declined retry-with-backoff | IBM/mcp-context-forge#258 | PRACTITIONER | Verified, closed as not planned |
| ContextForge declined three-state circuit breakers | IBM/mcp-context-forge#301 | PRACTITIONER | Verified, closed as not planned |
| agentgateway has passive health checks only | agentgateway/agentgateway#3352 | PRACTITIONER | Verified, PR still open |
| Registry not intended for direct host consumption; hourly aggregator pulls; preview with possible data resets | modelcontextprotocol.io/registry/about | OFFICIAL | Verified verbatim |
| No published SLA or SLO for the official registry | registry.modelcontextprotocol.io/docs, modelcontextprotocol.io/registry/about | OFFICIAL | Verified absence |
| 10,716 registry endpoints probed; 1,044 404, 446 DNS, 236 5xx, 160 timeout, 107 TLS | The Ops Log, dev.to, 2026-07-30 rev 2026-08-24 | MEASURED, PRACTITIONER | Verified via extraction; 734 endpoints unaccounted, see §3.4 |
| 15 MCP implementations, 50 VUs, 39.9M requests, Rust 4,845 RPS to Python 259 RPS | tmdevlab.com benchmark v2, 2026-02-28 | MEASURED, PRACTITIONER | Verified |
| Quarkus default pool caused 0 RPS; 1000 restored 4,739 RPS | same | MEASURED | Verified |
| JS SDK per-request instantiation floor of 5-10 ms | same | MEASURED | Verified |
| AWS Knowledge MCP about 1 req/15s per IP; handshake fails | awslabs/mcp#2949, 2026-04-10 | MEASURED | Verified, closed |
| 90 session startups, 2,021 connects, 69 429s before any tool call | btsouth/toolport#874, 2026-09-14 | MEASURED | Verified, open |
| Stalled tool call, cancel ineffective for 65s | strands-agents/harness-sdk#4403, 2026-09-19 | PRACTITIONER | Verified, open |
| 27.8 KB served, 56 KB kills the server | stack-chan#712, 2026-09-17 | MEASURED | Verified, open; embedded device, see §5.4 |
| Silent MCP startup failure, no error shown | anthropics/claude-code#25751, 2026-02-14 | PRACTITIONER | Verified, closed as duplicate |
| "No servers configured" for slow-starting stdio servers | anthropics/claude-code#29033 | PRACTITIONER | **UNVERIFIED** beyond the title; body not read |
| 3^5 = 243 retries; $2 to $0.01 with breaking; 32,000 tokens wasted | tianpan.co, 2026-04-10 | PRACTITIONER | Verified; 243 is modeled, dollars are one unmethodized measurement |
| Tasks gives durable handles; no idempotency or deduplication specified | modelcontextprotocol.io/extensions/tasks/overview | OFFICIAL | Verified; resolves an UNVERIFIED in `bestpractice/` §3.1 |
| Tasks client support varies by host | modelcontextprotocol.io/extensions/client-matrix | OFFICIAL | **UNVERIFIED**; matrix not read |
| Client best practices page has no timeout, retry or unavailability guidance | modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices | OFFICIAL | Verified by reading the page in full |
| "the model is responsible for reporting any partial side effects already committed" | same | OFFICIAL | Verified verbatim |
| "Treat server disconnection as a conversation-boundary operation" | same | OFFICIAL | Verified verbatim |
| Gateway Deployment Patterns Document still Planned, Q3 2026, champion TBD | modelcontextprotocol.io/community/interest-groups/enterprise | OFFICIAL | Re-verified 2026-09-21 |
| Google burn rates: 14.4/1h/5m page, 6/6h/30m page, 1/3d/6h ticket | sre.google/workbook/alerting-on-slos, Table 5-8 | SRE Workbook | Verified; corrects the vendor framework |
| Proposed MCP SLO targets (99.5%, P95 620 ms, 99% success) | digitalapplied.com, 2026-05-15 | VENDOR | Verified as published; **numbers are recommendations, not measurements. Do not use on a slide** |
| Liveness vs readiness split, separate HTTP endpoints, concrete intervals | agentcat.com health check guide | VENDOR | Verified as published; **UNVERIFIED** publication date |
| KEDA `concurrentRequests: 100`, min 2 / max 30, about 3,200 RPS peak, P95 120 ms | dev.to, kirandeepjassalcrypto, 2026-07-29 | PRACTITIONER | Date confirmed via dev.to API; the three operating figures carry no stated methodology |
| ARR affinity restricts scaling; set `clientAffinityEnabled: false` | learn.microsoft.com App Service automatic scaling | VENDOR | Verified |
| "a 502 from one instance is retryable against the pool without re-handshaking"; `job_id` pattern | bex.co, Dora Noda, 2026-09-09 | PRACTITIONER | Verified |
| Microsoft Locust post: 2,293 requests, three failures, 16 VUs, 2026-07-12 | techcommunity.microsoft.com blog 4522691 | VENDOR | **UNVERIFIED**; post could not be retrieved in full across two attempts. Read directly before use |
| C# Corner load-balancer benchmark figures | c-sharpcorner.com, Aarav Patel, 2026-08-11 | PRACTITIONER | Verified that the author disclaims his own numbers. Cite the method only |
| Ordering of what saturates first | this file | INFERENCE | Not published anywhere; reasoning stated in §4.3 |
| Keep advertising a tool whose backend is down, answer with `isError` | this file | INFERENCE | Derived from the spec error model plus prompt-cache behavior, §6.3 |
| Bypass the cache when probing with `server/discover` | this file | INFERENCE | Derived from SEP-2549, §7.2 rule 3 |
