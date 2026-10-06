---
title: "The MCP Cost Nobody Invoices: Tool Definitions Resent on Every Call"
subtitle: "Operating MCP at scale, part five: cost"
date: 2026-10-05
revised: 2026-10-06
status: draft
prefix: "Research"
series: "Operating MCP at Scale"
part: 5
sources_verified_on: 2026-10-06
---

# The MCP Cost Nobody Invoices: Tool Definitions Resent on Every Call

*Operating MCP at scale, part five: cost.*

Five common MCP servers put 55,000 tokens of tool definitions in front of the
model before a conversation starts, and a client that loads them all pays for
those tokens again on every model call [1]. Across a fleet that can be a
six-figure line every month, and nothing on the invoice, in the budget or in the
protocol names it as MCP. The team paying for it usually cannot see it, and the
team that controls it usually does not know it is a cost.

Here is how it plays out for one imagined fleet, and then why it happens.

## Who spends, and who can see it

| Party | What it controls | What it can see |
|---|---|---|
| The budget owner | The AI line in the plan | An invoice "by API key or project, not by business unit, cost center, application, or team" [2] |
| The platform team | Which clients run, which gateway they use, which servers each role gets | Input tokens at the gateway, with tool definitions counted like any other input |
| The client | Which tool definitions go into each model call, and in what order | Nothing about price |
| The server author | How many tools a server has, and how long each description is | Nothing about who loads them, or how often |
| The provider | The price of every token | Input tokens, "including in the `tools` parameter" [3] |

Every party can see part of the cost. None of them sees the tool surface as a line
of its own.

## A quiet month

Imagine a company running one million agent tasks a month, with 20 model calls
per task. Those volumes are my assumption, and you should swap in your
own. Its engineers use Claude Code with five servers like the ones in Anthropic's
example, GitHub, Slack, Sentry, Grafana and Splunk: "58 tools consuming
approximately 55K tokens before the conversation even starts" [1].

Most of that never reaches the model. Claude Code defers MCP tools by default and
discovers them on demand [4], so each call carries a tool search tool "(~500
tokens)" plus "3-5 relevant tools, ~3K tokens" [1]. At Opus 5 list prices,
read on 6 October, with one cache write at the start of each task and cache reads
after it, that surface costs about $55,000 a month [3]. It is real money, and
it is lost inside a much larger inference bill.

## The same fleet, one quarter later

Two reasonable changes land.

The platform team routes every client through its own LLM gateway, so it can
enforce budgets and keep logs in one place. It points `ANTHROPIC_BASE_URL` at the
gateway. Claude Code turns tool search off when that variable points to a
non-first-party host, "since most proxies don't forward `tool_reference` blocks"
[4]. From that day the full 55,000-token surface rides on every call.

Then security asks for least privilege. Under the 2026-07-28 revision a server's
tool set can "vary by the authorization presented on the request", for example
"returning only the tools the caller's granted scopes permit" [5]. The team
turns it on. Each distinct permission set is now a distinct prompt prefix, with
its own cache to warm.

The tasks are the same, the model is the same, and so is the number of calls.
Assume caching behaves as it did before. On the arithmetic below, the surface
line goes from about $55,000 a month to about $866,000, and the per-user tool
lists push it higher by an amount nobody has published a way to estimate. The
budget owner sees input tokens rise under the gateway's API key [2]. The
gateway sees more input tokens and has no field that says which of them were tool
definitions. Neither change was a mistake, and the fix for the first one is a
single environment variable, which comes later.

## Where the money goes

The arithmetic fits on one line, so you can redo it with your own numbers:

> monthly cost = tasks per month × model calls per task × surface tokens × price per million ÷ 1,000,000

Prices are Anthropic's list prices, read on 6 October [3]. Opus 5 input is $5
per million tokens, a five-minute cache write is $6.25, and a cache read is
$0.50. Opus 5.5 cache reads are $0.20.

