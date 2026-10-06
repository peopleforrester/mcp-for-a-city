---
title: "MCP Token Economics and the Arc to Fewer Tools"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
audience: "MCP maintainers and enterprise platform engineers, MCP Dev Summit Toronto 2026-10-06"
---

<!-- ABOUTME: Verified account of where MCP's token cost goes, how it interacts with prompt -->
<!-- ABOUTME: caching, and the security consequences of shrinking the tool surface to fix it. -->

# MCP Token Economics and the Arc to Fewer Tools

Research for topics A and B of "Governing MCP for a Workforce the Size of a City".

Companion to `06-research-and-source-ledger/ops/mcp-operations-at-scale-2026-09.md`. That file's Section 7
documents three widely circulated figures that are wrong. This file does not repeat them,
and Section 10 below adds two more that also fail verification.

## Sourcing labels

| Label | Meaning |
|---|---|
| **[PRIMARY]** | The spec, official docs, or a first-hand account by the people who built the thing |
| **[DERIVED]** | Arithmetic done here from published inputs, with the inputs named |
| **[PEER]** | Peer-reviewed or arXiv preprint with a stated method |
| **[VENDOR]** | Vendor marketing. A floor for scepticism, not evidence |
| **[SECONDHAND]** | Reported by someone who did not measure it |
| **[UNVERIFIED]** | Could not be traced to a source that makes the claim |

Everything below was fetched and read on **2026-09-18** unless a line says otherwise.

---

# PART A: TOKEN ECONOMICS

## 1. Where the tokens actually go

### 1.1 The maintainers' own framing, verified verbatim

Re-fetched and reproduced character for character on 2026-09-18. Authors David Soria
Parra and Den Delimarsky, lead maintainers, published 2026-08-22, under the heading
**"Improved primitives"**:

> "The other challenge we need to address for primitives is their ever-growing scale.
> Connecting to a server with a hundred tools means the model pays for that entire surface
> before the user has asked a single question, and tool selection tends to get worse as the
> list grows. We're starting a progressive discovery effort so a server can offer a small
> entry point and reveal more of its catalog as the conversation narrows."

<https://blog.modelcontextprotocol.io/posts/mcp-roadmap/> [PRIMARY]

**Quote it with the opening clause.** The shortened form circulating as "A server with a
hundred tools means the model pays for that entire surface" is close but is not what the
page says. The real sentence begins "Connecting to a server with a hundred tools". If the
talk puts this on a slide, put the whole sentence up, because the room contains the people
who wrote it.

The third sentence is the one most quotations drop, and it is the useful one for a
maintainer audience: progressive discovery is stated as an **effort that is starting**, not
a shipped protocol feature. See Section 4.2 on why that gap matters.

### 1.2 The four places tokens go

| # | Where | Mechanism | Quantified evidence |
|---|---|---|---|
| T1 | **Tool definitions in the prompt prefix** | Every connected server's `tools/list` output is serialised into the model's `tools` array before turn one | 55K tokens for five servers, below |
| T2 | **Tool results in context** | Every intermediate result of a chained call passes through the model even when the model does nothing with it | 150K to 2K on one workflow, below |
| T3 | **Multi-turn accumulation** | Definitions are re-sent every turn; results stay in the transcript; post-2026-07-28, cross-call state moved from the transport into tool arguments and therefore into the window | See 1.5 |
| T4 | **Schema verbosity** | Descriptions, argument names and argument descriptions are all prompt text, and JSON Schema 2020-12 now permits `oneOf`/`allOf`/`$ref` composition in `inputSchema` and `outputSchema` | See 1.6 |

### 1.3 T1, tool definitions: the measured figures and their methodology

All Anthropic figures are from two engineering posts and one product doc. Anthropic builds
both a model and a client, so these are first-hand measurements of their own stack and
[PRIMARY] for that stack only. No independent replication was found.

| Measurement | Figure | Source | Label |
|---|---|---|---|
| GitHub, Slack, Sentry, Grafana and Splunk connected, tool definitions only | **~55,000 tokens** before the conversation starts | Anthropic, advanced tool use, 2025-11-24 | [PRIMARY] |
| Same setup, stated as a tool count | **58 tools consuming approximately 55K tokens** | Same | [PRIMARY] |
| Same setup, restated in the product doc | "A typical multiserver setup (GitHub, Slack, Sentry, Grafana, and Splunk) can consume ~55k tokens in definitions before Claude does any work" | Tool search tool doc | [PRIMARY] |
| A larger unnamed setup | "tool definitions consume 134K tokens before optimization" | Anthropic, advanced tool use | [PRIMARY] |
| Traditional upfront loading in their eval harness | **~77K tokens before any work begins** | Same | [PRIMARY] |
| Same workload under Tool Search Tool | **~8.7K tokens, preserving 95% of context window** | Same | [PRIMARY] |
| Context left for work, upfront vs tool search | **122,800 vs 191,300 tokens** | Same | [PRIMARY] |
| The spec docs' own illustration of the same effect | "~150,000 tokens on definitions alone, while progressive discovery uses ~2,000 tokens" | MCP client best practices, progressive-discovery diagram alt text | [PRIMARY] |

**Methodology caveat, stated because the talk should state it.** None of these posts
publishes a tokeniser, a server version, or the exact tool set. "GitHub, Slack, Sentry,
Grafana, Splunk" names five products, not five pinned server builds, and server tool
surfaces change weekly. The figures are internally consistent across three Anthropic
surfaces and are the best published numbers that exist, and they are not reproducible from
the published material. Treat 55K as an order of magnitude that Anthropic stands behind,
not as a constant.

Sources: <https://www.anthropic.com/engineering/advanced-tool-use>,
<https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>,
<https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md>

### 1.4 T2, tool results: the larger and less discussed half

From Anthropic's code-execution post, 2025-11-04 [PRIMARY]:

> "This reduces the token usage from 150,000 tokens to 2,000 tokens, a time and cost saving
> of 98.7%."

That is one Google Drive to Salesforce workflow, and it is the most-quoted MCP token figure
in circulation. Read the mechanism rather than the number: the saving is not mostly from
loading fewer definitions, it is from **intermediate results never entering the model's
context**. The same post:

> "Tool descriptions occupy more context window space, increasing response time and costs.
> In cases where agents are connected to thousands of tools, they'll need to process
> hundreds of thousands of tokens before reading a request."

and on the result side:

> "Every intermediate result must pass through the model."

with the worked example that for "a 2-hour sales meeting, that could mean processing an
additional 50,000 tokens" because the transcript flows through the window twice.

The 98.7% figure therefore belongs to **code execution**, and it is a single-workflow
result, not an average. Anthropic's own average for the same feature across complex
research tasks is much smaller: **43,588 to 27,297 tokens, a 37% reduction**. If a slide
needs one number for code execution, 37% is the honest one and 98.7% is the best case.

<https://www.anthropic.com/engineering/code-execution-with-mcp>

### 1.5 T3, multi-turn accumulation, and why 2026-07-28 made it worse

The spec's removal of protocol-level sessions is a token event as well as an architecture
event. From the changelog, major change 1 [PRIMARY]:

> "Servers that need cross-call state use explicit, server-minted handles passed as ordinary
> tool arguments."

The tools page says the same thing in non-normative guidance and names the consequence:

> "The model is responsible for carrying `basket_id` forward"

State that used to live in an HTTP header now lives in the context window and is re-sent
every turn for as long as the conversation needs it. Artemii Amelin's framing of the
accounting, 2026-09-01 [PRIMARY, practitioner opinion]:

> "A protocol that is cheap per request and expensive per hour benchmarks very well and
> behaves differently in production."

This is the cost item nobody budgeted for, because it moved from an infrastructure line to a
token line and the two are owned by different teams.

<https://modelcontextprotocol.io/specification/2026-07-28/changelog>,
<https://modelcontextprotocol.io/specification/2026-07-28/server/tools>,
<https://dev.to/artem_a/mcp-2026-07-28-deleted-the-session-the-state-moved-into-your-context-window-1hde>

### 1.6 T4, schema verbosity

Three verified facts, no published token measurement isolating schema verbosity alone.

1. **Search indexes the whole schema, so the whole schema is prompt surface.** Anthropic's
   tool search "searches tool names, descriptions, argument names, and argument
   descriptions" [PRIMARY]. Every one of those fields is text the model reads when the tool
   is loaded.
