---
title: "Where an MCP Call Spends Its Time"
subtitle: "Operating MCP at scale, part four: performance"
date: 2026-10-05
status: draft
prefix: "Research"
series: "Operating MCP at Scale"
part: 4
sources_verified_on: 2026-10-06
---

# Where an MCP Call Spends Its Time

*Operating MCP at scale, part four: performance.*

The one peer-reviewed study I found that instruments an MCP workflow end to end
puts the time somewhere other than the tool. ProMCP, published in Findings of ACL
2026, splits the path from a user's query to the final answer into six stages
across 20 servers and 169 tools. With customized clients, 60 to 67% of total
latency went to "LLM planning and schema injection," and in every configuration
"tool execution contributes only a small fraction of the overall cost."

GitHub trimmed the default built-in toolset in VS Code from 40 tools to 13 and
reports that "users with the shrunken toolset experience an average decrease of
190 milliseconds in TTFT (Time To First Token), and an average decrease of 400
milliseconds in TTFT (Time to Final Token, or time to complete model response)."
The post uses one acronym for two quantities, so quote it exactly or not at all.
Against that, AIMultiple measured three self-hosted MCP gateways adding 840
microseconds (Bifrost), 1,134 (Docker MCP Gateway) and 23,058 (IBM ContextForge)
per call.

That supports a conditional thesis. **When the gateway is self-hosted and nearby,
the tool surface the model reads and plans over costs more time than the hop to
the tool. When the gateway inspects content or sits across a region, the two are
the same order of magnitude.** Each half rests on measurements, taken in
different studies, and the rest of this part is about the conditions.

## Where the time goes

| Segment | Figure | Who measured it | Label |
|---|---|---|---|
| Self-hosted gateway | Bifrost 840 µs (ships no content inspection); Docker MCP Gateway 1,134 µs (credential blocking on by default); ContextForge 23,058 µs | AIMultiple: median added latency at concurrency 1, routed call minus a matched direct call, one 8-vCPU box | Measured, independent |
| Content inspection, off then on | ContextForge pattern detectors 27.8 to 31.0 ms (+3,198 µs); TrueFoundry guardrails 55.5 to 172.1 ms (+116.6 ms) | AIMultiple, one setting changed per pair | Measured, independent |
| Hosted control plane | TrueFoundry 55.5 ms, of which the round trip is 14.1; Cortx 211.1 ms, of which roughly 200 is two network crossings | AIMultiple, over the WAN from the same box | Measured, independent, includes network |
| Server at 50 virtual users | p95 of 8.13 ms (Quarkus) to 342.41 ms (Python, at its 259 requests per second ceiling) | TM Dev Lab, k6, 2 vCPU per server, 2025-06-18 protocol | Measured, independent |
| Planning and schema injection | 60 to 67% of total latency with customized clients | ProMCP, 20 servers, 169 tools | Measured, peer-reviewed |
| One inference round trip | "hundreds of milliseconds to seconds" | Anthropic | Claimed by a model vendor, no method |

AIMultiple treats only the three self-hosted figures as comparable with each
other; the hosted pair carries network distance it could not separate from
processing. The planning row is the largest where it has a number. Three other
rows can reach its size: injection detection, a control plane in another region,
and a server at its ceiling. Python's p95 was taken while it served its maximum
of 259 requests per second, so I read most of it as queueing.

## What is MCP-specific about the surface

The cost of a large tool surface belongs to tool-calling agents in general.
Native function calling with no MCP reads the same kind of definitions, and
GitHub's trim was of built-in tools, though the post notes that with MCP servers
the count "can grow into the hundreds." There is also a counter-case, from a
vendor measuring its own server. Twilio ran the Cline agent on Claude 3.7 Sonnet
over three tasks, each at least ten times, against a control that used built-in
tools such as the terminal and web search. With MCP, "Tasks completed ~20.5%
faster on average," and "Cost increased by about 27.5% on average."

What MCP adds is that the operator does not own the surface. A third party
writes the definitions, chooses their number, wording and order, and can change
them at runtime with a `listChanged` notification. That matters because of
prompt caching. Anthropic's caching documentation says the cache follows the
hierarchy `tools`, `system`, `messages`, and that "Modifying tool definitions
(names, descriptions, parameters) invalidates the entire cache." With caching
on, a large surface costs most on a cache miss, and a surface someone else
controls decides how often the miss happens.

The surfaces are large. Anthropic's worked example, introduced with "Consider a
five-server setup," comes to "58 tools consuming approximately 55K tokens before
the conversation even starts." Of its own systems it says "we've seen tool
definitions consume 134K tokens before optimization."

