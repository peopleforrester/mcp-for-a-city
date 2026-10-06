---
title: "MCP Operations at Scale: What Actually Breaks"
date: 2026-09-17
sources_verified_on: 2026-09-17
status: draft
audience: "MCP maintainers and enterprise platform engineers, MCP Dev Summit Toronto 2026-10-06"
---

<!-- ABOUTME: What actually breaks when MCP runs at scale: failure modes, practitioner accounts, measured numbers and mitigations. -->
<!-- ABOUTME: Includes the widely repeated figures that do not survive being traced to their sources. -->

# MCP Operations at Scale: What Actually Breaks

> **Note added 2026-10-06, on publication:** The registry counts here are superseded by the dated recount in "Counting the MCP Ecosystem" (ecosystem/registry-count-verification.md).

Research for "Governing MCP for a Workforce the Size of a City".

## How to read the sourcing

Every claim below carries one of these labels. Nothing is stated from memory.

| Label | Meaning |
|---|---|
| **[PRIMARY]** | First-hand account by the people who built or ran the thing, or the spec itself |
| **[MEASURED-HERE]** | Measured by this research on 2026-09-17, command shown |
| **[PEER]** | Peer-reviewed or arXiv preprint with a stated method |
| **[VENDOR]** | Vendor marketing. Treat the numbers as a floor for scepticism, not evidence |
| **[SECONDHAND]** | A figure reported by someone who did not measure it. Chased to origin where possible |
| **[UNVERIFIED]** | Could not be traced to a source that actually makes the claim |

A dedicated section at the end, **Numbers that are wrong in the wild**, documents three widely repeated figures that do not survive contact with their sources. That section is probably the most useful thing here for a maintainer audience, because those numbers are in everyone's slides.

---

## 1. Failure modes table

Ordered by how often a practitioner account names them, not by severity.

| # | Failure mode | What it looks like in production | Evidence | Label |
|---|---|---|---|---|
| F1 | **Tool-definition context tax** | Definitions for connected servers consume the context window before the user's first message. Five servers (GitHub, Slack, Sentry, Grafana, Splunk) = ~55,000 tokens of definitions | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| F2 | **Tool-selection degradation with pool size** | Retrieval success above 90% for the first ~30 candidate tools, materially degraded beyond ~100, across a pool scaled to 11,100 | RAG-MCP, arXiv 2505.03275 | [PEER] |
| F3 | **Schema breaking changes break hardcoded callers** | Renaming one parameter (`question` to `query`) broke 2 to 5% of requests until both names were supported through a deprecation window | Microsoft Learn MCP team, 2026-02-11 | [PRIMARY] |
| F4 | **Silent resumability regression** | Spec 2026-07-28 removed `Last-Event-ID` and SSE event IDs. A broken response stream loses the in-flight request and the client MUST re-issue it with a new request ID. The regression is silent in the sense that upgrading surfaces no warning that redelivery is gone | MCP spec changelog 2026-07-28; WorkOS 2026-09-16 | [PRIMARY] |
| F5 | **Duplicated side effects on retry** | Because the transport no longer redelivers, a client retry of a lost request re-runs the tool. For a tool that charges a card or provisions infrastructure, that is a double execution. Idempotency is now application-level | WorkOS, 2026-09-16 | [PRIMARY-adjacent] |
| F6 | **Progressive discovery invalidates the prompt cache** | The fix for F1 can cost more than F1. Adding or removing tool definitions mid-conversation invalidates the cached prompt prefix, and the resulting miss can exceed the tokens saved | MCP client best practices, 2026-07-28 | [PRIMARY] |
| F7 | **Non-deterministic `tools/list` ordering** | Servers returning tools in varying order defeat client-side caching and prompt-cache hits. The spec now says servers SHOULD return a deterministic order, which is an admission this was happening | MCP spec changelog 2026-07-28, minor change 3 | [PRIMARY] |
| F8 | **Version skew between clients and servers** | Results from earlier-protocol servers omit the new required `resultType` field. Clients MUST treat those as `"complete"`. Every client has to carry this compatibility branch | MCP spec changelog 2026-07-28, major change 8 | [PRIMARY] |
| F9 | **Session affinity and sticky routing** | Under pre-2026-07-28 protocol a session lived on whichever instance issued it, forcing sticky routing or an external session store, with instance loss destroying in-flight sessions | AWS Architecture Blog, 2026-09-01 | [PRIMARY] |
| F10 | **Long-running calls hit layered idle timeouts** | Long-lived `subscriptions/listen` streams die at whichever of load balancer, proxy, or compute tier has the shortest idle timeout. The three are usually configured by three different teams | AWS Architecture Blog, 2026-09-01 | [PRIMARY] |
| F11 | **Retry storms amplify a degraded server** | Slow or overloaded instances cause queue buildup and request timeouts; user retry storms then amplify load. Agents retry more eagerly than humans | pgEdge, 2026-02-05 | [PRIMARY] |
| F12 | **stdio process death is a closed pipe** | "When the tool process crashes, the pipe closes." No transport-level recovery, state lost on restart, long-running work at risk of duplication | pgEdge, 2026-02-05 | [PRIMARY] |
| F13 | **Tool errors are successful responses** | MCP tool errors arrive as an HTTP-successful response with `isError: true`, not a transport failure. Monitoring that alerts on 5xx sees a perfectly healthy server while every call fails | MCP client best practices, 2026-07-28 | [PRIMARY] |
| F14 | **Unstructured output forces guesswork** | When a server omits `outputSchema`, the host either accepts `any` or routes the value through a small model to coerce it, which "can hallucinate or drop fields" | MCP client best practices, 2026-07-28 | [PRIMARY] |
| F15 | **Cache scope misconfiguration leaks tenant data** | The new `cacheScope` field (`"public"` / `"private"`) governs whether shared intermediaries may cache a result. Getting it wrong is tenant-data disclosure through a CDN | AWS Architecture Blog, 2026-09-01; spec minor change 5 | [PRIMARY] |
| F16 | **Non-adoption by non-technical staff** | Non-technical teams could not install servers, did not understand API key management, and could not find the tool they needed. This is a deployment failure, not a protocol one, and it is the one that kills rollouts | Block, via All Things Open 2025-12-02 | [SECONDHAND] |
| F17 | **Shadow servers with no inventory** | "Ask your security team how many MCP servers are running across your organization right now. If they cannot answer with confidence, you have a governance problem that is already in production" | TrueFoundry, 2026-09-11 | [VENDOR] |
| F18 | **Publicly exposed servers with no auth** | An internet-wide scan found 1,862 MCP servers exposed publicly; all 119 sampled listed their tools to anyone who asked, without credentials | Knostic scan, July 2025, via Maxim AI | [SECONDHAND] |
| F19 | **Registry entries are self-reported** | The official registry is where "maintainers publish and maintain their self-reported information." Nothing in the registry is attested by a third party | MCP blog, 2025-09-08 | [PRIMARY] |
| F20 | **Trajectory cost, not request cost** | "A protocol that is cheap per request and expensive per hour benchmarks very well and behaves differently in production" | Artemii Amelin, 2026-09-01 | [PRIMARY] |