2. **Descriptions are the highest-leverage text in a server.** Anthropic: prompt-engineering
   tool descriptions is "one of the most effective methods for improving tools", since
   descriptions are "loaded into your agents' context" [PRIMARY]. Microsoft Learn's team
   found that minor wording changes "materially influenced tool activation rates", and built
   automated evaluation to tune them [PRIMARY].
3. **The 2026-07-28 spec widened what a schema may contain.** Minor change 10 loosens
   `inputSchema` and `outputSchema` "to allow any JSON Schema 2020-12 keywords" with `$ref`
   resolution requirements and "composition-keyword resource bounds" (SEP-2106) [PRIMARY].
   The spec had to add resource bounds, which is an admission that schemas can now be made
   arbitrarily large. Clients **MUST NOT** auto-dereference external `$ref` URIs.

**No published figure separates description bytes from schema bytes in any real server.**
Mark any such claim [UNVERIFIED]. This is a gap a maintainer audience could close, and it is
worth asking the room for.

<https://www.anthropic.com/engineering/writing-tools-for-agents>,
<https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/>

### 1.7 The cost arithmetic

**Published inputs, both re-verified 2026-09-18:**

- Anthropic's five-server definition load: ~55,000 tokens.
- Claude Opus 5 list price: $5 per million input tokens. Cache reads 0.1x ($0.50/MTok).
  Five-minute cache writes 1.25x ($6.25/MTok). One-hour cache writes 2x ($10/MTok).
  <https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching>

**[DERIVED, this research, 2026-09-18]** Per model turn, carrying that surface:

| Condition | Arithmetic | Per turn |
|---|---|---|
| Definitions sent uncached every turn | 55,000 x $5 / 1e6 | **$0.275** |
| Definitions served from a warm prompt cache | 55,000 x $0.50 / 1e6 | **$0.0275** |
| First turn, writing a five-minute cache entry | 55,000 x $6.25 / 1e6 | **$0.344** |

The ratio is the point: **a cache hit costs one tenth of a cache miss, and a cache write
costs 1.25 times a miss.** Both numbers matter in Section 2, because they set the exchange
rate for the cache-invalidation trade.

Scaled illustratively to a workforce (assumptions are mine and are arguable): 10,000
employees, 20 agent turns each per working day, 250 working days, so 50 million turns a
year, tool definitions alone.

| Condition | Annual |
|---|---|
| Uncached | ~$13.75M |
| Fully cached | ~$1.38M |
| Definitions cut 85% (Anthropic's measured tool-search reduction), uncached | ~$2.06M |

Illustrative, not measured. The shape is what survives: **prompt caching is worth roughly as
much as an 85% cut to the tool surface, and it is free.** That is why Section 2 is the
non-obvious part of this topic.

---

## 2. The prompt cache interaction

This is the part of the token story that is counter-intuitive, the part where the published
guidance and the published implementations appear to disagree, and the part where the
disagreement resolves in a way that is worth a slide.

### 2.1 The warning, verified verbatim

From the official MCP client best practices for 2026-07-28, under the heading **"Interaction
with Prompt Caching"** [PRIMARY]:

> "Most providers cache the prompt prefix, including the `tools` array. Adding or removing
> tool definitions mid-conversation invalidates that cache, and the resulting miss can cost
> more tokens than the definitions you removed. To preserve caching:
>
> * Append newly discovered definitions after the cache breakpoint rather than re-sorting the
>   `tools` array, or route every call through a single stable `call_tool({name, args})`
>   meta-tool so the array never changes.
> * Treat server disconnection as a conversation-boundary operation rather than a per-turn one.
> * Consult your provider's caching documentation alongside the tool-search links above."

<https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md>

**The fix for tool sprawl can cost more than the sprawl.** A naive progressive-discovery
host that mutates the `tools` array per turn pays a full cache miss every turn, and by the
arithmetic in 1.7 a miss is ten times a hit. Removing 20% of a 55K surface saves 11K tokens
of definitions and costs a miss on the remaining 44K plus the entire system prompt and
transcript.

### 2.2 How the invalidation actually works, per provider

**Anthropic.** The cache prefix is built in a fixed order and tools are at the front:

> "Cache prefixes are created in the following order: `tools`, `system`, then `messages`.
> This order forms a hierarchy where each level builds upon the previous ones."

and the invalidation rule, verbatim from the same doc:

> "Modifying tool definitions (names, descriptions, parameters) invalidates the entire cache"

The published table shows a tool-definition change invalidating the tools cache, the system
cache **and** the messages cache. Because `tools` sits at the head of the hierarchy, a
one-character change to one tool description throws away the cached system prompt and the
cached transcript too. Up to four cache breakpoints; minimum cacheable prefix 512 tokens on
Opus 5 and the Fable/Mythos 5.1 generation, 1,024 on Sonnet 5 and Opus 4.8, 4,096 on Opus
4.5 and Haiku 4.5. [PRIMARY]

**OpenAI.** Same shape, stated differently:

> "OpenAI caches the model's full rendered context including OpenAI-provided instructions,
> developer messages, tool definitions, and conversation history"

> "Cache reuse requires the entire rendered prefix to match. If content or a relevant setting
> changes before a breakpoint, the prefix after that change cannot match the existing cache
> entry."

Tool modifications are named explicitly among the invalidating changes. Caching is on by
default; minimum 1,024 visible input tokens on GPT-5.6 and later; cached reads 0.1x, cached
writes 1.25x, which is the same exchange rate as Anthropic's. Their guidance is the general
form of the MCP doc's advice:

> "Put stable developer instructions and shared reference material first. If developer
> instructions or shared material contain timestamps, user-specific content, or other dynamic
> content, place those at the end rather than the beginning"

<https://developers.openai.com/api/docs/guides/prompt-caching> [PRIMARY]

**Convergence worth naming from the stage:** two independent vendors put tool definitions at
the head of the cache prefix and invalidate everything downstream when they change. This is
not an Anthropic quirk. Any host that reorders or mutates the tools array is paying for it
on both platforms.

### 2.3 Both vendors' native tool search sidesteps the problem entirely

This is the resolution, and it is the slide.

**Anthropic**, verbatim from the tool search tool doc [PRIMARY]:

> "Internally, the API excludes deferred tools from the system-prompt prefix. When Claude
> discovers a deferred tool through tool search, the API appends a `tool_reference` block
> inline in the conversation, then expands it into the full tool definition before passing it
> to Claude. The prefix is untouched, so prompt caching is preserved."

**OpenAI**, verbatim [PRIMARY]:

> "allows the model's cache to be preserved from one request to another, lowering overall
> costs and boosting speed."

with tools "loaded at the end of the model's context window" for both the hosted and the
client-executed variants.

**So the warning in 2.1 is a warning about naive hosts, not about progressive discovery as
such.** Both platforms took the first of the MCP doc's two mitigations (append after the
breakpoint) and built it into the API. The failure mode belongs to a host that rolls its own
discovery by rewriting the `tools` array, which is exactly what the MCP guidance tells you
not to do and exactly what an obvious implementation does.

Three implementation details that matter and are easy to get wrong:

1. **You still send every definition on every request.** Anthropic: "You still send every
   tool's full definition in the `tools` array on every request, including the deferred ones.
   The API needs them server-side to run the search and expand `tool_reference` blocks." The
   **context** cost drops; the bytes on the wire do not. A gateway metering request size will
   see no improvement at all.
2. **A deferred tool cannot carry a cache breakpoint.** "A tool with `defer_loading: true`
   can't also carry `cache_control`: the API returns a 400. Put the cache breakpoint on a
   non-deferred tool."
3. **At least one tool must stay loaded.** "At least one tool must have defer_loading=false."
   Anthropic's guidance is to keep "your 3-5 most frequently used tools non-deferred".

Tool search is not separately metered: "the tool definitions that search loads into context
count as input tokens like any other tool definition."

<https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>,
<https://developers.openai.com/api/docs/guides/tools-tool-search>

### 2.4 What deterministic `tools/list` ordering is for

Spec 2026-07-28, minor change 3, verbatim [PRIMARY]:

