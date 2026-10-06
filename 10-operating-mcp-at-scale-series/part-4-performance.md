---
title: "The Tool List Costs More Time Than the Gateway"
subtitle: "Operating MCP at scale, part four: performance"
date: 2026-10-05
revised: 2026-10-06
status: draft
prefix: "Research"
series: "Operating MCP at Scale"
part: 4
sources_verified_on: 2026-10-06
---

# The Tool List Costs More Time Than the Gateway

*Operating MCP at scale, part four: performance.*

GitHub cut the default built-in toolset for Copilot in VS Code from 40 tools to
13, and the answers came back faster: an average of 190 ms off the time to first
token and 400 ms off the time to the complete response [1]. The change touched
the list the model reads at the start of a turn, and nothing in the network path.
That is the claim this article will prove. In an MCP agent, the tool list costs
more time than the gateway most teams worry about, and the list is the part of
the request an operator controls least.

Here is how it plays out on a team that has not noticed yet. The team is
hypothetical. Every number attached to it is measured, and cited.

## Who is in the request path

Six things sit between a user's question and the answer, and only one of them
gets its own dashboard.

| Part | What it costs | Who decides |
|---|---|---|
| The model | Planning over the tool list: 60 to 67% of total latency with customized clients in one end-to-end study [2] | The model vendor, and whoever chooses what the model is sent |
| The tool list | 58 tools and about 55K tokens in Anthropic's five-server example [3] | Each server's author, who can change it at runtime |
| The prompt cache | Lost entirely when any tool definition changes [4] | Whoever changed the list last |
| The gateway | 840 µs (Bifrost) or 1,134 µs (Docker MCP Gateway) added per call, self-hosted [5] | The platform team |
| The server | p95 from 8.13 ms to 342.41 ms at 50 virtual users, depending on the implementation [6] | The server's author |
| The tool's own work | "only a small fraction of the overall cost" [2] | The system behind the tool |

The platform team owns one row, and it is the cheapest one.

## Monday, the agent is fast

Imagine an internal agent connected to five MCP servers, the shape of Anthropic's
worked example: "58 tools consuming approximately 55K tokens before the
conversation even starts" [3]. A user asks a question. The client sends the tool
definitions first, as it does every turn, and the provider finds them in the
prompt cache, because Anthropic's caching puts tools first in the hierarchy [4].
The model plans over a prefix it has already processed, picks a tool, and the
call passes through the team's self-hosted gateway, one like Bifrost or Docker's,
which AIMultiple measured at about a millisecond added per call [5]. The server answers. The model writes the reply.

The team argued for weeks about that gateway before they deployed it. On Monday its
panel is green, and so is everything else.

## Tuesday, after someone else's release

Overnight, the author of one of the five servers ships a release. It adds a few
tools, and it builds its tool list from a map with no fixed order. The client
gets a `listChanged` notification and fetches the new list.

Anthropic's caching documentation is blunt about what happens next: "Modifying
tool definitions (names, descriptions, parameters) invalidates the entire cache"
[4]. The first turn after the update starts cold. Because the new server can
return its tools in a different order on the next call, so can the turn after
that. The model is now planning over a list it has not seen, every time, and the
list is longer than Anthropic's own guidance on selection quality, which puts the
threshold at 30 to 50 tools [7]. OpenAI's guide aims lower, at "fewer than 20
functions available at the start of a turn" [8].

Users say the agent feels slow. The team opens the gateway panel, because the
gateway is the new component and the one they argued about. The panel shows what
it showed yesterday: the gateway's added latency sitting in the lowest bucket.
That is all it can show. The OpenTelemetry MCP conventions set histogram buckets
starting at 0.01 s [9], so Bifrost's and Docker's added latency both land in the
first bucket, and the default metrics cannot tell a fast gateway from a slow one.

Nobody on the team changed anything. The cost arrived inside a list written by a
third party, through a notification the protocol allows at any time, and it
landed on the one row of the cast table no dashboard watches.

## Planning over the tool list is the largest measured cost

ProMCP, published in Findings of ACL 2026, is a peer-reviewed study that
instruments an MCP workflow end to end. It splits the path from query to answer
into six stages across 20 servers and 169 tools. With customized clients, 60 to
67% of total latency went to "LLM planning and schema injection," and "tool
execution contributes only a small fraction of the overall cost" [2].

The gateway figures come from a separate, independent benchmark. AIMultiple
measured the added latency as the routed call minus the direct call, median at
concurrency 1, on one 8-vCPU host: 840 µs for Bifrost, 1,134 µs for Docker MCP
Gateway and 23,058 µs for ContextForge [5]. The planning stage is the largest
cost wherever it has a number.

Two configurations change that, and both are measured. Turning on content
inspection, the check for injected instructions, cost 3.2 ms with ContextForge's
detectors and took TrueFoundry from 55.5 ms to 172.1 ms, about 117 ms more per
call [5]. A hosted control plane in another region adds network: Cortx measured
211.1 ms, about 200 ms of it network [5]. In those two cases the gateway costs
time of the same order as the tool list, and part two of this series argues for
paying the inspection cost on traffic from servers you did not write.