---

## 2. Practitioner accounts

### 2.1 Block: 12,000 employees, 60+ to 100+ internal servers

Two primary sources, plus one secondary with larger numbers. The numbers differ by date, so both are given rather than picking one.

**[PRIMARY]** Angie Jones, VP Engineering AI Tools and Enablement, Block, 2025-04-22.
<https://dev.to/blockopensource/mcp-in-the-enterprise-real-world-adoption-at-block-ci5>

What they deployed: Snowflake, GitHub, Jira, Slack, Google Drive, and internal API servers for compliance checks and support triage. All internal MCP servers were authored by Block's own engineers. OAuth for token distribution with storage in native system keychains. LLM allowlists on some servers. Restricted tool-output sharing across systems. Designated sensitive data categories prohibited from Goose entirely.

The adoption lever they name is friction removal, not capability: adoption accelerated when "we made it to start - by pre-installing Goose, bundling MCPs, and auto-configuring models."

Note the gap honestly: this post names no operational failures. It is an adoption story.

**[PRIMARY]** Salman Mohammed and Kalvin Chau, Block engineering, 2025-06-16.
<https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers>

This is the more useful one for a maintainer audience because it is a design retrospective across 60+ internal servers.

The single most concrete finding is the Linear server's evolution: **30+ individual tools, then grouped tools, then two comprehensive tools that accept GraphQL queries directly.** That is a team walking the entire tool-sprawl arc internally and landing on "give the model a query language, not an endpoint per verb."

Their stated core principle: "Design top-down from workflows, not bottom-up from API endpoints."

On why naming matters operationally: "Tool names, descriptions, and parameters are treated as prompts for the LLM, so it's really important to have clear instructions."

They enforce a hard output guard: files over 400kB raise a tool execution error, to stop a single read from blowing the context window.

**[SECONDHAND]** All Things Open, 2025-12-02.
<https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions>

Reports 12,000 employees, 15 job functions, 100+ internal MCP servers, two months to enterprise-wide rollout, 75% of engineers within one month saving 8 to 10 hours weekly, and 80,000 sales leads analysed in an hour. Treat the productivity figures as company-reported.

What it adds that the Block posts do not: the named adoption failures. Non-technical teams could not install servers. Employees did not understand API key management. Users could not locate the tool they needed. Their mitigations were auto-installation through an internal software centre, OAuth via the identity provider, and **dynamic context management that enables and disables servers per user query** (which is the same pattern the spec now calls dynamic server management).

The 60+ versus 100+ discrepancy is most likely seven months of growth, not an error. Cite the dated figure you need.

### 2.2 Microsoft Learn MCP Server: the schema-break number

**[PRIMARY]** Tianqi Zhang, Eric Imasogie, Pieter de Bruin, Engineering@Microsoft, 2026-02-11.
<https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/>

This is the most quotable single sentence in the entire corpus for the breaking-changes section:

> "When we renamed a parameter from question to query, 2–5% of requests broke until we supported both names (optional) during a deprecation window."

A parameter rename. Not a removal, not a semantic change. 2 to 5% of traffic.

Their conclusion generalises the lesson: **"Defensive evolution is part of operating a public service."** Despite MCP's dynamic discovery model, expect hardcoded callers.

Design decisions worth noting: three tools only (`microsoft_docs_search`, `microsoft_docs_fetch`, `microsoft_code_sample_search`), deliberately collapsing an underlying service with topK, index selection, thresholds, OData filters, and vector-versus-hybrid search into search-and-fetch. Their principle: "Design tools for the agent workflow, not to mirror internal APIs."

They also report that tool descriptions materially affect activation rates, and that remote servers demand multi-region stateless distributed-systems practice rather than web-service practice.

### 2.3 The MCP maintainers on tool sprawl

**[PRIMARY]** David Soria Parra and Den Delimarsky, lead maintainers, 2026-08-22.
<https://blog.modelcontextprotocol.io/posts/mcp-roadmap/>

The line that will land hardest in a maintainer room, because it is their own maintainers saying it:

> "A server with a hundred tools means the model pays for that entire surface before the user has asked a single question"


> **MISQUOTE, corrected by the parent session 2026-09-18.** The sentence above drops the opening clause and changes the subject. The verified original, from https://blog.modelcontextprotocol.io/posts/mcp-roadmap/ (David Soria Parra and Den Delimarsky, 2026-08-22), reads: "Connecting to a server with a hundred tools means the model pays for that entire surface before the user has asked a single question, and tool selection tends to get worse as the list grows." Use the full sentence or do not quote it.

And: "tool selection tends to get worse as the list grows."

On the identity problem underneath enterprise governance:

> "More and more of the callers are agents running as cloud workloads with their own identity, acting on behalf of a user who isn't present"

They name the direction as DPoP and Workload Identity Federation, moving off "pasted API keys and long-lived tokens." The Server Card Working Group is building `.well-known` metadata conventions so "a server can be discovered and reasoned over without connecting to it," which is the registry-scale answer to F19.

### 2.4 The 2026-07-28 spec as an operational event

**[PRIMARY]** Spec changelog: <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
**[PRIMARY]** Release post, 2026-07-28: <https://blog.modelcontextprotocol.io/posts/2026-07-28/>

Nine major changes. The ones that are operations problems rather than API problems:

1. **Protocol-level sessions and `Mcp-Session-Id` removed.** Servers needing cross-call state now use "explicit, server-minted handles passed as ordinary tool arguments." State moved from the transport into the tool arguments, which means into the context window.
2. **The `initialize`/`notifications/initialized` handshake removed.** Every request carries its protocol version and client capabilities in `_meta`.
3. **`server/discover` added**, which servers MUST implement.
4. **SSE stream resumability and message redelivery removed.** "A broken response stream loses the in-flight request; clients MUST re-issue it as a new request with a new request ID."
5. **`ping`, `logging/setLevel`, `notifications/roots/list_changed` removed.**
6. **Roots, Sampling, and Logging deprecated**, with suggested migrations: tool parameters or resource URIs instead of Roots, direct LLM provider APIs instead of Sampling, stderr or OpenTelemetry instead of Logging.