| Tool surface per call | Where the count comes from | Opus 5, all cache reads | Opus 5, one write then 19 reads per task | Opus 5, uncached | Opus 5.5, all cache reads |
|---|---|---|---|---|---|
| ~3,500 tokens, deferred | Tool search "(~500 tokens)" plus "3-5 relevant tools, ~3K tokens" [1] | ~$35,000 | ~$55,000 | ~$350,000 | ~$14,000 |
| 55,000 tokens, all loaded | Anthropic's five-server example [1] | ~$550,000 | ~$866,000 | ~$5,500,000 | ~$220,000 |
| 134,000 tokens, all loaded | "tool definitions consume 134K tokens before optimization" [1] | ~$1,340,000 | ~$2,110,000 | ~$13,400,000 | ~$536,000 |

Worked through for the 55K row: 1,000,000 × 20 × 55,000 is 1.1 trillion tokens.
At the $0.50 cache-read price that is $550,000; at the $5 uncached price,
$5,500,000. The middle column charges one cache write at the start of each task
and reads after it, which averages about $0.79 per million and lands near
$866,000. That column is where the imagined fleet sat in both of its months.

Two cautions on the inputs. Anthropic published the counts in November 2025, and
its pricing page now says Claude 4.7 and later models use a tokenizer that
"produces approximately 30% more tokens for the same text" [3]. I did not
re-count. The table also leaves out tool results, which are input on every later
turn too. One transcript passed between two tools "could mean processing an
additional 50,000 tokens" [6], and I found no fleet-scale measurement of
results.

The one measurement of MCP's share against a no-MCP baseline comes from a vendor
measuring its own server. Twilio ran the Cline agent with and without its MCP
server, repeating each task at least ten times. Cost rose about 27.5% on average,
with "~28.5% more cache reads and ~53.7% more cache writes", and tasks finished
about 20.5% faster [7].

## A cached prefix is cheap until it moves

Caching is what takes the 55K row from $5.5 million to $550,000, and it holds
only while the prefix is identical. "Modifying tool definitions (names,
descriptions, parameters) invalidates the entire cache" [8]. On a 55K surface
on Opus 5, a write instead of a read costs about $0.32 more per call.

An upstream release is cheap. Each distinct surface in each workspace pays one
new write, plus rewriting the cached history of conversations in flight. For a
fleet with a few dozen distinct surfaces that is tens of dollars per release. On
the Claude API, Claude Platform on AWS and Microsoft Foundry the cache is isolated
per workspace, so a fleet split across workspaces warms each one separately
[8].

The expensive case is a prefix that never settles, and MCP has two ways to
produce one. The first is tool order. The 2026-07-28 revision says servers
"SHOULD return tools from `tools/list` in a deterministic order" to keep caches
warm [9]. A server that shuffles on every connection breaks the cache on every
connection. The client can fix this on its own: it assembles the `tools` array,
so sorting by server and tool name gives a stable prefix whatever the servers
return.

The second is the per-caller tool list from the imagined quarter. A fleet that
scopes tools per user can hold as many cached surfaces as it has permission
combinations, which moves it from the all-reads column toward the middle one.
Tighter access control costs cache hit rate, and nothing published measures by
how much.

One recent change helps. With Anthropic's `inline-tools-2026-09-15` beta, a client can
"add a tool, or change a tool's definition, partway through a conversation
without editing `tools`", after which "The cached prefix still matches" [8]. A
client that applies a `list_changed` notification that way keeps its cache.

## Nothing between the API key and the server names the line

The closest thing to MCP attribution is in Claude Code's telemetry. Its cost
counter carries `mcp_server.name`, the "MCP server whose tool result this request
consumed" [10]. That attributes the cost of reading a tool's output to the
server that produced it. It does not split tool-definition tokens by server, which
is the line this part prices. Configured server names are replaced with
`"custom"` unless `OTEL_LOG_TOOL_DETAILS=1` is set, which also exports tool
parameters and inputs [10]. Naming your internal servers in cost data means
exporting what was sent to them.

