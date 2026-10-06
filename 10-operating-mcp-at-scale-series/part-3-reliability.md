---
title: "The Server Was Fine: Why MCP Health Checks Keep Marking Working Servers Down"
subtitle: "Operating MCP at scale, part three: reliability"
date: 2026-10-01
revised: 2026-10-06
status: draft
prefix: "Research"
series: "Operating MCP at Scale"
part: 3
sources_verified_on: 2026-10-06
---

# The Server Was Fine: Why MCP Health Checks Keep Marking Working Servers Down

*Operating MCP at scale, part three: reliability.*

On September 30, 2026, Slack's production MCP server answered every tool call a
client sent it, and the client still listed it as "connecting" [1]. The client's
health check had asked the server for `ping`, the server had replied that it did
not know that method, and the client had read the reply as a dead peer. That was
one of five cases written up in September in which a health check looked at a
working MCP server and marked it down, each on a different codebase [1][2][3][4][5].
This article shows how it happens, why the probe that replaces `ping` has a trap
of its own, and what a health check looks like when it has to survive a fleet
that speaks two protocol revisions at once.

Let me start with the rule everyone was following.

## Clients were told to ping

Three parties meet on every one of these connections: a client or gateway built
to an older revision of the specification, a server that does not serve `ping`,
and the specification itself, which changed its mind between them.

The 2025-11-25 revision was explicit. A receiver "MUST respond promptly with an
empty response," implementations "SHOULD periodically issue pings to detect
connection health," and "Multiple failed pings MAY trigger connection reset" [6].
A client that pings every ten seconds and resets after three failures is following
that text to the letter.

On a normal day that loop is invisible. The exchange is one line each way:

```
→ {"jsonrpc":"2.0","id":2,"method":"ping"}
← {"jsonrpc":"2.0","id":2,"result":{}}
```

The server is marked ready, tools route to it, and nobody thinks about the probe
again until a server truly stops answering.

Then the 2026-07-28 revision removed `ping`, along with `logging/setLevel` and
`notifications/roots/list_changed` [7]. A server on the current revision answers
an unknown method with `-32601`, method not found, and on Streamable HTTP with a
`404` carrying that code [8]. Some servers send that reply even when they
negotiated an older revision that still requires `ping` [1]. Clients written to
the old rule kept pinging, and a refusal reads to them like a failure.

## Five working servers, marked down

**Slack.** The client was `penelope`, and its maintainer was validating Slack's
hosted server, which had negotiated protocol 2025-06-18 [1]. The client's own
test command passed: 26 tools listed and six real calls succeeded. Its server
list still showed Slack as `connecting`, with an error ending "Method not found:
ping." Its diagnostic command raised a warning and suggested reading the
logs and restarting the server, which changed nothing, because nothing was
broken. The maintainer filed the issue and closed it the same afternoon [1].

**A desktop-automation server.** `cua-driver` 0.22.0 on Windows answered the
same probe like this [2]:

```
→ {"jsonrpc":"2.0","id":2,"method":"ping"}
← {"jsonrpc":"2.0","id":2,"error":{"code":-32601,"message":"Unknown method: ping"}}
```

A gateway hosting it as a stdio child counted every reply as a failure and
restarted it on a cycle of 53 to 57 seconds: 131 and 132 disconnects in two hours
on two hosts, with windows in which clients saw zero tools [2]. With no pings
sent, the same process ran for 84 seconds without exiting. The workaround was to
tell the gateway not to ping, and the reporter named its cost: slower detection
of children that really are dead [2]. Here the server was the one out of line,
and the reporter asked it to implement `ping`. The outcome was the same. A server
that could do all of its work was taken offline roughly once a minute over the
one method it did not serve.

**A gateway's own test backend.** The clearest record comes from a gateway
project that caught the failure in its own load test before release [5]. Its
next major version probed every backend with `ping` every ten seconds and
escalated on the third refusal. Its benchmark fixture had never implemented
`ping`. The log reads:

```
11:45:20  Health probe was not served  method="ping" code=-32601 consecutive=1
11:45:30  Health probe was not served  method="ping" code=-32601 consecutive=2
11:45:40  record_failure{reason="health probe unserved"} failures=1..5 threshold=5
11:45:40  Circuit breaker opened backend=workload reason=health probe unserved
11:45:40  Circuit open, rejecting request
```

About thirty seconds after start, the breaker opened and the backend shed all of
its traffic. The breaker rebuilt the transport, and the rebuilt process still did
not serve `ping`, so the cycle repeated. Under a 60-second load with 50 virtual
users, `tools/call` succeeded 48.7% of the time against 100% on the previous
release, with 0.00% HTTP errors: every failure was an HTTP 200 carrying a
JSON-RPC error [5]. An alert built on HTTP error rates would have stayed quiet.
The project fixed it the next day by treating `-32601` as proof of life [5].