Selection quality degrades with the same surface, and the published thresholds
disagree. Anthropic's tool search documentation says Claude's ability to pick the
right tool degrades past 30 to 50 tools. OpenAI's guide says to aim for "fewer
than 20 functions available at the start of a turn at any one time, though this
is just a soft suggestion." The RAG-MCP preprint points the same way on a
different unit, reporting success above 90% for "MCP positions below 30," where a
position is a server schema.

## Deferring the surface, and what the hop costs

Both vendors document deferred loading on the pages quoted above. On Anthropic's
API a deferred tool found through tool search is expanded inline, and "The
prefix is untouched, so prompt caching is preserved"; for MCP servers it is set
"once on the `mcp_toolset` entry's `default_config` for the whole server."
OpenAI's guide says "you can defer loading some or all of those tools with
`tool_search`," and that only gpt-5.4 and later models support it.

Deferral trades the surface for a discovery hop, and GitHub names the price:
"each call to a virtual tool still results in a cache miss, an extra round trip,
and an opportunity for a small percentage of agent operations to fail." The hop
grows with the catalog. One preprint reports "sub-100ms retrieval latency" over
121 tools. A PayPal preprint with an overlapping author measured production
`tool_search` over 2,000 tools at an average of 572 ms, "median: 440 ms, P95: 936
ms," across 1,921 requests in 24 hours. That is a vendor measuring its own
system, and its figure caption reports a different sample. At that size the
median hop matches GitHub's whole 400 ms saving, so deferral moves the cost to
the turns that search.

## What the cache can and cannot hold

The 2026-07-28 revision requires `ttlMs` and `cacheScope` on every complete
`tools/list`, `prompts/list`, `resources/list`, `resources/templates/list` and
`resources/read` result, and the caching page adds `server/discover`. Ordering
also reaches the model's prompt cache. The tools page says servers "SHOULD return
tools in a deterministic order," because ordering "improves LLM prompt cache hit
rates when tools are included in model context."

The verb matters. AWS's Well-Architected post says tool lists "now return in
deterministic order," and Cloudflare's says "Tool catalogs are deterministically
ordered." The specification makes it a SHOULD. A server that builds its list from
an unordered map is conformant and can reorder it between calls, which misses the
prompt cache. The official Go SDK iterates its tools "sorted by unique ID." A
gateway that merges several upstream lists has to make the same choice.

Per-user filtering meets the scope rules next. The tools page allows a server to
return "only the tools the caller's granted scopes permit," and the caching page
says `"private"` is appropriate "for filtered list results that vary per user."
Private caches "MUST NOT be shared across authorization contexts," and a
different access token is a different context.

Gateways already cache upstream and filter on the way out. ContextForge's default
`cache` mode serves `tools/list` from its own database through a visibility
filter taken from the user context. Sigilum documents a 300-second discovery
cache that returns tools "filtered by subject policy." Neither takes its
freshness from the upstream `ttlMs`, in the code and documentation I read.
Kuadrant's `mcp-gateway` does, and its code shows what aggregation does to the
hints. The merged list gets the shortest upstream TTL and is `"private"` if any
upstream is private or user-specific. If any upstream returns a TTL of zero, the
whole merged list gets zero and is marked private. One volatile server sets the
cacheability of everything federated with it.

Defaults decide whether any of this fires. In the MCP Python SDK every server
result is `ttlMs: 0, cacheScope: "private"` out of the box, "immediately stale,
never shared." Its client "has a built-in response cache, on by default," and
honors a positive TTL. Sharing one cached copy across principals also needs
`share_public`, which is "Off by default," and a list identical for everyone.
The only effect size I found is a practitioner's statement, without a method,
that "Cacheable lists cut repeat traffic 22%."

## Headers versus bodies

Before 2026-07-28 the method and tool name lived only in the JSON-RPC body, so a
middlebox "had one option: buffer the request, parse the JSON-RPC envelope, and
make its decision from the body," as Tigera puts it. The revision mirrors them
into required `Mcp-Method` and `Mcp-Name` headers so intermediaries "can route
and inspect requests without parsing the body." GitHub reads request values for
logging and secret scanning and reports "no more inspecting the payload of every
single request before the SDK does," with no number. Three conditions limit the
fast path.

