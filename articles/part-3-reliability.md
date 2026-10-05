---
title: "Your Health Check Is Speaking a Different Protocol Version"
subtitle: "Operating MCP at scale, part three: reliability"
date: 2026-10-01
status: draft
series: "Operating MCP at Scale"
part: 3
sources_verified_on: 2026-09-30
---

# Your Health Check Is Speaking a Different Protocol Version

*Operating MCP at scale, part three: reliability.*

Slack runs a production MCP server at `mcp.slack.com/mcp`. It exposes 26 working
tools. In late September somebody filed a bug against an MCP client because that
server sat forever in "connecting" and never became usable.

The server was fine. The client health-checked it with `ping`, Slack's server
answered `-32601`, method not found, and the client read a valid answer as a
dead peer.

That is not an isolated defect. It is a failure class, it has been written up at
least five times in four weeks, and it will keep happening for a year.

| Project | What happened |
|---|---|
| A client holding Slack's server in "connecting" | Production server answers `-32601` to `ping`; 26 working tools never reachable |
| A runtime killing servers on a cycle | Server answers `-32601`; clients "kill and restart the server every cycle", about 55 seconds observed |
| A virtual-MCP health probe | Probes with HTTP GET; backends answering `405` or `400` per spec are excluded from tool routing, though `initialize`, `ping` and `tools/list` all work over POST |
| A gateway registry health service | Skips `notifications/initialized`, so the following `ping` gets `404 Session not found` and a hosted Salesforce server is marked unhealthy with zero tools |
| A gateway's own benchmark fixture | Fixture never implemented `ping`; the v4 branch's probe shed all its traffic |

Five instances, four different root causes, one shape: **a health check reading a
conformant answer as a failure and removing a working server.**

## Why it keeps happening

`ping` was removed from the protocol in the 2026-07-28 revision, alongside
`logging/setLevel` and `notifications/roots/list_changed`.

The important part is what the previous revision said. Under 2025-11-25 a
receiver "MUST respond promptly with an empty response," implementations
"SHOULD periodically issue pings to detect connection health," and "Multiple
failed pings MAY trigger connection reset."

So a client that pings every ten seconds and resets after three failures is not
badly written. **It is doing exactly what its own specification told it to do.**
It is simply speaking to a server from a different era, and both sides are
compliant with the revision they think they are in.

That is the shape of every row in the table. Not negligence on either side.
Version skew where each party is correct.

The maintainers explain the removal in SEP-2575, and the reasoning is sound:

> "Client-to-server ping is also removed because any normal RPC call already
> proves server liveness, and transport-layer mechanisms (HTTP keep-alives, SSE
> comments, STDIO process state) already cover connection health."

That is true, and it is worth saying that a fourth row in the table predates the
revision entirely. The class is not caused by the removal. The removal enlarged
it.

## The new probe has an edge the changelog does not mention

`server/discover` is the replacement and it is better for readiness than a ping
ever was. It is a mandatory RPC returning supported protocol versions,
capabilities and identity in one call, which tells you the peer is alive **and**
which era it speaks. In a mixed fleet that second half is the question you
actually have.

But it is a capability read, not a no-op, and capability reads are cacheable.

The caching page lists `server/discover` first among the results on which
"Servers MUST include caching hints." The `server/discover` page's own example
response carries `"ttlMs": 3600000, "cacheScope": "public"`. And the scope table
defines a public response as one that "Any client, shared gateway, or caching
proxy MAY store and serve the cached response to any user."

Read those three together. **A shared gateway may answer your liveness probe out
of a cache with an hour's freshness, without the backend being involved at all.**

Check the changelog and you will not find this: its list of cacheable results
omits `server/discover`. The two specification pages are where it lives. If you
are designing a health check on top of `server/discover`, that is the detail
that decides whether it measures anything.

## What gateways actually ship, stated precisely

It is tempting to say the ecosystem has not built resilience. That is wrong, and
a maintainer will produce the code in about a minute.

**ContextForge ships retry with backoff and automatic recovery.** Its
`retry_manager.py` implements exponential backoff with jitter and has been in
tree since July 2025, wired into both the gateway and tool services. Its health
checker flips a `reachable` flag rather than disabling anything, and the next
passing probe reactivates the backend on its own. Only a gateway an operator
disabled by hand stays down.

The narrower and true claim is about defaults. Its three-state circuit breaker,
with a half-open trial request, exists as a plugin and **ships with
`mode: "disabled"`.** So a team that installs the most documented open-source MCP
gateway and changes nothing gets retry and reactivation, and does not get a
breaker unless it goes looking.

The gap worth naming is elsewhere and it is a project-level one. The official
client best-practices page carries **no guidance at all** on health checks,
timeouts, retries or reconnection. Every implementer in that table above was
making it up, which is why five of them made it up differently.

## Session startup is what trips your rate limits

The usual mental model says tool calls generate load. The measured evidence puts
the first failure somewhere else entirely.

One deployment made 2,021 downstream connections across 90 session startups,
about 22.5 per session, and collected 69 HTTP 429s from a provider that was
serving **zero tools** at the time. Those rejections came from session-start
connects and tool-list loads, before any tool was invoked.

That measurement comes from one client-side aggregator on one machine, so treat
the ratio as an existence proof rather than a benchmark. The design conclusion
survives the caveat: if you throttle tool invocation and not session
establishment, you are throttling the thing that was not the problem.

## The SLO picture is not empty, it is misaligned

I expected to find nothing here. That was wrong, and the real picture is more
useful.

