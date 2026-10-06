---
title: "Nothing Pages You: Which Side Moves First When an MCP Fleet Upgrades to 2026-07-28"
subtitle: "Operating MCP at scale, part one: operational excellence"
date: 2026-09-21
revised: 2026-10-06
status: draft
prefix: "Research"
series: "Operating MCP at Scale"
part: 1
sources_verified_on: 2026-10-05
---

# Nothing Pages You: Which Side Moves First When an MCP Fleet Upgrades to 2026-07-28

*Operating MCP at scale, part one: operational excellence.*

On 2026-07-28 the Model Context Protocol deleted the `initialize` handshake,
protocol sessions and the server's ability to send requests to the client [1].
Every organization running MCP clients and servers now has to move a mixed fleet
across that line, and the failures that cost the most on the way across are the
ones that raise no alert. The order you move in decides how many of them you
meet, and the rule this article argues for fits in a sentence: make whichever
side you control speak both eras before anything moves to one.

Here is how it plays out at a company that gets the order wrong. The company is
invented. Every failure it runs into comes from the specification and the SDK
documentation.

## Who moves on whose schedule

Five parties share the fleet, and the platform team controls two of them.

| Party | What it controls | What it does not control |
|---|---|---|
| The platform team | The servers, the gateway, the dashboards | The desktop clients on employees' laptops |
| A desktop MCP client | When it updates, and which era it speaks | Which era the server it calls speaks |
| An internal browser-based client | The headers it sends | The server's CORS allow-list |
| A Java service another team owns | Which SDK version it runs | When the Java SDK ships the new revision |
| A billing server on the Python SDK, two workers behind a load balancer | Whether a repeated call writes twice | Whether a client repeats a call |

That table is the whole problem in miniature. The party with the dashboards owns
the least of the moving parts.

## Before the upgrade, the dashboard is quiet

Imagine a fleet where everything speaks `2025-11-25`. A client opens a connection with `initialize`,
receives an `Mcp-Session-Id`, and calls tools under that session. Agents look up
customers, open invoices and summarize tickets. The platform team's dashboard
tracks latency and the rate of 5xx responses, and it is quiet, because nothing is
wrong.

## After the upgrade, the dashboard is still quiet

Now the desktop client's vendor ships a release that speaks only the new era,
and the laptops pick it up overnight. The first request each one sends lands on a
server the platform team has not touched yet. The specification lists what a
legacy server may do with it: "reject the request with an implementation-defined
error, stay silent, or even process an era-ambiguous method under legacy
semantics" [2]. The first is a ticket. The other two are nothing at all. A
request processed under the old semantics returns a result, and the dashboard
counts it as a success.

Around the same time, the team that owns the browser client upgrades its SDK. The
revision adds required `Mcp-Method` and `Mcp-Name` headers beside the existing
`MCP-Protocol-Version`, and `Mcp-Name` is required on `tools/call`,
`resources/read` and `prompts/get` [3]. The server's CORS allow-list predates
both headers, so the browser refuses at preflight. Python's ASGI guide puts it
plainly: "a header the preflight doesn't grant is a request the browser never
sends" [4]. The server never sees the request, so its logs have nothing to show.

In the afternoon, a long-running invoice call loses its response stream partway
through. The revision removed SSE resumability, so on Streamable HTTP the server
MUST treat the closed stream as cancellation and the client MUST re-issue the
request with a new JSON-RPC id [3]. If the billing tool had already written the
invoice, it writes another one. The schema's `idempotentHint` would have told the
client whether a repeat was harmless, but the schema also tells clients not to
trust that hint from an untrusted server, and the hint deduplicates nothing [5].
Whether a retry charges a customer twice depends entirely on how the tool was
written.

Later still, the billing tool starts failing on a downstream timeout. It reports
each failure as `isError: true` inside a successful HTTP response, which tools
have done since the first revision of the protocol [6]. That is correct design,
because a tool failing is not a transport failure. It also means a dashboard
built on 5xx rates has never seen a tool error, and it does not see these.