**Two more, with other causes.** A virtual-MCP layer probed its backends with
HTTP GET, which Streamable HTTP makes optional. The report's example was
Tableau's MCP server, which accepts POST only. A backend answering `405` or `400`,
as the transport allows, was excluded from tool routing while `initialize`,
`ping` and `tools/list` all worked over POST [3]. A gateway
registry's health service skipped `notifications/initialized`, so its next `ping`
got `404 Session not found`, and a hosted Salesforce server was marked unhealthy
with zero tools [4].

That is three different root causes and one shape. In every case a server
answered, the answer was a JSON-RPC error in three cases and an HTTP status in
two, and the health check treated an answer as an absence.

## Any reply proves the server is alive

The maintainers explained the removal of `ping` in SEP-2575:

> "Client-to-server ping is also removed because any normal RPC call already
> proves server liveness, and transport-layer mechanisms (HTTP keep-alives, SSE
> comments, STDIO process status) handle connection-health checks more
> appropriately." [9]

That reasoning holds, and it is also the fix. A server that sends back `-32601`
has received the request, parsed it, and written a reply. Only silence, a refused
connection or a timeout says otherwise.

The removal did not create this failure class, since two of the five cases have
nothing to do with `ping`. It did enlarge it, and it will stay enlarged for as
long as clients and servers from two revisions share a fleet.

## The replacement probe can be answered from a cache for an hour

`server/discover` takes over from `ping`, and for readiness it is better. It is a
mandatory call that returns supported protocol versions, capabilities and
identity, so one request tells you the peer is alive and which revision it
speaks [10]. In a mixed fleet the second answer is the one you need.

It is also a capability read, and capability reads are cacheable. The caching
page lists `server/discover` first among the results on which "Servers MUST
include caching hints" [11]. The `server/discover` page's own example response
carries `"ttlMs": 3600000, "cacheScope": "public"` [10], and the caching page
defines a public response as one that "Any client, shared gateway, or caching
proxy MAY store and serve the cached response to any user" [11].

Put those three lines together and a shared gateway may answer your liveness
probe from its cache for an hour without the backend being involved. The
changelog's list of cacheable results omits `server/discover` [7], so a team that
reads only the changelog will not see it. If you own the server, return
`ttlMs: 0`, which the caching page says "SHOULD be considered immediately stale"
[11]. If you do not, probe the backend directly.

## Nothing upstream will catch it for you

Each implementer in those five cases wrote its own health rule, because there
was no current one to copy. The official client best-practices page carries no
guidance on health checks, timeouts, retries or reconnection [12].

The gateways have built more resilience than their reputation suggests, and the
gap is in the defaults. ContextForge has had exponential backoff with jitter in
tree since July 2025, wired into its gateway and tool services [13]. Its health
checker flips a `reachable` flag, and the next passing probe brings a backend
back on its own; only a gateway an operator disabled by hand stays down [14]. Its
per-tool circuit breaker, with a half-open trial request, exists as a plugin and
ships with `mode: "disabled"` in the default configuration [15]. Install it and
change nothing, and you get retry and recovery with no breaker.

Nor will anyone you depend on hand you an availability number to alert against.
The MCP Registry working group lists "Registry uptime ≥ 99.9% with automated
monitoring and alerting" among its success criteria [16], while the registry's
terms of service disclaim any guarantee [17], so that is an objective. TrueFoundry's
SLA commits to 99.9% and names "MCP control surfaces" [18], and MintMCP's status
page shows an "MCP Gateway" component with a ninety-day uptime bar [19]. Azure API
Management documents its MCP feature with no MCP-specific availability commitment
[20]. The hosted servers in your critical path show a status light and no number,
so the objective is yours to set.

## What to do, depending on who you are

Here is the whole argument as a probe specification you can check line by line
against the sources:

```yaml
# MCP backend health probe, for a fleet that mixes 2025-11-25 and 2026-07-28 peers
probe:
  method: server/discover          # replaces ping; also reports the revision spoken [10]
  path: direct-to-backend          # never through a shared gateway or caching proxy [11]
  alive_if: any_response           # a JSON-RPC error or HTTP status is still an answer [9]
  treat_as_alive:
    - jsonrpc_error: -32601        # unknown method, the current-revision refusal of ping [8]
    - http_status: 404             # Streamable HTTP carrying -32601 [8]
  dead_only_if:
    - connect_failure
    - timeout
server_side:
  server_discover_ttl_ms: 0        # "SHOULD be considered immediately stale" [11]
alerting:
  objective: 0.999                 # yours; hosted servers publish none [20]
  page: [{window: 1h, short: 5m, burn: 14.4}, {window: 6h, short: 30m, burn: 6}]
  ticket: [{window: 3d, short: 6h, burn: 1}]   # Google SRE Workbook Table 5-8 [21]
```