A server running at its ceiling can also reach that size. In TM Dev Lab's
benchmark the Python server's p95 of 342.41 ms was taken at its limit of 259
requests per second, so most of that figure is queueing [6].

## You do not own the list, so you do not own the cache

A large tool list slows any tool-calling agent, with or without MCP. What MCP
changes is ownership. A third party writes the definitions, chooses how many there
are and in what order, and can change them at runtime. With caching on, a large
list costs the most on a cache miss, and someone else's server decides how often
the miss happens.

The lists get large. Beyond the 55K example, Anthropic reports seeing tool
definitions consume 134K tokens in its own systems before optimization [3].

The 2026-07-28 revision of the protocol gives servers a way to help. It requires
`ttlMs` and `cacheScope` on every complete `tools/list` result [10], and the tools
page says servers "SHOULD return tools in a deterministic order," because ordering
"improves LLM prompt cache hit rates" [11]. That word is SHOULD. The server in the
story, building its list from an unordered map, is conformant. The official Go SDK
sorts its tools by unique ID [12]; other implementations have to make the same
choice, and so does any gateway that merges several upstream lists.

Merging decides cacheability for the whole set. Kuadrant's `mcp-gateway` gives a
merged list the shortest upstream TTL, marks it private if any upstream is
private, and sets it to zero if any upstream returns zero [13]. One volatile
server makes everything federated with it uncacheable.

Defaults decide whether any of this happens at all. In the MCP Python SDK every
server result ships as `ttlMs: 0, cacheScope: "private"`, "immediately stale,
never shared," while the client's response cache is on by default [14]. A server
that never sets a TTL gets nothing from the client's cache.

## Every way to shrink the list adds a step

Both major model vendors now document deferred loading. On Anthropic's API a tool
found through tool search is expanded inline, and "The prefix is untouched, so
prompt caching is preserved"; for an MCP server it is set once for the whole
server [7]. OpenAI supports `tool_search` from gpt-5.4 onward [8].

Deferral replaces the long list with a discovery step, and GitHub names its
price: "each call to a virtual tool still results in a cache miss, an extra round
trip, and an opportunity for a small percentage of agent operations to fail" [1].
The hop grows with the catalog. PayPal measured its production `tool_search` over
2,000 tools at a median of 440 ms and a p95 of 936 ms across 1,921 requests in 24
hours, in a preprint about its own system [15]. At that size the median search hop
equals the whole 400 ms GitHub saved by trimming. Deferral pays on turns that use
a few known tools and costs on turns that have to search.

Code execution is the other way to shrink the list, and it makes its own trade.
AIMultiple ran two web-browsing tasks on GPT-4.1 against an MCP server with 63
tool definitions. Code execution cut total tokens by 77.4% and raised average
latency from 9.66 s to 10.37 s, with output tokens rising from 87 to 192 per run
and no cause published [16]. Fewer tokens did not mean a faster answer.

## The protocol's own overhead is real and narrow

Below the model, the protocol has costs of its own, and they show up in specific
places. TM Dev Lab benchmarked 15 server implementations with real Redis and HTTP
work, 39.9 million requests and 0% errors, on the 2025-06-18 protocol [6]. Rust
reached 4,845 requests per second and Python 259, and the author names "FastMCP
session overhead" as Python's bottleneck, a cost the new revision is designed to
remove. Creating a server per request, the intended design for stateless servers
in Node.js and Bun, "sets a fixed 5-10ms overhead floor per request" [6]. And rmcp
before v0.17.0 answered every response as an event stream, adding "approximately
40ms of pure transport overhead per request" on some tools; switching to JSON
responses took the same server from 1,283 to 4,845 requests per second [6][17].

The new revision also helps gateways route cheaply. It mirrors the method and tool
name into required `Mcp-Method` and `Mcp-Name` headers, so intermediaries "can
route and inspect requests without parsing the body" [18]. The fast path has
limits. Free-text arguments and tool results, where injected instructions arrive,
have no header form. A server that processes the body must still reject
mismatched headers with `HeaderMismatch` [18]. And for requests on an older protocol version, an
enforcing intermediary "SHOULD reject the request rather than trusting
unvalidated header values" [18], so in a mixed fleet the fast path covers only
migrated clients.

Where no model is in the loop, the protocol hop is the whole cost. MADBench, a
University of Waterloo master's thesis presented on 2026-09-18, measured that hop
across 5,378 traces with no model involved [19]. Its abstract reports the overhead
ranging from a thousandth of database execution time for an in-process engine to
three times it for a subprocess server on PostgreSQL, with the server's process
model mattering more than the wire format. That figure comes from the abstract
alone.

## What to do, depending on who you are