The one loud failure of the day lands on the Java team. The Java SDK still
tracks `2025-11-25` [7], so their service keeps opening legacy sessions. The
Python SDK's dual-era server keeps those sessions in "a plain in-process `dict`",
and its documentation says "There is no distributed session store and no way to
plug one in" [8]. Whenever the load balancer sends the Java client's next request
to the other worker, it gets `404 Session not found` [8]. The Java team files a
bug against the billing service, which is the wrong service.

By the end of Tuesday, customers have duplicate invoices, a browser tool has
stopped working without a single server-side error, and a fleet of laptops is
getting answers under semantics their client no longer speaks. The dashboard is
green.

## The breakage pattern is real

That company is invented. The way it broke is documented. Microsoft's Learn team
renamed one parameter on their MCP server, from `question` to `query`, and
between 2 and 5 percent of requests broke until they accepted both names through
a deprecation window [9]. Their lesson is headed "Expect (and defend against)
hardcoded callers", and the sentence under it explains why a protocol revision is
riskier than it looks: "Even with MCP dynamic tool discovery, some clients still
hardcode tool schemas as if they were fixed APIs." [9]

One renamed parameter did that. The 2026-07-28 revision removes five things a
running client or server may depend on, and replaces three of them [1]:

| Removed in 2026-07-28 | Replaced by |
|---|---|
| Protocol-level sessions and the `Mcp-Session-Id` header | Nothing; per-connection session state is gone |
| The `initialize` handshake | `server/discover`, a mandatory call returning supported versions, capabilities and identity |
| SSE resumability and `Last-Event-ID` | Nothing |
| The standalone HTTP GET stream | `subscriptions/listen`, for server-to-client change notifications |
| Server-sent JSON-RPC requests | Multi Round-Trip Requests: the server returns `InputRequiredResult` and the client retries with `inputResponses` under a new JSON-RPC id [10] |

Most of this makes MCP easier to run. Without protocol sessions, an MCP server is
an ordinary horizontally scalable HTTP workload, and the new routing headers let
a load balancer or gateway route a request without parsing its body. The cost is
that every client and server in your estate has to cross the line, and you do not
control all of them.

## Two cells of the matrix fail, and both hold a single-era client

The Versioning and Compatibility page defines the two protocol eras and how they
negotiate, and its compatibility matrix has exactly two failing cells [2]:

| Client | Server | Specification's verdict | How it fails |
|---|---|---|---|
| Modern only | Legacy only | Fails | The server "may reject the request with an implementation-defined error, stay silent, or even process an era-ambiguous method under legacy semantics" |
| Legacy only | Modern only | Fails | There is no fall-forward mechanism |

Every row where one side speaks both eras works. The invented company's desktop
clients went modern-only while legacy servers were still running, which put them
in the first row. That gives one rule for the whole migration: never move either
population to a single era while the other population still contains the other
era. Make the side you control dual-era first, then move the rest.

For most organizations that side is the servers, because the clients are desktop
applications on machines platform engineering does not manage. If you control the
clients and not the servers, reverse the order; the matrix supports both. On
stdio, the specification says clients SHOULD send `server/discover` first, which
turns the silent outcome in the first row into a deterministic failure [2], so
turn it on wherever you can.

In TypeScript, a packaging detail decides what dual-era means. The v2 server
entry points serve both eras from the same factory by default, and `legacy:
'reject'` makes an endpoint modern-only [11]. A hand-constructed v2 client or
server still speaks the 2025 protocol until you opt in, and the old package name
still resolves to the v1 line [12]. A team that has not edited its
`package.json` is on `2025-11-25` without having chosen to be.

## Three SDKs set part of your schedule

There are ten official SDKs [13]. On 2026-10-05, all six Tier 1 SDKs shipped
2026-07-28 [14][15][16], and so did PHP, a Tier 3 SDK [17]. Three had not. Java,
the only Tier 2 SDK, tracks `2025-11-25` in its changelog [7]. Kotlin's
`LATEST_PROTOCOL_VERSION` is still `2025-11-25` [18]. Swift has not shipped the
revision [19]. Under the project's tier rules none of them is late: Tier 2 has
six months to reach a new revision, and Tier 3 carries no commitment [20].