> "Servers **SHOULD** return tools from `tools/list` in a deterministic order to enable
> client-side caching and improve LLM prompt cache hit rates."

The tools page states it at greater length:

> "Servers **SHOULD** return tools in a deterministic order (i.e., the same ordering across
> requests when the underlying set of tools has not changed). Deterministic ordering enables
> clients to reliably cache the tool list and improves LLM prompt cache hit rates when tools
> are included in model context."

**Read it as an admission.** A SHOULD this specific only gets written after somebody watched
a server return the same tools in a different order on consecutive calls, serialise into a
different `tools` array, and miss the prompt cache every turn for no reason. The cost of
that bug, by 1.7, is $0.275 a turn instead of $0.0275 across an unchanged tool surface.

**This is the cheapest fix in the whole of Part A.** Sorting a list is free, it needs no
client change, no gateway, and no sandbox, and it is worth an order of magnitude on the
largest line item. If the talk gives server authors one instruction, this is a strong
candidate.

### 2.5 What a gateway or registry does to cache behaviour

Three verified mechanisms, and one genuine hazard the spec names itself.

**Mechanism 1: MCP-level caching is now in the protocol.** Every `resultType: "complete"`
result from `server/discover`, `tools/list`, `prompts/list`, `resources/list`,
`resources/templates/list` and `resources/read` MUST carry `ttlMs` and `cacheScope`
(SEP-2549) [PRIMARY]. `ttlMs` is "analogous to HTTP `Cache-Control: max-age`". Absent, the
client assumes 0 and re-fetches. This is protocol-level caching of the tool **list**, which
is a different cache from the model provider's prompt cache. Do not conflate the two on a
slide: the MCP cache saves an HTTP round trip to the server, the prompt cache saves money at
the model.

**Mechanism 2: `cacheScope` decides whether a shared intermediary may serve one caller's
tool list to another.** Verbatim:

> `"public"`: "The response does not contain user-specific data. Any client, shared gateway,
> or caching proxy **MAY** store and serve the cached response to any user."
>
> `"private"`: "The response contains private data that is not meant to be shared between
> callers. Cached responses **MAY** be reused for the same authorization context. Caches
> **MUST NOT** be shared across authorization contexts (e.g. a different access token requires
> a different cache)."

And the choosing guidance: `"public"` "is appropriate for lists of tools, prompts, and
resource templates when they are identical for all users"; `"private"` for "filtered list
results that vary per user".

**Mechanism 3: a gateway that aggregates servers must rename tools, and renaming is a cache
event.** The spec is explicit that name uniqueness is per server:

> "Clients or proxies that aggregate tools from multiple servers **MAY** encounter naming
> collisions (for example, two servers each exposing a `search` tool) and **SHOULD** implement
> a disambiguation strategy such as prefixing tool names with a server identifier."

A prefixing gateway changes every tool name it passes through. That is stable across turns,
so it costs nothing ongoing, and it means the enterprise's prompt cache is keyed on the
gateway's naming scheme. **Change the prefix scheme and you cold-start the prompt cache for
every agent in the company on the same deploy.** [DERIVED from the spec's disambiguation
guidance plus the vendor invalidation rules in 2.2; no published account of this happening.]

**The hazard, stated by the spec.** Section "Security Considerations" of the caching
utility, verbatim:

> "Servers MUST be aware that responses with a `"public"` `cacheScope` may be shared between
> callers even if the Result is coming from an authenticated endpoint. For example, the Result
> from an authenticated `tools/list` call with a `"public"` `cacheScope` may be cached by a
> client and may be shared outside of the initial requests authorization context. (i.e.
> different access tokens can leverage the same cache)."
>
> "Server implementors ... MUST apply appropriate per-primitive access controls, and MUST NOT
> rely on `cacheScope` alone to prevent unauthorized access to primitives."

See Section 5.4. This is where the cost lever and the security lever collide.

<https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching>,
<https://modelcontextprotocol.io/specification/2026-07-28/server/tools>

---

## 3. Downstream client problems caused by token growth

### 3.1 Context exhaustion and truncation

| Claim | Figure | Source | Label |
|---|---|---|---|
| Three-server combo (GitHub, Playwright, IDE) consumes 143,000 of a 200,000 window on schemas alone | 72% of the window | AgentPMT via Unblocked | [SECONDHAND] |
| GitHub MCP server, 35 tools | ~26,000 tokens | AgentPMT | [SECONDHAND] |
| Slack MCP server, 11 tools | ~21,000 tokens | AgentPMT | [SECONDHAND] |
| Five-server setup at conversation start | ~55,000 tokens | Anthropic | [PRIMARY] |
| Anthropic's own worst published case | 134,000 tokens of definitions before optimisation | Anthropic | [PRIMARY] |

The AgentPMT numbers are the ones in everyone's slides and they are secondhand with no
published method. **They are also the same source that inverted the RAG-MCP finding** (ops
file Section 7.1). Prefer Anthropic's 55K and 134K, which are first-hand for a real stack.

### 3.2 Degraded tool selection as the pool grows

This is the best-evidenced downstream harm, with two independent sources that agree on the
threshold.

| Source | Finding | Label |
|---|---|---|
| RAG-MCP, arXiv 2505.03275 | Retrieval success **above 90% for candidate positions 1 to 30**; degrades through 31 to 70 from semantic overlap between tool descriptions; **substantial degradation beyond ~100**; pool scaled 1 to 11,100 | [PEER] |
| Anthropic tool search doc | "Claude's ability to pick the right tool degrades once you exceed 30-50 available tools." | [PRIMARY] |
| MCP maintainers, roadmap | "tool selection tends to get worse as the list grows" | [PRIMARY] |
| OpenAI function calling guide | "Keep the number of initially available functions small for higher accuracy"; keep "fewer than 20 functions available at the start of a turn at any one time, though this is just a soft suggestion" | [PRIMARY] |
| OpenAI tool search guide | "aim to keep each namespace to fewer than 10 functions for better token efficiency and model performance" | [PRIMARY] |

**A peer-reviewed study and two model vendors independently land on roughly 30 as the point
where selection starts to hurt.** That convergence is stronger evidence than any single
number and it is the honest replacement for the inverted "43% to 14%" figure. OpenAI's 20 and
10 are tighter still, and they are guidance rather than measurement.

**Do not use** the circulating "43% collapses to under 14% as tool count grows". 43.13% is
RAG-MCP's proposed method and 13.62% is its naive baseline; it is a method comparison, not a
degradation curve. Verified again 2026-09-18 in the paper's abstract, and the error is live
in at least two secondary sources (ops file Section 7.1, plus Unblocked, which repeats it
verbatim as "from a 43% baseline to under 14%").

### 3.3 Latency

| Claim | Figure | Source | Label |
|---|---|---|---|
| Direct tool calling round trips avoided by code execution | "Eliminate 19+ inference passes"; "hundreds of milliseconds to seconds" per round trip avoided | Anthropic, advanced tool use | [PRIMARY] |
| Code execution adds per-call latency | ~7% (10.37s vs 9.66s) | AIMultiple, via summaries; original not read here | [SECONDHAND] |
| Tool-definition loading itself | "Loading every tool definition into the model's context window upfront wastes tokens, increases latency, and degrades model performance" | MCP client best practices | [PRIMARY, unquantified] |

Code execution cuts total latency by removing inference passes and adds latency per call
because the model writes more output tokens. Both are true. On Opus 5, output tokens are 5x
input, so an input-side win can be partly repaid on the output side.

### 3.4 Cost per task, and the metric that actually matters

Anthropic's recommended eval metric set names **"tokens per completed task"**, not tokens per
call. The distinction is the whole argument against a per-request view: a server needing 40
calls where another needs 3 is a cost problem that per-request metering cannot see [PRIMARY,
writing tools for agents].

Amelin's version of the same point, for the protocol rather than the server: "cheap per
request and expensive per hour".

### 3.5 Rate limit and quota pressure

**No published MCP-specific quota incident was found.** Mark it [UNVERIFIED] and do not
assert it from the stage as a cited finding. What can be said with sourcing:

- Tool search has its own rate limit and returns `too_many_requests` as an `error_code`
  inside a 200 response, not as an HTTP error [PRIMARY, Anthropic]. A monitor watching HTTP
  status codes will not see it. This is the same class of failure as `isError: true` (ops
  file F13).