**Argument policy can move to headers; content inspection cannot.** A server may
annotate primitive parameters with `x-mcp-header`, and conforming clients "MUST
mirror the designated parameter values into HTTP headers," so a gateway can route
or rate-limit by tenant without the body. Free-text arguments still need the
body, and tool results, where injected instructions arrive, have no header form.
Kuadrant's pull request #1500, open on 2026-10-06, skips body buffering only
"when no prefix rewriting or guardrail inspection is required," prefixes being
how that gateway federates tools without name collisions.

**The header is only as good as the body behind it.** A server that processes the
body must reject mismatched headers with `HeaderMismatch` (`-32020`). The
specification's reason is "potential security vulnerabilities when different components in the network
rely on different sources of truth." The intermediary saves the parse; the server
still parses and compares.

**Older traffic carries no trustworthy header.** For requests whose
`MCP-Protocol-Version` predates header and body validation, an enforcing
intermediary "SHOULD reject the request rather than trusting unvalidated header
values." In a mixed fleet the cheap path covers only migrated traffic.

When you do open the body, the cost depends on the detector. ContextForge's
credential patterns added 3.2 ms. TrueFoundry's injection detection added about
117 ms, with totals from 152.6 to 200.3 ms across three repetitions, and it was
the only injection detector of the six gateways tested, stopping 55 of 60 injected
instructions. Part 2 argues for paying that on traffic from servers you did not
write.

## Throughput, and what the revision deleted

TM Dev Lab's benchmark is the most complete cross-implementation MCP server
comparison I found with a published method: 15 implementations, real Redis and
HTTP work, 39.9 million requests, 0% errors. Rust reached 4,845 requests per
second and Python 259. It ran on the 2025-06-18 transport, the author says the
results "do not constitute a general ranking of programming languages or
frameworks," and names "FastMCP session overhead" as Python's bottleneck, a
cost the new revision is designed to remove. I found no re-run.

Two findings transfer. Creating a server per request in Node.js and Bun "is the
intentional design for stateless MCP servers," which the author says "sets a
fixed 5-10ms overhead floor per request." And rmcp v0.16 answered every response
as an event stream, with "approximately 40ms of pure transport overhead per
request" on tools returning HTTP payloads; JSON responses took the same server
from 1,283 to 4,845 requests per second. The benchmark's author fixed it upstream in
rmcp v0.17.0. A pure-Redis tool ran at 1.11 ms on the same path, and no root
cause was published, so the lesson is narrow: check your SDK's response mode and
measure it.

The best measurement of per-session cost I found predates the revision.
Stacklok's 2025 benchmark of its own ToolHive deployment ran Streamable HTTP at 50
connections against a 100 requests per second target: 96.78 per second with a
pool of ten sessions, 33.03 with a new session per request, and average response
time rising from 6.68 ms to 1.12 s. It ran on a local kind cluster, and the page
says its load generator could not send the full intended load, so part of the
gap may be the generator.

The after is thin. The maintainers describe "a stateless core that scales on
ordinary HTTP infrastructure," Google says that moving these values into headers
"drastically lowers the latency and processing overhead at the gateway layer," and GitHub, which removed
Redis session reads from every call, says it "makes things snappier." None gives
a number. The only before-and-after table I found is a practitioner's, on three
FastMCP servers: 1,840 to 5,900 requests per minute, with no method and a row
labeled "Throughput P99."

## Where MCP is structurally slower

When no model is in the loop, the protocol hop is pure overhead. A scheduled
reconciliation that pushes 500 records through an MCP tool pays the hop on every
record for an endpoint that was never in doubt, and routing it through an agent
adds an inference pass per record on top.

The hop's size depends mostly on the server's process model. MADBench, a
University of Waterloo master's thesis presented on September 18, 2026, measured
this overhead with no model in the loop across 5,378 traces. Its abstract reports
it ranging from a thousandth of the database execution time for an in-process
engine to three times it for a subprocess server on PostgreSQL, with the process
model rather than the wire format dominant. I have read the abstract, not the
thesis.

Two features of the revision move cost from the connection to the wire. Multi
round-trip requests turn a tool that needs user input into independent requests,
each re-sending the parameters and an opaque `requestState`. Servers "MUST treat
`requestState` as an attacker-controlled input" and, where it affects
authorization or business logic, must protect its integrity. Servers "MAY choose to return an
`InputRequiredResult` on multiple attempts at the same request," so no limit is
set on rounds. And with stream resumability removed, a broken stream means
re-issuing the call.

Code execution shows the trade. AIMultiple ran two web-browsing tasks on GPT-4.1
through an MCP server exposing 63 tool definitions. Code execution cut total
tokens by 77.4% and raised average latency from 9.66 s to 10.37 s, with no
variance published and no cause given. Output tokens rose from 87 to 192 per run,
and my reading is that serially generated code accounts for some of the rise.
Anthropic's "19+ inference passes" saved by orchestrating 20 or more calls in
code describes a different task shape. The crossover is unpublished.