That makes the lag a planning input. The Java service in the story is the reason
the billing servers cannot drop legacy support, and the date it can move belongs
to another project's release schedule. The tier does not predict support either:
PHP is Tier 3 and ships the new era, while Java is Tier 2 and does not. Check
each SDK you actually run.

## Each SDK explains how to move itself, and nobody explains how to move a fleet

The project's documentation index, `llms.txt`, ran to 356 lines on 2026-10-05
with zero matches for "migrat" or "upgrad" [21]. The SDKs filled part of the gap.
TypeScript ships a guide to supporting 2026-07-28 [12]. AWS published a
Well-Architected review of the revision on 2026-09-01, with a ten-question
self-check and a migration path for its own platform [22]. A community tool,
`mcp-migrate`, carries 21 rules with automatic fixes for 19 of them [23]. At MCP
Dev Summit Toronto this week, Akash Sathish is presenting what he calls "the
migration guide I had to write for myself" [24].

Each of these explains how to move one SDK, one platform or one team's servers.
None of them, as of 2026-10-05, is a project-published document that tells an
operator what order to move a whole fleet in, and order is what decided the
invented company's Tuesday. The maintainers did not hide the cost. The release
post said there would be migration cost, four SDKs shipped with migration notes on
the day, and the project adopted a deprecation policy with a twelve-month minimum
window [25]. What is left over is the estate-level plan, and every organization
writes its own.

## What to do, depending on who you are

**If you run the platform:** inventory every client and server by protocol era
and SDK, including any Java, Kotlin or Swift ones, and watch those SDKs'
releases from the first day of the plan. Make the side you control dual-era
before moving anything to a single era. Have clients send `server/discover` first
wherever they run over stdio. Add a response-body check for `isError: true` to
health checks and alerts; teams rebuild monitoring during a migration anyway, and
this is the check the invented company's dashboard was missing.

**If you write MCP servers:** define an idempotency rule for every tool that
changes state, and do not leave it to `idempotentHint`. AWS's self-check asks the
right question: "Are your tools idempotent so clients can safely re-issue any
broken call?" [22] Add `Mcp-Method` and `Mcp-Name` to the CORS allow-list before
any browser client upgrades. The allow-list lives on the server, so the fix goes
there:

```http
Access-Control-Allow-Headers: Content-Type, Authorization, MCP-Protocol-Version, Mcp-Method, Mcp-Name
```

If you run more than one worker on the Python SDK, pick a side for the legacy
leg before the window opens: sticky routing, or `stateless_http=True`, which
removes the need for sticky routing and drops the features that depend on
session state [8].

**If you own security:** stateless servers carry state in application-level
handles, and the project's security best practices say servers "MUST NOT treat
possession of a state handle as authentication" [26]. Key stored state as
`<user_id>:<handle>`, with the user ID taken from the verified token [26]. An
authenticated server that looks state up by handle alone has issued a credential
to anyone who sees the handle. Track the deprecated features, Roots, Sampling,
Logging and OAuth Dynamic Client Registration, as inventory: none of them can be
removed before the first revision released on or after 2027-07-28 [27].

## What is still unsolved

The move does not end. Clients update on their own schedules. Public servers come
and go: in one measurement study of internet-facing servers, 193 of 464 confirmed
servers, 41.6 percent, had disappeared 72 hours later [28]. Three of the ten SDKs
have not shipped the revision, and the deprecated features will be in your fleet,
on purpose, until at least the first revision released on or after 2027-07-28
[27]. The planning question is what your systems do when both eras are present
with no end date.

Some of that has no answer yet. Neither the changelog nor the best-practices
documentation defines an idempotency key, so every server invents its own. The
dynamically named `Mcp-Param-*` headers cannot be allow-listed for a browser at
all, and the TypeScript SDK has browser clients skip mirroring them for that
reason [12]. And there is still no project-published order for moving a fleet
that no single team controls.

The limit of this article is that the Tuesday above is constructed. Each failure
in it is taken from the specification or an SDK's documentation, and the only
production breakage cited is Microsoft's renamed parameter. Until an organization
publishes an account of moving a real fleet across this revision, the matrix is
the best evidence anyone has for which side should move first.