**If you write an MCP client or gateway,** stop health-checking with `ping` and
count any reply as proof of life. The gateway in the third case fixed its own
bug in a day by doing exactly that [5]. Any probe that still counts `-32601` as a
failure will mark down the next working server that declines.

**If you operate a platform,** check your gateway's defaults before its feature
list, because the breaker you are counting on may ship disabled [15]. Alert on
JSON-RPC errors as well as HTTP status, since the third case lost half its tool
calls behind a clean HTTP error rate [5]. Set your own objective at the MCP
boundary and use the burn rates above, which come from Google's SRE Workbook for
a 99.9% objective [21].

**If you run an MCP server,** return `ttlMs: 0` on `server/discover` so no
intermediary can answer a probe in your place, and serve every method your
negotiated revision still requires. Slack's server negotiated a revision that
requires `ping` and refused it [1].

## What is still unsolved

The protocol has no shared answer to "is this server healthy." The specification
removed the old probe for a sound reason, the client best-practices page says
nothing about health checks [12], and the replacement probe is cacheable by
default. Until that page carries guidance, every client and gateway will keep
writing its own rule, and the September list will keep growing.

The limit of this article is that its evidence is five issue reports, most of
them filed by the people who found and fixed the bug. I know of no published
measurement of how many MCP deployments probe with `ping` today, and no
post-mortem of a production outage caused by one. The five cases show the
mechanism; they cannot tell you how often it is costing anyone traffic.

## What it adds up to

In each of the five cases the server was fine and the check was wrong. The
revision removed `ping`, production servers answer it with an error, and any
answer at all proves the server is alive. Treat it that way, make sure the probe
that replaced `ping` cannot be answered from a cache, and read your gateway's
defaults before you rely on its features.

---

*Part three of five on operating MCP at scale. Parts one and two cover upgrading
a fleet to the 2026-07-28 revision and security; parts four and five cover
performance and cost.*

## Sources

All URLs verified 2026-10-05; issue reports [1], [2], [3] and [5] re-read on 2026-10-06.

1. `edouard-claude/penelope` #276, Slack's production server held in "connecting", protocol 2025-06-18. https://github.com/edouard-claude/penelope/issues/276
2. `trycua/cua` #4001, a server killed and restarted on a cycle. https://github.com/trycua/cua/issues/4001
3. `stacklok/toolhive` #6497, GET probes excluding conformant backends. https://github.com/stacklok/toolhive/issues/6497
4. `agentic-community/mcp-gateway-registry` #1817, the skipped initialization and the unhealthy Salesforce server. https://github.com/agentic-community/mcp-gateway-registry/issues/1817
5. `MikkoParkkola/mcp-gateway` #567, the benchmark fixture, and PR #576, the fix merged 2026-09-19. https://github.com/MikkoParkkola/mcp-gateway/issues/567 and https://github.com/MikkoParkkola/mcp-gateway/pull/576
6. Ping, revision 2025-11-25, for the periodic-ping recommendation and connection reset. https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/ping
7. Changelog 2026-07-28, for the removal of `ping` and the list of cacheable results. https://modelcontextprotocol.io/specification/2026-07-28/changelog
8. Streamable HTTP, for the `404` carrying `-32601` on an unknown method. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
9. SEP-2575, Make MCP Stateless, for the rationale behind removing `ping`. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/seps/2575-stateless-mcp.md
10. `server/discover`, for the method and the example response carrying `ttlMs` and `cacheScope`. https://modelcontextprotocol.io/specification/2026-07-28/server/discover
11. Caching, for the cacheable-results list, the scope table and `ttlMs: 0`. https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
12. Client best practices, which carries no health check, timeout, retry or reconnection guidance. https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices
13. ContextForge retry manager, exponential backoff with jitter. https://github.com/IBM/mcp-context-forge/blob/main/mcpgateway/utils/retry_manager.py
14. ContextForge ADR-0009, built-in health checks and automatic reactivation. https://github.com/IBM/mcp-context-forge/blob/main/docs/docs/architecture/adr/009-built-in-health-checks.md
15. ContextForge circuit-breaker plugin, and the default plugin configuration that ships it disabled. https://github.com/IBM/mcp-context-forge/tree/main/plugins/circuit_breaker and https://github.com/IBM/mcp-context-forge/blob/main/plugins/config.yaml
16. MCP Registry working group charter, the 99.9% success criterion. https://modelcontextprotocol.io/community/working-groups/registry
17. MCP Registry terms of service, which disclaim any guarantee of availability. https://modelcontextprotocol.io/registry/terms-of-service
18. TrueFoundry service level agreement, naming MCP control surfaces. https://www.truefoundry.com/service-level-agreement
19. MintMCP status page, MCP Gateway component. https://status.mintmcp.com/
20. Azure API Management, overview of MCP servers. https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview
21. Google SRE Workbook, alerting on SLOs, Table 5-8. https://sre.google/workbook/alerting-on-slos/