The maintainers' stated rationale: "any request can now land on any server instance behind a plain round-robin load balancer without needing shared storage," addressing "one of the most highly-requested features from developers who were eager to get better reliability and scalability."

They acknowledge the cost: "there will be some migration cost, especially for developers that did depend on session identifiers."

**The governance response is the underrated part.** The same release adopted a feature lifecycle policy with a **minimum twelve-month deprecation window** and a registry of deprecated features, so that "you can plan upgrades instead of reacting to them." Roots, Sampling and Logging "still work, and they'll keep working for at least twelve months." HTTP+SSE got "a year-long offramp." For an enterprise platform team, a published deprecation window is worth more than any individual protocol feature, because it is the thing you can put in a rollout plan.

Two minor changes that are pure operations wins and easy to miss:

- **OpenTelemetry trace context propagation** conventions for `_meta` keys (`traceparent`, `tracestate`, `baggage`), SEP-414. Distributed tracing across an agent-to-server call chain is now conventional rather than bespoke.
- **`ttlMs` and `cacheScope` required** on list and read results via a `CacheableResult` interface, SEP-2549. Caching is now in the protocol rather than in each gateway.

### 2.5 The dissent: stateless is not free

**[PRIMARY, practitioner opinion]** Artemii Amelin, 2026-09-01.
<https://dev.to/artem_a/mcp-2026-07-28-deleted-the-session-the-state-moved-into-your-context-window-1hde>

The most quotable critique, and the one that reframes the whole stateless debate for an operations audience:

> "A protocol that is cheap per request and expensive per hour benchmarks very well and behaves differently in production."

His argument: "Connection state has become context-window state. It costs tokens on every turn it survives, it competes with everything else in the window." And on resumability: "For a thirty second retrieval over a flaky mobile link, the work is thrown away and repeated from zero."

He summarises the accounting as: "If handles accumulate in context and every dropped connection replays a slow tool call, the win at the HTTP layer is being financed somewhere harder to see."

This is not a claim that the spec is wrong. He positions the tradeoffs as deliberate. It is a claim that the bill moved from the infrastructure budget to the token budget, and that the two are owned by different people.

**[PRIMARY]** WorkOS, Maria Paktiti, 2026-09-16.
<https://workos.com/blog/mcp-stateless-spec-2026-07-28>

The same concern stated as a reliability issue:

> "Stream resumability was removed, and nothing will tell you."

> "For a tool that charges a card, sends an email, or provisions something, a lost request that the client then retries is a duplicated side effect."

She also flags the elicitation redesign as "an architectural inversion, not a rename": the callback model became a retry loop, so code targeting the 2025-11-25 design needs rework rather than migration.

### 2.6 AWS: what stateless actually buys you

**[PRIMARY]** Anand Komandooru, Steven DeVries, Haleh Najafzadeh, AWS Architecture Blog, 2026-09-01.
<https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/>

The honest version of the savings, from the vendor who sells the infrastructure being deleted: "A two-node Amazon ElastiCache (cache.t4g.micro) session store is about $23/month." They immediately add that "the larger saving is eliminating an entire class of infrastructure and the operational burden around it."

$23 a month is a rounding error. Quote it precisely because it is small: the argument for stateless was never the session store bill, it was the on-call surface.

Their operational checklist items worth carrying into a talk: check idle timeouts across load balancer, proxy, and compute tier for `subscriptions/listen` streams; Multi Round-Trip Requests mean "no instance holds a connection open for client input," which is what makes Lambda viable.

Named failure modes: instance loss during stateful sessions, broken response streams requiring manual re-issue, uneven load distribution from sticky routing, tenant-data disclosure through misconfigured cache scope, and UI template injection via MCP Apps.

### 2.7 pgEdge: transport failure modes

**[PRIMARY]** Ibrar Ahmed, pgEdge, 2026-02-05.
<https://www.pgedge.com/blog/mcp-transport-architecture-boundaries-and-failure-modes>

The clearest enumeration of transport-level failure. For stdio: "When the tool process crashes, the pipe closes," with memory loss on restart and long-running work at risk of duplication. For HTTP with SSE: DNS failures, stale endpoints, load balancers routing to unhealthy instances, and "Slow or overloaded instances can lead to queue buildup and request timeouts. User retry storms can amplify load and make a bad situation worse."

For TLS specifically: certificate expiry, version mismatches, cipher misconfiguration, and clock skew breaking validity checks. Unglamorous, and the reason a server that worked for six months stops on a Tuesday.

His concrete timeout numbers, stated for a Postgres-backed server and offered as a starting point rather than a universal: connection timeout around 600 seconds, idle session timeout 300 seconds, hard request timeout 30 seconds as a baseline. He also recommends a backpressure policy and per-call timeouts **even on a pipe**, plus a concurrency cap on tool calls, which is the stdio-specific advice most implementations skip.

### 2.8 Honeycomb: agents are already a fifth of the traffic

**[SECONDHAND, attributed in a primary post]** Cited by the MCP maintainers in the 2026-07-28 release post: Honeycomb.io reports that "nearly 20% of all monthly interactive queries are now made by agents."

This is the single best statistic for establishing that this is a production capacity-planning problem and not a pilot. Flagged secondhand because the underlying Honeycomb post was not reachable during this research; the attribution is in the maintainers' own release note.

---

## 3. Measured numbers

### 3.1 Context consumption by tool definitions

| Measurement | Figure | Source | Label |
|---|---|---|---|
| Five-server setup (GitHub, Slack, Sentry, Grafana, Splunk), tool definitions only | ~55,000 tokens | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Traditional upfront loading, before any work begins | ~77,000 tokens | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Same workload with Tool Search Tool | ~8,700 tokens (85% reduction) | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Context left for work: traditional vs Tool Search | 122,800 vs 191,300 tokens | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Google Drive to Salesforce workflow, direct tool calls vs code execution | 150,000 to 2,000 tokens (98.7%) | Anthropic engineering, 2025-11-04 | [PRIMARY] |
| Complex research tasks, programmatic tool calling | 43,588 to 27,297 tokens (37%) | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| GitHub MCP server (35 tools) | ~26,000 tokens | Stephanie Goodman, AgentPMT, 2026-02-27 | [SECONDHAND] |
| Slack MCP server (11 tools) | ~21,000 tokens | Stephanie Goodman, AgentPMT, 2026-02-27 | [SECONDHAND] |
| Three-server combo (GitHub, Playwright, IDE) | ~143,000 tokens of a 200k window (72%) | Stephanie Goodman, AgentPMT, 2026-02-27 | [SECONDHAND] |
| Tool-use system prompt overhead, Claude Opus 5 | 286 tokens (`auto`/`none`), 406 tokens (`any`/`tool`) | Anthropic pricing docs, retrieved 2026-09-17 | [PRIMARY] |
| Default tool-response cap in Claude Code | 25,000 tokens | Anthropic engineering, 2025-09-11 | [PRIMARY] |

