---
title: "Cost: the total cost of operating MCP at enterprise scale"
date: 2026-09-21
sources_verified_on: 2026-09-21
status: draft
---

<!-- ABOUTME: Total cost of ownership for an enterprise MCP deployment, line by line, separating what is published from what nobody prices. -->
<!-- ABOUTME: Token cost and prompt-cache economics live in bestpractice/mcp-token-economics-and-tool-consolidation.md and are referenced, not repeated. -->

## Scope, and what this deliberately does not re-cover

> **Corrections, 2026-10-05 (part five verification):** three claims below are out of date.
> Control-plane person-month estimates exist (Zuplo, Composio). A gateway prices tool calls
> (Bifrost's per-tool price setting), so payment protocols are not the only case. Datadog now
> states its billing unit on its own pricing page. Their sources are recorded with
> the review of part five of the article series.

Token counts, the prompt-cache multiplier arithmetic, the cache-invalidation
interaction with progressive discovery, and the tool-consolidation arc are
covered in depth elsewhere in this repo. They are the largest single line on the
bill and they are already done. This brief is the rest of the bill.

| Already covered | Where |
|---|---|
| Where tokens go, T1 to T4, with measured figures and methodology | `bestpractice/mcp-token-economics-and-tool-consolidation.md` 1.1 to 1.7 |
| Prompt cache mechanics, per-provider invalidation, what a gateway does to hit rate | same, 2.1 to 2.5 |
| Cost control effect sizes correctly attributed | same, 4.1 to 4.6 |
| Illustrative annual token arithmetic for a 10,000 person workforce | `ops/mcp-operations-at-scale-2026-09.md` 3.4 |
| Gateway and registry operations, 13 gateways compared, registry mirror mechanics | `bestpractice/mcp-gateway-and-registry-operations.md`, `scale/mcp-at-scale-architecture-2026-09.md` |
| Server vetting checklist and supply chain controls | `bestpractice/mcp-server-vetting-and-supply-chain.md` |
| Observability platform list, OTel MCP conventions read from source, first pass at storage pricing | `components/supporting-layers.md` 1.1 to 1.3 |
| AI gateway category, budgets column per product, Bedrock and Azure routing savings with methodology | `components/inference-gateways.md` 4.2, 5.3, 6 |
| CVE list, attack classes, incident record | `security/mcp-security-failures-2026-09.md` |

Where this brief revises an earlier claim in the repo, it says so in the text.
Two claims are revised: the flat statement that nothing attributes cost to a
person (section 4), and the first pass at observability storage pricing, which
missed that vendors disagree about what a billable unit is (section 3).

Sourcing labels used throughout: **OFFICIAL** (the maintaining body or the
vendor's own product documentation for its own product), **VENDOR** (marketing
or a benchmark the vendor ran on itself), **PREPRINT** (arXiv, not peer
reviewed), **PRACTITIONER** (a named person writing from experience),
**SECONDHAND** (a third party reporting someone else's number), **DERIVED**
(arithmetic performed in this brief from stated inputs).

---

## 1. The full cost surface

Eleven lines. The column that matters is the last one.

| # | Line item | Unit it is billed in | Published price? | Who pays it |
|---|---|---|---|---|
| 1 | **Inference tokens** | per million input/output, with cache multipliers | **Yes, fully.** Every frontier vendor publishes a rate card | Application or platform budget |
| 2 | **Agent session runtime** | per session-hour, separate from tokens | **Yes**, on at least one platform. $0.08 per session-hour, Claude Managed Agents | Same budget, new line |
| 3 | **Server-side tool calls** | per call (web search), per container-hour (code execution) | **Yes.** $10 per 1,000 searches; 1,550 free container-hours then $0.05/hour/container | Same budget |
| 4 | **Inference gateway infrastructure** | compute for the hop, plus a license fee if commercial | **Partly.** Latency overhead published by two vendors; almost no gateway publishes a rate card | Platform team |
| 5 | **MCP gateway infrastructure** | same | **Barely.** Most require a sales conversation | Platform team |
| 6 | **Registry operation and its ingest pipeline** | compute and storage for the mirror, plus the poller | **No.** Nobody prices this | Platform team |
| 7 | **Observability ingest, processing and retention** | per trace, per span, per observation, or per GB, and the vendors disagree | **Partly, and the unit is the problem.** See section 3 | Platform or observability budget |
| 8 | **Secret management for non-human identities** | per secret per month, plus per API call | **Yes.** $0.40 per secret per month on AWS Secrets Manager. The count of secrets is the architecture decision | Security or platform |
| 9 | **Engineering cost of building the control plane** | person-time | **No.** No published figure specific to MCP | Platform team headcount |
| 10 | **Vetting and review effort per server** | person-time per server, per version | **No.** No published figure at all | Security review capacity |
| 11 | **Revocation and re-review** | person-time, recurring | **No.** The requirement is documented; the cost is not | Same |

Lines 1 through 3 and line 8 are priced to the cent. Lines 9, 10 and 11 have no
published price anywhere, and they are the ones that scale with the number of
servers rather than the number of requests, which is the growth curve an
enterprise actually rides.

### 1.1 What is new on this list

**Session runtime is a line item now, and it is not a token.** Claude Managed
Agents bills on two dimensions: tokens at the standard rates, plus session
runtime at **$0.08 per session-hour**, metered to the millisecond and accruing
only while a session's status is `running`. Idle time does not count. The Batch
API discount explicitly does not apply, because "Sessions are stateful and
interactive. There is no batch mode." Session runtime replaces container-hour
billing rather than stacking on it.
[OFFICIAL, <https://platform.claude.com/docs/en/about-claude/pricing>, read
2026-09-21.]

The vendor's own worked example is worth reproducing because it shows the
proportions. A one-hour coding session on Claude Opus 5 consuming 50,000 input
and 15,000 output tokens: input $0.25, output $0.375, session runtime $0.08,
total **$0.705**. With prompt caching active on 40,000 of the input tokens:
uncached input $0.05, cache reads $0.02, output $0.375, runtime $0.08, total
**$0.525**. [OFFICIAL, same source.] Runtime is 11% of the uncached total and
15% of the cached total, so as caching improves the runtime line grows as a
share of the bill.

**Secret count is an architecture decision priced at four orders of magnitude.**
AWS Secrets Manager is **$0.40 per secret per month** plus **$0.05 per 10,000
API calls**, with no free tier for the service itself beyond general AWS Free
Tier credits, and rotation creating a new version is not charged.
[OFFICIAL, <https://aws.amazon.com/secrets-manager/pricing/>, read 2026-09-21.]

**[DERIVED, this brief, 2026-09-21]** The published price is not the interesting
part. The count is. Two credential-brokering architectures for 10,000 people
across 50 approved servers:

| Architecture | Secret count | Monthly | Annual |
|---|---|---|---|
| One secret per user per server (user-held credentials) | 500,000 | $200,000 | $2,400,000 |
| One secret per server, gateway brokers on behalf of the user | 50 | $20 | $240 |

The ratio is 10,000 to 1. The identity model decides which row you land in, and
no amount of vendor negotiation moves you between them. `components/supporting-layers.md` 2.4 records that the published
secret-management patterns break for agents specifically. This is the price of
getting that wrong at fleet scale. API-call volume is not the driver: 30 million
credential fetches a year costs $150 at the published rate, so caching the fetch
saves nothing worth the complexity.

---

## 2. Quantified versus unpriced

### 2.1 Quantified, from a primary source

| Claim | Figure | Source, all read 2026-09-21 | Label |
|---|---|---|---|
| Claude Opus 5 input / output | $5 / $25 per MTok | platform.claude.com pricing | OFFICIAL |
| Claude Sonnet 5 input / output | $2 / $10 per MTok. The scheduled increase to $3/$15 on 2026-09-01 "will not occur" | same | OFFICIAL |
| Cache read multiplier | 0.1x base input on all models except Fable 5.1 and Mythos 5.1, which are 0.025x | same | OFFICIAL |
| Cache write multiplier | 1.25x for 5 minutes, 2x for 1 hour | same | OFFICIAL |
| Cache break-even | "after one cache read for the 5-minute duration (1.25x write), or after two cache reads for the 1-hour duration (2x write)" | same | OFFICIAL |
| Batch API | 50% off both input and output | same | OFFICIAL |
| Tool-use system prompt overhead, Opus 5 | 286 tokens (`auto`/`none`), 406 (`any`/`tool`) | same | OFFICIAL |
| Web search | $10 per 1,000 searches | same | OFFICIAL |
| Code execution | 1,550 free container-hours per org per month, then $0.05/hour/container. Free when used with web search or web fetch | same | OFFICIAL |
| Session runtime | $0.08 per session-hour | same | OFFICIAL |
| US-only inference | 1.1x multiplier on every token category | same | OFFICIAL |
| Secrets Manager | $0.40/secret/month, $0.05/10,000 calls | aws.amazon.com/secrets-manager/pricing | OFFICIAL |
| Grafana Cloud traces | $0.050/GB process, $0.400/GB write, $0.100/GB retain; 30-day minimum retention on paid | grafana.com/pricing | OFFICIAL |
| Langfuse Cloud | Core $29, Pro $199, Enterprise $2,499 per month; 100k units included; $8 per 100k units overage | langfuse.com/pricing | OFFICIAL |
| ElastiCache session store deleted by stateless MCP | "about $23/month" | AWS Architecture Blog | OFFICIAL, see section 7 |

One tokenizer change invalidates every arithmetic in this repo performed
against an older model. Anthropic states that "Claude 4.7 and later models and Claude
Mythos Preview use a newer tokenizer ... This tokenizer produces approximately
30% more tokens for the same text."
[OFFICIAL, <https://platform.claude.com/docs/en/about-claude/pricing>, read
2026-09-21.] A token count measured on Sonnet 4.6 is not the token count on a
4.7-or-later model, and a cost projection that carries an old count forward
understates by roughly that margin. The 55,000-token five-server tool surface
cited in `ops/` 3.4 should be re-measured before it is used against a current
model.

### 2.2 Unpriced, and the absence is the finding

**Nobody publishes an engineering cost for building an MCP control plane.** The
closest published statements are directional and come from vendors selling the
alternative: that organizations "that tried to build internal governance in
early 2026 are now evaluating external platforms because the spec moved faster
than their engineering teams," and that scaling to enterprise "requires
significant DIY effort to bolt on authentication, identity management, and audit
infrastructure." [SECONDHAND and VENDOR, surfaced across several 2026 gateway
comparison posts, none carrying a figure, checked 2026-09-21.] No person-month
number, no team size, no elapsed time, from any source.

**Nobody publishes a vetting effort figure per server.** The vetting literature
is extensive on *what* to check. Searched across the enterprise vetting guidance
published in 2026, no source states hours per server, reviewer count, or
throughput. [Checked 2026-09-21 across the vendor and practitioner vetting
guides; the vetting checklist content itself is in
`bestpractice/mcp-server-vetting-and-supply-chain.md`.] This matters because the
repo already establishes the workload: a live registry walk on 2026-09-18
returned **33,830 distinct servers across 339 requests in 160.8 seconds**, of
which 2.2% were already `deleted` and 1.0% `deprecated`
[MEASURED, this repo, `bestpractice/mcp-gateway-and-registry-operations.md` 9].
The crawl is minutes. The review of what the crawl surfaces is the cost, and it
has no published unit rate.

It is worse than an absence of pricing, because the same file records that
`list_changed` semantics after approval is an **Open** item in the Security
Interest Group: a server can change its tools after you approved it. Re-review
is therefore not a one-time cost but a recurring one whose trigger rate is also
unpublished.

**The MCP-specific TCO literature does not exist.** The published agent-TCO
material is content marketing: ranges of $20,000 to $300,000 to build an agent,
maintenance at "15 to 30 percent of the original build," three-year TCO at "40 to
80 percent above the build number," development as "25 to 35% of the three-year
total." [SECONDHAND across several 2026 consultancy and vendor blog posts, read
2026-09-21. None publishes a methodology, a sample, or a definition of what is
inside the range, and none is MCP-specific.] Do not put any of these in a
business case. They are quoted here so that the next person who finds them knows
they were checked and rejected.

---

## 3. Observability storage at fleet scale

`components/supporting-layers.md` 1.3 priced the platforms and named the unit
mismatch. Going deeper produces one finding that changes the conclusion: **the
vendors do not bill the same unit, and for agent workloads the difference between
their units is larger than the difference between their prices.**

### 3.1 The billable unit, per vendor

**Langfuse bills every data point.** Quoted exactly: "A billable unit in Langfuse
is any tracing data point sent to the platform -- including traces (complete
application interactions), observations (individual steps: spans, events, and
generations), and scores (evaluations)."
[OFFICIAL, <https://langfuse.com/pricing>, read 2026-09-21.] Tiers: Hobby free
with 50k units and 30-day access; Core $29 with 100k units and 90-day access;
Pro $199 with 100k units and 3-year access; Enterprise $2,499 with 100k units and
3-year access. Overage on all paid tiers is **$8 per 100k units**, "lower with
volume."

Set that against Langfuse's own description of what an agent trace contains:
agent workloads produce "deep traces (hundreds to thousands of operations per
trace)."
[VENDOR, <https://langfuse.com/resources/engineering/clickhouse-at-agent-scale>,
read 2026-09-21.]

**[DERIVED, this brief, 2026-09-21]** Assumptions stated so they can be argued
with: 10,000 people, 4 agent tasks per working day each, 250 working days, giving
10 million agent tasks per year. One trace plus N observations per task, at the
published $8 per 100k units:

| Observations per task | Units per year | Annual overage cost |
|---|---|---|
| 20 (a short tool-using turn) | 210 million | ~$16,800 |
| 200 (Langfuse's low end for agents) | 2.01 billion | ~$161,000 |
| 1,000 (Langfuse's high end) | 10.01 billion | ~$801,000 |

The price per unit never changes. The bill moves by a factor of 48 on a number
most enterprises have not measured, which is the average step count of their own
agent runs. That measurement is the first thing to do before any observability
contract is signed, and it costs one instrumented week.

**Datadog reportedly bills only LLM spans.** The circulating description is that
"an LLM span is one call to an LLM provider," that "one agent workflow can create
multiple LLM spans," and that "tool spans, embedding spans, retrieval spans and
agent spans are not billed at all, so an agent that grows from 3 steps to 12
steps costs nothing extra unless the extra steps are model calls."
[SECONDHAND, multiple 2026 pricing explainers, read 2026-09-21.]

**That claim could not be confirmed against Datadog.** Two Datadog-controlled
pages were fetched directly on 2026-09-21: the LLM Observability cost
documentation at `docs.datadoghq.com/llm_observability/monitoring/cost/` and the
pricing page filtered to the product. Neither states which span kinds are billed,
what an LLM span is for billing purposes, the included volumes, or the on-demand
rate. The cost documentation covers monitoring *your model spend*, not what
Datadog charges you. **UNVERIFIED**, and it is the most consequential unverified
claim in this brief: if it is right, Datadog's unit is roughly an order of
magnitude cheaper than Langfuse's for the same agent workload, and if it is wrong
the comparison inverts. Get it in writing from an account team. This confirms and
sharpens the earlier finding in `components/supporting-layers.md` 1.3 that the
Datadog rates are not published.

**Grafana Cloud bills bytes, which sidesteps the unit question entirely.**
Traces: "$0.050/GB Process", "$0.400/GB Write", "$0.100/GB Retain", with a $19
monthly platform fee on Pro and a free tier of 50 GB per month at 14-day
retention. Logs carry identical rates.
[OFFICIAL, <https://grafana.com/pricing/>, read 2026-09-21.] The documentation
defines the two volumes precisely: "Processed volume is what arrives at Grafana
Cloud. Written volume is what's stored after optimization. Sampling and Adaptive
Traces reduce written volume." Minimum retention is 14 days free, 30 days paid,
and beyond 30 days is charged per GB per additional 30-day increment.
[OFFICIAL, <https://grafana.com/docs/grafana-cloud/platform/pricing-and-usage/traces/>,
read 2026-09-21.]

**[DERIVED]** At those rates, a fleet writing 1 TB of trace data per month pays
about $50 to process, $400 to write, and $100 per additional 30-day retention
increment, so roughly **$450 per month for 30 days of retention and $100 per
month for each extra month kept**. The missing input is bytes per trace, which
only your own measurement provides.

### 3.2 The single largest storage lever is a boolean

Claude Code's OpenTelemetry integration is the best-documented agent telemetry
surface published by any vendor, and it makes the cost driver explicit. Content
logging is **off by default** on every flag:

| Variable | What it exports | Default |
|---|---|---|
| `OTEL_LOG_USER_PROMPTS` | user prompt content | disabled |
| `OTEL_LOG_ASSISTANT_RESPONSES` | assistant response text | disabled |
| `OTEL_LOG_TOOL_DETAILS` | tool parameters and input arguments | disabled |
| `OTEL_LOG_TOOL_CONTENT` | tool content in span events | disabled |
| `OTEL_LOG_RAW_API_BODIES` | full Messages API request and response JSON | disabled |

[OFFICIAL, <https://code.claude.com/docs/en/monitoring-usage>, read 2026-09-21.]

The cap on a content-bearing attribute is published:
`CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` defaults to **61440 UTF-16 code units,
about 60 KB**, covering "model responses, tool content, system prompts, and raw
API bodies."

**[DERIVED]** A span carrying no content is on the order of a kilobyte. A span at
the 60 KB cap is roughly sixty times that. At Grafana's $0.45/GB for process plus
write, 60 KB spans cost about **$0.000026 each**, so an agent run producing 1,000
content-bearing spans costs about **2.6 cents to store for 30 days** and the same
run without content logging costs well under a tenth of a cent. Across the 10
million annual tasks assumed above, that is the difference between roughly
$260,000 a year and roughly $4,000 a year, on one environment variable.

The documentation also names the metrics cardinality controls directly: "Lower
cardinality generally means better performance and lower storage costs but less
granular data for analysis," and "Each custom key becomes a label on every metric
series, so high-cardinality values increase storage cost in your metrics
backend." `OTEL_METRICS_INCLUDE_SESSION_ID` defaults to **true**, which puts a
per-session label on every metric series, and `OTEL_METRICS_INCLUDE_ACCOUNT_UUID`
also defaults to true. [OFFICIAL, same source.] On Grafana's metrics pricing of
"$6.50 / 1k series," a session-id label on a fleet's metrics is the expensive
default, and it is on unless turned off.

### 3.3 What sampling is defensible

There is no official MCP or OTel guidance on sampling agent traces. The
practitioner consensus, consistent across several 2026 write-ups, is tail
sampling with outcome-based keep rules rather than head sampling at a fixed rate.
The argument stated most clearly: "randomly keeping one percent is cheap, but it
can remove the only examples of a rare tool failure or newly introduced answer
defect," and tail sampling "lets you decide after you've seen the whole trace
whether to keep it, which is perfect for agents because you often don't know a
run is 'interesting' until the end."
[PRACTITIONER, <https://oneuptime.com/blog/post/2026-09-12-sample-llm-traces-rare-quality-tool-failures/view>
and <https://dev.to/gabrielanhaia/trace-sampling-for-llm-apps-keep-the-spans-that-matter-drop-the-rest-3ejj>,
read 2026-09-21.]

The recurring keep rule, quoted: "keep every trace that errored, keep every trace
slower than 10 seconds, keep every trace that cost more than a dollar, and keep
5% of the rest." [PRACTITIONER, same sources.] The threshold at which sampling
starts being necessary is given as "under a few thousand traces per day you can
keep 100%."

Two operational caveats that come with it. Tail sampling is stateful, so "spans
for the same trace need to reach the same collector instance so the decision sees
the full trace," and round-robin routing splits the evidence. And a keep rule
that triggers on cost requires the cost to be on the span, which returns to
section 4: the OTel MCP semantic conventions carry no cost attribute, so that
rule has to be implemented against a private attribute.

**This is consensus rather than measurement.** No source publishes a measured retention
rate, a measured bill before and after, or a measured detection loss from
sampling. The rule of thumb is reasonable and it is unvalidated.

---

## 4. Cost attribution through a delegation chain

The repo's existing finding, in `scale/` 7.6 and restated in
`components/inference-gateways.md` 5.3, is that budgets exist and attribution
does not. **That finding needs revision on one axis and holds on the other.**

### 4.1 What changed: per-user cost attribution now exists for first-party surfaces

**Anthropic ships per-user cost in USD, and it is not a proxy.** The Claude
Enterprise Analytics API includes `GET /v1/organizations/analytics/user_cost_report`,
described as: "Get per-user cost in USD across a date range. Returns one row per
user, ranked by spend. Use this to see which users account for the most cost."
Available `group_by` dimensions include `claude_tag_user_id`, `rbac_group_id`,
`product` (chat, claude_code, cowork, office_agent and others), `model`,
`cost_type` (tokens, web_search, code_execution), `token_type`, `context_window`,
`inference_geo`, `speed`, and `slack_channel_id`. All the analytics endpoints are
**beta**, require a Claude Enterprise plan and an API key with `read:analytics`
scope, cover data "no earlier than 2026-01-01", carry a one-day lag, refresh
every four hours, and are "not final until about 30 days after the usage date."
[OFFICIAL, <https://platform.claude.com/docs/en/api/admin/analytics>, read
2026-09-21.]

The Claude Code Analytics API does the same for one product at daily granularity,
keyed on an `actor` that is either a `user_actor` with `email_address` or an
`api_actor` with `api_key_name`, returning `estimated_cost.amount` in cents per
model per user per day. [OFFICIAL,
<https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api>,
read 2026-09-21.] Note the field name: **estimated**.

And Claude Code's OpenTelemetry export emits `claude_code.cost.usage` in USD as a
metric, carrying `session.id`, `user.id`, `user.email`, `user.account_uuid`,
`user.account_id` and `organization.id` as attributes.
[OFFICIAL, <https://code.claude.com/docs/en/monitoring-usage>, read 2026-09-21.]
That is a cost figure joined to a person and a session, in real time, in an open
format. It is the closest thing to a solved attribution problem in this brief.

### 4.2 What did not change: the raw API still attributes to a key, not a person

For the general API rather than the seat products, the picture is the one the
FinOps Foundation describes.

The Anthropic Usage API groups by `model`, `service_tier`, `context_window`,
`workspace_id`, `api_key_id`, `inference_geo` and `speed`. The **Cost** API
groups by `workspace_id` and `description` only, with daily granularity only.
There is no user, actor, session or request dimension on the cost endpoint.
Anthropic's own FAQ points elsewhere for the question: "How do I get per-user cost
breakdowns for Claude Code? Use the Claude Code Analytics API ... For general API
usage with many keys, use the Usage API to track token consumption as a cost
proxy."
[OFFICIAL, <https://platform.claude.com/docs/en/build-with-claude/usage-cost-api>,
read 2026-09-21.] A cost proxy is the honest phrase for it.

OpenAI splits the same way and in the same direction. The organization Usage
endpoints accept `user_id` as a `group_by` value, so **tokens** can be attributed
to an end user. The Costs endpoint accepts `project_id`, `line_item` and
`api_key_id`, so **dollars** cannot.
[OFFICIAL for the endpoint shapes via
<https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs>
and <https://platform.openai.com/docs/api-reference/usage/completions>; both
pages returned 403 or 404 to direct fetch on 2026-09-21 and the parameter lists
were read through search result summaries of those same pages, so treat the exact
enumeration as **SECONDHAND** pending a direct read.]

The FinOps Foundation states the general case plainly, and this is the single
best citation for the problem: "An OpenAI or Anthropic invoice will show spend by
API key or project, not by business unit, cost center, application, or team," and
"The data that FinOps teams need to perform showback and chargeback does not exist
in the provider's billing export unless the organization builds the
instrumentation layer itself."
[OFFICIAL, FinOps Foundation AI Value Working Group, "Tokenomics: Managing AI
Value in SaaS Model Token Costs", published 2026-06-03,
<https://www.finops.org/wg/token-economics-saas/>, read 2026-09-21.]

### 4.3 The delegation chain specifically, and the one mechanism that addresses it

**Nothing joins a person to the full tree of model and tool calls made on their
behalf through a chain of agents.** Verified three ways on 2026-09-21:

1. The vendor cost APIs above expose no session, trace, request or parent-agent
   dimension. Anthropic's Enterprise Analytics cost response object carries
   `amount`, `cost_type`, `token_type`, `model`, `product`, `inference_geo`,
   `speed` and `context_window`, and no identifier that would let two rows be
   joined into a chain.
2. The OTel MCP semantic conventions define no identity, principal, or
   authorization-decision attribute. `mcp.session.id` identifies a session, not a
   person or an agent. Established from the source file in
   `components/supporting-layers.md` 1.4 and unchanged.
3. MCP itself has no cost concept. A tool call carries no price, no token count,
   and no budget field, so the tool half of the tree is unpriced at the protocol
   level.

**The closest published mechanism is LiteLLM's session-scoped budget, and it is
worth reading carefully because it is the shape a real answer would take.**
LiteLLM enforces two agent controls keyed on a session identifier carried in the
`x-litellm-trace-id` header or `metadata.session_id`: `max_iterations`, "Hard cap
on the number of LLM calls per session", and `max_budget_per_session`, "Dollar cap
per session (identified by x-litellm-trace-id)". Two flags make the identifier
mandatory in each direction: `require_trace_id_on_calls_to_agent` "Requires
callers invoking this agent to include `x-litellm-trace-id`. Use when the agent
should only be called as a sub-agent with a trace context. Returns 400 if
missing", and `require_trace_id_on_calls_by_agent` "Requires all LLM/MCP calls
made by this agent (via its virtual key) to include `x-litellm-trace-id`. This is
what enables `max_iterations` and `max_budget_per_session` tracking. Returns 400
if missing." Counters expire after one hour by default, configurable via
`LITELLM_MAX_ITERATIONS_TTL` and `LITELLM_MAX_BUDGET_PER_SESSION_TTL`.
[OFFICIAL, <https://docs.litellm.ai/docs/a2a_iteration_budgets>, read 2026-09-21.]

Note what this is and what it is not. It is a **correlation identifier that the
gateway will refuse a request without**, which is the hard part of the problem
and is exactly right. It covers both LLM and MCP calls made by the agent, which
is the other hard part. What it does not do is propagate the identifier
automatically: the documentation describes requiring the header, not minting or
forwarding it, and does not state how a session id flows through an agent
hierarchy. The caller sets it. A sub-agent that forgets to forward it gets a 400,
which is a good failure, but the chain is stitched by convention rather than by
the protocol.

That is the state of the art as of 2026-09-21: **a gateway can refuse to work
without a correlation id, and the correlation id is still the caller's job.** The
repo's claim that attribution through a delegation chain is unsolved stands. The
claim that nothing attributes cost to a person does not, and should be narrowed
to the raw API path.

### 4.4 Context: the industry is measuring the same gap

The FinOps Foundation's State of FinOps 2026, 1,192 respondents representing
"more than $83 billion in annual cloud spend," published 2026-02-19: "Almost all
the 1,192 survey respondents (98%) are managing AI spend," up from 63% in 2025
and 31% in 2024, and the report names "Allocating AI costs to business units:
harder than traditional infrastructure" among the top practitioner challenges.
[OFFICIAL, <https://www.linuxfoundation.org/press/state-of-finops-survey-ai-value-and-skills-top-priorities-as-finops-matures-across-technology-value-98-manage-ai-90-saas-64-licensing-48-data-center-1>
and <https://data.finops.org/>, both read 2026-09-21.]

A "73% of AI costs exceed budgets" figure circulates attached to this report. It
did not appear on either primary page checked. **UNVERIFIED, do not use.**

FOCUS, the open billing specification, is moving toward this. FOCUS 1.3 shipped
in December 2025 and a 1.4 said to add token-economics columns is reported as
ratified in June 2026. [SECONDHAND, several 2026 summaries including
<https://siliconangle.com/2026/06/08/ai-token-economics-focus-specification-updates-finopsx/>,
read 2026-09-21. The version number and the ratification date were not confirmed
against <https://focus.finops.org/> directly and should be before citing.] Even
if confirmed, a billing schema standardizes how a provider reports a charge. It
does not create the delegation-chain identifier that nobody emits.

---

## 5. Budget enforcement: what is actually enforced, and what happens mid-task

Five products read directly on 2026-09-21. They enforce at different scopes, in
different units, with different guarantees, and the differences matter more than
the feature checkbox.

| Product | Scope | Unit | On exhaustion | Guarantee |
|---|---|---|---|---|
| **LiteLLM** | virtual key, team, tag, org, **session** | dollars, iterations | `429`, `{"type": "budget_exceeded"}` | Session counters TTL out after 1 hour by default |
| **LiteLLM budget fallbacks** | per key, per model | dollars | **No error. Silently reroutes to another model** | Caller cannot tell |
| **Portkey** | API key, workspace | cost (min $1) or tokens | blocks further usage | Alert threshold is notify-only; key keeps working until the hard limit |
| **agentgateway** | one API key (fixed window), or any descriptor (token bucket) | dollars or tokens per key; tokens only for rate-limit budgets | "Reject the request" | **"The request that crosses the limit still completes. Agentgateway rejects the next request."** |
| **TrueFoundry** | tenant, team; partitioned per user, per model, per virtual account, or per metadata key | cost only | `429` plus `x-tfy-applied-rules` header naming the rule | Three modes: `enforce`, `audit` (allow and alert), `soft_enforce` (block only if every matching budget is over) |
| **Cloudflare AI Gateway** | provider, model, or custom metadata key | dollars | `429`, or fall back to a cheaper model via a Dynamic Route | **"Spend limits are eventually consistent ... a burst of concurrent requests can briefly exceed the limit before enforcement catches up"** |

Sources, all read 2026-09-21:
<https://docs.litellm.ai/docs/a2a_iteration_budgets>,
<https://docs.litellm.ai/docs/proxy/budget_fallbacks>,
<https://portkey.ai/docs/product/administration/enforce-budget-and-rate-limit>,
<https://agentgateway.dev/docs/standalone/latest/llm/cost-controls/budget-limits/>,
<https://www.truefoundry.com/docs/ai-gateway/budget-limiting-v2>,
<https://developers.cloudflare.com/ai-gateway/features/spend-limits/>. All
OFFICIAL, each being the vendor's documentation for its own product.

### 5.1 Three findings the feature matrix hides

**Not one of these is a hard spending ceiling.** agentgateway says so in its own
documentation: the request that crosses the limit completes, and the next one is
rejected. Cloudflare says so differently: enforcement is eventually consistent
and a concurrent burst can overshoot. Cloudflare goes further and labels its own
cost figure "a best-effort estimation based on token counts and model pricing,"
recommending you "check your provider's dashboard for exact billing amounts." For
ordinary chat traffic the overshoot is one request. For an agent that can emit a
single 900,000-token request, or fan out to twelve concurrent sub-agents, the
overshoot is the thing you were trying to cap.

**Silent model substitution is the most dangerous default in the category.**
LiteLLM budget fallbacks exist to "Reroute requests to a fallback model when a
key's `model_max_budget` is exceeded, instead of returning a `budget_exceeded`
error," and the documentation is explicit that "Once the cap is crossed subsequent
requests are transparently served by `gpt-5.6-terra` without any
`budget_exceeded` error surfacing to the caller." Cloudflare offers the same
behavior as one of two spend-limit options. This keeps the agent running, which
is the point. It also means an agent doing accuracy-sensitive work can be moved
to a weaker model partway through a task by a budget event, and neither the agent
nor the person who asked for the work is told. In any fleet, that is a correctness control being changed by a cost
control, silently. If fallbacks are enabled, the model actually used has to be
surfaced in the response metadata and logged, or the audit trail says a task
succeeded without saying what did it.

**Only two of the five enforce on anything smaller than a key or a team.**
TrueFoundry can partition by metadata key-value pairs, which is how a per-user or
per-agent budget gets built. LiteLLM can scope to a session. Everything else caps
a credential. A credential shared by an agent fleet is not a budget on any agent
in it, which is the same structural problem as section 4 wearing different
clothes: the enforcement point and the causal actor are not the same object.

**An honest alert-only mode is rarer than it should be.** TrueFoundry's `audit`
mode allows requests through while still tracking usage and firing alerts, and
its `soft_enforce` blocks only when every other matching budget is also over.
Portkey's alert threshold is notify-only by construction, with the key continuing
to work until the hard limit. That pairing, observe first and enforce second, is
the deployment order any enterprise should want, and three of the five products
do not document it.

### 5.2 Tool calls are outside all of this

Every mechanism above meters **inference**. An MCP tool call has no price at the
protocol level, so a budget that caps model spend does not cap what the tools do:
the database query, the third-party API charge, the compute the server burns.
`components/inference-gateways.md` 5.3 records the split of what each plane can
see, and nothing found in this research closes it.

Two payment protocols now price a tool call directly, and they come from outside
the enterprise governance world. **x402** returns HTTP 402 with a payment URI on
an unpaid call. **Stripe's Machine Payments Protocol**, co-authored with Tempo
and launched 2026-03-18, is "an open standard, internet-native way for agents to
pay," supporting stablecoin and fiat through Shared Payment Tokens, aimed at
agents paying for APIs without a checkout UI.
[OFFICIAL, <https://stripe.com/blog/machine-payments-protocol> and
<https://docs.stripe.com/payments/machine/mpp>, read 2026-09-21.] These solve
paying an external vendor for a tool call. They are not internal cost controls
and nothing suggests an enterprise is using them to meter internal servers. They
are worth watching because they are the only published mechanism that attaches a
price to an individual tool invocation.

---

## 6. The cheapest controls, ranked by measured saving per unit of effort

Ranked by effect size divided by how much work the change takes, with the
measurement quality stated. Effort is this brief's judgment; the effect sizes are
cited.

| Rank | Lever | Measured effect | Effort | Evidence quality |
|---|---|---|---|---|
| 1 | **Prompt caching** | Cache read at **0.1x** base input. Break-even after 1 read (5m) or 2 reads (1h) | One field on the request | **OFFICIAL price, deterministic arithmetic.** The strongest item on the list |
| 2 | **Turn off telemetry content logging** | Up to the 60 KB per-attribute cap removed from every span | One environment variable, and it is already the default | **OFFICIAL defaults**, saving is DERIVED |
| 3 | **Deterministic `tools/list` ordering** | No published figure. Raises prompt-cache hit rate, which is lever 1 | Sort a list | **OFFICIAL** spec SHOULD, effect unmeasured |
| 4 | **Tool filtering and per-role tool sets** | 85% token reduction, and MCP eval accuracy 79.5% to 88.1% | Config per role | **OFFICIAL, measured by Anthropic** |
| 5 | **Result truncation and output guards** | 25,000-token default response cap; 72 vs 206 tokens on a `concise` vs `detailed` response | Server-side defaults | **OFFICIAL**, single-example figures |
| 6 | **Batch API for non-interactive work** | Flat **50%** on input and output | Restructure to async. Does not apply to interactive agent sessions | **OFFICIAL price** |
| 7 | **Semantic tool retrieval** | **99.6%** tool-token reduction, 97.1% hit rate at K=3, MRR 0.91, over 140 queries / 121 tools / 5 servers | Build or adopt a retrieval layer | **PREPRINT**, arXiv:2603.20313, 2026-03-19 |
| 8 | **Dynamic tool gating and lazy schema loading** | 47.3k to 2.4k tokens per turn (**95.0%**), context utilization 24% to 91% | Client change | **PREPRINT**, arXiv:2604.21816, 2026-04-23. **Simulated** 120-tool benchmark; the authors state end-to-end metrics are "projected values derived from the measured token counts", not live agent runs |
| 9 | **Code execution instead of direct tool calls** | 98.7% on one workflow, 37% average on complex research | Sandbox, generated stubs, new threat model | **OFFICIAL**, but costs ~7% latency and output tokens at 5x input |
| 10 | **Model routing** | 63.6% on one RAG workload against an all-Sonnet baseline | Gateway config | **OFFICIAL**, single workload |
| 11 | **Token-efficient serialization formats** | up to 27% (TRON) and ~40% (TOON) fewer tokens | Format change end to end | **PREPRINT**, arXiv:2605.29676 and arXiv:2605.04107. TRON keeps accuracy "within 14 percentage points of the JSON baseline", which is a large accuracy cost |
| 12 | **Gateway semantic caching** | **No hit rate or saving published by any vendor checked** | Config, plus a correctness review per workload | **Do not model.** See below |

Sources for the OFFICIAL rows are the Anthropic pricing page and engineering
posts already indexed in `ops/mcp-operations-at-scale-2026-09.md` 3.4 and 4, and
the AWS RAG figure in `components/inference-gateways.md` 6.1. Preprint rows read
from arXiv on 2026-09-21 at the identifiers given.

### 6.1 Three cautions on this table

**The top of the list beats the bottom by a wide margin and takes less work.**
Caching, a boolean, a sort, and a per-role tool config account for the first four
places. Everything requiring a sandbox, a retrieval layer, or a serialization
change sits below them and carries either an accuracy cost or a measurement
caveat.

**The preprint figures are the largest on the list and the weakest evidence.**
99.6% and 95.0% are both larger than Anthropic's own measured 85%, and both come
from unreviewed preprints, one of which explicitly runs on a simulated benchmark
with projected end-to-end metrics. Treat them as directionally consistent with
the official figure rather than as improvements on it. The honest reading is that
several independent efforts converge on "most of the tool-token bill is
avoidable," which is a stronger statement than any single percentage.

**Vendor routing percentages have already been shown to use the wrong baseline.**
`components/inference-gateways.md` 6.1 established that AWS's headline routing
savings of 35%, 56% and 16% are measured against **random routing**, which AWS
itself says are "only meant for comparing against random routing within the
family", and that nobody routes randomly. Only the 63.6% RAG figure has a usable
baseline. That correction is not repeated here beyond this note, and it should be
applied to any routing number encountered elsewhere.

**Semantic caching remains unpriceable.** Cloudflare publishes the mechanism
(exact-match SHA-256 over the request body) and no hit rate. Kong's circulating
speed figures have no published harness. Both were checked in
`components/inference-gateways.md` 6.3 and nothing found on 2026-09-21 changes
it. A lever with no published effect size cannot be ranked, and the
cross-user-response-reuse correctness question makes it the wrong place to start
regardless.

---

## 7. The cost of the control plane itself

The question is whether anyone has priced governance against the incidents it
prevents. **For MCP specifically, no. Nobody has published that calculation.**

### 7.1 What exists instead

The closest published work is the IBM Cost of a Data Breach 2026, which prices
the *incidents* without pricing the *controls*, and does it on a defined sample.
Methodology, quoted: "The 2026 report, conducted by Ponemon Institute and
sponsored and analyzed by IBM, is based on breaches experienced by 602
organizations globally between March 2025 and February 2026," with follow-up
research on "456 organizations of the 602."
[OFFICIAL, <https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average>,
published 2026-07-29, read 2026-09-21.]

From the press release, verbatim:

- Global average breach cost: **"$4.99 million"**
- AI-enabled breaches: **"One in four malicious breaches were AI-enabled, a 56% increase over last year"**, costing **"$6 million"**
- Security AI and automation **"cut breach costs by an average of almost $2 million dollars"**, and **"one in four organizations have still not adopted these tools"**
- **"More than 20% of organizations reported a breach targeting AI models or applications"**

From IBM's own analysis of the same study, verbatim:

- **"roughly one in five organizations reported an AI-related breach"**, and of those, **"the vast majority (92%) lacked proper AI access controls"**
- Prompt injection **"led to average losses of USD 5.89 million"**; model inversion **"led to average losses of USD 6.07 million"**
- **"only 40% of organizations reported using access controls on AI models and data"**

[OFFICIAL, <https://www.ibm.com/think/x-force/2026-cost-of-a-data-breach-ai-adversaries-enterprise-risk>,
read 2026-09-21.]

Two widely repeated figures attached to this report could not be found on either
IBM page checked: a shadow-AI incident rate of 43% up from 20%, and a paired
$5.33M versus $4.70M comparison. **SECONDHAND and UNVERIFIED**; several
third-party summaries carry them and they conflict with the $6M / $4.99M pairing
IBM publishes, which suggests they measure a different cut. Do not use either
without reading the report itself.

### 7.2 Why this is not the calculation, even though it is close

The 92% figure is the most quotable number in this brief for an audience being
asked to fund a control plane, and it needs to be used precisely. It says that
among organizations that suffered an AI-related breach, almost all lacked AI
access controls. It does not say that access controls prevented breaches at the
organizations that had them, because the sample is organizations that were
breached. The correct reading is that absent access control is near-universal
among AI breach victims, which is a strong signal and is not a measured
prevention rate.

More to the point for this repo: **none of it is about MCP.** No source found
prices an MCP gateway, an MCP registry, or a server vetting program against MCP
incidents. The `security/mcp-security-failures-2026-09.md` record in this repo
contains CVEs and attack classes with no cost attached to any of them. The
governance-ROI material that does exist is vendor playbooks proposing a formula,
"(Avoided incident cost + Avoided regulatory exposure + Compliance hours
recovered + Velocity value) minus (Platform + implementation cost)", with no
populated instance. [SECONDHAND, several 2026 vendor playbooks, read 2026-09-21.]
A formula with no measured inputs is a slide, not an analysis.

### 7.3 What the hop itself costs

The gateway adds latency, and two vendors publish a number for their own product
under conditions that overstate it: LiteLLM's Rust proxy at **0.7 ms p99** against
a local deterministic mock, explicitly with "no logging callbacks, spend tracking
or persistence," and Bifrost at **11 microseconds** of overhead at 5,000 rps.
Both are recorded in `components/inference-gateways.md` 5.4, with the standing
caution that a benchmark with spend tracking disabled does not describe a gateway
enforcing budgets. Spend tracking is the feature this brief is about, so neither
figure applies to a governed deployment.

No gateway checked publishes an infrastructure cost for itself. Kong's paid plans
are reported at $499 to $2,999 per month [SECONDHAND, third-party pricing
summaries, read 2026-09-21], Docker's MCP Enterprise Gateway requires a sales
form, MintMCP gates identity features behind undisclosed enterprise tiers, and
TrueFoundry and Obot publish a free tier and nothing above it. **The control
plane's own price is a sales conversation in nearly every case**, which is itself
a finding for anyone building a budget.

---

## 8. The AWS stateless figure, used carefully

Verified verbatim against the primary source on 2026-09-21:

> "A two-node Amazon ElastiCache (cache.t4g.micro) session store is about
> $23/month"

attributed by AWS to the AWS Pricing Calculator, July 2026.
[OFFICIAL, <https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/>.]

The surrounding sentences, which is where the value is. AWS advises: "Audit for
anything that exists only to preserve sessions (ElastiCache clusters,
sticky-routing rules, session-replication logic) and delete it." And immediately
after quoting the price, AWS says the money is not the point: "The larger saving
is eliminating an entire class of infrastructure and the operational burden
around it," adding that "Sticky routing costs capacity too by distributing load
unevenly, and the savings scale with the size of your fleet."

**Use it because it is small.** A vendor with every incentive to make its own
architectural recommendation sound valuable published a number that is a rounding
error on any enterprise bill, and then said so. That is the honest shape of the
stateless argument: the session store was never the expense, the on-call surface
was. Anyone citing this figure as a cost saving has misread it.

It also has a counterpart that must travel with it. Artemii Amelin's critique,
recorded in `ops/mcp-operations-at-scale-2026-09.md` 2.3, is that statelessness
moved the cost rather than removing it: "Connection state has become
context-window state. It costs tokens on every turn it survives, it competes with
everything else in the window." Deleting a $23 ElastiCache cluster and adding
tokens to every turn of every conversation is not obviously a saving. It is a
transfer from the infrastructure budget to the token budget, and those budgets
have different owners. Nobody has published the arithmetic on which side comes
out ahead, and it would be workload-specific if they did.

---

## 9. Open gaps

Stated as findings. Each is an absence verified on 2026-09-21, not an absence of
searching.

1. **No published engineering cost for an MCP control plane.** No person-months,
   no team size, no elapsed time, from any vendor, practitioner or analyst.
   Everyone agrees it is significant and nobody has counted it.

2. **No published vetting effort per server.** The checklists are detailed and the
   unit cost of executing one is unstated. With 33,830 distinct servers upstream
   and a documented open problem around post-approval drift, this is the line item
   most likely to determine whether a program is affordable, and it is the one
   with the least data.

3. **No re-review trigger rate.** `list_changed` semantics after approval is an
   Open item in the Security Interest Group. Nobody publishes how often an
   approved server changes its tool surface, so the recurring review cost cannot
   be estimated even in principle.

4. **Datadog's LLM Observability billing unit is not published.** The claim that
   only LLM spans are billed and tool, agent, retrieval and embedding spans are
   free is SECONDHAND and changes the bill by roughly an order of magnitude for
   agent workloads. Two Datadog-controlled pages checked directly do not state it.

5. **No measured before-and-after for trace sampling on agent workloads.** The
   tail-sampling keep rules are a defensible consensus with no published
   validation: no retention rate, no bill delta, no measured detection loss.

6. **No cost attribute anywhere in the agent telemetry standards.** The OTel MCP
   semantic conventions carry no cost, token, principal, or authorization
   attribute. Every cost-based sampling rule and every per-agent budget is
   therefore built on a private attribute, which means none of them are portable
   between platforms.

7. **Attribution through a delegation chain is still unsolved, narrowed.** The
   repo's prior flat claim should be narrowed: per-user cost in USD now exists for
   first-party seat products in beta, and `claude_code.cost.usage` joins cost to a
   user and a session in OTel. What does not exist is a chain: no vendor cost API
   exposes a session, trace or parent-agent dimension, and the one mechanism that
   requires a correlation id (LiteLLM's `x-litellm-trace-id`) does not propagate
   it, it only refuses without it.

8. **No budget mechanism is a hard ceiling, and two vendors say so.**
   agentgateway lets the crossing request complete; Cloudflare is eventually
   consistent and calls its own cost figure best-effort estimation. For agent
   workloads that can emit one enormous request or fan out concurrently, the
   overshoot is unbounded in the worst case and nobody publishes its distribution.

9. **Silent model substitution on budget exhaustion is undocumented as a risk.**
   Two products ship it, both describe it as a feature, and neither discusses that
   it changes model quality mid-task without telling the caller. No published
   guidance exists on surfacing the substitution in the audit trail.

10. **Nobody has priced MCP governance against MCP incidents.** The IBM study
    prices AI breaches on a defined sample and says nothing about MCP. The
    governance-ROI formulas published by vendors have no populated instances. This
    is the calculation an enterprise is repeatedly asked to make and there is no
    published attempt at it.

11. **The tokenizer change invalidates carried-forward token counts.** Models from
    4.7 onward produce "approximately 30% more tokens for the same text." Any cost
    projection in this repo or elsewhere built on a token count measured against
    an earlier model understates by roughly that margin and needs re-measuring
    before reuse.

---

## Source index

All URLs read 2026-09-21 unless stated.

**OFFICIAL, vendor documentation for its own product**
- <https://platform.claude.com/docs/en/about-claude/pricing>
- <https://platform.claude.com/docs/en/build-with-claude/usage-cost-api>
- <https://platform.claude.com/docs/en/api/admin/analytics>
- <https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api>
- <https://code.claude.com/docs/en/monitoring-usage>
- <https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/>
- <https://aws.amazon.com/secrets-manager/pricing/>
- <https://grafana.com/pricing/>
- <https://grafana.com/docs/grafana-cloud/platform/pricing-and-usage/traces/>
- <https://langfuse.com/pricing>
- <https://docs.litellm.ai/docs/a2a_iteration_budgets>
- <https://docs.litellm.ai/docs/proxy/budget_fallbacks>
- <https://portkey.ai/docs/product/administration/enforce-budget-and-rate-limit>
- <https://agentgateway.dev/docs/standalone/latest/llm/cost-controls/budget-limits/>
- <https://www.truefoundry.com/docs/ai-gateway/budget-limiting-v2>
- <https://developers.cloudflare.com/ai-gateway/features/spend-limits/>
- <https://stripe.com/blog/machine-payments-protocol>, <https://docs.stripe.com/payments/machine/mpp>
- <https://www.finops.org/wg/token-economics-saas/> (published 2026-06-03)
- <https://www.linuxfoundation.org/press/state-of-finops-survey-ai-value-and-skills-top-priorities-as-finops-matures-across-technology-value-98-manage-ai-90-saas-64-licensing-48-data-center-1> (published 2026-02-19)
- <https://data.finops.org/>
- <https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average> (published 2026-07-29)
- <https://www.ibm.com/think/x-force/2026-cost-of-a-data-breach-ai-adversaries-enterprise-risk>

**VENDOR, marketing or self-run benchmark**
- <https://langfuse.com/resources/engineering/clickhouse-at-agent-scale>

**PREPRINT, arXiv, not peer reviewed**
- arXiv:2603.20313, "Semantic Tool Discovery for Large Language Models: A Vector-Based Approach to MCP Tool Selection", submitted 2026-03-19
- arXiv:2604.21816, "Tool Attention Is All You Need: Dynamic Tool Gating and Lazy Schema Loading for Eliminating the MCP/Tools Tax in Scalable Agentic Workflows", submitted 2026-04-23
- arXiv:2605.29676, "Notation Matters: A Benchmark Study of Token-Optimized Formats in Agentic AI Systems"
- arXiv:2605.04107, "TSCG: Deterministic Tool-Schema Compilation for Agentic LLM Deployments"

**PRACTITIONER**
- <https://oneuptime.com/blog/post/2026-09-12-sample-llm-traces-rare-quality-tool-failures/view>
- <https://dev.to/gabrielanhaia/trace-sampling-for-llm-apps-keep-the-spans-that-matter-drop-the-rest-3ejj>

**SECONDHAND, recorded so the next reader knows it was checked**
- OpenAI usage and cost endpoint `group_by` enumerations: primary pages returned 403 and 404 to direct fetch; parameter lists read through search summaries of <https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs> and <https://platform.openai.com/docs/api-reference/usage/completions>
- Datadog LLM Observability billing unit and on-demand rates: not present on <https://docs.datadoghq.com/llm_observability/monitoring/cost/> or the product pricing page
- FOCUS 1.4 token-economics columns and June 2026 ratification: not confirmed against <https://focus.finops.org/>
- Kong paid plan range, $499 to $2,999 per month
- "73% of AI costs exceed budgets", attributed to State of FinOps 2026, not on either primary page
- IBM shadow-AI 43% figure and the $5.33M / $4.70M pairing, not on either IBM page checked

### Claims carried as UNVERIFIED

| Claim | Why it is unverified | What would settle it |
|---|---|---|
| Datadog bills only LLM spans, not tool/agent/retrieval/embedding spans | Not on any Datadog-controlled page checked | A written rate card from a Datadog account team |
| Datadog on-demand rate above 100k LLM spans, and the per-10,000-span retention add-on price | Not published | Same |
| ClickHouse at 2.5 GB compressed per 1M traces versus 8.3 GB on PostgreSQL, and $3,000/yr versus $30,000/yr | Appeared in a third-party summary, not on the Langfuse engineering page when fetched | Langfuse or ClickHouse publishing the benchmark |
| FOCUS 1.4 added token-economics columns, ratified June 2026 | Reported by summaries only | Direct read of the FOCUS specification index |
| OpenAI Costs endpoint cannot group by `user_id` | Consistent across two independent summaries of OpenAI's own reference, but the reference pages would not fetch | One authenticated read of the API reference |
| "73% of AI costs exceed budgets" | Not on the State of FinOps primary pages | Reading the report itself |
| IBM shadow-AI incident rate of 43%, up from 20% | Not on either IBM page checked; conflicts with the cut IBM does publish | Reading the full Cost of a Data Breach report |