- Retry storms amplify a degraded server, and "Agents retry more eagerly than humans"
  [PRIMARY, pgEdge].

### 3.6 What happens when several servers are connected at once

Verified mechanisms, in order of how certain each is.

1. **Definitions add linearly and the window does not.** Five servers is ~55K [PRIMARY].
2. **Tool-name collisions are guaranteed at scale and the spec says so**: "two servers each
   exposing a `search` tool". Disambiguation is a SHOULD on the client or proxy, not a MUST,
   so behaviour differs per client [PRIMARY].
3. **Selection accuracy degrades past roughly 30 tools**, which three or four servers reach
   easily (35 tools in the GitHub server alone) [PEER + PRIMARY].
4. **Cross-server data flow is an untrusted-input problem.** "Tool results from one server are
   untrusted input to another" [PRIMARY, MCP client best practices]. Connecting more servers
   does not just cost more, it composes trust boundaries.
5. **Per-client behaviour is not documented anywhere.** The ops file's [MEASURED-HERE] finding
   stands: there is no per-client feature support matrix in the MCP docs. **Re-checked
   2026-09-18 for the specific claim that Cursor caps tools at 40: that number circulates
   widely and is not in Cursor's own MCP documentation, which states no tool limit at all.**
   Mark the 40-tool cap [UNVERIFIED] and do not repeat it.

<https://cursor.com/docs/context/mcp>

---

## 4. Cost control that works, with effect sizes correctly attributed

**Read this table before quoting any of these numbers.** The published secondary reporting
routinely attaches the Tool Search Tool's accuracy result to programmatic tool calling. The
two features have different effect sizes.

| Feature | Token effect | Accuracy effect | Benchmark | Label |
|---|---|---|---|---|
| **Tool Search Tool** | 77K to 8.7K (~85 to 89%); 95% of window preserved; 122,800 to 191,300 tokens left for work | **49% to 74% on Opus 4**; **79.5% to 88.1% on Opus 4.5** | Anthropic MCP evaluations | [PRIMARY] |
| **Programmatic tool calling (code execution)** | **43,588 to 27,297, a 37% reduction** (average, complex research tasks); 150,000 to 2,000 (98.7%) on one Drive-to-Salesforce workflow | **25.6% to 28.5%** internal knowledge retrieval; **46.5% to 51.2%** GIA | Anthropic | [PRIMARY] |
| **Tool use examples** | not reported | **72% to 90%** | complex parameter handling | [PRIMARY] |
| **Response format enum** (`concise` / `detailed`) | 206 tokens to 72 tokens on the same data | not reported | Anthropic's own example | [PRIMARY] |

**The correction, stated plainly:** 49% to 74% is Tool Search Tool on Opus 4. It is not code
execution. Code execution's accuracy gains are single-digit points on two benchmarks. A slide
claiming code execution improves tool selection by 25 points is citing the wrong row.

### 4.1 Tool filtering and per-role tool sets

The cheapest control, and the only one the spec makes a first-class protocol capability.

**Spec-level.** `tools/list` "**MAY** vary by the authorization presented on the request, for
example, returning only the tools the caller's granted scopes permit, since credentials are
per-request input, not connection state" [PRIMARY, tools page]. Per-role tool sets are
sanctioned by the protocol as of 2026-07-28, and the stateless redesign is what makes them
work: the list no longer varies per connection, it varies per credential.

**Implementation-level, with a primary source.** The GitHub MCP server ships `--toolsets`
(and `GITHUB_TOOLSETS`), `--tools` (`GITHUB_TOOLS`), and `--read-only`. Their stated
rationale, verbatim:

> "Enabling only the toolsets that you need can help the LLM with tool choice and reduce the
> context size."

Precedence rule worth noting because it is the safe default: "write tools are skipped if
`--read-only` is set, even if explicitly requested via `--tools`." The `default` toolset is
context, repos, issues, pull_requests, users.

Docker's MCP Gateway does the same at the aggregation layer, with per-tool allow/deny in
`<server>.<tool>` dot notation (`--enable github.create_issue`, `--disable
github.search_code`) [PRIMARY].

**Measured effect size: none published.** Nobody has published "we filtered from N to M tools
and measured X". The effect is derivable from Section 1 (definitions are linear in tool
count) but it has not been measured by anyone whose work is public. That is a gap worth
naming.

<https://github.com/github/github-mcp-server>, <https://github.com/docker/mcp-gateway>

### 4.2 Dynamic and progressive discovery

Now official guidance, with an unusually specific threshold for a spec document [PRIMARY]:

> "Implement a threshold as a percentage of the context window. For example, 1%-5%. Load tool
> definitions. Once the threshold is reached, switch to progressive discovery."