Sources: <https://www.anthropic.com/engineering/advanced-tool-use>, <https://www.anthropic.com/engineering/code-execution-with-mcp>, <https://www.anthropic.com/engineering/writing-tools-for-agents>, <https://platform.claude.com/docs/en/about-claude/pricing>, <https://www.agentpmt.com/articles/thousands-of-mcp-tools-zero-context-left-the-bloat-tax-breaking-ai-agents>

### 3.2 Accuracy versus tool count

| Measurement | Figure | Source | Label |
|---|---|---|---|
| RAG-MCP retrieval vs naive all-tools-in-prompt baseline, tool selection accuracy | 43.13% vs 13.62% | RAG-MCP, arXiv 2505.03275, 2025-05-06 | [PEER] |
| RAG-MCP stress test, candidate pool range | 1 to 11,100 MCPs | RAG-MCP | [PEER] |
| RAG-MCP stress test, success by candidate position | above 90% for positions 1 to 30; degraded 31 to 70 from semantic overlap; substantial degradation beyond ~100 | RAG-MCP | [PEER] |
| Average prompt tokens: RAG-MCP / actual-match / blank-conditioning baseline | 1,084 / 1,646 / 2,133.84 | RAG-MCP | [PEER] |
| Anthropic MCP evals with Tool Search Tool, Opus 4 | 49% to 74% | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Anthropic MCP evals with Tool Search Tool, Opus 4.5 | 79.5% to 88.1% | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Programmatic tool calling, internal knowledge retrieval | 25.6% to 28.5% | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Programmatic tool calling, GIA benchmark | 46.5% to 51.2% | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| Tool-use examples, complex parameter handling | 72% to 90% | Anthropic engineering, 2025-11-24 | [PRIMARY] |
| MCP-Universe, real MCP servers, GPT-5 success rate | 43.72% | arXiv 2508.14704, 2025-08-20 | [PEER] |
| MCP-Universe, Grok-4 | 33.33% | arXiv 2508.14704 | [PEER] |
| MCP-Universe, Claude-4.0-Sonnet | 29.44% | arXiv 2508.14704 | [PEER] |
| MCPToolBench++ underlying marketplace size | 4,000+ MCP servers, 40+ categories, as of July 2025 | arXiv 2508.07575, 2025-08-11 | [PEER] |

**The MCP-Universe numbers are the ones to put on a slide.** Best frontier model, real MCP servers, 43.72%. Their stated reasons are exactly the two problems this talk is about: "the number of input tokens increases rapidly with the number of interaction steps," and "LLM agents often lack familiarity with the precise usage of the MCP servers." They also note that "Enterprise-level agents like Cursor cannot achieve better performance than standard ReAct frameworks," which is a useful corrective to buying your way out of this.

Sources: <https://arxiv.org/abs/2505.03275>, <https://arxiv.org/abs/2508.14704>, <https://arxiv.org/abs/2508.07575>

### 3.3 Adoption and ecosystem size

| Measurement | Figure | As of | Source | Label |
|---|---|---|---|---|
| Official MCP registry, published server-version records | **28,000+ (lower bound, crawl incomplete)** | 2026-09-17 | registry API, see method below | [MEASURED-HERE] |
| Official MCP registry, distinct server names | **2,660 in the first 7,500 records**; ~10,000 estimated | 2026-09-17 | registry API, see method below | [MEASURED-HERE] |
| Glama open-source MCP server directory | 88,809 | 2026-09-17 17:02 UTC | <https://glama.ai/mcp/servers> | [PRIMARY, directory self-report] |
| PulseMCP directory | 21,880 | 2026-09-17 | <https://www.pulsemcp.com/servers> | [PRIMARY, directory self-report] |
| MCP SDK downloads per month, Tier 1 SDKs | "close to half-a-billion downloads a month" | 2026-07-28 | MCP maintainers | [PRIMARY] |
| TypeScript and Python SDK lifetime downloads | each crossed 1 billion | 2026-07-28 | MCP maintainers | [PRIMARY] |
| Honeycomb monthly interactive queries made by agents | nearly 20% | 2026-07-28 | Honeycomb via MCP maintainers | [SECONDHAND] |
| Manufact Cloud hosted MCP servers | "thousands" | 2026-07-28 | MCP maintainers | [PRIMARY, unquantified] |
| Concurrently connected agents | ~250,000 | 2026-09-01 | Artemii Amelin | [UNVERIFIED] |
| Publicly exposed MCP servers found by internet-wide scan | 1,862, all 119 sampled listed tools without credentials | July 2025 | Knostic, via Maxim AI | [SECONDHAND] |

**Use the spread, not a single number.** The honest headline is that "how many MCP servers exist" has no answer, and the three directories disagree by a factor of four on the same day. That dispersion is itself the governance point: an enterprise registry that mirrors "the ecosystem" is mirroring a number nobody agrees on, built from self-reported entries.

The MCP maintainers are explicit that the official registry holds "self-reported information" from maintainers and is designed as an upstream feed for public marketplaces and private enterprise sub-registries, not as an attestation authority. <https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/>

#### [MEASURED-HERE] Counting the official registry, 2026-09-17

Do not quote a registry number without knowing what it counts. This was paginated directly:

```
GET https://registry.modelcontextprotocol.io/v0/servers?limit=100[&cursor=...]
```

**The unit is not what it looks like.** The pagination cursor is of the form `<name>:<version>` (`ac.inference.sh/mcp:1.0.0`, then `:1.0.1`), and each record nests the server under a `server` key. **One record is one published server version, not one server.** A naive crawl that counts records overstates the number of distinct servers, and that is the crawl most people run.

Two crawls were run. Results as of 19:23 UTC+2 on 2026-09-17, with the crawl still paginating when this draft was written, so **both figures are lower bounds, not totals**:

| Quantity | Measured | Note |
|---|---|---|
| Published server-version records | **at least 28,000** | crawl not yet exhausted |
| Distinct server names | **2,660 within the first 7,500 records** | ratio ~2.8 versions per server |

Applying that ratio to the record floor puts the registry on the order of **10,000 distinct servers**, which is an estimate and is labelled as one. Anyone quoting a registry figure should re-run the crawl to completion and state which of the three numbers they mean: version records, distinct servers, or an estimate derived from a ratio.

Set that against the two large public directories counted the same day: PulseMCP at 21,880 and Glama at 88,809. **Three sources, same day, spanning roughly an order of magnitude.** Each is counting something different and none of them is wrong.

The practical consequence for anyone building an enterprise sub-registry: the upstream feed is versioned, so "mirror the registry" means deciding a version policy (latest only, all versions, pinned) before you have counted anything. And because entries are self-reported, the count tells you how many things were published, not how many work.

### 3.4 Cost

Published cost figures for MCP specifically are thin. Most of what circulates is token counts, which are inputs to a cost, not a cost. The arithmetic below is **derived by this research** from two published inputs and is labelled as such.

**Published inputs** (both retrieved 2026-09-17):
- Anthropic's measured five-server tool-definition load: ~55,000 tokens. <https://www.anthropic.com/engineering/advanced-tool-use>
- Claude Opus 5 list price: $5 per million input tokens; cache hits and refreshes $0.50 per million (0.1x); 5-minute cache write $6.25 per million (1.25x). <https://platform.claude.com/docs/en/about-claude/pricing>

**[DERIVED, this research, 2026-09-17]** Cost of carrying that tool surface, per model turn:

| Condition | Arithmetic | Per turn |
|---|---|---|
| Definitions sent uncached every turn | 55,000 x $5 / 1,000,000 | $0.275 |
| Definitions served from prompt cache | 55,000 x $0.50 / 1,000,000 | $0.0275 |

Scaled to a workforce, with assumptions stated so they can be argued with: 10,000 employees, 20 agent turns each per working day, 250 working days, giving 50 million turns per year.

| Condition | Annual, tool definitions alone |
|---|---|
| Uncached | ~$13.75M |
| Fully cached | ~$1.38M |
| Progressive discovery at Anthropic's measured 85% reduction, uncached | ~$2.06M |

These are illustrative, not measured. The assumptions about turns per employee are mine. The point is the shape rather than the figure: **the delta between cached and uncached on a surface nobody chose to load is roughly an order of magnitude**, and prompt caching is the single largest cost lever available before any tool-count work happens.

Which is exactly why F6 matters and why it is the most counter-intuitive finding in this research. From the official client best practices:

> "Most providers cache the prompt prefix, including the `tools` array. Adding or removing tool definitions mid-conversation invalidates that cache, and the resulting miss can cost more tokens than the definitions you removed."

A naive progressive-discovery implementation that mutates the `tools` array per turn can therefore cost more than the sprawl it was built to fix. The documented mitigations are to append new definitions after the cache breakpoint rather than re-sorting the array, to route every call through a single stable `call_tool({name, args})` meta-tool so the array never changes, and to treat server disconnection as a conversation-boundary operation rather than a per-turn one.

**Other published cost data points:**
- Anthropic code execution: 150,000 to 2,000 tokens on one workflow (98.7%). [PRIMARY]
- AIMultiple measured ~7% latency increase per call under code execution (10.37s vs 9.66s), because the agent generates more output tokens of code. Output tokens are 5x input on Opus 5, so a code-execution win on input can be partly eaten on output. [SECONDHAND, via multiple summaries; the AIMultiple original was not read directly]
- Bifrost: 92.8% input-token reduction at 508 tools across 16 MCP servers, and 11 microseconds of gateway overhead per request at 5,000 rps. [VENDOR, Maxim AI]
- AWS: a two-node ElastiCache session store is about $23/month. [PRIMARY]
- Code execution tool billing, for reference when sandboxing MCP calls: 1,550 free container-hours per organisation per month, then $0.05 per hour per container. [PRIMARY, Anthropic pricing]

---

## 4. Mitigations that work

Ordered by how much evidence supports them, strongest first.

### 4.1 Progressive tool discovery (now official)

The spec's own client best practices document this as the primary answer to F1, with a concrete threshold recommendation that is worth quoting because it is unusually specific for a spec document:

> "Implement a threshold as a percentage of the context window. For example, 1%-5%. Load tool definitions. Once the threshold is reached, switch to progressive discovery."

The documented three-layer pattern is catalog (`search_tools` returns names and one-line descriptions), inspect (`get_tool_details` returns one full schema), execute.

Four retrieval strategies are named, with an honest cost note on each: keyword (BM25, regex), embedding, subagent (a small fast model such as Haiku or Gemini Flash, which "usually works very well but can be more costly"), and hybrid. Both OpenAI and Anthropic ship native tool search, and the guidance is to prefer the platform's implementation unless you need access-control-aware ranking, which is precisely the enterprise case.

Measured effect: 85% token reduction and MCP eval accuracy from 79.5% to 88.1% on Opus 4.5. [PRIMARY]

Source: <https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md>

### 4.2 Dynamic server management

The same document extends discovery from tools to whole servers: maintain a registry of available servers with high-level descriptions, connect only when the model determines it needs that server, disconnect when no longer relevant to free context. Agent skills can declare which servers they need so the host connects them on skill invocation.

Block shipped this independently before it was written down, as "dynamic context management enabling/disabling servers by user query." Convergent evolution between a large deployment and the spec is a good sign this one is real.

### 4.3 Programmatic tool calling / code execution

The model writes code against generated typed stubs; the sandbox executes; only `console.log` output returns to the model. Measured 98.7% on one Anthropic workflow, 37% average on complex research tasks. [PRIMARY]

The security properties are the underrated part for an enterprise audience, and the spec is explicit about them: the sandbox has no network access, credentials are held by the host and never exposed to generated code, and per-call authorization still applies because "Approving the script does not grant blanket approval for every tool call it makes at runtime." Tool results from one server are treated as untrusted input to another, and "output truncation alone does not prevent exfiltration."

Named sandbox options with their host languages: Deno and `isolated-vm` for JavaScript, Monty (experimental) for Python, pctx (early-stage) for TypeScript, Wasmtime for anything via Wasm.

Cost caveat: roughly 7% latency increase per call, and code is output tokens at 5x the input rate.

### 4.4 Collapse tools into query interfaces

