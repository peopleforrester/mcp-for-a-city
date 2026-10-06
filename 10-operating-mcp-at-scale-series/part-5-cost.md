---
title: "The MCP Bill Is Hiding in the Token Bill"
subtitle: "Operating MCP at scale, part five: cost"
date: 2026-10-05
status: draft
series: "Operating MCP at Scale"
part: 5
sources_verified_on: 2026-10-06
---

# The MCP Bill Is Hiding in the Token Bill

*Operating MCP at scale, part five: cost.*

Anthropic's worked example of an MCP setup connects five servers (GitHub,
Slack, Sentry, Grafana and Splunk) and counts "58 tools consuming approximately
55K tokens before the conversation even starts." A client that loads every
definition up front sends those tokens as input on every model call.

Whether yours does depends on the client. In Claude Code, MCP tool search "is
enabled by default: MCP tools are deferred and discovered on demand", and the
same holds for `claude -p` and Agent SDK runs. Claude Code turns it off when
`ANTHROPIC_BASE_URL` "points to a non-first-party host, since most proxies don't
forward `tool_reference` blocks", so routing it through your own LLM gateway puts
the full surface back on every call unless you override that. On the Messages
API, tools passed in the `tools` parameter load in full unless they are marked
`defer_loading`.

For a fleet that carries the full surface, the arithmetic is simple enough to
redo with your own numbers:

> monthly cost = tasks per month × model calls per task × surface tokens × price per million tokens ÷ 1,000,000

My assumptions, which are mine and not sourced: one million agent tasks a month
and 20 model calls per task. With the 55K surface that is 1.1 trillion input
tokens a month spent on tool definitions. At Opus 5's cache-read price of $0.50
per million, with every call a cache hit, it is about **$550,000 a month**. On
Opus 5.5, whose cache reads cost $0.20, it is about $220,000. The agent
observability bill for the same fleet, at 100 tool calls per task and Langfuse
and Datadog list prices, is about $7,000 to $15,000 a month (my arithmetic).

No invoice has a line called MCP. The tool surface is billed as input tokens
under whatever API key made the call. That is the finding of this part: **for a
client that does not defer tools, the tool surface is the largest MCP-specific
cost that can be priced from published counts, and no budget, cost API or
protocol field names it.** The tool results that agents carry forward are
billed the same way and may rival it, but I found no fleet-scale measurement of
them.

Part four found that when the gateway is self-hosted and nearby, the tool
surface costs more time than the hop to the tool, and that otherwise the two are
the same order of magnitude. It also named what makes the surface an MCP problem
and not a general tool-calling one: "the operator does not own the surface." A
third party writes the definitions and can change them at runtime. That is the
thread through this part.

**Prior art.** WorkOS's Maria Paktiti covered the per-turn cost in a September
vendor post, "Tool definitions are billed on every turn", using the same 55K
example, and made the cache point first: a server whose tool order varies is
"invalidating your users' prompt caches every time they reconnect." AWS's
Well-Architected review of the stateless revision treats cost briefly and links
to its Agentic AI Lens, whose cost pillar covers tool serving, attribution and
budget governance on AWS services; the Lens cost pages I read do not mention MCP.
This part adds fleet-scale dollars, the cost of a cache write against a read,
the specification's per-caller tool lists, and why nothing attributes the line.

## The tool surface, priced

Prices are Anthropic's list prices, read on 6 October. The scenario is the one
above: one million tasks a month, 20 model calls per task.

| Tool surface per call | Source of the count | Opus 5, all cache reads | Opus 5, one write then 19 reads per task | Opus 5, uncached | Opus 5.5, all cache reads |
|---|---|---|---|---|---|
| ~3,500 tokens, deferred | Tool search tool "(~500 tokens)" plus "3-5 relevant tools, ~3K tokens", Anthropic's figures for a 50+ tool library | ~$35,000 | ~$55,000 | ~$350,000 | ~$14,000 |
| 55,000 tokens, all loaded | Anthropic's five-server worked example | ~$550,000 | ~$866,000 | ~$5,500,000 | ~$220,000 |
| 134,000 tokens, all loaded | "At Anthropic, we've seen tool definitions consume 134K tokens before optimization" | ~$1,340,000 | ~$2,110,000 | ~$13,400,000 | ~$536,000 |