**The MCP Registry working group publishes a numeric target.** Its charter lists
under success criteria "Registry uptime ≥ 99.9% with automated monitoring and
alerting," and scopes the group to uptime, monitoring and incident response. The
terms of service disclaim any guarantee, which makes it an objective rather than
an agreement, and that is exactly what an objective is. The same charter still
shows its uptime and monitoring automation as planned.

**At least one gateway vendor names MCP inside an availability commitment.**
TrueFoundry's SLA commits to 99.9% and lists "MCP control surfaces" among covered
components. MintMCP's status page carries a component called "MCP Gateway" with a
ninety-day uptime bar.

What is genuinely missing is narrower and more interesting: **the large
first-party hosted MCP servers publish status components without numbers.**
Cloudflare, Notion, Zapier, Figma and Atlassian Rovo each list an MCP component
on a public status page and attach no availability figure to it. Azure API
Management's MCP feature sits under the service's existing SLA, which does not
name MCP.

So the commitments that exist come from the registry and from gateway vendors.
The servers most enterprises actually depend on expose a status light and no
number.

One warning if you go looking for targets. The one framework that addresses MCP
SLOs directly is content marketing, attributes its latency distribution to its
own unpublished production observability, and **misquotes Google's burn-rate
table**, presenting 6x as a ticketing threshold. In the SRE Workbook, for a 99.9%
objective, 6x is a page:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|---|---|---|---|---|
| Page | 1 hour | 5 minutes | 14.4 | 2% |
| Page | 6 hours | 30 minutes | 6 | 5% |
| Ticket | 3 days | 6 hours | 1 | 10% |

Cite Google directly. The table is free and correct.

## What to actually do

**Do not health-check with `ping`.** It does not exist in the current revision,
a compliant server will refuse it, and five projects have now shipped that bug.
If your client or gateway pings, it is removing working servers from your estate
right now.

**If you probe with `server/discover`, make sure your probe cannot be served from
cache.** Its example response ships an hour of public freshness. A probe a proxy
can answer is not a liveness check.

**Treat a protocol error as an answer, not a failure.** Every incident in that
table came from reading a valid JSON-RPC error as a dead peer. A response proves
liveness whatever its content, which is the maintainers' own argument for
removing the ping in the first place.

**Check your gateway's defaults, not its features.** The resilience you want may
be present and switched off. For the most documented open-source option, retry
and reactivation are on and the circuit breaker is not.

**Throttle session establishment, not just tool calls.** That is where the
measured rate limiting happened.

**Set your own objective at the MCP boundary.** The registry publishes one for
itself and some gateway vendors name MCP in an SLA, but the hosted servers you
depend on almost certainly do not, so an end-to-end number you did not define
measures something nobody has promised you.

---

*Part three of five on operating MCP at scale. Parts one and two cover
operational excellence and security. Parts four and five cover performance and
cost.*

*AWS published an architecture view of this revision on 1 September, reaching
several of the same conclusions from the platform side and assuming their
services throughout. It is worth reading alongside this.*

## Sources

All URLs verified 2026-09-30.

**Specification**
1. Changelog 2026-07-28, for the removal of `ping`. https://modelcontextprotocol.io/specification/2026-07-28/changelog
2. Caching, for the cacheable-results list and the scope table. https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
3. `server/discover`, for the example response carrying `ttlMs` and `cacheScope`. https://modelcontextprotocol.io/specification/2026-07-28/server/discover
4. Ping, revision 2025-11-25, for the periodic-ping recommendation and connection reset. https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/ping
5. Client best practices, which carries no health check, timeout, retry or reconnection guidance. https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices
6. Streamable HTTP, for the required routing headers. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http

**The failure class**
7. `edouard-claude/penelope` #276, Slack's production server and the 26 unreachable tools. https://github.com/edouard-claude/penelope/issues/276
8. `trycua/cua` #4001, servers killed and restarted on a cycle. https://github.com/trycua/cua/issues/4001
9. `stacklok/toolhive` #6497, GET probes excluding conformant backends. https://github.com/stacklok/toolhive/issues/6497
10. `agentic-community/mcp-gateway-registry` #1817, the skipped initialization and the unhealthy Salesforce server. https://github.com/agentic-community/mcp-gateway-registry/issues/1817
11. `MikkoParkkola/mcp-gateway` #567, the benchmark fixture. https://github.com/MikkoParkkola/mcp-gateway/issues/567

**Gateway implementation**
12. ContextForge retry manager, exponential backoff with jitter. https://github.com/IBM/mcp-context-forge/blob/main/mcpgateway/utils/retry_manager.py
13. ContextForge ADR-0009 on built-in health checks and automatic reactivation. https://github.com/IBM/mcp-context-forge/blob/main/docs/docs/architecture/adr/009-built-in-health-checks.md
14. ContextForge circuit-breaker plugin, which ships disabled. https://github.com/IBM/mcp-context-forge/tree/main/plugins/circuit_breaker

**Objectives**
15. MCP Registry working group charter, the 99.9% success criterion. https://modelcontextprotocol.io/community/working-groups/registry
16. TrueFoundry service level agreement, naming MCP control surfaces. https://www.truefoundry.com/service-level-agreement
17. MintMCP status page, MCP Gateway component. https://status.mintmcp.com/
18. Google SRE Workbook, alerting on SLOs. https://sre.google/workbook/alerting-on-slos/

**Prior art**
19. Komandooru, DeVries and Najafzadeh, "MCP went stateless: is your AWS MCP server deployment Well-Architected?", 2026-09-01. https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