Block's Linear server went 30+ tools, then grouped tools, then **two tools accepting GraphQL directly**. Microsoft Learn ships three tools over a service with topK, index selection, thresholds, OData filters, and vector-versus-hybrid search.

Both teams independently concluded: design top-down from workflows, not bottom-up from endpoints. This is the cheapest mitigation on the list because it requires no client changes, no sandbox, and no gateway. It requires a server author to say no.

### 4.5 Namespacing

Anthropic's guidance, from running evals on human-written versus optimised Slack and Asana servers: prefix-based (`asana_search`) or suffix-based both work, "Effects vary by LLM," test in your own evals. The payoff is stated as dual: "By selectively implementing tools whose names reflect natural subdivisions of tasks, you simultaneously reduce the number of tools and tool descriptions loaded into the agent's context."

Note the honest bit that vendor content omits: they do not claim a universal winner between prefix and suffix. <https://www.anthropic.com/engineering/writing-tools-for-agents>

### 4.6 Deterministic `tools/list` ordering plus TTL caching

Spec-level, 2026-07-28. Servers SHOULD return tools in deterministic order to enable client-side caching and improve prompt cache hit rates. List and read results carry `ttlMs` and `cacheScope`. Clients should treat a cached list as stale on `list_changed` even before TTL expiry.

This is free money for any server author: sort your tool list.

### 4.7 Output guards

Block: files over 400kB raise a tool execution error. Anthropic: Claude Code caps tool responses at 25,000 tokens by default, and the guidance is pagination, range selection, filtering, and truncation with sensible defaults, plus an optional `ResponseFormat` enum letting the agent request `"concise"` or `"detailed"` (their example: 72 tokens versus 206).

### 4.8 Error messages as prompts

Anthropic: error responses should "clearly communicate specific and actionable improvements, rather than opaque error codes or tracebacks." The generated-wrapper guidance in the spec goes further: convert `isError: true` into a thrown exception so model-authored code can `try`/`catch`, and if an uncaught error kills the script, surface it as the script's result so the model can self-correct.

---

## 5. Measurement, evals, and what "good" looks like

There is no official MCP eval standard. The closest thing to authoritative practitioner guidance is Anthropic's, 2025-09-11: <https://www.anthropic.com/engineering/writing-tools-for-agents>

**Their recommended harness** is deliberately unglamorous: "simple agentic loops (`while`-loops wrapping alternating LLM API and tool calls): one loop for each evaluation task."

**Their task construction rules:**
- Dozens of prompt-response pairs grounded in realistic workflows
- Avoid "overly simplistic or superficial 'sandbox' environments"
- Strong tasks require multiple tool calls, potentially dozens
- Pair each prompt with verifiable outcomes
- Avoid "overly strict verifiers that reject correct responses due to spurious differences"

**Their metric set**, which doubles as a usable SLI list for an approval gate:

| Metric | Why an enterprise gate wants it |
|---|---|
| Top-level task accuracy | The only metric that means anything to the requester |
| Runtime per tool call and per task | Feeds a latency SLO and catches servers that will time out under MRTR |
| Total number of tool calls | A server that needs 40 calls where another needs 3 is a cost problem |
| Token consumption | The actual bill, and the number that justifies or kills the server |
| Tool errors | The `isError: true` rate, which your HTTP monitoring cannot see (F13) |

They add a qualitative step that is easy to skip and is where the real findings come from: read the agent's reasoning traces, because "what agents omit in their feedback and responses can often be more important than what they include."

**Tooling named by practitioners:** the MCP Interviewer, used by the Microsoft Learn team for schema validation, and Microsoft Research's "tool space interference" guidance. The MCP Inspector ships in three forms (web, CLI, TUI) with documented exit codes and CI recipes, which makes the CLI the obvious basis for an automated approval gate. <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli.md>

**Existing benchmarks usable as an external yardstick:** MCP-Universe (11 real MCP servers, 6 domains, open-source harness with UI), MCPToolBench++ (built on a 4,000+ server marketplace across 40+ categories), MCP-Bench, MCP-RADAR. MCPToolBench++ makes the point an enterprise gate needs to internalise: "unlike existing tool-use benchmarks with high success rates in functions like programming and math functions, the success rate of real-world MCP tool is not guaranteed and varies across different MCP servers."

**A defensible operational SLI set for an internal MCP server**, assembled from the above rather than invented:

1. Tool-call success rate, counting `isError: true` as failure (F13)
2. p95 and p99 tool-call latency, measured against the tightest idle timeout in the path (F10)
3. Tokens per completed task, not tokens per call
4. Tool-definition footprint in tokens, tracked as a percentage of the context window against the spec's 1% to 5% threshold
5. Schema change rate, with mandatory dual-name deprecation windows (F3)
6. `tools/list` order stability, as a binary check (F7)
7. Idempotency coverage on every side-effecting tool, as a binary check (F5)

---

## 6. Organisational gotchas

This section is the weakest evidentially, and that is itself the finding. **Almost everything published about MCP governance is vendor marketing, and none of it names an incident.** The Maxim AI piece, reviewed for this research, "describes the threat model but provides no documented incidents, breach reports, or real-world compromise cases. No organizations are named as affected."

What can be said with sourcing:

**Shadow servers.** The strongest framing is a rhetorical test rather than a statistic: "ask your security team how many MCP servers are running across your organization right now. If they cannot answer with confidence, you have a governance problem that is already in production." [VENDOR, TrueFoundry, 2026-09-11] The one attributed practitioner quote in that piece is from a Medtronic security leader: "MCP opens a lot of opportunities to do a lot of damage very quickly."

**Credentials in desktop clients.** Block's published mitigation is the useful artifact: OAuth for token distribution with storage in native system keychains, rather than API keys in config files. [PRIMARY] The maintainers' roadmap confirms this is the ecosystem direction, naming the goal as moving off "pasted API keys and long-lived tokens" toward DPoP and Workload Identity Federation. [PRIMARY]

**Exposed servers.** 1,862 MCP servers found on the public internet, all 119 sampled listing their tools without credentials. [SECONDHAND, Knostic July 2025]

**Local stdio bypasses central controls.** This is structural rather than anecdotal: a stdio server is a child process on a laptop. There is no gateway in the path, no TLS to inspect, no load balancer to instrument, and the process's failure mode is a closed pipe [PRIMARY, pgEdge]. The spec's programmatic-tool-calling guidance is explicit that a host broker intercepting calls "over an in-process or stdio channel (so network permissions can stay fully denied)" is the control point, which is an admission that the control has to live in the host, because it cannot live in the network.