The middle column assumes one five-minute cache write ($6.25 per million, 1.25x
base input) at the start of each task and cache reads after it. Opus 5 leads the
table because it is the model in Anthropic's own worked pricing example. On the
Claude API, Claude Platform on AWS and Microsoft Foundry the cache is isolated
per workspace, so a fleet split across workspaces warms each one separately;
Bedrock and Google Cloud isolate per organization.

Two cautions on the inputs. Anthropic published those counts in November 2025,
and its pricing page now says Claude 4.7 and later models use a tokenizer that
"produces approximately 30% more tokens for the same text." I did not re-count.
And `tool_use` and `tool_result` blocks are also input on every later turn.
Anthropic's code-execution post gives a sense of scale for one case: a meeting
transcript passed between two tools "could mean processing an additional 50,000
tokens." The table leaves results out.

The only measurement of MCP's share against a no-MCP baseline in this series
comes from a vendor measuring its own server. Twilio ran the Cline agent on
Claude 3.7 Sonnet with and without its MCP server, repeating each task at least
ten times, and found "~28.5% more cache reads and ~53.7% more cache writes".
"Cost increased by about 27.5% on average," while tasks finished about 20.5%
faster.

## What changes the surface, and what it costs

Caching is what brings the 55K case down from $5.5 million to $550,000, and the
cache holds only while the prefix stays identical. Anthropic's caching
documentation: "Modifying tool definitions (names, descriptions, parameters)
invalidates the entire cache." On a 55K surface on Opus 5, a write instead of a
read costs about $0.32 more per call.

**One upstream change is cheap.** When a server's tools change, each distinct
surface in each workspace pays one new write, plus re-writing the cached history
of conversations in flight. For a fleet with a few dozen distinct surfaces that
is tens of dollars per release, against a line measured in hundreds of
thousands. The expensive case is a prefix that never settles.

**Ordering.** The 2026-07-28 revision says servers "SHOULD return tools from
`tools/list` in a deterministic order to enable client-side caching and improve
LLM prompt cache hit rates." A server that shuffles its tools on every
connection breaks the cache on every connection. The client can fix this too:
it assembles the `tools` array, and a client that sorts by server and tool name
gets a stable prefix whatever order the servers return.

**Per-caller tool lists.** The same revision says the tool set "MAY vary by the
authorization presented on the request", for example "returning only the tools
the caller's granted scopes permit". Every distinct permission set is a distinct
prefix, so a fleet whose servers scope tools per user can have as many cached
surfaces as it has permission combinations. This is the MCP mechanism most
likely to push a fleet from the all-reads column toward the middle one, and it
is a direct trade between access control and cache hit rate.

**Mid-conversation changes.** Anthropic documents an `inline-tools-2026-09-15`
beta with which a client can "add a tool, or change a tool's definition, partway
through a conversation without editing `tools`", after which "The cached prefix
still matches," on models that support mid-conversation tool changes. A client
that applies a `list_changed` this way keeps its cached prefix.

**Change after approval.** The MCP Security Interest Group lists "Runtime drift:
`list_changed` semantics after approval" as an open item, scoped to whether such
changes "are versioning, re-approval, or security events." The cache cost of an
upstream change is small. The review it may oblige is the larger cost, and I
found no published figure for it (see below).

## Levers, ranked by the evidence behind them

| Lever | Effect | Evidence |
|---|---|---|
| Tool search or deferred loading | Tool-definition tokens from ~72K to ~3.5K in Anthropic's example, about 95% (my arithmetic); 85% of total context | Anthropic's own worked comparison; on by default in Claude Code |
| Code execution in place of direct tool calls | 77.4% fewer total tokens; output up 120%, latency up 7% | AIMultiple, independent, two tasks, GPT-4.1 |
| Prompt caching | Cache reads at 0.1x base input on Opus 5; "pays off after one cache read" for a five-minute write | Published price; holds only while the prefix is unchanged |
| Deterministic tool order, server or client side | Keeps the cached prefix stable | Specification SHOULD; I found no measured effect |

