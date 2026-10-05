---
title: "The Protocol Moved Under You and Nobody Migrates You"
subtitle: "Operating MCP at scale, part one: operational excellence"
date: 2026-09-21
status: draft
series: "Operating MCP at Scale"
part: 1
sources_verified_on: 2026-09-21
---

# The Protocol Moved Under You and Nobody Migrates You

*Operating MCP at scale, part one: operational excellence.*

Microsoft's Learn team renamed one parameter on their MCP server, from `question`
to `query`. Between 2 and 5 percent of requests broke, and stayed broken until
they supported both names through a deprecation window.

They also named the cause, in a numbered lesson headed "Expect (and defend
against) hardcoded callers", and it is why this anecdote belongs at the top of an
article about a protocol revision:

> "Even with MCP dynamic tool discovery, some clients still hardcode tool schemas
> as if they were fixed APIs."

Their conclusion from that incident is the most useful sentence written about
operating this protocol so far:

> "Defensive evolution is part of operating a public service."

One parameter, on a first-party server, run by a team that knows what it is
doing. Nobody has published the equivalent number for a whole protocol revision.
What follows is the shape of that cost rather than its size, which is the honest
thing available.

## What 2026-07-28 removed

The current specification revision is the largest since MCP launched, and the
headline is subtraction:

- Protocol-level sessions, and the `Mcp-Session-Id` header
- The `initialize` handshake
- SSE resumability, and with it `Last-Event-ID`
- The standalone HTTP GET stream
- The ability for servers to send JSON-RPC requests at all

Server-initiated interaction was replaced by Multi Round-Trip Requests: a server
returns an `InputRequiredResult`, and the client retries the original request
carrying `inputResponses` under a new JSON-RPC id. Four primitives were
deprecated in the same release, with earliest removal in the first revision
released on or after 2027-07-28: Roots, Sampling, Logging, and OAuth Dynamic
Client Registration.

Three of those five were replaced in the same release, and saying so matters
because the article you are reading is about cost. `server/discover` is a new
mandatory RPC returning supported versions, capabilities and identity in one
call. `subscriptions/listen` carries server-to-client change notifications.
Multi Round-Trip Requests replaces server-initiated interaction. Two were not
replaced: SSE resumability, and per-connection session state.

Most of this is good. Removing protocol-level sessions is what makes an MCP
server an ordinary horizontally scalable HTTP workload, and the new required
routing headers let an intermediary route without parsing a body. The protocol
became easier to operate.

It also became a thing you had to migrate to, across every client and server you
run, at once, in a fleet you do not fully control.

## The migration guide is ten repositories deep

The documentation site does not carry one. Its index at
`modelcontextprotocol.io/llms.txt` is 354 lines and contains **zero** matches for
"migrat" or "upgrad", checked on 2026-09-21. What the site gives you is a
**Versioning and Compatibility** page, which specifies what the eras are and how
they negotiate. Moving a running estate between them is a different document, and
the site does not have it.

The guidance exists in the SDKs. The TypeScript SDK ships
`docs/migration/support-2026-07-28.md` covering exactly this move, plus an
automated codemod you invoke as `npx @modelcontextprotocol/codemod@latest
v1-to-v2 .`. Python ships `docs/migration.md` and `docs/protocol-versions.md`.
Java ships `MIGRATION-2.0.md`. C# ships `docs/versioning.md`. Ruby and PHP both
ship protocol-version documentation.

Others have filled the gap from outside. AWS published "MCP went stateless: is
your AWS MCP server deployment Well-Architected?" on 2026-09-01, reaching the
same pillar frame from the platform side, with a ten-question self-check and a
migration path. There is a community tool, `mcp-migrate`, carrying 21 rules with fixers for
19 of them. And at this very summit, Akash Sathish is presenting a session
billed, in his own words, as "the migration guide I had to write for myself",
with code diffs in both the TypeScript and Python SDKs.

So the honest claim is narrow, and it is still worth making. Ten SDK repositories
each tell you how to move that SDK. One cloud vendor tells you how to move on
their platform. One conference talk tells you what one auditor found. **No
project-published, operator-facing document tells you what order to move a fleet
in**, and order is the whole problem, because the compatibility matrix has two
cells that carry the operational risk:

**A modern client against a legacy server** fails, and the specification says so
in that word. What makes it dangerous is the third of the three shapes that
failure can take. The server "may reject the request with an
implementation-defined error, stay silent, or even process an era-ambiguous
method under legacy semantics". The first two page you. The third does not.

There is a mitigation and it is worth taking: on stdio the specification says
clients **SHOULD** send `server/discover` first, precisely so the failure becomes
deterministic rather than silent.

**A legacy client against a modern server** has no fall-forward mechanism at all.

The matrix does not dictate an order. Look at which rows fail and both contain a
single-era client; the dual-era client rows work against both kinds of server. So
what the matrix actually rules out is one move: **never take either population to
a single era while the other still contains the other era.** Whichever side you
control, make it dual-era first.