**Client fragmentation.** MCP names Claude, ChatGPT, VS Code, Cursor, and MCPJam among supported clients, each with its own configuration file, its own trust model, and its own tool-loading behaviour. Two pieces of evidence, neither of them anecdotal:

1. The official client best-practices document *recommends* progressive discovery with a suggested 1% to 5% threshold rather than specifying it. Each host decides independently when to stop loading tools, so two employees on two clients hitting the same server get different tool surfaces and different bills. [PRIMARY, by inference from the guidance being advisory]
2. **[MEASURED-HERE, 2026-09-17]** There is no published per-client feature support matrix. The full docs index at `llms.txt` was searched; the 2026-07-28 docs carry `learn/client-concepts`, `develop/build-client` and `develop/clients/client-best-practices`, and nothing enumerating which client supports which feature. A platform team standardising on a client set has to determine this empirically.

**Ownership decay after the author changes team.** No published source found. Mark as **[UNVERIFIED]**. If the talk asserts it, assert it as an observation from the room, not as a cited finding.

**Approval bottlenecks and gateway avoidance.** No published practitioner account found with numbers. The closest real data point is Block's inverted version of the same problem: their named failure was that people *could not* self-serve (F16), and their fix was to remove friction rather than add gates. That is a more interesting story for this audience than an unsourced claim about bottlenecks, because it says the registry becomes the enemy by being slow, not by being strict.

---

## 7. Numbers that are wrong in the wild

Three widely repeated figures do not survive being chased to their sources. All three were traced during this research on 2026-09-17. This section is the most defensible original contribution here, because a maintainer audience has seen all three in someone else's deck.

### 7.1 The RAG-MCP "43% to 14% collapse" is inverted

**What circulates:** "Tool selection accuracy collapsed from 43% to under 14% as tool count grew, a threefold degradation." Appears in AgentPMT (2026-02-27) and is repeated onward from there.

**What the paper says:** RAG-MCP, arXiv 2505.03275, Gan and Sun, 2025-05-06, reports that their retrieval method "more than triples tool selection accuracy (43.13% vs 13.62% baseline)."

**43.13% is the fix. 13.62% is the naive baseline.** The figure is a comparison between two *methods* on the same tool pool, not a degradation curve over tool count. The secondary reporting reversed the direction of the finding and reassigned it to a different independent variable.

The paper does contain a real tool-count finding, and it is more useful: in the MCP stress test, with the candidate pool scaled from 1 to 11,100, retrieval success is above 90% for the first ~30 positions, drops through positions 31 to 70 due to semantic overlap between tool descriptions, and degrades substantially beyond ~100. Cite that instead.

<https://arxiv.org/abs/2505.03275>

### 7.2 The Cloudflare "1.17 million tokens" figure is not in the Cloudflare post

**What circulates:** "Cloudflare's API as native MCP would be 1.17M tokens across 2,500+ endpoints, compressed to ~1,000 tokens by Code Mode." Attributed to Cloudflare engineering.

**What the Cloudflare post says:** the Code Mode post (Kenton Varda and Sunil Pai, 2025-09-26) was retrieved and read for this research. It contains **no quantified token comparison**. Its central claim is qualitative: "agents are able to handle many more tools, and more complex tools, when those tools are presented as a TypeScript API."

VERIFICATION NOTE, parent session 2026-09-17: the post was independently re-read. Both reads agree on the load-bearing point, that it contains **no quantified token comparison**. The two reads disagree about which incidental figures the post does contain. Assert only the absence of a token comparison. Do not claim to know what the post's only figure is.

Mark the 1.17M figure **[UNVERIFIED]**. It may originate in a Cloudflare talk or a different post; it is not in the one it is attributed to.

<https://blog.cloudflare.com/code-mode/>

### 7.3 The "49% to 74%" figure is attributed to the wrong feature

**What circulates:** AgentPMT attributes "49% to 74% on tool selection" to Anthropic's *programmatic tool calling*.

**What Anthropic's post says:** 49% to 74% on Opus 4 is the **Tool Search Tool** result on MCP evaluations. Programmatic tool calling's reported accuracy gains are different and smaller: internal knowledge retrieval 25.6% to 28.5%, and GIA 46.5% to 51.2%.

Two different features, two different effect sizes. If a slide claims code execution fixes tool selection accuracy by 25 points, it is citing the wrong row.

<https://www.anthropic.com/engineering/advanced-tool-use>

### 7.4 A mis-citation worth noting

Jentic's "The MCP Tool Trap" cites arXiv 2411.15399 for "how tool calling accuracy declines as more tools are added to context." That paper is "Less is More: Optimizing Function Calling for LLM Execution on Edge Devices" (Paramanayakam et al., 2024-11-23), whose headline results are execution time reduced up to 70% and power consumption up to 40% on edge devices. It is not a tool-count-versus-accuracy study in the sense the citation implies.

**The pattern across all four:** the tool-sprawl argument is correct and well evidenced by primary sources. The numbers most often used to make it are not the numbers their sources report. That is worth saying out loud to a room that is about to build governance policy on top of them.

---

## 8. Open problems

Things with no published answer as of 2026-09-17.

1. **Idempotency has no protocol-level story.** Resumability was removed and the answer offered in practitioner writing is application-level idempotency keys. No idempotency convention appears in the 2026-07-28 changelog, which was read in full, nor in the client best-practices document, which was read in full, nor among the `_meta` keys those two define. Every server author now invents one, or does not. This is the highest-consequence gap in the current spec for enterprise use, because F5 is a money and provisioning bug rather than a latency bug. *(Method: full read of the changelog and client best-practices; not an exhaustive SEP search.)*

2. **Progressive discovery has no interop story.** Each host decides its own threshold, its own retrieval strategy, and its own catalog schema. `search_tools` is a pattern in a best-practices doc, not a protocol method. A server cannot know, and cannot influence, whether its tools are loaded eagerly or on demand, which means it cannot reason about its own context cost on any given client.

3. **No standard way to publish a server's context cost.** A server card that declared "my full tool surface is N tokens" would let a host decide before connecting. The Server Card Working Group's `.well-known` metadata is the obvious home, and the roadmap's stated goal that "a server can be discovered and reasoned over without connecting to it" points at it, but no token-footprint field was found in any published draft.

4. **Registry entries are self-reported with no attestation.** The official registry is upstream data for downstream marketplaces and private enterprise sub-registries. Nothing establishes that a listed server does what it says. An enterprise sub-registry inherits that and has to build its own attestation.