## What it adds up to

The 2026-07-28 revision made MCP easier to run at scale, and the price of
crossing to it is paid in failures that look like successes: a legacy server that
answers a modern request under the old rules, a browser that never sends the
request, a retry that runs a tool twice. None of them pages anyone. The order you
move in is the control you have. Make whichever side you control speak both eras
before anything moves to one, measure tool results instead of status codes, and
write down your idempotency rule before the first broken stream forces a retry.

---

*Part one of five on operating MCP at scale. Part two covers security, part three
reliability, part four performance and part five cost.*

## Sources

All sources were read between 2026-10-05 and 2026-10-06.

1. MCP specification 2026-07-28, changelog. https://modelcontextprotocol.io/specification/2026-07-28/changelog
2. MCP specification 2026-07-28, Versioning and Compatibility, including the compatibility matrix. https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
3. MCP specification 2026-07-28, Streamable HTTP transport. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
4. Python SDK, CORS for browser clients. https://py.sdk.modelcontextprotocol.io/run/asgi/
5. MCP schema 2026-07-28, `ToolAnnotations.idempotentHint`. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.ts
6. MCP specification 2026-07-28, Tools, for `isError`. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
7. Java SDK changelog. https://github.com/modelcontextprotocol/java-sdk/blob/main/CHANGELOG.md
8. Python SDK, legacy clients and the in-process dictionary. https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/legacy-clients.md
9. Tianqi Zhang and colleagues, "How we built the Microsoft Learn MCP Server", Engineering@Microsoft, 2026-02-11. https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/
10. MCP specification 2026-07-28, Multi Round-Trip Requests. https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr
11. TypeScript SDK, serving legacy clients and the `legacy: 'reject'` opt-out. https://ts.sdk.modelcontextprotocol.io/v2/serving/legacy-clients
12. TypeScript SDK, guide to supporting 2026-07-28, including the opt-in and the CORS notes. https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/migration/support-2026-07-28.md
13. MCP SDK list and tiers. https://modelcontextprotocol.io/docs/2026-07-28/sdk
14. Go SDK README, version-to-protocol table. https://github.com/modelcontextprotocol/go-sdk/blob/main/README.md
15. TypeScript SDK. https://github.com/modelcontextprotocol/typescript-sdk
16. Ruby SDK. https://github.com/modelcontextprotocol/ruby-sdk
17. PHP SDK. https://github.com/modelcontextprotocol/php-sdk
18. Kotlin SDK, `LATEST_PROTOCOL_VERSION`. https://github.com/modelcontextprotocol/kotlin-sdk/blob/main/kotlin-sdk-core/src/commonMain/kotlin/io/modelcontextprotocol/kotlin/sdk/types/common.kt
19. Swift SDK. https://github.com/modelcontextprotocol/swift-sdk
20. MCP SDK tiering system. https://modelcontextprotocol.io/community/sdk-tiers
21. MCP documentation index, `llms.txt`, read 2026-10-05. https://modelcontextprotocol.io/llms.txt
22. Anand Komandooru, Steven DeVries and Haleh Najafzadeh, "MCP went stateless: is your AWS MCP server deployment Well-Architected?", AWS Architecture Blog, 2026-09-01. https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
23. `mcp-migrate`, community migration tool. https://github.com/dheerajjha/mcp-migrate
24. Akash Sathish, "Sessions Are Dead. Now What Breaks?", MCP Dev Summit Toronto, session listing. https://events.linuxfoundation.org/mcp-dev-summit-toronto/program/schedule/?id=1287461
25. David Soria Parra and Den Delimarsky, release announcement for 2026-07-28. https://blog.modelcontextprotocol.io/posts/2026-07-28/
26. MCP Security Best Practices, source of the state-handle rule. https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
27. MCP specification 2026-07-28, deprecated features registry. https://modelcontextprotocol.io/specification/2026-07-28/deprecated
28. Nicolás Padilla, "Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale", arXiv:2608.00150, preprint. https://arxiv.org/abs/2608.00150