Three-layer pattern: **catalog** (`search_tools` returns names plus one-line descriptions),
**inspect** (`get_tool_details` returns one full schema), **execute**. Four retrieval
strategies with honest cost notes: keyword (BM25, regex), embedding, subagent ("usually works
very well but can be more costly"), hybrid. The guidance is to prefer the platform's native
implementation "when available", and to build your own "when you need specialized retrieval
logic (e.g., domain-specific ranking or **access-control filtering**)". That parenthesis is
the enterprise case, and Section 5.2 is about what it buys.

**Measured effect: 85% token reduction; MCP eval accuracy 79.5% to 88.1% on Opus 4.5** (the
Tool Search Tool row above).

**The interop gap is real and should be said out loud.** `search_tools` and `get_tool_details`
are patterns in a best-practices document. Neither is a protocol method. The maintainers'
roadmap describes progressive discovery as an effort that is "starting". So a server cannot
know, cannot influence, and cannot reason about whether its tools are loaded eagerly or on
demand on any given client, which means it cannot publish its own context cost.

### 4.3 Dynamic server management

The same document extends discovery from tools to whole servers: maintain a registry of
available servers with high-level descriptions, connect when the model determines it needs
that server, "Disconnect servers that are no longer relevant to the current task, freeing
context" [PRIMARY]. An agent skill can declare which servers it needs, so the host connects
them on skill invocation.

Block shipped this independently before it was written down, as "dynamic context management
that enables and disables servers per user query" [SECONDHAND, All Things Open]. Convergent
evolution between a large deployment and the spec is a reason to believe this one.

**Caution from 2.1:** "Treat server disconnection as a conversation-boundary operation rather
than a per-turn one." Disconnecting a server mid-conversation to free context invalidates the
prompt cache for everything.

### 4.4 Code execution with MCP instead of direct tool calls

Effect sizes: **37% average, 98.7% best case, 25.6% to 28.5% and 46.5% to 51.2% on accuracy.**
Costs: a sandbox to build and run, ~7% per-call latency [SECONDHAND], and output tokens at 5x
input on Opus 5.

Sandbox options named by the spec, with host languages: Deno and `isolated-vm` (JavaScript),
Monty (Python, experimental), pctx (TypeScript, early-stage), Wasmtime (any, via Wasm). The
spec frames these as "example runtimes rather than endorsements" [PRIMARY].

### 4.5 Result truncation, pagination, and output guards

| Control | Figure | Source | Label |
|---|---|---|---|
| Claude Code default tool-response cap | **25,000 tokens** | Anthropic | [PRIMARY] |
| `ResponseFormat` enum, same data | **206 tokens detailed, 72 concise** | Anthropic | [PRIMARY] |
| Block's hard output guard | files over **400kB** raise a tool execution error | Block | [PRIMARY] |
| Recommended techniques | "pagination, range selection, filtering, and/or truncation with sensible default parameter values" | Anthropic | [PRIMARY] |

Block's guard is the one to quote to server authors, because it is enforced by the server
rather than requested of the client: "Explicitly raise an MCP tool execution error" when the
limit is exceeded, which lets the agent recover rather than silently blowing the window.

`tools/list` itself supports pagination, and each page is independently cacheable with its own
`ttlMs`. Servers **MUST** apply the same `cacheScope` to every page of a given list request
[PRIMARY].

### 4.6 Caching

Covered in Section 2. Effect size: **10x on the definition line item**, free, and defeated by
non-deterministic `tools/list` ordering.

---

## 5. Security interaction with token economics

The literature treats cost and security as separate topics. They are the same lever pulled
for two reasons, and sometimes the same lever pulled in opposite directions. This section is
the original contribution of this file. Every claim is sourced; the synthesis is labelled as
synthesis.

### 5.1 Does filtering the tool surface reduce attack surface as well as cost?

**Yes, and this is the strongest cost-security alignment in the whole protocol.** Three
independent lines of evidence.

**Evidence 1: a tool the model cannot see cannot be induced to call.** MCPTox measured tool
poisoning across 45 live real-world MCP servers, 353 authentic tools, 1,348 malicious cases (1,312 in v1; v2 read 2026-10-06)
in 10 risk categories. Attack success reached **72.8% on o1-mini**. The best refusal rate
observed, on Claude-3.7-Sonnet, was **under 3%**. More capable models were **more**
susceptible, which the authors attribute to "the attack exploits their superior
instruction-following abilities" [PEER, arXiv:2508.14925]. A model-side control that fails 97%
of the time at its best is not a control; removing the tool from the surface is.

**Evidence 2: the spec makes per-credential filtering a protocol capability.** `tools/list`
MAY vary by the authorization presented (Section 4.1). So the same mechanism that cuts the
token bill cuts the reachable surface, and after 2026-07-28 it is credential-scoped rather
than connection-scoped, which is what makes it auditable.

**Evidence 3: the read-only precedent, twice, from opposite directions.**
- GitHub's server: `--read-only` overrides an explicit `--tools` request for a write tool
  [PRIMARY].
- General Analysis on the Supabase breach: read-only mode "would have prevented the data
  exfiltration write-back in this case" [PRIMARY].

One is a cost-and-usability feature. One is an incident post-mortem. They describe the same
switch.

**[SYNTHESIS, this research]** Tool filtering is the rare control with no trade-off: it
reduces tokens, improves selection accuracy past the ~30-tool threshold, and shrinks the set
of tools an injected instruction can reach. If the talk recommends one thing to a platform
team, this is it, and it should be sold on all three grounds at once, because the cost
argument gets budget and the security argument gets mandate.

### 5.2 Does dynamic discovery make poisoned descriptions easier or harder to catch?

**Harder in one specific, mechanical way, and the reason is that descriptions are precisely
what the discovery index searches.**

The chain, each link sourced:

1. **Tool poisoning hides instructions in the description**, which enters the model's context
   as trusted content and renders benignly in the clients Invariant tested [PRIMARY, Invariant
   Labs 2025-04-01].
2. **Discovery ranks on description text.** Anthropic's tool search searches "tool names,
   descriptions, argument names, and argument descriptions" [PRIMARY]. The spec's catalog
   layer returns "matching tool names with brief descriptions" [PRIMARY].
3. **Anthropic's own optimisation advice is, mechanically, discovery-ranking advice**: "Add
   common keywords to tool descriptions to improve discoverability", "Use keywords in
   descriptions that match how users describe tasks" [PRIMARY].

**[SYNTHESIS, this research, marked as synthesis because no source states it]** Progressive
discovery creates an incentive gradient that points the wrong way for defence. A server that
wants to be selected writes a description engineered to win retrieval, and a server that wants
to be *maliciously* selected does exactly the same thing with the same technique. Retrieval
ranking is a new, quiet, per-query channel by which a description competes for the model's
attention, and the competition is invisible to a human who never sees a description that lost.

Two aggravating factors, both verified:

- **Under eager loading, every description is in the window, so a manifest diff catches a rug
  pull.** Under progressive discovery, a description only enters the window when it is
  retrieved, so a poisoned description can sit dormant in a catalog indefinitely and surface
  on one query. The sleeper rug pull is documented [PRIMARY, Invariant, mcp-injection-
  experiments].
- **The spec tells clients to re-index on `list_changed`**: "Re-index the search catalog when
  a server sends `notifications/tools/list_changed`" [PRIMARY]. That is the rug-pull event
  wired directly into the retrieval index, with no mention of re-consent.

**Easier in exactly one respect, and it is worth conceding:** a catalog is a single place to
scan. Pinning a manifest and diffing it is more tractable against one host-side catalog than
against N clients each holding their own view, and the client best practices already tell
hosts to "memoize the definition host-side". The control exists; nothing in the spec asks for
it.

### 5.3 Does code execution change the injection surface?

**It moves it and it shrinks one part of it. It does not remove it, and the spec says so.**

**What improves, per the spec's own security section** [PRIMARY]:

- **Network isolation.** "The sandbox should have no direct network access." Stubs are
  intercepted "over an in-process or stdio channel (so network permissions can stay fully
  denied)".
- **No credential exposure.** "API keys and tokens are held by the host. The generated code
  calls typed functions; the host adds authentication when forwarding to servers."
- **Less untrusted data reaches the model.** Anthropic: "intermediate results stay in the
  execution environment by default... data you don't wish to share with the model can flow
  through your workflow without ever entering the model's context." Plus automatic
  tokenisation of PII, so real email addresses "flow from Google Sheets to Salesforce, but
  never through the model."

That last one is the underrated security property: **the token-saving mechanism and the
data-minimisation mechanism are the same mechanism.** Fewer tool results in context is
simultaneously a smaller bill and a smaller indirect-injection surface, because an injected
instruction in a tool result cannot reach the model if the result never reaches the model.

**What does not improve, per the same section** [PRIMARY]:

- **Authorization is not delegated.** "Approving the script does not grant blanket approval for
  every tool call it makes at runtime; hosts may grant categorical approval... but the broker
  must still evaluate each call against that grant."
- **Cross-server flow is still untrusted.** "Tool results from one server are untrusted input
  to another. The broker should apply the same input-review policy to brokered calls as to
  direct ones; **output truncation alone does not prevent exfiltration**."
- **A new code-execution surface exists.** "Programmatic tool calling introduces a code
  execution surface that requires careful sandboxing."

**[SYNTHESIS]** Code execution converts a large, legible surface (every result in the
transcript, every call approved individually by a human who can read it) into a small,
illegible one (a script the human approves once, executing calls they will not individually
see). The spec compensates with per-call brokering. Whether a given host implements that is
the question to ask a vendor, and it is not visible from the outside.

### 5.4 What a gateway sees, and stops seeing

Four cases, each with a verified basis. This is where "what does the registry actually know"
gets answered.

| Host behaviour | What the gateway still sees | What it loses | Basis |
|---|---|---|---|
| **Progressive tool discovery** (tools deferred in context) | **Everything. `tools/list` is unchanged.** | Nothing | Spec: "The host fetches tool definitions via `tools/list` as normal, but **defers injecting them into the model's context**" [PRIMARY] |
| **Anthropic / OpenAI native tool search** | Everything, plus full definitions on every API request | Nothing at the MCP layer | "You still send every tool's full definition in the `tools` array on every request" [PRIMARY] |
| **Dynamic server management** | Only servers currently connected | **Inventory.** A server nobody has needed today generates no traffic and appears in no gateway log | Spec: connect "only when the model determines it needs that server's capabilities"; "Disconnect servers that are no longer relevant" [PRIMARY] |
| **Code execution** | Every `tools/call`, because the broker "dispatches them as `tools/call` requests" | **The data and the reasoning.** Intermediate results never enter the model, so a gateway logging model context sees a summary line where it used to see the payload | Spec execution architecture [PRIMARY] |

**The first row is the useful correction.** The natural assumption is that deferring tools
blinds the gateway. It does not. Progressive discovery is a host-side decision about the model's
context window, taken **after** `tools/list` has already crossed the wire. A gateway's
inventory of tool definitions is unaffected. What it cannot see, and never could, is which of
those definitions the model was actually shown.

**The third row is the real inventory problem**, and it is the one that matters for a
governance story: dynamic server management makes "how many MCP servers are running here" a
question that gateway traffic cannot answer, because absence of traffic is now the expected
state for most servers most of the time. The ops file's shadow-server test ("ask your security
team how many MCP servers are running right now") gets harder, not easier, as hosts adopt the
spec's recommended cost control.

**And the hazard from 2.5.** Put together:

- A server filters `tools/list` by the caller's granted scopes (spec-sanctioned, Section 4.1).
- The server marks the list `cacheScope: "public"` because "lists of tools... when they are
  identical for all users" is the documented case for public, and the author does not connect
  that their list is no longer identical for all users.