5. **No published operational SLO conventions.** Nobody has published what a good p99 for an MCP tool call is, or what an acceptable `isError` rate is. The SLI list in section 5 is assembled from eval guidance, not from published operational targets.

6. **Client fragmentation has no compatibility matrix in the spec docs.** **[MEASURED-HERE, 2026-09-17]** The full documentation index at <https://modelcontextprotocol.io/llms.txt> was retrieved and searched for a client directory or support-matrix page. For the 2026-07-28 docs set it contains `learn/client-concepts`, `develop/build-client`, and `develop/clients/client-best-practices`, and no per-client feature support matrix. `modelcontextprotocol.io/clients` resolves to the general overview page. So "which of my employees' clients support elicitation, or MRTR, or `server/discover`" currently has no authoritative published answer, which is a governance problem for any org running five clients.

7. **No published incident post-mortems surfaced.** None were found in this research. Every failure mode in section 1 comes from a spec document, an architecture blog, or a design retrospective, and not one from a public outage write-up. The closest thing to an incident number in the entire corpus is Microsoft's 2 to 5% of requests broken by a parameter rename. For a protocol at half a billion SDK downloads a month, that absence is worth naming from the stage, stated as an absence of evidence rather than proof that none exist. Ask the room; that is a question a maintainer audience can answer live.

---

## Appendix: source index

**Primary, spec and maintainers**
- MCP spec 2026-07-28 changelog: <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
- MCP 2026-07-28 release post, Soria Parra and Delimarsky, 2026-07-28: <https://blog.modelcontextprotocol.io/posts/2026-07-28/>
- The New MCP Roadmap, Soria Parra and Delimarsky, 2026-08-22: <https://blog.modelcontextprotocol.io/posts/mcp-roadmap/>
- Client Best Practices, 2026-07-28: <https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md>
- MCP Registry preview, 2025-09-08: <https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/>
- MCP Inspector CLI: <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli.md>

**Primary, practitioners**
- Block, Angie Jones, 2025-04-22: <https://dev.to/blockopensource/mcp-in-the-enterprise-real-world-adoption-at-block-ci5>
- Block, Mohammed and Chau, 2025-06-16: <https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers>
- Microsoft Learn, Zhang / Imasogie / de Bruin, 2026-02-11: <https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/>
- AWS, Komandooru / DeVries / Najafzadeh, 2026-09-01: <https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/>
- pgEdge, Ibrar Ahmed, 2026-02-05: <https://www.pgedge.com/blog/mcp-transport-architecture-boundaries-and-failure-modes>
- WorkOS, Maria Paktiti, 2026-09-16: <https://workos.com/blog/mcp-stateless-spec-2026-07-28>
- Artemii Amelin, 2026-09-01: <https://dev.to/artem_a/mcp-2026-07-28-deleted-the-session-the-state-moved-into-your-context-window-1hde>
- Cloudflare Code Mode, Varda and Pai, 2025-09-26: <https://blog.cloudflare.com/code-mode/>

**Primary, Anthropic engineering**
- Code execution with MCP, 2025-11-04: <https://www.anthropic.com/engineering/code-execution-with-mcp>
- Advanced tool use, 2025-11-24: <https://www.anthropic.com/engineering/advanced-tool-use>
- Writing tools for agents, 2025-09-11: <https://www.anthropic.com/engineering/writing-tools-for-agents>
- Pricing, retrieved 2026-09-17: <https://platform.claude.com/docs/en/about-claude/pricing>

**Peer / preprint**
- RAG-MCP, arXiv 2505.03275: <https://arxiv.org/abs/2505.03275>
- MCP-Universe, arXiv 2508.14704: <https://arxiv.org/abs/2508.14704>
- MCPToolBench++, arXiv 2508.07575: <https://arxiv.org/abs/2508.07575>
- Less is More (mis-cited elsewhere), arXiv 2411.15399: <https://arxiv.org/abs/2411.15399>

**Secondhand and vendor, use with the label**
- AgentPMT, Stephanie Goodman, 2026-02-27: <https://www.agentpmt.com/articles/thousands-of-mcp-tools-zero-context-left-the-bloat-tax-breaking-ai-agents>
- Unblocked, Dennis Pilarinos, 2026-05-16: <https://getunblocked.com/blog/mcp-tool-overload/>
- All Things Open on Block, 2025-12-02: <https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions>
- TrueFoundry [VENDOR], 2026-09-11: <https://www.truefoundry.com/blog/enterprise-mcp-governance-control-audit-secure-mcp-server-access>
- Maxim AI [VENDOR], 2026-09-02: <https://www.getmaxim.ai/articles/shadow-mcp-servers-visibility-and-control-at-the-gateway/>
- Jentic, The MCP Tool Trap: <https://jentic.com/blog/the-mcp-tool-trap>

**Directories, counted 2026-09-17**
- Official registry API: <https://registry.modelcontextprotocol.io/v0/servers>
- Glama: <https://glama.ai/mcp/servers>
- PulseMCP: <https://www.pulsemcp.com/servers>


---

## 9. Independent verification by the parent session, 2026-09-17

Section 7 is the highest exposure material in this repository, because it is a
claim about other people being wrong, delivered to a room that may include them.
It was re-checked against primary sources before being cleared for use.

| Claim | Verdict |
|---|---|
| RAG-MCP 43.13% is the proposed method and 13.62% is the baseline, so the circulating "43% collapses to 14%" is inverted | CONFIRMED. The abstract reads "more than triples tool selection accuracy (43.13% vs 13.62% baseline)". 43.13% is the fix |
| RAG-MCP is a method comparison, not a degradation curve over tool count | CONFIRMED by the same sentence |
| The Cloudflare Code Mode post contains no 1.17M token figure | CONFIRMED. Two independent reads, neither found a token comparison |
| The circulating misquotes are traceable to named sources rather than asserted generally | CONFIRMED in the file: AgentPMT 2026-02-27 for 7.1 and 7.3, Jentic for 7.4 |

Delivery guidance, which is a separate question from whether the finding is true:

1. **Do not name AgentPMT or Jentic from the stage.** The point stands without
   naming anyone, and naming them converts a useful correction into a callout
   that the room will remember instead of the argument. The sourcing exists in
   this file for anyone who asks afterwards, which is where it belongs.
2. Lead with the part that is generous: the tool sprawl argument is correct and
   well evidenced. It is the numbers that got reversed in transmission.
3. Offer the better finding as a replacement rather than only removing the bad
   one. Above 90% for the first 30 candidates, degrading past 100, across a pool
   scaled to 11,100, is a more useful number than the one it replaces.