For most organizations that is the servers, because the clients are desktop
applications on laptops you do not administer. If you control the clients and not
the servers, the inverse is correct, and the matrix supports it just as well.

## The SDKs are behind, and that is not a criticism

There are **ten** official SDKs. Tier 1 is TypeScript, Python, C#, Go and Rust.
Tier 2 is Java and Ruby. Tier 3 is Swift, PHP and Kotlin.

Measured from the repositories themselves, all of Tier 1 ships `2026-07-28`:
TypeScript on its v2 line, Python at v2.2.0, C# at v2.2.0, Go at v1.8.0 where it
has been the default since v1.7.0, Rust at v3.4.0. Ruby and PHP ship it too,
which is worth saying because both are routinely left out of these lists.

One packaging detail catches teams out. TypeScript's v2 serves both eras from the
same factory by default, and `legacy: 'reject'` is what makes an endpoint
modern-only. But the old package name still resolves to the v1 line, so a team
that has not changed its `package.json` is on `2025-11-25` without having chosen
anything.

Three do not: **Java**, whose changelog release-line table tracks `2025-11-25`,
**Kotlin**, where `LATEST_PROTOCOL_VERSION` is still `2025-11-25` in `common.kt`,
and **Swift**.

Under the project's published tier obligations, **none of those is late**. Tier 2
has six months. Tier 3 carries no commitment at all. The lag is bounded and it is
legible, which is more than most ecosystems offer.

Do not read the tier as a predictor, though. PHP is Tier 3 and dual-era. Ruby is
Tier 2 and modern. Java is Tier 2 and is not. The tier sets the obligation, not
the outcome, so the only way to know where an SDK stands is to look.

It is still a planning input. If your estate has a Java client, your migration
window is not set by your own engineering capacity. It is set by someone else's
release schedule, and you should know that before you write the plan rather than
after.

## What breaks quietly

Loud failures are cheap. These are the ones that will not page you.

**Idempotency is now your problem, and what the specification offers does not
solve it.** The schema defines `ToolAnnotations.idempotentHint`, which says
whether repeating a call is harmless. It is a hint the same schema tells clients
not to trust from an untrusted server, and it deduplicates nothing, so it gives
you no way to make a retry safe when the answer is false. Resumability was
deleted. On Streamable HTTP, closing the response
stream **MUST** be treated by the server as cancellation, and the client **MUST**
re-issue with a new JSON-RPC id. So a retried tool call is a fresh call, and
whether that double-charges a customer is entirely a property of your
application. There is no `Idempotency-Key` convention in the changelog or the
best-practices documentation. Nothing warns you about this at upgrade time.

**Your monitoring may be reporting health while every call fails, and this one is
not new.** Tool execution errors have been returned as `isError: true` **inside
an HTTP 200** since the first revision, so a dashboard built on 5xx rates has
been blind to them for two years. That is correct protocol design, since a tool
failing is not a transport failure. The revision did not cause it. The revision
is simply when a lot of teams will rebuild their monitoring anyway, which makes
it the moment to fix it. Health checks have to inspect the body.

**The new required headers break 2025-era CORS configurations.** The allow-list
lives on the server, not the client. A browser-based client calling a 2025-era
server whose `Access-Control-Allow-Headers` predates `Mcp-Method` and `Mcp-Name`
is blocked at preflight, and the request is never sent. Two of the ten SDKs
document this. TypeScript ties it to the migration directly, and Python's ASGI
guide is arguably the better treatment, noting that "a header the preflight
doesn't grant is a request the browser never sends".

Two precision points while you are here. The specification lists three required
standard headers, not two: `MCP-Protocol-Version` as well, which is not new,
which is why the two new ones are the interesting part. And `Mcp-Name` is
conditional rather than universal, required on `tools/call`, `resources/read` and
`prompts/get`. The harder case is one further out: `Mcp-Param-*` headers
generated from `x-mcp-header` are dynamically named, and dynamically named
headers cannot be statically allow-listed for credentialed CORS at all.

**A new attack class arrives with the migration.** Stateless servers need
application-level state handles, and the project's security best practices are
explicit: "MCP servers **MUST NOT** treat possession of a state handle as
authentication." Where that sentence lives matters. The normative specification
says it "has no concept of a state handle", and that from the wire's perspective
a handle is an ordinary string. The guidance sits in the documentation, and the
tools page puts it plainly: "For authenticated servers, a handle is a name, not a
capability." An implementation that treats a returned handle as a capability has
built a bearer token by accident.

**And one admission worth reading between the lines.** The revision now says
servers **SHOULD** return `tools/list` in deterministic order. A specification
only needs to say that because implementations were shuffling, which was
invalidating clients' prompt caches. Your costs were being set by somebody else's
iteration order.

## Version skew is an operating condition, not an event

The instinct is to treat a protocol revision as a project with an end date. At
fleet scale it is not.

Clients update on their own schedules and some of them are desktop applications
on laptops you do not administer. Servers update when their maintainers choose,
and in one measurement study 193 of 464 confirmed servers, 41.6 percent, had
disappeared 72 hours later. Three of the ten SDKs are on the previous era by
design. The deprecated primitives have a removal date more than a year out, which
means you will be running code that uses them, knowingly, for a long time.