- A shared gateway caches it and serves it across authorization contexts, which the spec says
  it MAY do: "different access tokens can leverage the same cache."

The result is that an unprivileged caller receives the privileged caller's tool list. The
spec anticipates exactly this and says "Server implementors... MUST apply appropriate
per-primitive access controls, and MUST NOT rely on `cacheScope` alone to prevent
unauthorized access to primitives" [PRIMARY].

**[SYNTHESIS]** This is a **new** misconfiguration class created by the same release that made
per-role tool filtering possible. The cost control (cache the tool list at the gateway) and the
security control (vary the tool list by credential) are individually correct and jointly
produce a disclosure. The correct setting is `cacheScope: "private"` for any filtered list,
which is exactly the setting that gives up the shared-cache saving. **The trade is real and
the spec does not price it.** Nothing here is a vulnerability in the spec; it is a footgun the
spec names and then leaves to server authors, which is worth saying to a room of server
authors.

Note also what a public-cached tool list discloses even when access control holds: the
**existence and description** of privileged tools. Tool metadata is reconnaissance.

---

# PART B: THE ARC FROM MANY COMPLEX TOOLS TO FEW

## 6. Published accounts of consolidation

### 6.1 Block's Linear server, the primary source

**[PRIMARY]** Salman Mohammed and Kalvin Chau, Block engineering, 2025-06-16.
<https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers>

Re-fetched 2026-09-18. The three-stage arc, with what drove each move:

**Stage 1, endpoint-shaped.** The first iteration exposed "many tools that were essentially
variations of GraphQL queries under the hood". Driver for change: a workflow like "what issues
is bob@example.com working on" took "anywhere from 4-6 tool calls".

**Stage 2, grouped by entity.** Read-only tools were bundled. Instead of `get_team_members`
and `get_team_projects`, one `get_team_info`. Stated benefit: "the model can now find the
necessary parameters by checking the description of a single, relevant tool instead of
choosing from numerous specific ones". Still insufficient: complex queries still needed
individual calls.

**Stage 3, a query language.** Two foundational tools, **`execute_readonly_query`** and
**`execute_mutation_query`**, accepting GraphQL directly. Result: "what originally took 4+
tool calls is now a single GraphQL call that the model can generate."

**The detail almost every retelling drops, and it is the important one.** Block did not
consolidate to *one* tool. They consolidated to *two*, and the axis they split on is not
functionality. It is risk:

> "Goose tools support three permission levels: _Always Allow_, _Allow Once_, and _Denied_. To
> help users make safe choices, each tool should stick to a single risk level, read-only (low
> risk) or non-read (higher risk)."

> "Tools that mix both make it harder for users to judge the risk accurately."

> "**Do:** Build tools with one risk level only: either read-only (safe) or non-read
> (write/delete). Bundle related read-only actions into a single tool."

> "**Don't:** If possible, don't mix read and write operations in the same tool. It confuses
> users and makes permission settings harder."

They also note the annotation gap: "tool annotations (e.g. `readOnlyHint`) are currently
optional in the MCP spec. However, Goose uses server instructions to construct the system
prompt and tool annotations for smart approval of tool calls."

**Read the two-tool split as the answer to Section 7.** The reason `execute_readonly_query`
and `execute_mutation_query` are separate tools is not that the code differs. It is that a
consent decision has to be attachable to something, and a single `execute_query` tool would
make "Always Allow" unanswerable. **Consolidation stops exactly where the approval boundary
is.** Block arrived at this in a design retrospective; General Analysis arrived at the same
line from an incident (Section 7.1).

Their stated core principle, and the naming principle that supports it:
- "Design top-down from workflows, not bottom-up from API endpoints."
- "Tool names, descriptions, and parameters are treated as prompts for the LLM, so it's really
  important to have clear instructions."

Output guard: files over 400kB "Explicitly raise an MCP tool execution error".

**What it cost and what it broke: not published.** The post is a design retrospective, not a
migration post-mortem. It names no regression, no client breakage, and no rollback. Do not
claim it was free; claim that the cost was not published.

### 6.2 Microsoft Learn: three tools over a large surface

**[PRIMARY]** Zhang, Imasogie and de Bruin, 2026-02-11, re-verified 2026-09-18.