The code-execution saving depends on the price of the tokens it removes.
Repricing AIMultiple's GPT-4.1 token counts at Opus 5 rates (my arithmetic),
the cost per run falls about 73% when input is uncached and about 35% when input
is billed at the cache-read rate, because the extra output tokens cost $25 per
million either way. A fleet that already caches well gets the smaller number.

Tool search and code execution are the levers measured against the surface
itself. Caching is the only one whose effect you can compute without measuring
your own fleet, and it depends on the prefix holding still.

## Nothing attributes it

The surface is billed per call under an API key, and provider billing stops
about there. In the FinOps Foundation's words, "An OpenAI or Anthropic invoice
will show spend by API key or project, not by business unit, cost center,
application, or team."

The most MCP-specific attribution I found is in Claude Code's telemetry. Its
cost counter carries `mcp_server.name`, defined as the "MCP server whose tool
result this request consumed", and a matching `mcp_tool.name`. That attributes
the cost of a request that read a tool's output to the server that produced it.
Two limits apply. It covers results, and nothing I found splits the
tool-definition tokens by server. And user-configured server names are replaced
with `"custom"` unless `OTEL_LOG_TOOL_DETAILS=1` is set (and only from v2.1.273
on the cost counter), which also exports tool parameters and input arguments.
Naming your internal servers in cost data means exporting what was sent to them.

**The protocol carries no cost and no principal for cost.** The 2026-07-28
tools page has no price, cost or budget field. The revision reserves
`traceparent`, `tracestate` and `baggage` in `_meta` for OpenTelemetry context,
with no key defined for a user or a cost center. Baggage is caller-asserted, so
it can correlate but should not decide who pays. The authenticated carrier is
the token: OAuth token exchange, and MCP's Enterprise-Managed Authorization
extension, which puts the organization's identity provider in charge of server
access. What I could not find is a published convention that joins the principal
in that token to a cost record.

OpenTelemetry's GenAI and MCP conventions define token counts and no cost
attribute. A 2024 proposal to add one was withdrawn after a maintainer asked,
"How would instrumentation code know the cost of token?" Two broader proposals,
"Ownership / Cost Centre Conventions" and "Cloud Financial Management
Conventions", have been open since November 2024. `service.instance.cost_center.id`
and `.name` were merged on 16 September at development status and are not yet in
a release. They record who owns a service instance, which for an MCP server is
the team running it; the person an agent was acting for appears nowhere in them.
Instrumentation fills the gap with its own attributes: OpenLIT ships
`gen_ai.usage.cost`, marked in its source as an "OpenLIT vendor extension; not
OTel GenAI semconv".

Payment proposals for MCP itself have not progressed. SEP-2007 proposed "a
protocol-agnostic framework supporting multiple payment methods", with x402 as
one, and was closed in June as dormant for lack of a sponsor, with the note "This
is not a permanent decision." Issue #3393, a paid-tools proposal built on x402,
was closed as not planned on 28 September, with a maintainer directing it to the
SEP process.

## Tool calls inside a budget

Gateway budgets cap inference. They see the tool surface as input tokens and a
tool's own cost only if someone enters it.

**Tool prices are operator-entered.** LiteLLM tracks MCP tool cost two ways: a
fixed `default_cost_per_query` per server with `tool_name_to_cost_per_query`
overrides, or a post-MCP hook that sets a cost per call with custom logic, which
can read the tool's response. Bifrost has a per-client `tool_pricing` map,
"cost per execution". LiteLLM's page says the hook's costs go to "LiteLLM's
logging system". Neither page I read says whether tool cost counts against the
same budget as inference.

**A stopped task leaves its tool calls in place.** A budget fires on a model
call, after earlier tool calls have run, and restarting the task can issue them
again. MCP tool annotations include `idempotentHint` and `destructiveHint`, the
protocol's own description of whether a repeat is safe. The specification says
clients must treat annotations as untrusted unless they come from trusted
servers, so check them against your vetting record before relying on them.

## Observability: your servers set the ratio