So the operational question is not "when is the migration finished". It is
**"what does my fleet do when it contains both eras at once, indefinitely"**, and
that is a design problem rather than a scheduling one.

One concrete trap from the migration window itself: the Python SDK's dual-era
server keeps legacy sessions in a plain in-process dictionary. There is no
distributed session store and no way to plug one in. So two workers means sticky
routing or a `404 Session not found`, during exactly the period when you are
carrying both eras.

There is one escape and it is worth knowing: `stateless_http=True` applies to the
legacy leg and buys free load balancing for legacy clients, at the cost of the
features that need session state. It is a trade rather than a fix, which is the
honest way to hold most things in a migration window.

## What operational excellence actually means here

Most of what is written about operating a service assumes the interface is yours
and changes when you change it. Neither is true here. The protocol is governed
elsewhere, the servers are largely other people's code, and the caller is
non-deterministic.

Four things follow, and none of them are generic advice:

1. **Instrument the body, not the status code.** Anything else reports health
   that is not there.
2. **Sequence the migration servers-first**, because the failure mode of the
   other order is silent rather than loud.
3. **Decide your idempotency convention yourself, and write it down**, because
   the specification will not do it for you and a retry is a new call.
4. **Design for permanent version skew**, because your fleet will contain both
   eras for longer than any migration plan will admit.

The protocol got better on 2026-07-28. The maintainers said in the release post
that there would be a migration cost, shipped four Tier 1 SDKs with migration
notes on the day, and set a twelve-month floor under every deprecation so the
exits can be scheduled. That is more than most protocols offer and it should be
said plainly.

What none of it answers is the estate-level question: in what order does an
organization move a fleet it does not fully control. That part is unwritten, and
it is the part that lands on operators.

That is not a complaint about the change. It is the beginning of the job.

---

*Part one of five on operating MCP at scale. Part two covers security and the
chain that ends with you. Parts three, four and five cover reliability,
performance and cost.*

*Every figure in this article is sourced below and was verified against the
primary source on 2026-09-22.*

## Sources

All URLs returned HTTP 200 on 2026-09-22.

**Specification, revision 2026-07-28**
1. Changelog. https://modelcontextprotocol.io/specification/2026-07-28/changelog
2. Versioning and Compatibility, including the matrix. https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
3. Deprecated features registry. https://modelcontextprotocol.io/specification/2026-07-28/deprecated
4. Streamable HTTP transport. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
5. Multi Round-Trip Requests. https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr
6. Tools, for `isError` and the stateful-tools guidance. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
7. Feature lifecycle and deprecation policy. https://modelcontextprotocol.io/community/feature-lifecycle

**Documentation and governance**
8. Documentation index, the 354-line file. https://modelcontextprotocol.io/llms.txt
9. Security Best Practices, source of the state-handle rule. https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
10. SDK tiering system. https://modelcontextprotocol.io/community/sdk-tiers
11. The authoritative list of ten SDKs and their tiers. https://modelcontextprotocol.io/docs/2026-07-28/sdk

**SDK evidence**
12. TypeScript SDK. https://github.com/modelcontextprotocol/typescript-sdk
13. TypeScript upgrade guide and codemod. https://ts.sdk.modelcontextprotocol.io/v2/migration/upgrade-to-v2
14. TypeScript legacy-client serving and the `legacy: 'reject'` opt-out. https://ts.sdk.modelcontextprotocol.io/v2/serving/legacy-clients
15. Python SDK legacy clients, the in-process dictionary. https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/legacy-clients.md
16. Python SDK CORS for browser clients. https://py.sdk.modelcontextprotocol.io/run/asgi/
17. Go SDK version-to-protocol table. https://github.com/modelcontextprotocol/go-sdk/blob/main/README.md
18. Java SDK changelog. https://github.com/modelcontextprotocol/java-sdk/blob/main/CHANGELOG.md
19. Kotlin SDK `LATEST_PROTOCOL_VERSION`. https://github.com/modelcontextprotocol/kotlin-sdk/blob/main/kotlin-sdk-core/src/commonMain/kotlin/io/modelcontextprotocol/kotlin/sdk/types/common.kt
20. Swift SDK. https://github.com/modelcontextprotocol/swift-sdk
21. Ruby SDK. https://github.com/modelcontextprotocol/ruby-sdk
22. PHP SDK. https://github.com/modelcontextprotocol/php-sdk

**External**
23. Anand Komandooru, Steven DeVries and Haleh Najafzadeh, "MCP went stateless: is your AWS MCP server deployment Well-Architected?", AWS Architecture Blog, 2026-09-01. https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
24. `mcp-migrate`, community migration tool. https://github.com/dheerajjha/mcp-migrate
25. Tianqi Zhang and colleagues, "How we built the Microsoft Learn MCP Server", Engineering@Microsoft, 2026-02-11. https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/
26. Nicolás Padilla, "Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale", arXiv:2608.00150. https://arxiv.org/abs/2608.00150