The protocol carries no cost and no payer. The 2026-07-28 tools page has no price,
cost or budget field [5]. `_meta` reserves `traceparent`, `tracestate` and
`baggage` for OpenTelemetry context [11], with no key for a user or cost center,
and baggage is asserted by the caller, so it can correlate but should not decide
who pays. The authenticated carrier is the token: OAuth token exchange, and the
Enterprise-Managed Authorization extension, which puts the organization's identity
provider in charge of server access [12]. I found no published convention that
joins the principal in that token to a cost record.

OpenTelemetry does not fill the gap yet. Its GenAI conventions define token counts
and no cost attribute [13]. A 2024 proposal to add one was withdrawn after a
maintainer asked, "How would instrumentation code know the cost of token?"
[14]. Payment inside MCP has not moved either: SEP-2007 was closed in June as
dormant [15], and a paid-tools issue built on x402 was closed as not planned on
28 September [16].

Gateways count a tool's own cost only if an operator types in its price. LiteLLM
takes a fixed `default_cost_per_query` per server with per-tool overrides, or a
hook that sets a cost per call [17]. Bifrost has a per-client `tool_pricing`
map, "cost per execution" [18]. Neither page says whether tool cost counts
against the same budget as inference.

## Four levers, and what each one costs you

| Lever | Measured effect | Evidence |
|---|---|---|
| Tool search or deferred loading | Definition tokens from ~72K to ~3.5K, about 95% (my arithmetic) | Anthropic's own comparison [1]; default in Claude Code [4] |
| Code execution in place of direct tool calls | 77.4% fewer total tokens; output up 120%, latency up 7% | AIMultiple, independent, two tasks, GPT-4.1 [19] |
| Prompt caching | Reads at 0.1x base input on Opus 5; a five-minute write "pays off after one cache read" | Published price [3] |
| Deterministic tool order | Keeps the prefix stable | Specification SHOULD [9]; no measured effect found |

Deferred loading is the lever the imagined fleet lost, and it is the cheapest to
get back. Claude Code behind your own gateway keeps tool search off unless you set
`ENABLE_TOOL_SEARCH` [4]. On the Messages API, tools load in full unless marked
`defer_loading` [3]. The cost of deferring is that the model has to search for
a tool before it can call one.

Code execution's saving depends on what the removed tokens cost. Repricing
AIMultiple's token counts at Opus 5 rates (my arithmetic), cost per run falls
about 73% when input is uncached and about 35% when input is billed at the
cache-read rate. The extra output tokens cost $25 per million either way. A fleet
that already caches well gets the smaller number, and pays for it in latency.

Caching and ordering cost nothing to adopt, but they reward the opposite of what
per-caller tool lists ask for. That trade between access control and cache hit
rate is the one this part cannot price for you.

## What to do, depending on who you are

**If you own the AI budget,** ask the platform team for one number: definition
tokens per model call, per client. Put it and your own task volume into the
formula above, and carry it as its own line. Until someone measures it, it is
invisible inside "input tokens."

**If you run the clients and the gateway,** check whether every client and agent
runtime defers tools, including Claude Code behind your own gateway. Give each
role only the servers it needs. Sort the `tools` array in the client. Count how
many distinct permission sets your per-caller tool lists produce, because each is
a cache you pay to warm. Enter prices for the tools that wrap paid APIs, or they
cost zero in your spend data. Derive the payer from the authenticated token at
each hop and use `baggage` only to correlate.

**If you write MCP servers,** return `tools/list` in a deterministic order and
keep descriptions short. Every token you add to a description is billed on every
call of every client that loads your server.

## What nobody has priced yet

Three lines on an MCP budget still have no independent figure. Building the
control plane has only vendor estimates from companies selling the alternative,
such as Zuplo's "2-4 engineers working for 3-6 months" for a production server
[20], with no sample or method. Reviewing servers has none at all: part two
counted 39,617 servers in the official registry on October 5, and I found
published effort figures for building servers and none for reviewing them. The
third is re-review, which a `list_changed` from an approved server may oblige,
and I found no figure for how often approved servers change.