Three tools: `microsoft_docs_search` ("returns titles, content sections, and URLs to the
source article"), `microsoft_docs_fetch` ("fetches the full-page article content for
additional context"), `microsoft_code_sample_search` ("optimized for finding code snippets and
examples within Learn documentation").

The underlying service exposes topK, index selection, thresholds, OData filters, and
vector-versus-hybrid search. All of it was collapsed into search and fetch. Principle, quoted:
**"design tools for the agent workflow, not to mirror internal APIs."**

**What consolidation cost them, and this is the only published number on the cost side of the
whole arc.** Renaming one parameter from `question` to `query` broke, verbatim:

> "2-5% of requests broke until we supported both names (optional) during a deprecation
> window."

Their generalisation: "Defensive evolution is part of operating a public service." Despite
MCP's dynamic discovery model, clients hardcode schemas.

**[SYNTHESIS]** This is the hidden cost of consolidation, and it is structural. Fewer tools
means each tool's schema carries more meaning, so each parameter is load-bearing for more
callers. A 30-tool server can deprecate one tool and affect the fraction of traffic that used
it; a 2-tool server cannot change anything without affecting everyone. **Consolidation
concentrates schema risk in the same way it concentrates authorization risk.**

They also report that tool descriptions materially affect activation rates, and built
automated evaluation to tune them.

### 6.3 GitHub: filtering rather than consolidating

**[PRIMARY]** The GitHub MCP server took the other branch. It kept a large tool surface (35
tools per AgentPMT's secondhand count) and shipped selection controls instead: `--toolsets`,
`--tools`, `--read-only`, a `default` toolset of context/repos/issues/pull_requests/users, and
an `all` escape hatch. Stated reason: "Enabling only the toolsets that you need can help the
LLM with tool choice and reduce the context size."

**This is a genuine fork in the road and the talk should present it as one.** Block moved the
decision to the server author (two tools, always). GitHub moved it to the deployer (many
tools, choose). They optimise the same quantity and distribute the authorization decision to
different people.

### 6.4 Cloudflare Code Mode

**[PRIMARY]** Varda and Pai, 2025-09-26. Central claim is qualitative:

> "agents are able to handle many more tools, and more complex tools, when those tools are
> presented as a TypeScript API."

**The post contains no quantified token comparison.** Verified twice in prior research and not
re-litigated here. The "1.17 million tokens across 2,500+ endpoints" figure attributed to it
is [UNVERIFIED] and must not be repeated. It is still circulating: Unblocked carries it as
"1.17 million tokens of tool definitions" attributed to Cloudflare, February 2026.

<https://blog.cloudflare.com/code-mode/>

### 6.5 Anthropic's own guidance as an account

**[PRIMARY]** From writing tools for agents, this is a worked consolidation example rather
than a case study, and it is the most-quoted sentence in the genre:

> "Instead of implementing a `list_users`, `list_events`, and `create_event` tools, consider
> implementing a `schedule_event` tool which finds availability and schedules an event."

> "More tools don't always lead to better outcomes."

> "too many tools or overlapping tools can also distract agents from pursuing efficient
> strategies."

Note the shape of their example: three tools become one, and the one that results is **more
specific**, not more general. `schedule_event` does a named thing. That is the opposite
direction from `execute_readonly_query`, and Section 7.2 is about why the difference matters.

---

## 7. The counter-evidence: where consolidation hurts

### 7.1 The incident that is the same shape as the endpoint

The Supabase MCP leak, 2025-07-06 to 2025-07-08, documented by General Analysis and by Simon
Willison. Re-verified against General Analysis on 2026-09-18.

**The tool shape.** The server executes SQL through a credential holding `service_role`, which
"bypasses RLS" by design. The attack used two queries: one reading `integration_tokens`, one
inserting the result into `support_messages`.

**The chain.** An attacker embeds instructions in a support ticket. A developer asks Cursor to
review open tickets. The assistant ingests the attacker's text, generates SQL under
`service_role`, and writes the stolen tokens back into the ticket thread the attacker can read.

**The stated weakness**, verbatim: the assistant "ingests untrusted customer text **and** holds
`service_role` privileges."

**Their mitigations, and note which ones are tool-design mitigations:**
- `read_only=true`, running queries as a read-only Postgres user
- restricting to specific tables via `project_ref`
- limiting tool groups via the `features` parameter
- "Keep untrusted results as data" rather than letting them influence tool execution

And the sentence that closes the loop with Block: **read-only mode would have prevented the
exfiltration write-back.**

<https://generalanalysis.com/blog/supabase-mcp-blog>,
<https://simonwillison.net/2025/Jul/6/supabase-mcp-lethal-trifecta/>

### 7.2 The tension, stated precisely

**The two shapes are not equivalent, and conflating them is the error.**

| Shape | Example | What the model supplies | What an approval means |
|---|---|---|---|
| **Consolidated and specific** | `schedule_event`, `get_team_info`, `microsoft_docs_search` | Arguments within a fixed, typed vocabulary | "You may schedule events" |
| **Consolidated and generic** | `execute_query(graphql)`, `execute_sql(query)`, `kubectl_generic(args)` | **An arbitrary program in a second language** | "You may do anything the credential permits" |

Both reduce tool count. Only the second moves the authorization decision from the schema into
the argument string, where no schema validator, no approval UI and no gateway policy can read
it without implementing a parser for that second language.

**The corroborating cases, all verified:**

1. **CVE-2026-47250** (mcp-server-kubernetes, `< 3.7.0`, CVSS 6.1, fixed 3.7.0). The tool is
   `kubectl_generic`. Flags passed straight through, so `--server` and
   `--insecure-skip-tls-verify` were reachable, and the bearer token went to an attacker's
   endpoint. The prior research's remediation is exactly a statement of this tension:
   "Allowlist the arguments, do not blocklist them... Passing user-supplied flags to a CLI is a
   design decision, not an oversight."
2. **Supabase**, above: a generic SQL tool plus an over-scoped credential.
3. **The spec's own example is this shape.** The `x-mcp-header` documentation in the 2026-07-28
   tools page illustrates the feature with:
   `{"name": "execute_sql", "description": "Execute SQL on Google Cloud Spanner", ...}`
   with `region` and `query` parameters. The spec is not endorsing it, and it does not flag it
   either, which tells you how normal this shape has become.
4. **The MCP spec says annotations are not a control.** "For trust & safety and security,
   clients **MUST** consider tool annotations to be untrusted unless they come from trusted
   servers." So `readOnlyHint` on a generic tool is a claim, not an enforcement point. Block
   notes independently that annotations are "currently optional in the MCP spec."

### 7.3 Has anyone written about the tension directly?

**Searched and largely not found, and that absence is itself reportable.**

- **Block states the principle without naming it as a tension**: single risk level per tool,
  don't mix read and write, because it "makes permission settings harder". That is the
  authorization argument for *not* fully consolidating, arrived at from usability.
- **General Analysis states the remedy without generalising it**: read-only mode would have
  prevented it.
- **Jentic's "The MCP Tool Trap"** critiques tool sprawl and proposes a centralised knowledge
  layer. Re-checked 2026-09-18: it does **not** address whether consolidation improves or
  worsens security, beyond a general warning that embedding credentials in manifests
  "dramatically expands the agent's attack surface". It is also the source that mis-cites
  arXiv 2411.15399 (ops file Section 7.4).
- **Unblocked's "MCP tool overload"** is entirely a cost argument. Re-checked 2026-09-18: **no
  documented case of a team reducing tool counts and reporting the cost or the breakage**, and
  it repeats both the inverted RAG-MCP figure and the unverified Cloudflare figure.

**[SYNTHESIS, and the most original claim available to the talk]** The consolidation
literature is written entirely in the cost register. The security literature is written
entirely in the injection register. The single sentence that joins them exists in Block's post
and is about a permission dialog: *each tool should stick to a single risk level*. That
sentence is the whole governance argument, and it was published as a usability tip.

The defensible formulation for the stage: **consolidate along the workflow axis and stop at
the authorization boundary.** `schedule_event` is a good consolidation because the boundary
survives it. `execute_query` is a good consolidation for the model and a bad one for everyone
downstream, unless it is split by risk level and paired with a credential scoped to match,
which is precisely what Block did and precisely what Supabase did not.

---

## 8. Official tool design guidance

### 8.1 From the MCP specification, 2026-07-28

All [PRIMARY], <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>

**Naming.** 1 to 128 characters; case-sensitive; only `A-Z a-z 0-9 _ - .`; no spaces or
commas; unique within a server. Uniqueness is **scoped to a single server**, so aggregating
proxies "SHOULD implement a disambiguation strategy such as prefixing tool names with a server
identifier". `serverInfo.name` "is not guaranteed to be unique across servers and **SHOULD NOT**
be relied upon for disambiguation."

**Ordering.** Deterministic order SHOULD, for client caching and prompt cache hit rate.

**Authorization-varying lists.** The tool set "**MUST NOT** vary per-connection or as a side
effect of other requests on the connection", but "**MAY** vary by the authorization presented
on the request".

**Schemas.** `inputSchema` MUST be a valid JSON Schema object, not `null`. For no parameters,
`{"type": "object", "additionalProperties": false}` is **recommended** over `{"type":
"object"}`. Defaults to JSON Schema 2020-12 absent `$schema`.

**Output schemas.** Optional. If provided, servers **MUST** return conforming structured
results and clients **SHOULD** validate. Stated benefits: strict validation, type information,
better parsing by clients and LLMs, better documentation. "For backwards compatibility, a tool
that returns structured content SHOULD also return the serialized JSON in a TextContent
block."

**Annotations.** Optional, and **MUST** be treated as untrusted unless from a trusted server.

**Pagination.** `tools/list` supports cursor pagination and caching; each page is
independently cacheable; same `cacheScope` across all pages of one request.

**Error handling.** Protocol errors for unknown tool and malformed requests; tool execution
errors as `isError: true` in a successful result. Clients **SHOULD** pass execution errors to
the model "to enable self-correction".

**Security considerations for tools.** Servers **MUST** validate all inputs, implement access
controls, rate limit invocations, and sanitise outputs. Clients **SHOULD** prompt for
confirmation on sensitive operations, "Show tool inputs to the user before calling the server,
to avoid malicious or accidental data exfiltration", validate results before passing to the
LLM, implement timeouts, and "Log tool usage for audit purposes".

**Stateful tools.** Non-normative but directly relevant to a consolidated query tool: "For
authenticated servers, a handle is a name, not a capability. The server should validate the
caller's authorization against the handle on every call."

### 8.2 From Anthropic

<https://www.anthropic.com/engineering/writing-tools-for-agents> [PRIMARY]

- Consolidate toward workflows: the `schedule_event` example.
- "More tools don't always lead to better outcomes."
- Namespacing "can help delineate boundaries between lots of tools", by service (`asana_search`)
  or by resource (`asana_projects_search`), with "non-trivial effects on tool-use evaluations".
  Anthropic does **not** declare a winner between prefix and suffix; test in your own evals.
- `ResponseFormat` enum: `DETAILED` vs `CONCISE`, 206 vs 72 tokens on their example.
- "pagination, range selection, filtering, and/or truncation with sensible default parameter
  values"; 25,000-token default response cap in Claude Code.
- Descriptions: prompt-engineering them is "one of the most effective methods for improving
  tools".
- Error messages should "clearly communicate specific and actionable improvements, rather than
  opaque error codes or tracebacks."
- Eval harness: "simple agentic loops (`while`-loops wrapping alternating LLM API and tool
  calls): one loop for each evaluation task." Metrics: task accuracy, runtime per call and per
  task, total tool calls, token consumption, tool errors.

Tool-search-specific optimisation guidance [PRIMARY]:
- Keep 3-5 most-used tools non-deferred.
- "Use consistent namespacing in tool names: prefix by service or resource (for example,
  `github_`, `slack_`) so one search matches the whole group."
- "Add a system prompt section describing available tool categories."
- When **not** to use tool search: "fewer than 10 tools, every tool is used in every request,
  or your tool definitions are small (less than 100 tokens total)."
- When to use it: "10 or more tools", "definitions consume more than 10k tokens", "You
  aggregate multiple MCP servers (200+ tools)".

### 8.3 From OpenAI