Agent telemetry vendors bill different units. Langfuse bills traces,
observations and scores, and "Every LLM call, tool execution, retrieval, and
intermediate step becomes its own observation". Datadog bills model calls only:
"Tool, workflow, agent, embedding, and retrieval spans are all free." How many
tool calls an agent makes per model call depends on the servers it was given,
so the servers decide which vendor is cheaper. At list prices, counting one
trace per task and one observation per model or tool call, Datadog becomes
cheaper above about 4 to 5 tool calls per model call when Langfuse Pro is
compared with Datadog's 15-day retention, and above about 10.5 to 11.5 when both
are at 90 days (my arithmetic, across 5 to 50 model calls per task). Count spans the way your instrumentation emits
them: in Claude Code, "Tool spans have two child spans of their own."

## The lines without an independent price

**The control plane.** The published estimates come from vendors selling the
alternative. Zuplo puts a production-ready MCP server with auth, rate limiting
and basic observability at "2-4 engineers working for 3-6 months", and Composio
says of an enterprise MCP gateway that "The proxy itself is 2–4 weeks of work.
Everything around it is where the cost lives, and where most internal builds
stall." Neither publishes a sample or a method.

**Vetting, and vetting again.** Part two counted 39,617 servers in the official
registry on 5 October, up from 33,366 sixteen days earlier. I searched for a
published effort figure for reviewing a server, in hours, reviewers or
throughput, and found estimates for building servers and none for reviewing
them. Re-review after a tool change is recurring, and I found no figure for how
often approved servers change.

**The session store you deleted.** AWS gives the saving from going stateless as
"about $23/month" for a two-node ElastiCache store, then: "The larger saving is
eliminating an entire class of infrastructure and the operational burden around
it. Sticky routing costs capacity too by distributing load unevenly, and the
savings scale with the size of your fleet."

## What to do

**Find out whether your clients defer tools.** Check every client and agent runtime in
the fleet, including Claude Code behind your own gateway, where tool search is
off unless you set `ENABLE_TOOL_SEARCH`.

**Price the surface you carry.** Count the definition tokens per call, put your
own task volume and calls per task into the formula above, and give the result
to whoever owns the AI budget.

**Cut the surface before tuning anything else.** Give each role the servers it
needs, defer loading where the client supports it, and test code execution at
your own cache hit rate.

**Keep the prefix stable.** Sort tools in the client, require deterministic
`tools/list` order from the servers you admit, apply mid-conversation tool
changes without rewriting `tools` where your provider supports it, and count how
many distinct permission sets your per-caller tool lists produce.

**Treat `list_changed` from an approved server as a review trigger.**

**Enter prices for the tools that wrap paid APIs.** LiteLLM and Bifrost both
accept them, and without one a tool call has no cost in the gateway's spend data.

**Check `idempotentHint` and `destructiveHint`, from servers you trust, before
restarting a task a budget stopped.**

**Derive the payer from the authenticated token.** Use the identity from token
exchange or your identity provider at each hop, and carry `baggage` in `_meta`
only as a correlation key.

**Measure tool calls per model call before signing an observability contract,**
and compare vendors at the retention you will buy.

**Count review hours from your first vetted server,** including every re-review
triggered by a tool change after approval.

---

*Part five of five on operating MCP at scale. Parts one to four cover
operational excellence, security, reliability and performance.*

## Sources

All URLs verified 2026-10-06. Vendor posts are marked.

**Tool surface and token pricing**
1. Anthropic, "Introducing advanced tool use on the Claude Developer Platform", 2025-11-24: 55K, 72K and 134K counts, tool search figures. https://www.anthropic.com/engineering/advanced-tool-use
2. Anthropic pricing: Opus 5 and Opus 5.5 rates, cache multipliers and break-even, tool use pricing, tokenizer note. https://platform.claude.com/docs/en/about-claude/pricing
3. Anthropic prompt caching: tool-definition invalidation, workspace isolation, `inline-tools-2026-09-15`. https://platform.claude.com/docs/en/build-with-claude/prompt-caching
4. Claude Code MCP documentation: tool search default and the `ANTHROPIC_BASE_URL` fallback. https://code.claude.com/docs/en/mcp
5. Anthropic, "Code execution with MCP", the 50,000-token transcript example. https://www.anthropic.com/engineering/code-execution-with-mcp
6. Maria Paktiti, WorkOS, "What an MCP server costs you in tokens", 2026-09-18 (vendor). https://workos.com/blog/mcp-server-token-cost
7. Şevval Alper, "Code Execution with MCP", AIMultiple. https://aimultiple.com/code-execution-with-mcp
8. Noah Mogil, "Performance Testing of Twilio Alpha's MCP Server", Twilio, 2025-04-10 (vendor). https://www.twilio.com/en-us/blog/developers/twilio-alpha-mcp-server-real-world-performance