**If you run agents for a platform team:** count the tools the model sees at the
start of a turn, and keep it under 20 where you can [8]. Turn on deferred loading,
then measure the search hop it adds, since PayPal's median was 440 ms at 2,000
tools [15]. Treat a `listChanged` notification or a newly connected server as a
prompt-cache event, and alert on it. That alert is the one the team in the story
needed.

**If you write MCP servers:** return `tools/list` in a sorted, byte-stable order.
Set a positive `ttlMs` where the list is stable, and mark it `public` only when it
is identical for every caller. Check your SDK's response mode and measure it; rmcp
before v0.17.0 paid about 40 ms per call on some tools [17].

**If you operate a gateway:** label every request that passes content inspection
and report latency by that label, because one detector added 3.2 ms and another
about 117 ms [5]. Keep a hosted control plane in the client's region; Cortx's 211
ms was mostly network [5]. Measure the protocol-version mix, because it bounds the
header fast path. And know how your gateway merges cache hints, since one private
or zero-TTL upstream sets the result for the whole list [13].

## What is still unsolved

The default metrics cannot see the cheapest component. With histogram buckets
starting at 0.01 s [9], a fast gateway and a slow one look the same, so use
traces or override the bucket boundaries until the conventions change.

Nobody has yet published a before-and-after measurement of the stateless revision
with its method, so the size of that improvement is unmeasured.

The limit of this article is that its numbers come from separate studies on
different setups. ProMCP is the one source here that measures a whole request
path, and it measured a research setup of 20 servers and 169 tools. Until an
operator publishes a trace of a production agent from question to answer, the
cast table above compares studies, and should be read that way.

## What it adds up to

The time an MCP agent spends is mostly spent before any tool runs: the model
reading and planning over the tool list, and the cache that list either hits or
misses. The gateway most teams worry about is usually the smallest term, and the
list is the one a third party can change overnight. Count the tools each agent
sees, keep the list stable and short, and measure the gateway with traces rather
than default histograms, so the slow part is the one you look at first.

---

*Part four of five on operating MCP at scale. Parts one to three cover
operational excellence, security and reliability. Part five, on cost, follows.*

## Sources

All URLs verified 2026-10-06.

1. Anisha Agarwal and Connor Peet, "How we're making GitHub Copilot smarter with fewer tools", GitHub, 2025-11-19. https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/
2. Anjum, Zheng, Kettimuthu, Fan and Feng, "ProMCP: Profiling Token Flows and Latency Costs in Model Context Protocol-Based LLM Agents", Findings of ACL 2026. https://aclanthology.org/2026.findings-acl.1967.pdf
3. Anthropic, "Introducing advanced tool use on the Claude Developer Platform", 2025-11-24. https://www.anthropic.com/engineering/advanced-tool-use
4. Anthropic, prompt caching documentation. https://platform.claude.com/docs/en/build-with-claude/prompt-caching
5. Berk Kalelioğlu, "MCP Gateway Benchmark: Latency & Security of 6 Gateways", AIMultiple, updated 2026-10-05, with its data download. https://aimultiple.com/mcp-gateway
6. Thiago Mendes, "MCP Server Performance Benchmark v2", TM Dev Lab, 2026-02-28. https://www.tmdevlab.com/mcp-server-performance-benchmark-v2.html
7. Anthropic, tool search tool documentation. https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
8. OpenAI, function calling guide. https://developers.openai.com/api/docs/guides/function-calling
9. OpenTelemetry MCP semantic conventions. https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md
10. MCP specification, Caching, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
11. MCP specification, Tools, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
12. MCP Go SDK, `mcp/features.go`. https://github.com/modelcontextprotocol/go-sdk/blob/main/mcp/features.go
13. Kuadrant `mcp-gateway` broker, aggregated `ttlMs` and `cacheScope`. https://github.com/Kuadrant/mcp-gateway/blob/main/internal/broker/protocol_handler_2026.go
14. MCP Python SDK, client caching. https://py.sdk.modelcontextprotocol.io/client/caching/
15. Saha, Wang and Manoharan, "Hybrid Semantic Tool Discovery for Enterprise MCP Gateway: Architecture and Implementation", PayPal, arXiv:2608.23992, preprint, 2026-08-25. https://arxiv.org/abs/2608.23992
16. Şevval Alper, "Code Execution with MCP", AIMultiple, updated 2026-08-14. https://aimultiple.com/code-execution-with-mcp
17. rmcp pull request #683, "feat(streamable-http): add json_response option for stateless server mode", merged 2026-02-27. https://github.com/modelcontextprotocol/rust-sdk/pull/683
18. MCP specification, Streamable HTTP, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
19. Yaseen Ahmed, "MADBench: Measuring Agentic Databases: Quantifying the Protocol Tax of MCP-Mediated Query Workloads", master's thesis presentation, University of Waterloo, 2026-09-18. https://cs.uwaterloo.ca/events/masters-thesis-presentation-data-systems-madbench-measuring-agentic-databases-quantifying-protocol-tax-mcp-mediated-query-workloads