## The default histogram cannot resolve the fast gateways

The OpenTelemetry MCP conventions advise bucket boundaries starting at 0.01
seconds for both operation-duration metrics. Bifrost's and Docker's added
latency, and ContextForge's 3.2 ms detector increment, all land in that first
bucket, so the default histogram cannot tell them apart. Traces can, as can an
exponential histogram or overridden boundaries. The same document still defines
session-duration metrics for a construct the revision deleted; alignment issue
#437 was open on 2026-10-06, and the repository has no releases.

## Relationship to the AWS post

AWS's Well-Architected post of September 1, 2026, names three performance
changes: protocol-declared caching (which it pairs with deterministic ordering),
freshness semantics and header-based routing. It attaches no measurement to any
of them. This part adds the measurements that exist and the conditions under
which each mechanism does not fire.

## What to actually do

**Defer tool loading before you trim by hand.** Both major model vendors document
it, and Anthropic's keeps the cached prefix intact. Measure the discovery hop
that replaces the surface; PayPal's median was 440 ms at 2,000 tools.

**Count the tools the model sees at the start of a turn.** Vendor guidance runs
from under 20 to 50; stay toward the low end. GitHub's trim from 40 to 13 came
with 190 ms off the first token and 400 ms off the final token.

**Make your `tools/list` byte-stable, and treat changes as cache events.** Sort
it, emit a positive `ttlMs` where it is stable, and mark it `public` only when it
is identical for every caller. A `listChanged` notification or a newly connected
server costs a prompt-cache miss.

**Know how your gateway merges cache hints.** In a federated list, one private or
zero-TTL upstream can make the whole list private or uncacheable. For per-user
lists, cache upstream and filter at the edge, and budget for the filter.

**Route on headers, and label every request that gets inspected.** Put tenant or
region policy on `x-mcp-header` parameters. Inspection added 3.2 ms with one
detector and about 117 ms with another, so make guardrail state a label on your
latency metrics.

**Expect the cheap path only for migrated traffic.** Measure the protocol-version
mix at the gateway, because it bounds the fast path.

**Check your SDK's response mode, and measure.** rmcp before v0.17.0 paid about
40 ms per call on some tools.

**Keep a hosted MCP control plane in the client's region.** It sits on every tool
call, and Cortx's 211 ms was roughly 200 ms of network.

**Use traces or finer buckets to see the gateway.** Client duration minus server
duration per call separates a slow server from a slow path without tracing.

**Do not put MCP in a loop with no model in it.** If code already knows the
endpoint, call the endpoint.

---

*Part four of five on operating MCP at scale. Parts one to three cover
operational excellence, security and reliability. Part five, on cost, follows.*

## Sources

All URLs verified 2026-10-06.

**Specification and SDKs**
1. Caching, 2026-07-28, for the cacheable results, the scope rules and the security considerations. https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
2. Tools, 2026-07-28, for deterministic ordering as a SHOULD and per-authorization tool lists. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
3. Streamable HTTP, 2026-07-28, for the mirrored headers, `x-mcp-header`, header-body validation and the guidance on unvalidated headers. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
4. Multi round-trip requests, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr
5. Changelog, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/changelog
6. MCP Python SDK, client caching, for the server and client defaults. https://py.sdk.modelcontextprotocol.io/client/caching/
7. MCP Go SDK, `mcp/features.go`, for features sorted by unique ID. https://github.com/modelcontextprotocol/go-sdk/blob/main/mcp/features.go