**Specification**
9. MCP specification 2026-07-28 changelog, deterministic tool ordering. https://modelcontextprotocol.io/specification/2026-07-28/changelog
10. MCP specification 2026-07-28, tools: per-authorization tool sets, no cost field, annotations untrusted. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
11. MCP specification 2026-07-28, schema: `idempotentHint`, `destructiveHint`. https://modelcontextprotocol.io/specification/2026-07-28/schema
12. MCP specification 2026-07-28, `_meta` and OpenTelemetry trace context. https://modelcontextprotocol.io/specification/2026-07-28/basic/index
13. MCP Security Interest Group charter, runtime drift item. https://modelcontextprotocol.io/community/interest-groups/security
14. MCP Enterprise-Managed Authorization extension. https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization
15. SEP-2007, payment support, closed as dormant 2026-06-24. https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2007
16. MCP issue #3393, paid MCP tools with x402, closed as not planned 2026-09-28. https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3393

**Attribution**
17. FinOps Foundation, "Tokenomics: Managing AI Value in SaaS Model Token Costs". https://www.finops.org/wg/token-economics-saas/
18. Claude Code monitoring: cost counter MCP attributes, redaction, version floor, span hierarchy. https://code.claude.com/docs/en/monitoring-usage
19. OpenTelemetry GenAI attribute registry. https://github.com/open-telemetry/semantic-conventions/blob/main/docs/registry/attributes/gen-ai.md
20. OpenTelemetry semantic conventions issue #1062, token cost. https://github.com/open-telemetry/semantic-conventions/issues/1062
21. OpenTelemetry issue #1593, ownership and cost centre conventions. https://github.com/open-telemetry/semantic-conventions/issues/1593
22. OpenTelemetry issue #1598, cloud financial management conventions. https://github.com/open-telemetry/semantic-conventions/issues/1598
23. OpenTelemetry PR #3866, service instance cost center, merged 2026-09-16. https://github.com/open-telemetry/semantic-conventions/pull/3866
24. OpenLIT semantic conventions, `gen_ai.usage.cost`. https://github.com/openlit/openlit/blob/main/sdk/python/src/openlit/semcov/__init__.py

**Tool pricing**
25. LiteLLM MCP cost tracking. https://docs.litellm.ai/docs/mcp_cost
26. Bifrost MCP client schema, `tool_pricing`. https://github.com/maximhq/bifrost/blob/main/core/schemas/mcp.go

**Observability**
27. Langfuse pricing. https://langfuse.com/pricing
28. Langfuse, "How Langfuse runs ClickHouse at agent scale" (vendor). https://langfuse.com/resources/engineering/clickhouse-at-agent-scale
29. Datadog Agent Observability product page. https://www.datadoghq.com/products/ai/agent-observability/
30. Datadog price list, retention tiers. https://www.datadoghq.com/pricing/list/

**Unpriced lines**
31. Zuplo, "Build vs Buy MCP Server Infrastructure", 2026-04-22 (vendor). https://zuplo.com/learning-center/build-vs-buy-mcp-server-infrastructure
32. Dumebi Okolo, Composio, "Building vs Buying an Enterprise MCP Gateway", 2026-05-14 (vendor). https://composio.dev/content/building-vs-buying-an-enterprise-mcp-gateway

**Prior art**
33. Komandooru, DeVries and Najafzadeh, "MCP went stateless: is your AWS MCP server deployment Well-Architected?", 2026-09-01. https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
34. AWS Well-Architected Agentic AI Lens, cost optimization. https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/cost-optimization.html