The limit of this part is that its dollar figures rest on published token counts,
list prices and an assumed volume. I have seen no fleet's invoice. My guess is that
the review cost is larger than the cache cost of the same change, and nobody,
including me, has measured it. If you run an MCP review process, count the hours
from your first server and publish them.

## What it adds up to

The largest MCP cost you can price today is the tool surface your clients resend
on every model call. It is billed as ordinary input tokens under whoever's key
made the call, so no invoice, budget or protocol field names it. It is also the
cost you can cut fastest. Find out which clients load every definition, price the
surface you carry, keep it short and stable, and put the number in front of
whoever owns the AI budget.

---

*Part five of five on operating MCP at scale. Parts one to four cover
operational excellence, security, reliability and performance.*

## Sources

All URLs verified 2026-10-06. Vendor posts are marked.

1. Anthropic, "Introducing advanced tool use on the Claude Developer Platform", 2025-11-24: 55K, 72K and 134K counts, tool search figures. https://www.anthropic.com/engineering/advanced-tool-use
2. FinOps Foundation, "Tokenomics: Managing AI Value in SaaS Model Token Costs". https://www.finops.org/wg/token-economics-saas/
3. Anthropic pricing: Opus 5 and Opus 5.5 rates, cache multipliers and break-even, `defer_loading`, tokenizer note. https://platform.claude.com/docs/en/about-claude/pricing
4. Claude Code MCP documentation: tool search default and the `ANTHROPIC_BASE_URL` fallback. https://code.claude.com/docs/en/mcp
5. MCP specification 2026-07-28, tools: per-authorization tool sets, no cost field, annotations untrusted. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
6. Anthropic, "Code execution with MCP", the 50,000-token transcript example. https://www.anthropic.com/engineering/code-execution-with-mcp
7. Noah Mogil, "Performance Testing of Twilio Alpha's MCP Server", Twilio, 2025-04-10 (vendor). https://www.twilio.com/en-us/blog/developers/twilio-alpha-mcp-server-real-world-performance
8. Anthropic prompt caching: tool-definition invalidation, workspace isolation, `inline-tools-2026-09-15`. https://platform.claude.com/docs/en/build-with-claude/prompt-caching
9. MCP specification 2026-07-28 changelog, deterministic tool ordering. https://modelcontextprotocol.io/specification/2026-07-28/changelog
10. Claude Code monitoring: cost counter MCP attributes, redaction. https://code.claude.com/docs/en/monitoring-usage
11. MCP specification 2026-07-28, `_meta` and OpenTelemetry trace context. https://modelcontextprotocol.io/specification/2026-07-28/basic/index
12. MCP Enterprise-Managed Authorization extension. https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization
13. OpenTelemetry GenAI attribute registry. https://github.com/open-telemetry/semantic-conventions/blob/main/docs/registry/attributes/gen-ai.md
14. OpenTelemetry semantic conventions issue #1062, token cost. https://github.com/open-telemetry/semantic-conventions/issues/1062
15. SEP-2007, payment support, closed as dormant 2026-06-24. https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2007
16. MCP issue #3393, paid MCP tools with x402, closed as not planned 2026-09-28. https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3393
17. LiteLLM MCP cost tracking. https://docs.litellm.ai/docs/mcp_cost
18. Bifrost MCP client schema, `tool_pricing`. https://github.com/maximhq/bifrost/blob/main/core/schemas/mcp.go
19. Şevval Alper, "Code Execution with MCP", AIMultiple. https://aimultiple.com/code-execution-with-mcp
20. Zuplo, "Build vs Buy MCP Server Infrastructure", 2026-04-22 (vendor). https://zuplo.com/learning-center/build-vs-buy-mcp-server-infrastructure