**Measurement**
8. Anjum, Zheng, Kettimuthu, Fan and Feng, "ProMCP: Profiling Token Flows and Latency Costs in Model Context Protocol-Based LLM Agents", Findings of ACL 2026. https://aclanthology.org/2026.findings-acl.1967.pdf
9. Berk Kalelioğlu, "MCP Gateway Benchmark: Latency & Security of 6 Gateways", AIMultiple, updated 2026-10-05, with its data download. https://aimultiple.com/mcp-gateway
10. Thiago Mendes, "MCP Server Performance Benchmark v2", TM Dev Lab, 2026-02-28. https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html
11. rmcp pull request #683, "feat(streamable-http): add json_response option for stateless server mode", merged 2026-02-27. https://github.com/modelcontextprotocol/rust-sdk/pull/683
12. Şevval Alper, "Code Execution with MCP", AIMultiple, updated 2026-08-14. https://aimultiple.com/code-execution-with-mcp
13. Chris Burns, "MCP server performance: Transport protocol matters", Stacklok, 2025-08-19. https://stacklok.com/blog/mcp-server-performance-transport-protocol-matters/
14. Noah Mogil, "Performance Testing of Twilio Alpha's MCP Server", Twilio, 2025-04-10. https://www.twilio.com/en-us/blog/developers/twilio-alpha-mcp-server-real-world-performance
15. Yaseen Ahmed, "MADBench: Measuring Agentic Databases: Quantifying the Protocol Tax of MCP-Mediated Query Workloads", master's thesis presentation, University of Waterloo, 2026-09-18. https://cs.uwaterloo.ca/events/masters-thesis-presentation-data-systems-madbench-measuring-agentic-databases-quantifying-protocol-tax-mcp-mediated-query-workloads
16. Deepak Bagada, "MCP Roadmap 2026 Goes Stateless: Tasks and Cards Ship Live", Daily AI World, 2026-09-21, for the unmethoded before-and-after table and the 22% figure. https://dailyaiworld.com/blogs/mcp-roadmap-stateless-tasks-server-cards

**Tool surface and discovery**
17. Anisha Agarwal and Connor Peet, "How we're making GitHub Copilot smarter with fewer tools", GitHub, 2025-11-19. https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/
18. Anthropic, "Introducing advanced tool use on the Claude Developer Platform", 2025-11-24. https://www.anthropic.com/engineering/advanced-tool-use
19. Anthropic, tool search tool documentation, for thresholds and deferred loading. https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
20. Anthropic, prompt caching documentation, for the cache hierarchy and invalidation. https://platform.claude.com/docs/en/build-with-claude/prompt-caching
21. OpenAI, function calling guide, for the soft threshold and `tool_search`. https://developers.openai.com/api/docs/guides/function-calling
22. Gan and Sun, "RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval-Augmented Generation", arXiv:2505.03275, preprint. https://arxiv.org/abs/2505.03275
23. Mudunuri, Wan, Qin and Manoharan, "Semantic Tool Discovery for Large Language Models: A Vector-Based Approach to MCP Tool Selection", arXiv:2603.20313, preprint. https://arxiv.org/abs/2603.20313
24. Saha, Wang and Manoharan, "Hybrid Semantic Tool Discovery for Enterprise MCP Gateway: Architecture and Implementation", PayPal, arXiv:2608.23992, preprint, 2026-08-25. https://arxiv.org/abs/2608.23992

**Gateways, headers and the revision in practice**
25. ContextForge `streamablehttp_transport.py`, for the default `cache` mode and the visibility filter. https://github.com/IBM/mcp-context-forge/blob/main/mcpgateway/transports/streamablehttp_transport.py
26. Sigilum gateway MCP runtime documentation, for the discovery cache and per-subject filtering. https://mintlify.wiki/PaymanAI/sigilum/api-reference/gateway/mcp
27. Kuadrant `mcp-gateway` broker, for aggregated `ttlMs` and `cacheScope`. https://github.com/Kuadrant/mcp-gateway/blob/main/internal/broker/protocol_handler_2026.go
28. Kuadrant `mcp-gateway` pull request #1500, "perf(router): skip prefix-free 2026 request bodies". https://github.com/Kuadrant/mcp-gateway/pull/1500
29. GitHub changelog, "GitHub MCP Server supports the next MCP specification", 2026-07-23. https://github.blog/changelog/2026-07-23-github-mcp-server-supports-the-next-mcp-specification/
30. Alister Baroi, "The New MCP Headers Are a Gift to Gateways", Tigera, 2026-08-06. https://www.tigera.io/blog/the-new-mcp-headers-are-a-gift-to-gateways/
31. David Soria Parra and Den Delimarsky, release candidate post for 2026-07-28, 2026-05-21. https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
32. Kurtis Van Gent and Alan Blount, "Scaling AI agent infrastructure with the MCP stateless updates", Google, 2026-08-05. https://developers.googleblog.com/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/
33. Matt Carey, "The next generation of MCP", Cloudflare, 2026-08-06. https://blog.cloudflare.com/mcp-v2/

**Observability**
34. OpenTelemetry MCP semantic conventions. https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md
35. `semantic-conventions-genai` issue #437, alignment with protocol 2026-07-28. https://github.com/open-telemetry/semantic-conventions-genai/issues/437

**Prior art**
36. Komandooru, DeVries and Najafzadeh, "MCP went stateless: is your AWS MCP server deployment Well-Architected?", 2026-09-01. https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