<https://developers.openai.com/api/docs/guides/function-calling>,
<https://developers.openai.com/api/docs/guides/tools-tool-search> [PRIMARY]

- "Keep the number of initially available functions small for higher accuracy."
- "fewer than 20 functions available at the start of a turn at any one time, though this is
  just a soft suggestion."
- "aim to keep each namespace to fewer than 10 functions for better token efficiency and model
  performance."
- Prefer "namespaces or MCP servers over individual functions", because models are "primarily
  trained to search those surfaces".
- Remedies for token pressure: "limiting the number of functions loaded up front, shortening
  descriptions where possible, or using tool search."

### 8.4 The one place the three disagree

Nowhere on granularity in principle. All three say: fewer, workflow-shaped, well-described,
namespaced. **None of them says anything about where consolidation should stop.** The only
published stopping rule in the entire corpus is Block's risk-level line, and it appears in a
paragraph about a permission dialog rather than in any vendor's tool-design guidance.

---

## 9. Open problems

1. **No measured effect size for tool filtering.** Everyone ships the feature (GitHub toolsets,
   Docker gateway allow/deny, spec-level scope-varying lists). Nobody has published "we went
   from N to M tools and measured X on tokens, accuracy and latency."
2. **No published breakdown of schema verbosity.** Nobody has isolated description bytes from
   schema bytes in a real server, so "shorten your descriptions" has no price tag.
3. **No server-published context cost.** The Server Card Working Group's `.well-known` metadata
   is the obvious home for a "my full tool surface is N tokens" field, and no published draft
   contains one. A host cannot decide whether to connect without connecting.
4. **Progressive discovery has no interop story.** `search_tools` and `get_tool_details` are
   patterns in a best-practices document, not protocol methods, and the roadmap describes the
   effort as starting.
5. **The `cacheScope` and scope-filtering interaction is unpriced.** A filtered `tools/list`
   must be `"private"`, which gives up the shared-cache saving, and the spec states the hazard
   without stating the trade.
6. **No published account of a consolidation's cost.** Block published the design, Microsoft
   published one number (2 to 5% of requests, from a parameter rename). Nobody published a
   rollback, a regression, or a client breakage from collapsing a tool surface.
7. **No per-client tool-loading matrix.** Re-confirmed for Cursor on 2026-09-18: its MCP docs
   state no tool limit and no filtering feature, so the widely repeated 40-tool cap has no
   primary source.

---

## 10. Numbers that did not survive verification

Additions to the ops file's Section 7. Same discipline: the argument is right, the numbers
travelled badly.

### 10.1 The Cursor 40-tool cap

**What circulates:** "Cursor: 40-tool hard cap based on telemetry showing degraded outputs",
alongside "Claude Code: quality decline observable past 50 tools", "OpenAI Tools API: 128-tool
maximum", and "Claude tool-list capacity: approximately 120 tools". Source: Unblocked, "MCP
tool overload".

**What verification found, 2026-09-18:** Cursor's own MCP documentation contains no tool limit,
no statement about tool count degrading performance, and no tool-filtering feature. OpenAI's
function-calling guide states no 128 hard cap; it gives a **soft** suggestion of fewer than 20
functions at the start of a turn. Anthropic's tool search doc gives a degradation range of
**30 to 50**, not 50, and a deferred-tool limit of **10,000**, not 120.

**Verdict:** [UNVERIFIED] for all four. The real published thresholds are RAG-MCP's ~30,
Anthropic's 30-50, and OpenAI's soft 20 and per-namespace 10. Those three agree with each
other and have sources.

### 10.2 The roadmap quote's opening clause

**What circulates**, including in this repository's own ops file: "A server with a hundred
tools means the model pays for that entire surface before the user has asked a single
question".

**What the page says:** "Connecting to a server with a hundred tools means the model pays for
that entire surface before the user has asked a single question, and tool selection tends to
get worse as the list grows."

**Verdict:** a small misquote of the maintainers, in front of the maintainers. Fix it in the
deck. Re-verified character for character 2026-09-18.

### 10.3 Still circulating, still wrong (carried forward, not re-litigated)

- **RAG-MCP "43% collapses to under 14%"**: inverted. 43.13% is the proposed method, 13.62% the
  naive baseline, and it is a method comparison rather than a tool-count curve. Confirmed live
  in Unblocked on 2026-09-18.
- **Cloudflare "1.17 million tokens"**: not in the Code Mode post. Confirmed live in Unblocked
  on 2026-09-18.
- **"49% to 74%" attributed to programmatic tool calling**: it is the Tool Search Tool on Opus
  4. Code execution's accuracy figures are 25.6% to 28.5% and 46.5% to 51.2%.

**Delivery guidance carried over from the ops file:** do not name the outlets from the stage.
Lead with the part that is generous, which is that the tool-sprawl argument is correct and
well evidenced. Offer the better number as a replacement rather than only removing the bad one.

---

## Appendix: source index

**MCP specification and official docs, 2026-07-28**
- Changelog: <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
- Server tools: <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
- Caching utility: <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching>
- Client best practices: <https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md>
- Docs index: <https://modelcontextprotocol.io/llms.txt>

**MCP maintainers**
- The New MCP Roadmap, Soria Parra and Delimarsky, 2026-08-22: <https://blog.modelcontextprotocol.io/posts/mcp-roadmap/>
- 2026-07-28 release post: <https://blog.modelcontextprotocol.io/posts/2026-07-28/>

**Model vendors**
- Anthropic, advanced tool use, 2025-11-24: <https://www.anthropic.com/engineering/advanced-tool-use>
- Anthropic, code execution with MCP, 2025-11-04: <https://www.anthropic.com/engineering/code-execution-with-mcp>
- Anthropic, writing tools for agents, 2025-09-11: <https://www.anthropic.com/engineering/writing-tools-for-agents>
- Anthropic, tool search tool: <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>
- Anthropic, prompt caching: <https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching>
- OpenAI, prompt caching: <https://developers.openai.com/api/docs/guides/prompt-caching>
- OpenAI, tool search: <https://developers.openai.com/api/docs/guides/tools-tool-search>
- OpenAI, function calling: <https://developers.openai.com/api/docs/guides/function-calling>

**Practitioners**
- Block playbook, Mohammed and Chau, 2025-06-16: <https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers>
- Microsoft Learn MCP, Zhang / Imasogie / de Bruin, 2026-02-11: <https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/>
- GitHub MCP server: <https://github.com/github/github-mcp-server>
- Docker MCP Gateway: <https://github.com/docker/mcp-gateway>
- Cloudflare Code Mode, Varda and Pai, 2025-09-26: <https://blog.cloudflare.com/code-mode/>
- Cursor MCP docs: <https://cursor.com/docs/context/mcp>
- Artemii Amelin, 2026-09-01: <https://dev.to/artem_a/mcp-2026-07-28-deleted-the-session-the-state-moved-into-your-context-window-1hde>
- pgEdge, Ibrar Ahmed, 2026-02-05: <https://www.pgedge.com/blog/mcp-transport-architecture-boundaries-and-failure-modes>

**Security**
- MCPTox, arXiv:2508.14925: <https://arxiv.org/abs/2508.14925>
- General Analysis, Supabase MCP: <https://generalanalysis.com/blog/supabase-mcp-blog>
- Simon Willison on the same: <https://simonwillison.net/2025/Jul/6/supabase-mcp-lethal-trifecta/>
- Invariant Labs, tool poisoning, 2025-04-01: <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks>
- CVE-2026-47250 advisory: <https://github.com/Flux159/mcp-server-kubernetes/security/advisories/GHSA-6mx4-4h42-r8vh>

**Peer / preprint**
- RAG-MCP, arXiv 2505.03275: <https://arxiv.org/abs/2505.03275>
- MCP-Universe, arXiv 2508.14704: <https://arxiv.org/abs/2508.14704>

**Secondhand, use with the label**
- Unblocked, MCP tool overload: <https://getunblocked.com/blog/mcp-tool-overload/>
- Jentic, The MCP Tool Trap: <https://jentic.com/blog/the-mcp-tool-trap>
- AgentPMT, 2026-02-27: <https://www.agentpmt.com/articles/thousands-of-mcp-tools-zero-context-left-the-bloat-tax-breaking-ai-agents>
