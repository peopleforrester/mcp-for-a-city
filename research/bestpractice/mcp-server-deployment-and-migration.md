---
title: "Deploying and Operating MCP Servers: the 2026-07-28 Migration and What Best Practice Actually Says"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
audience: "Agentic AI Foundation and MCP maintainers, MCP Dev Summit Toronto 2026-10-06"
---

<!-- ABOUTME: Verified architectural guidance for deploying and operating MCP servers at scale, covering the 2026-07-28 breaking changes, migration, and official best practice. -->
<!-- ABOUTME: Every claim carries a source URL and a verification date; unverified items are marked UNVERIFIED inline. -->

# Deploying and Operating MCP Servers

Research for "Governing MCP for a Workforce the Size of a City", MCP Dev Summit
Toronto, 2026-10-06. Companion to `research/spec/`, `research/ops/`,
`research/scale/` and `research/security/` in this repo.

## How to read the sourcing

| Label | Meaning |
|---|---|
| **[SPEC]** | The normative specification text at modelcontextprotocol.io, quoted verbatim |
| **[OFFICIAL]** | Non-normative official documentation, an official SDK repo, or the MCP blog |
| **[MEASURED]** | Measured by this research on 2026-09-18, with the command or endpoint shown |
| **[VENDOR]** | A vendor's own recommendation about its own product |
| **[PRACTITIONER]** | First-hand operator experience, not normative |
| **[UNVERIFIED]** | Could not be traced to a source that makes the claim |

Elisions inside quoted blocks are marked `[...]`; nothing else inside a quote is
altered, including the source's own punctuation.

Nothing below is stated from memory. Where a verbatim quote exists it is quoted
rather than paraphrased, because this deck is delivered to the people who wrote
the text.

---

## 0. The two blocking answers

### 0.1 `Mcp-Method` and `Mcp-Name`: verified verbatim

**[SPEC]** Source:
https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
section "Request Metadata" then "Standard Request Headers" (verified 2026-09-18).

The table, reproduced exactly:

> | Header Name  | Source Field                  | Required For                                           |
> | ------------ | ----------------------------- | ------------------------------------------------------ |
> | `Mcp-Method` | `method`                      | All requests                                           |
> | `Mcp-Name`   | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` requests |
>
> These headers are **REQUIRED** for compliance.

The rationale sentence, from the same page, "Request Metadata" preamble:

> The Streamable HTTP transport mirrors selected JSON-RPC body fields into HTTP
> headers so that intermediaries (load balancers, gateways, observability
> tooling) can route and inspect requests without parsing the body.

The client obligation, from "Client Behavior" on the same page:

> When constructing a `tools/call` request via HTTP transport, the client
> **MUST**:
>
> 1. Extract the values for any standard headers from the request body (e.g.,
>    `method`, `params.name`, `params.uri`).
> 2. Append the `Mcp-Method` header and, if applicable, `Mcp-Name` header to
>    the request.

The enforcement, from "Server Validation" on the same page:

> Servers that process the request body **MUST** reject requests where the
> values specified in the headers do not match the corresponding values in the
> request body. This prevents potential security vulnerabilities when
> different components in the network rely on different sources of truth
> (e.g., a load balancer routing on the header value while the MCP server
> executes based on the body value).

> When rejecting a request due to header validation failure, servers **MUST**
> return HTTP status `400 Bad Request` and **MUST** include a JSON-RPC error
> response using the following error code:
>
> | Code     | Name             | Description                                                                                                            |
> | -------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------- |
> | `-32020` | `HeaderMismatch` | The HTTP headers do not match the corresponding values in the request body, or required headers are missing/malformed. |

And the explicit list of what counts as a failure, verbatim:

> Validation failure conditions include:
>
> * A required standard header (`MCP-Protocol-Version`, `Mcp-Method`,
>   `Mcp-Name`) is missing.
> * A header value does not match the corresponding request body value. [...]
> * A header value contains invalid characters.

Three further details that matter for a gateway deployment and are easy to miss:

1. **Base64 sentinel encoding.** A tool name or resource URI that is not plain
   ASCII is carried as `Mcp-Name: =?base64?{Base64EncodedValue}?=`. Verbatim:
   "The prefix `=?base64?` and suffix `?=` indicate that the value is
   Base64-encoded. These markers are case-sensitive and **MUST** appear exactly
   as shown (lowercase). Servers and intermediaries that need to inspect these
   values **MUST** decode them accordingly."
2. **Intermediaries must check the version before trusting the header.**
   Verbatim: "Intermediaries that enforce policy based on mirrored headers (e.g.,
   routing or rate-limiting by tenant) **SHOULD** verify that the
   `MCP-Protocol-Version` header indicates a version that requires header-body
   validation. If the version is older or the header is absent, the intermediary
   **SHOULD** reject the request rather than trusting unvalidated header values."
   This is the sentence that stops a gateway from being fooled by a legacy-shaped
   request carrying forged routing headers.
3. **Header requirements are undefined for notification POSTs.** Verbatim:
   "header requirements for notification POSTs are not defined by this revision."

`MCP-Protocol-Version` is separately required on every POST:

> Every POST request to the MCP endpoint **MUST** include an
> `MCP-Protocol-Version` header.

> The header value **MUST** match the
> `io.modelcontextprotocol/protocolVersion` field carried in the request body's
> `_meta`. If the values do not match, the server **MUST** reject the request
> with `400 Bad Request` and a `HeaderMismatch` JSON-RPC error

SEP of record for the header standardisation: SEP-2243,
https://modelcontextprotocol.io/seps/2243-http-standardization.

### 0.2 SDK support status, measured 2026-09-18

**[MEASURED]** Release tags and dates from
`gh api repos/modelcontextprotocol/<sdk>/releases`, run 2026-09-18. Protocol
support read from each repo's own documentation or source constant on the same
date, path given per row.

| SDK | Tier | Latest release (2026-09-18) | Released | Speaks `2026-07-28`? | Evidence |
|---|---|---|---|---|---|
| TypeScript | 1 | `@modelcontextprotocol/server@2.0.0` (core `1.30.0`) | 2026-07-27 | Yes, **opt-in only** | `docs/migration/support-2026-07-28.md` |
| Python | 1 | `v2.2.0` | 2026-09-07 | Yes, **default** | `docs/protocol-versions.md`, v2.2.0 release notes |
| C# | 1 | `v2.2.0` | 2026-08-13 | Yes | `docs/versioning.md` |
| Go | 1 | `v1.8.0` | 2026-09-14 | Yes, since `v1.7.0` | `README.md` support matrix |
| Rust | 1 | `rmcp-v3.4.0` | 2026-09-15 | Yes | `README.md` |
| Java | 2 | `v2.0.1` | 2026-08-19 | **No** | `CHANGELOG.md` release-line table |
| Ruby | 2 | `v1.5.1` | 2026-09-09 | Yes | `CHANGELOG.md` 1.4.0, `subscriptions/listen` |
| PHP | 3 | `v0.8.1` | 2026-08-29 | Partial, alpha-scored | `README.md` conformance badges |
| Kotlin | 3 | `0.15.0` | 2026-07-28 | **No** | source constant, below |
| Swift | 3 | `0.12.1` | 2026-05-07 | **No** | `README.md` |

Tier assignments are **[OFFICIAL]** from
https://modelcontextprotocol.io/docs/2026-07-28/sdk (verified 2026-09-18).

**The two hard negatives, with their evidence.**

Java, **[OFFICIAL]** from
https://raw.githubusercontent.com/modelcontextprotocol/java-sdk/main/CHANGELOG.md
(verified 2026-09-18), verbatim:

> | Line   | Latest | Spec revision | Status |
> |--------|--------|---------------|--------|
> | 2.0.x  | 2.0.1 (2026-08-19) | 2025-11-25 | Active development |
> | 1.1.x  | 1.1.4 (2026-08-19) | 2025-06-18 | Security patches only |
> | 0.18.x | 0.18.4 (2026-08-19) | 2025-06-18 | Security patches only |

Kotlin, **[MEASURED]** from
`kotlin-sdk-core/src/commonMain/kotlin/io/modelcontextprotocol/kotlin/sdk/types/common.kt`
on `main` (verified 2026-09-18), verbatim:

```kotlin
/** The latest supported MCP protocol version string. */
public const val LATEST_PROTOCOL_VERSION: String = "2025-11-25"

/** All MCP protocol versions supported by this SDK. */
public val SUPPORTED_PROTOCOL_VERSIONS: List<String> = listOf(
    LATEST_PROTOCOL_VERSION,
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
```

Swift, **[OFFICIAL]** from the repo README (verified 2026-09-18), line 10:
the SDK is described as implementing the `2025-11-25` specification, which the
README labels "(latest)". Last release `0.12.1`, 2026-05-07, which is over four
months before this check and predates the current revision.

**The stated obligation, so the lag can be judged against it.** **[OFFICIAL]**
https://modelcontextprotocol.io/community/sdk-tiers (verified 2026-09-18),
verbatim from the tier requirements table, row "New Protocol Features":

> Tier 1: Before new spec version release, timeline agreed per release based on feature complexity
> Tier 2: Within 6 months
> Tier 3: No timeline commitment

So Java at Tier 2 has until roughly 2027-01-28 and is not late. Kotlin and Swift
at Tier 3 have no commitment at all. **All five Tier 1 SDKs met their
obligation.** The honest headline is not "the SDKs are behind"; it is that the
tiering system makes the lag legible and bounded, and that an organisation
standardised on Java, Kotlin or Swift cannot adopt `2026-07-28` today through an
official SDK.

**The conformance suite is itself split.** **[MEASURED]** npm registry for
`@modelcontextprotocol/conformance`, 2026-09-18: `dist-tags` are
`latest: 0.1.16` and `alpha: 0.2.0-alpha.11` (published 2026-08-07). The `latest`
tag, `0.1.16`, was released 2026-03-27, four months before the current revision.
The PHP SDK README states this directly: "The `2026-07-28` scores run against the
framework's `alpha` releases, so they move as [they change]". So conformance
against the current revision is, as of 2026-09-18, an alpha artefact.

---

## 1. The breaking change inventory

Every row verified against the specification on 2026-09-18. "Quote" is the
normative or changelog text; "Source" is the page that carries it. The changelog
is https://modelcontextprotocol.io/specification/2026-07-28/changelog; where a
normative page states the same thing more strongly, the normative page is cited.

| # | Change | What breaks | Verbatim | Source |
|---|---|---|---|---|
| B1 | **Protocol is stateless** | Any server inferring context from the connection | "The Model Context Protocol (MCP) is a **stateless protocol**: all the information needed to process a request is contained in the request itself. A server processes each request independently; no state should be inferred from previous requests, even those on the same connection or stream." | `/specification/2026-07-28/basic/index` |
| B2 | **`initialize` handshake removed** | Every client and server opening a session | "Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request now carries its protocol version and client capabilities in `_meta`" (SEP-2575) | changelog, major change 2 |
| B3 | **`Mcp-Session-Id` removed** | Sticky routing, session stores, per-connection tool lists | "Remove protocol-level sessions and the `Mcp-Session-Id` header from the Streamable HTTP transport. List endpoints (`tools/list`, `resources/list`, `prompts/list`) no longer vary per-connection. Servers that need cross-call state use explicit, server-minted handles passed as ordinary tool arguments (SEP-2567)." | changelog, major change 1 |
| B4 | **SSE resumability removed** | Redelivery, `Last-Event-ID`, at-most-once semantics | "Resumable SSE streams via `Last-Event-ID` are not supported." and "A broken response stream loses the in-flight request; clients **MUST** re-issue it as a new request with a new request ID (SEP-2575)." | streamable-http page; changelog major change 9 |
| B5 | **HTTP GET stream removed** | Any client opening a standalone notification stream | "Removal of the GET stream endpoint." Replaced by `subscriptions/listen`: "Replace the HTTP GET endpoint and `resources/subscribe`/`resources/unsubscribe` with `subscriptions/listen`: a single long-lived POST-response stream" | streamable-http page; changelog major change 4 |
| B6 | **Servers cannot send JSON-RPC requests** | Sampling, elicitation and roots callbacks | "The server **MUST NOT** send independent JSON-RPC *requests* on this stream. [...] This is a change from Streamable HTTP in protocol versions `2025-03-26` through `2025-11-25`, where servers could send such requests on SSE streams." | streamable-http page |
| B7 | **MRTR replaces server-initiated interaction** | The whole callback programming model | "Multi Round-Trip Requests (MRTR) pattern introduced which replaces the previous approach of sending server-initiated requests, such as `roots/list`, `sampling/createMessage`, or `elicitation/create`. Servers return an `InputRequiredResult` (`resultType: \"input_required\"`) [...] Clients respond with `inputResponses` on a retry of the original request (SEP-2322)." | changelog, major change 7 |
| B8 | **`resultType` required on all results** | Clients parsing results from mixed-version fleets | "All results now carry a required `resultType` field: `\"complete\"` for ordinary results and `\"input_required\"` [...] Clients **MUST** treat results from earlier-protocol servers that omit the field as `\"complete\"`." | changelog, major change 8 |
| B9 | **`Mcp-Method` and `Mcp-Name` required** | Every hand-rolled HTTP client and every proxy | "These headers are **REQUIRED** for compliance." Full text in Section 0.1. | streamable-http page |
| B10 | **`server/discover` mandatory for servers** | Any server that does not implement it | "`server/discover` lets a client query a server's supported protocol versions, capabilities, and identity before sending any other requests. Servers **MUST** implement it." Calling it is optional: "Calling `server/discover` is optional for clients" | `/specification/2026-07-28/server/discover` |
| B11 | **Tasks moved to an extension** | Anyone on experimental core tasks from `2025-11-25` | "Move experimental tasks out of the core protocol and into an official extension (`io.modelcontextprotocol/tasks`). The redesigned extension replaces the blocking `tasks/result` method with polling via `tasks/get` and a new `tasks/update` for client-to-server input, removes `tasks/list`, and allows servers to return task handles unsolicited (SEP-2663)." | changelog, major change 6 |
| B12 | **`ping`, `logging/setLevel`, `notifications/roots/list_changed` removed** | Liveness checks built on `ping`; runtime log-level control | "Remove `ping`, `logging/setLevel`, and `notifications/roots/list_changed`. Log level is now set per-request via `io.modelcontextprotocol/logLevel` in `_meta`." | changelog, major change 5 |
| B13 | **`ttlMs` and `cacheScope` required on list and read results** | Any server returning those results without the fields | "Require `ttlMs` and `cacheScope` fields on results returned by `tools/list`, `prompts/list`, `resources/list`, `resources/read`, and `resources/templates/list` via a new `CacheableResult` interface." | changelog, minor change |
| B14 | **Resource-not-found error code changed** | Clients matching on `-32002` | "Change resource not found error code from `-32002` to `-32602` (Invalid Params)." | changelog, minor change |

Two corrections to common framings of this list, both worth making from the stage
because they are the kind of thing a maintainer will correct you on:

- **B10 is asymmetric.** Servers MUST implement `server/discover`; clients MAY
  call it. A talk that says "discovery is now mandatory" is half right in a way
  that reverses the burden.
- **B3 does not remove per-caller variation in tool lists.** The tools page is
  explicit: the set "**MUST NOT** vary per-connection or as a side effect of
  other requests on the connection. The set **MAY** vary by the authorization
  presented on the request [...] since credentials are per-request input, not
  connection state."
  (https://modelcontextprotocol.io/specification/2026-07-28/server/tools). A
  multi-tenant server can still scope tools per tenant. It just has to do it off
  the token, not off the connection.

---

## 2. Migration: what official guidance exists, and what does not

### 2.1 There is no migration guide on modelcontextprotocol.io

**[MEASURED]** The site's own documentation index,
https://modelcontextprotocol.io/llms.txt (354 lines, fetched 2026-09-18),
contains **zero** entries matching "migrat" or "upgrad". There is no
`/docs/migration` page, no upgrade guide, and no compatibility shim published by
the project.

What exists instead, in descending order of authority:

1. **[SPEC]** The versioning page's backward-compatibility section and
   compatibility matrix,
   https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning.
   This is a specification of interoperability, not a migration procedure.
2. **[SPEC]** Per-transport backward-compatibility sections on the stdio and
   Streamable HTTP pages.
3. **[OFFICIAL]** The release blog post,
   https://blog.modelcontextprotocol.io/posts/2026-07-28/.
4. **[OFFICIAL]** Per-SDK migration documentation, which is where the actual
   procedural guidance lives. See 2.3.

**The gap to name from the stage:** an organisation with a fleet of servers is
handed a compatibility matrix and told to read nine SDK repositories. The
deprecation policy gives them a schedule (Section 5); nothing gives them a
method. That is a concrete, fixable, non-hostile ask to put to the room.

### 2.2 The era model and the compatibility matrix

**[SPEC]** https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
(verified 2026-09-18). The terminology, verbatim:

> * **Modern**: protocol versions that convey version, identity, and
>   capabilities as per-request metadata (revision `2026-07-28` and later).
> * **Legacy**: protocol versions that establish a session with an
>   `initialize` handshake (`2025-11-25` and earlier).
> * **Dual-era**: an implementation that supports both modern and legacy
>   versions.

The negotiation model, verbatim:

> There is no negotiation handshake. Every request carries its protocol
> version, and the server accepts or rejects each request independently

> If the server does not implement the requested version (whether the version
> is unknown to the server, or is a known version the server has chosen not to
> support), it **MUST** respond with an `UnsupportedProtocolVersionError`
> listing the versions it does support

The error carries `-32022` with a `data.supported` array and a `data.requested`
value. Verbatim: "The client **SHOULD** select a mutually supported version from
the `supported` list and retry the request, or surface an error to the user if
no compatible version exists."

Backward compatibility, verbatim:

> A server that wishes to support both legacy clients (which expect an
> `initialize` handshake) and modern clients (which use per-request metadata)
> **MAY** implement both behaviors.

Note the **MAY**. Dual-era operation is permitted, not required, and not
specified beyond detection.

**The compatibility matrix, reproduced verbatim.** This is the single most
useful artefact for planning a mixed fleet and belongs on a slide:

| Client | Server | Outcome |
|---|---|---|
| Modern | Modern | Works. `server/discover` is optional; version mismatches surface as `UnsupportedProtocolVersionError` and the client retries with a mutually supported version. |
| Modern | Legacy | **Fails.** "The server may reject the request with an implementation-defined error, stay silent, or even process an era-ambiguous method under legacy semantics." |
| Dual-era | Modern | Works. |
| Dual-era | Legacy | Works. |
| Legacy | Modern | **Fails.** "Legacy clients have no fall-forward mechanism." |
| Legacy | Dual-era | Works. |
| Legacy | Legacy | Works according to the legacy revision. |

Two rows carry the whole migration risk. **Modern client to legacy server can
silently succeed in the wrong semantics**, per the spec's own words, "or even
process an era-ambiguous method under legacy semantics". And **legacy client to
modern server has no recovery path at all**: there is no fall-forward.

The consequence for sequencing is direct and is the practical recommendation
this section supports: **upgrade servers to dual-era first, clients second.**
Every other order passes through a failing cell.

The spec also asks a modern-only server to help the clients it cannot serve:

> A server that supports only modern versions **SHOULD** name the protocol
> versions it supports in any error it returns to an `initialize` request, on any
> transport: legacy clients have no fall-forward mechanism, and this message may
> be the only diagnostic they can surface to users.

And it asks clients to cache the determination:

> The era determination is a property of the server, not of an individual
> request. Clients **SHOULD** cache the result for the lifetime of the server
> process (stdio) or origin (HTTP), and **MAY** persist it across restarts of
> the same server configuration, re-probing if the cached assumption later
> fails.

### 2.3 Detection mechanics, per transport

**[SPEC]** Streamable HTTP, verbatim:

> A client that supports both modern (per-request-metadata) MCP versions and a
> legacy version that requires an `initialize` handshake **MAY** detect which
> era the server implements by attempting a modern request first. On
> `400 Bad Request`, the client **SHOULD** inspect the response body before
> falling back: modern servers also use `400` for
> `UnsupportedProtocolVersionError`, `MissingRequiredClientCapabilityError`, and
> header-validation failures.

> * If the body contains a recognized modern JSON-RPC error, the server speaks
>   a modern version of MCP [...]
> * If the body is empty or is not a recognized modern JSON-RPC error, fall
>   back to `initialize`

On stdio the probe is `server/discover`, per
https://modelcontextprotocol.io/specification/2026-07-28/server/discover:

> **stdio backward-compatibility probe.** On stdio, there is no per-request
> HTTP status code to drive fallback. A client that supports both modern
> (per-request `_meta`) and legacy (`initialize` handshake) servers **SHOULD**
> send `server/discover` first

And how a modern server should answer legacy traffic, verbatim from the
Streamable HTTP page:

> * HTTP GET or DELETE to the MCP endpoint: respond with `405 Method Not Allowed`.
> * An `Mcp-Session-Id` header on a request: ignore it, and do not mint or echo session IDs.
> * A `Last-Event-ID` header: ignore it; streams are not resumable.

Note "ignore it" for `Mcp-Session-Id`. A legacy client sending a session ID gets
no error, no warning, and stateless behaviour. That is B3's silent failure mode
written into the specification.

### 2.4 The compatibility shims that do exist, at SDK level

There is no project-level shim. There are three good SDK-level ones, and they
differ in a way that will bite anyone who assumes they are the same.

**Python** **[OFFICIAL]**,
`https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/docs/protocol-versions.md`
and `docs/run/legacy-clients.md` (verified 2026-09-18).

Client side, four modes: `mode="auto"` (probe with `server/discover`, fall back
to `initialize`), `mode="legacy"` (never probe), a version pin, and
`prior_discover=` to skip the probe on reconnect. Verbatim on the default:

> You didn't pass `mode`, so you got the default: `"auto"`.

Server side, verbatim, and this is the strongest dual-era story of any SDK:

> the `streamable_http_app()` you already deploy serves both.

> The SDK routes every request by its `MCP-Protocol-Version` header. [...] It
> happens per request, before your code, on the one app.

> Nothing, literally. There is no `legacy=` option, no version allowlist, no way
> to reject or disable an era: not on `streamable_http_app()`, not on `run()`,
> not on the session manager. Both eras are always on.

**TypeScript** **[OFFICIAL]**,
`docs/migration/support-2026-07-28.md` (verified 2026-09-18). The opposite
default, stated verbatim in the second paragraph:

> Nothing in v2 puts a 2026-07-28 byte on the wire by default: a hand-constructed
> `Client` / `Server` / `McpServer` keeps speaking the 2025-era protocol it was
> written for. Serving or speaking 2026-07-28 is always an explicit opt-in [...]

Opt-in is `ClientOptions.versionNegotiation`, with `mode: 'legacy'` (the
default), `'auto'`, or `{ pin: '2026-07-28' }`. The probe-policy section is worth
reading in full before deploying `'auto'`; three of its rules are the kind of
detail that produces a bad outage postmortem:

> an HTTP `401` or `403` rejecting the probe is never era evidence [...] instead
> of falling back

> on **stdio** a server that does not answer within `timeoutMs` is treated as
> legacy and the client falls back to `initialize` [...] on **HTTP** a probe
> timeout rejects with `SdkError(RequestTimeout)`

> an opaque CORS/preflight `TypeError` during the probe falls back to the legacy
> era, because deployed 2025 servers commonly have CORS allow-lists that predate
> the 2026 headers

That last one is a direct operational consequence of B9: adding two required
headers breaks CORS preflight on servers whose allow-lists were written in 2025.

The same document also warns who should not use `'auto'`, verbatim: "spawn-per-invocation
CLI and debugging tools", because "a legacy server that never answers unknown
pre-`initialize` requests stalls `connect()` for the full probe timeout".

**C#** **[OFFICIAL]**, `docs/versioning.md` (verified 2026-09-18), verbatim:

> The 2.0.0 SDK implements the `2026-07-28` MCP specification revision while
> retaining compatibility with peers that negotiate `2025-11-25` and earlier. A
> v2 client automatically uses the legacy `initialize` handshake when it connects
> to a down-level server, and a v2 server continues to accept that handshake from
> a down-level client.

**Go** **[OFFICIAL]**, README support matrix (verified 2026-09-18), verbatim rows:

> | v1.7.0+         | 2026-07-28       | 2026-07-28, 2025-11-25*, 2025-06-18, 2025-03-26, 2024-11-05 |
> | v1.4.0 - v1.6.1 | 2025-11-25*      | 2025-11-25*, 2025-06-18, 2025-03-26, 2024-11-05             |

**The portability trap:** Python is modern-by-default on the client and
dual-era-always on the server. TypeScript is legacy-by-default on both and
requires opt-in. A polyglot organisation that upgrades SDK versions uniformly
will end up with a fleet whose era behaviour depends on which language each
team chose. That is a governance problem, not a bug, and it is exactly the kind
of thing a platform team should pin in policy rather than discover.

---

## 3. What breaks silently on upgrade

Ordered by how hard it is to notice. "Silent" here means: no error is raised, no
warning is logged, and the symptom appears somewhere other than the change.

### 3.1 Idempotency, after resumability was removed

**[SPEC]** The removal, verbatim from the changelog, major change 9:

> Remove SSE stream resumability and message redelivery (the `Last-Event-ID`
> header and SSE event IDs) from the Streamable HTTP transport. A broken response
> stream loses the in-flight request; clients **MUST** re-issue it as a new
> request with a new request ID (SEP-2575).

**[SPEC]** And the cancellation rule that interacts with it, verbatim from the
Streamable HTTP page:

> Closing the SSE response stream **MUST** be treated by the server as
> cancellation of that request.

Put those together and the operational consequence is specific. A dropped
connection is indistinguishable, at the server, from a cancellation. The server
stops work. The client, per the MUST, re-issues with a new request ID. If the
tool already performed its side effect before the stream broke, **it performs it
twice**.

**[PRACTITIONER]** WorkOS, Maria Paktiti, 2026-09-16,
https://workos.com/blog/mcp-stateless-spec-2026-07-28, states the same thing and
names the class of tool that cares:

> "Stream resumability was removed, and nothing will tell you."

> "For a tool that charges a card, sends an email, or provisions something, a
> lost request that the client then retries is a duplicated side effect."

**What the specification provides instead: nothing, in core.** There is no
idempotency key, no request deduplication, no exactly-once semantics anywhere in
`2026-07-28`. Searched the transports, tools, and basic pages on 2026-09-18; the
word does not appear. The only durable-execution path is the Tasks extension,
`io.modelcontextprotocol/tasks`, which is opt-in by definition. **[UNVERIFIED]:
whether the Tasks extension itself specifies idempotency or at-most-once
delivery.** Do not assert that it does without reading
https://modelcontextprotocol.io/extensions/tasks/overview.

**The honest framing for a maintainer audience:** this is a deliberate trade, it
was made for horizontal scalability, and the maintainers said so. But
idempotency moved from a transport guarantee to an application responsibility
without a protocol-level place to put it, and application authors will not all
notice.

### 3.2 A dual-era server still needs sticky routing for half its traffic

This one is not in the specification at all and is the most underrated finding
in this document.

**[OFFICIAL]** Python SDK, `docs/run/legacy-clients.md` (verified 2026-09-18),
verbatim:

> A `2026-07-28` connection is **sessionless**: every request stands alone, and
> the modern handler never issues an `Mcp-Session-Id`. A legacy connection is the
> opposite. The moment a pre-2026 client sends `initialize`, the SDK mints an
> `Mcp-Session-Id`, returns it in a response header, and keeps a live record
> behind it [...]

> That record is a **plain in-process `dict`**. There is no distributed session
> store and no way to plug one in.

So the headline benefit of `2026-07-28`, stated by the maintainers as "any
request can now land on any server instance behind a plain round-robin load
balancer without needing shared storage", **does not apply to a dual-era
deployment for as long as any legacy client remains**. The load balancer still
needs affinity, or legacy sessions break. And because dual-era is how the
specification tells you to migrate, the period during which you get neither the
old guarantees nor the new benefit is exactly the migration window.

This is a strong, specific, verifiable point for the talk, and it is not a
criticism of the spec. It is a consequence of the transition that nobody has
written down in one place.

### 3.3 Version skew, the `resultType` branch

**[SPEC]** Changelog major change 8, verbatim:

> Clients **MUST** treat results from earlier-protocol servers that omit the
> field as `"complete"`.

Every modern client carries this compatibility branch permanently. There is no
sunset date attached to it in the changelog or the deprecated registry.

### 3.4 CORS preflight, an unannounced consequence of B9

Covered in 2.4 from the TypeScript probe-policy text. Adding two required headers
to every POST means a 2025-era CORS allow-list rejects a 2026-era browser client
at preflight, and the failure surfaces as an opaque `TypeError` rather than
anything naming MCP. The TypeScript SDK works around it by treating that
`TypeError` as legacy evidence. A server operator upgrading a browser-facing MCP
endpoint should update `Access-Control-Allow-Headers` before, not after.
**[UNVERIFIED]:** whether any MCP specification page or official doc states the
CORS requirement explicitly. I did not find one on 2026-09-18; the only source
for it is the TypeScript SDK migration guide.

### 3.5 `Mcp-Session-Id` is ignored, not rejected

From 2.3. A legacy client sending a session ID against a modern-only server gets
no signal at all. Its state silently stops persisting.

### 3.6 Deprecated features keep working, so nothing surfaces the clock

The deprecation policy is annotation-only at the wire level. Roots, Sampling and
Logging all still function. The only mechanism that will tell a developer is the
SDK obligation, and it binds only Tier 1 SDKs. **[SPEC]**
https://modelcontextprotocol.io/community/feature-lifecycle, verbatim:

> Once the revision in which a feature becomes Deprecated is released as Current,
> Tier 1 SDKs:
>
> * Must mark the corresponding API surface deprecated using the language's
>   native mechanism [...] in their next release, referencing the deprecation SEP
>   and the earliest removal date where the mechanism permits.
> * Should emit a runtime warning when a deprecated feature is exercised

A Java, Kotlin, Swift, Ruby or PHP shop gets neither guarantee. **[UNVERIFIED]:**
whether each Tier 1 SDK has actually shipped the deprecation annotations. The
C# repo has a `src/Common/Obsoletions.cs` matching a `2026-07-28` search and the
Go README carries a note that "The roots, sampling, and logging features are
deprecated as of protocol version 2026-07-28", which is corroborating but not a
systematic check.

---

## 4. Deprecated features: what an organisation with these in production does

**[SPEC]** The registry, https://modelcontextprotocol.io/specification/2026-07-28/deprecated
(verified 2026-09-18). Reproduced verbatim, with the migration paths as written:

| Feature | Deprecation SEP | Deprecated in | Migration path | Earliest removal |
|---|---|---|---|---|
| Roots | SEP-2577 | `2026-07-28` | "Pass directories or files via tool parameters, resource URIs, or server configuration" | First revision released on or after 2027-07-28 |
| Sampling | SEP-2577 | `2026-07-28` | "Integrate directly with LLM provider APIs" | First revision released on or after 2027-07-28 |
| Logging | SEP-2577 | `2026-07-28` | "Log to `stderr` for stdio transports; use OpenTelemetry for observability" | First revision released on or after 2027-07-28 |
| Dynamic Client Registration | PR #2858 | `2026-07-28` | "Client ID Metadata Documents" | First revision released on or after 2027-07-28 |
| `includeContext: "thisServer"` / `"allServers"` | SEP-2596 | `2025-11-25` | "Omit the field or use `\"none\"`" | Follows Sampling (SEP-2577) |
| HTTP+SSE transport | SEP-2596 | `2025-03-26` | "Streamable HTTP" | Three months after SEP-2596 reaches Final |

Removed section, verbatim, as of 2026-09-18:

> No features have been removed under this policy yet.

And the reassurance an enterprise planner needs, verbatim from the same page:

> The earliest removal marks when a feature becomes *eligible* for removal; the
> actual removal is a Core Maintainer decision taken during release preparation
> and may happen later.

Plus, from the lifecycle policy: "Features may remain Deprecated, without
removal, for much longer than the minimum deprecation window."

**The window, and its escape hatch.** **[SPEC]**
https://modelcontextprotocol.io/community/feature-lifecycle, verbatim:

> Specify the **minimum deprecation window**: the number of months, at least
> twelve, that the feature must remain Deprecated before it is eligible for
> removal. The window is measured from the release of the specification revision
> in which the feature is first marked Deprecated, not from the date the SEP
> reaches Final.

> The twelve-month floor may be shortened when the feature presents an active
> security risk, meaning a vulnerability with a published security advisory or
> documented in-the-wild exploitation for which no in-place mitigation exists.
> [...] The shortened window must still provide at least ninety days between the
> feature becoming Deprecated and its earliest removal.

**A detail that changes the calculus and is easy to miss.** Verbatim:

> ### SDKs
>
> Removal from the specification does not oblige an SDK to drop the feature from
> releases. That timeline is governed by the SDK's own revision-support policy.

So the cliff is softer than it looks. Spec removal in 2027-07-28 does not mean
the code stops working then. It means new revisions stop defining it.

### 4.1 What each migration actually costs

Judged against the migration path the registry names, not invented.

**Roots to tool parameters.** Cheapest of the four. Roots were a client
capability; the replacement is an ordinary argument. The cost is that the
directory list now travels in the context window on every call that needs it,
which is the general shape of the stateless trade. **[PRACTITIONER]** Artemii
Amelin, 2026-09-01,
https://dev.to/artem_a/mcp-2026-07-28-deleted-the-session-the-state-moved-into-your-context-window-1hde:
"Connection state has become context-window state. It costs tokens on every turn
it survives".

**Sampling to direct LLM provider APIs.** The most expensive, and it is an
architectural change rather than a rename. Sampling let a server borrow the
host's model, the host's model choice, the host's billing relationship and the
host's consent surface. "Integrate directly with LLM provider APIs" means the
server now needs its own provider credentials, its own model selection policy,
its own token budget and its own spend attribution. For an enterprise, that is a
procurement and cost-allocation change, not a code change. It also moves the
model call outside whatever guardrails the host applied.

**Logging to stderr and OpenTelemetry.** The most operationally positive. The
protocol is naming OpenTelemetry by name as the observability path, and
`2026-07-28` added W3C Trace Context propagation conventions in `_meta`
(`traceparent`, `tracestate`, `baggage`, SEP-414). An organisation that already
runs OTel gets a better answer than it had. One that does not now has to.
The removal of `logging/setLevel` (B12) is the sharp edge: runtime log-level
control is gone, replaced by `io.modelcontextprotocol/logLevel` per request, so
"turn up logging on the running server" becomes a client-side change.

**DCR to Client ID Metadata Documents.** Covered in depth in
`research/spec/mcp-specification-state-2026-09.md` Section 3.10. The operational
summary: CIMD requires the client to host a JSON document at an HTTPS URL whose
`client_id` matches the URL exactly, which is a hosting requirement most desktop
and CLI clients did not previously have. In exchange, verbatim from the spec:
"Client IDs based on Client ID Metadata Documents are portable across
authorization servers [...] No re-registration is needed when the authorization
server changes." For a large organisation that is the better deal, because the
alternative is now bound by a new rule: clients "**MUST NOT** reuse client
credentials from a different authorization server and **MUST** re-register with
the new authorization server."

---

## 5. Official best practice for building and operating a server

Everything in this section is **[SPEC]** or **[OFFICIAL]** and quoted. Vendor and
practitioner material is in `research/scale/` and `research/ops/`.

### 5.1 The four transport-security requirements

**[SPEC]** https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http,
"Security & Endpoint", verbatim and complete:

> 1. Servers **MUST** validate the `Origin` header on all incoming connections
>    to prevent DNS rebinding attacks.
>    * If the `Origin` header is present and invalid, servers **MUST** respond
>      with HTTP 403 Forbidden. The HTTP response body **MAY** comprise a
>      JSON-RPC *error response* that has no `id`.
> 2. When running locally, servers **SHOULD** bind only to localhost
>    (127.0.0.1) rather than all network interfaces (0.0.0.0).
> 3. Servers **SHOULD** implement proper authentication for all connections.
>
> Without these protections, attackers could use DNS rebinding to interact with
> local MCP servers from remote websites.

Read the normative levels carefully, because this is the spine of the "optional
but load-bearing" argument in `research/spec/` Section 8. Origin validation is a
**MUST**. Binding to localhost is a **SHOULD**. **Authentication on the
network-exposed transport is a SHOULD.** A server can be fully conformant,
reachable on the public internet, and unauthenticated.

Note also the refinement in the 2026-07-28 wording: the MUST is conditional on
the header being *present*. A request with no `Origin` header at all is not
covered by clause 1.

### 5.2 The six server security requirements on the tools page

**[SPEC]** https://modelcontextprotocol.io/specification/2026-07-28/server/tools,
"Security Considerations", verbatim and complete:

> 1. Servers **MUST**:
>    * Validate all tool inputs
>    * Implement proper access controls
>    * Rate limit tool invocations
>    * Sanitize tool outputs
>
> 2. Clients **SHOULD**:
>    * Prompt for user confirmation on sensitive operations
>    * Show tool inputs to the user before calling the server, to avoid malicious or
>      accidental data exfiltration
>    * Validate tool results before passing to LLM
>    * Follow the `$ref` resolution requirements when validating tool inputs and outputs
>    * Implement timeouts for tool calls
>    * Log tool usage for audit purposes

**Rate limiting is a server MUST.** That is a stronger statement than most MCP
server implementations honour, and it is one sentence long in a page most people
read for schema guidance. Worth putting on a slide verbatim.

And the consent posture, verbatim from the same page:

> For trust & safety and security, there **SHOULD** always
> be a human in the loop with the ability to deny tool invocations.

Plus the trust boundary on annotations:

> For trust & safety and security, clients **MUST** consider tool annotations to
> be untrusted unless they come from trusted servers.

### 5.3 Scale: statelessness, list stability, caching, ordering

**[SPEC]** The statelessness contract,
https://modelcontextprotocol.io/specification/2026-07-28/basic/index, verbatim:

> * Servers **MUST NOT** rely on prior requests over the same connection to
>   establish context (e.g., capabilities, protocol version, client identity).
> * Servers **SHOULD** be prepared to handle requests associated with multiple
>   tasks, threads, or conversations.
> * Servers **SHOULD NOT** require that a client reuse the same connection or process to
>   perform related operations.
> * State that needs to span multiple requests (e.g., long-running tasks,
>   application-level handles) **MUST** be referenced by an explicit identifier
>   the client passes on each request.

**[SPEC]** List stability, the property that makes caching and horizontal
scaling safe, from the tools page, verbatim:

> This set **MAY** be empty and **MAY** change over time [...] but **MUST NOT**
> vary per-connection or as a side effect of other requests on the connection.
> The set **MAY** vary by the authorization presented on the request

**[SPEC]** Deterministic ordering, with its stated reason, verbatim:

> Servers **SHOULD** return tools in a deterministic order (i.e., the same
> ordering across requests when the underlying set of tools has not changed).
> Deterministic ordering enables clients to reliably cache the tool list and
> improves LLM prompt cache hit rates when tools are included in model context.

This is a SHOULD whose violation costs money on every turn, in prompt-cache
misses, at the client. The server operator who ignores it does not pay the bill.
That asymmetry is worth naming.

**[SPEC]** Caching. `ttlMs` and `cacheScope` are required on `tools/list`,
`prompts/list`, `resources/list`, `resources/read`, `resources/templates/list`
(B13) and are also supported on `server/discover`. `cacheScope` takes `"public"`
or `"private"` and governs whether a shared intermediary may cache the result.
Getting it wrong on a multi-tenant server is tenant-data disclosure through a
CDN; that failure mode is catalogued as F15 in `research/ops/`.

### 5.4 Long-running operations and streams

**[SPEC]** Cancellation on Streamable HTTP is transport-level, verbatim:

> Closing the SSE response stream **MUST** be treated by the server as
> cancellation of that request. Because each request has its own response
> stream, the transport-level disconnect is unambiguous. The server **SHOULD**
> stop work on the cancelled request as soon as practical and **MUST NOT** send
> any further messages for it.

**[SPEC]** Two proxy-facing requirements that are pure operations guidance and
are easy to miss, verbatim:

> When initiating an SSE stream, servers **SHOULD** include the
> `X-Accel-Buffering: no` header in the HTTP response. This instructs reverse
> proxies (such as nginx) to disable response buffering

> For long-lived streams [...] servers are encouraged to periodically emit an SSE
> comment line (a line beginning with a colon, e.g. `:\r\n`) as a keep-alive.
> This keeps the connection from being closed by intermediaries or client idle
> timeouts during quiet periods

The keep-alive guidance pairs directly with the layered-idle-timeout failure mode
catalogued as F10 in `research/ops/` from the AWS Architecture Blog. The spec
names the mitigation; the AWS post names the three tiers whose timeouts have to
agree.

### 5.5 Error semantics: `isError` on HTTP 200

**[SPEC]** From the tools page, verbatim, the two-mechanism model:

> 1. **Protocol Errors** indicate issues with the request structure itself that
>    models are less likely to be able to fix:
>    * Unknown tool
>    * Malformed requests
>    * Server errors
>
>    They are returned as standard JSON-RPC errors

> 2. **Tool Execution Errors** contain actionable feedback that language models
>    can use to self-correct and retry with adjusted parameters:
>    * API failures
>    * Input validation errors (e.g., date in wrong format, value out of range)
>    * Business logic errors
>
>    They are reported in tool results with `isError: true`

> Clients **MAY** provide protocol errors to language models, though these are
> less likely to result in successful recovery.
> Clients **SHOULD** provide tool execution errors to language models to enable
> self-correction.

The operational consequence, catalogued as F13 in `research/ops/`: a tool
execution error is a JSON-RPC *result*, carried on a successful HTTP response.
Monitoring that alarms on 5xx sees a perfectly healthy server while every tool
call fails. **Any MCP server SLO built on HTTP status codes is measuring the
wrong thing.** The correct signal is the rate of results carrying `isError: true`,
which needs application-level instrumentation, which is the same instrumentation
the deprecation of Logging pushed onto OpenTelemetry. Those two facts belong
together on a slide.

### 5.6 Stateful tools: the explicit-handle pattern

**[SPEC]** From the tools page, flagged non-normative, verbatim:

> This section is non-normative guidance for tool design. The protocol has no
> concept of a state handle; from the wire's perspective a handle is an ordinary
> string in a tool result and an ordinary argument to subsequent tool calls.

Design guidance, verbatim, condensed to the four bullets the spec gives:

> * **Authorization.** For authenticated servers, a handle is a name, not a
>   capability. The server should validate the caller's authorization against the
>   handle on every call. For unauthenticated servers, where the handle is
>   necessarily a bearer token, it should be generated with sufficient entropy
>   (e.g., a UUIDv4) and given a bounded lifetime.
> * **Opacity.** Handles that encode internal structure invite parsing or
>   guessing; opaque identifiers do not.
> * **Lifetime.** Because handles outlive any single connection, the server's
>   retention policy should be stated in the creation tool's description [...]
> * **Expiry errors.** A call against an expired or unknown handle should return
>   a tool execution error that says so, so the model can recover by creating a
>   new one.

Note that the whole replacement for protocol sessions is **non-normative
guidance**, while the thing it replaced was normative. That is a real observation
about where the load moved, and it is fair to say from the stage without it being
an attack.

### 5.7 Tool naming

**[SPEC]** From the tools page, all SHOULDs, verbatim:

> * Tool names **SHOULD** be between 1 and 128 characters in length (inclusive).
> * Tool names **SHOULD** be considered case-sensitive.
> * The following **SHOULD** be the only allowed characters: uppercase and
>   lowercase ASCII letters (A-Z, a-z), digits (0-9), underscore (_), hyphen (-),
>   and dot (.)
> * Tool names **SHOULD NOT** contain spaces, commas, or other special characters.
> * Tool names **SHOULD** be unique within a server.

And the aggregation warning, which is the one that matters for a gateway, verbatim:

> Tool name uniqueness is scoped to a single server. Clients or proxies that
> aggregate tools from multiple servers **MAY** encounter naming collisions [...]
> and **SHOULD** implement a disambiguation strategy such as prefixing tool names
> with a server identifier.
>
> The server `name` (from `serverInfo`) is not guaranteed to be unique across
> servers and **SHOULD NOT** be relied upon for disambiguation.

Two SHOULDs that together mean: an enterprise MCP gateway has no protocol-provided
way to name a tool unambiguously across its catalogue, and the obvious
disambiguator is explicitly disclaimed. The registry namespace
(`io.github.user/server`) is the nearest thing, and it is preview.

Because tool names are only SHOULD-constrained to header-safe characters, the
Streamable HTTP page requires the Base64 sentinel for `Mcp-Name` when a name
falls outside the safe set (Section 0.1). A gateway matching on raw `Mcp-Name`
without decoding will silently fail on exactly the tools whose names were
non-conforming.

---

## 6. Hardening

**[SPEC]** The security best practices page,
https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
(verified 2026-09-18), is the official hardening document. It runs to ten attack
classes. The ones a server operator owns:

### 6.1 Token passthrough

> MCP servers **MUST NOT** accept any tokens that were not explicitly
> issued for the MCP server.

The stated harms, verbatim and condensed: "Security Control Circumvention",
"Accountability and Audit Trail Issues", "Trust Boundary Issues", "Future
Compatibility Risk". The audit sentence is the one that lands with a governance
audience:

> The downstream Resource Server's logs may show requests that appear
> to come from a different source with a different identity, rather
> than the MCP server that is actually forwarding the tokens.

### 6.2 State handle hijacking, new in this revision

This attack class exists only because sessions were removed. Verbatim:

> MCP is stateless and has no protocol-level sessions. Servers that need state
> spanning multiple requests mint an explicit handle [...] State handle hijacking
> is an attack vector where an unauthorized party obtains or guesses such a
> handle and uses it to access or modify another user's state.

Mitigation, verbatim:

> MCP servers that implement authorization **MUST** verify all inbound
> requests. MCP servers **MUST NOT** treat possession of a state handle
> as authentication.

> MCP servers **SHOULD** use secure, non-deterministic handles generated
> with secure random number generators.

> MCP servers **SHOULD** bind handles server-side to the authenticated
> user, for example by keying stored state as `<user_id>:<handle>` where
> the user ID is derived from the verified token rather than supplied by
> the client, and reject a handle presented by any other principal.

**This is the migration hazard nobody schedules.** A team that mechanically
converts a session ID into a state handle has reproduced session hijacking with a
new name and no transport-level protection, and the specification's answer is a
MUST NOT plus two SHOULDs on a documentation page rather than anything the wire
enforces.

### 6.3 SSRF

Applies to clients fetching OAuth metadata, and equally to authorization servers
fetching Client ID Metadata Documents. Verbatim:

> MCP clients deployed to a server **MUST** consider SSRF risks and
> implement appropriate mitigations when fetching OAuth-related URLs.

The named mitigations, all SHOULD: enforce HTTPS, block private IP ranges
(`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `::1`,
`169.254.0.0/16`, `fc00::/7`, `fe80::/10`), validate redirect targets, use an
egress proxy, and account for DNS TOCTOU. The spec's own caution, verbatim:

> Avoid implementing IP validation manually. Attackers exploit encoding tricks
> (octal, hex, IPv4-mapped IPv6) that custom parsers often miss.

Named tooling, verbatim: "Use tools like Smokescreen or similar egress proxies
that prevent SSRF by design."

### 6.4 Command injection and sandboxing for local servers

Verbatim, the client obligation:

> If an MCP client supports one-click local MCP server configuration, it
> **MUST** implement proper consent mechanisms prior to executing commands.

The MUST list for that dialog, verbatim: "Show the exact command that will be
executed, without truncation", "Clearly identify it as a potentially dangerous
operation that executes code on the user's system", "Require explicit user
approval before proceeding", "Allow users to cancel the configuration".

The SHOULD list includes the sandboxing guidance an enterprise would want as
policy, verbatim:

> * Execute MCP server commands in a sandboxed environment with minimal
>   default privileges
> * Launch MCP servers with restricted access to the file system, network,
>   and other system resources
> * Use platform-appropriate sandboxing technologies (containers, chroot,
>   application sandboxes, etc.)
> * Keep sandboxing solutions up-to-date to account for emerging
>   vulnerabilities

And the server-side counterpart, verbatim:

> MCP servers intending for their servers to be run locally **SHOULD**
> implement measures to prevent unauthorized usage from malicious
> processes:
>
> * Use the `stdio` transport to limit access to just the MCP client
> * Restrict access if using an HTTP transport, such as:
>   * Require an authorization token
>   * Use unix domain sockets or other Interprocess Communication (IPC)
>     mechanisms with restricted access

### 6.5 URL scheme validation and no shell execution

Verbatim:

> MCP clients **MUST** validate authorization URLs and reject dangerous schemes:
>
> * **MUST** only allow `http://` and `https://` schemes for authorization URLs [...]
> * **MUST** reject `javascript:`, `data:`, `file:`, `vbscript:`, and other potentially dangerous schemes
> * **SHOULD** use allowlist-based validation rather than blocklist-based approaches

> MCP clients **MUST** avoid shell execution when opening URLs:
>
> * **MUST NOT** use shell commands (e.g., `cmd.exe`, `sh`, PowerShell) to open URLs

### 6.6 Least privilege and scope design

Verbatim from the Scope Minimization section, the common mistakes list:

> * Publishing all possible scopes in `scopes_supported`
> * Using wildcard or omnibus scopes (`*`, `all`, `full-access`)
> * Bundling unrelated privileges to preempt future prompts
> * Returning entire scope catalog in every challenge
> * Silent scope semantic changes without versioning
> * Treating claimed scopes in token as sufficient without server-side
>   authorization logic

And the default that undermines it, verbatim:

> When the initial `WWW-Authenticate` challenge carries no `scope`
> parameter, the Scope Selection Strategy directs clients to fall back to
> requesting all scopes listed in `scopes_supported`.

Because emitting `scope` in the challenge is only a **SHOULD** for servers, the
least-privilege model degrades to maximum-privilege by default whenever a server
omits it. The spec is candid about why: general-purpose MCP clients "typically
lack domain-specific knowledge to make informed decisions about individual scope
selection". That is an honest trade and it should be presented as one.

### 6.7 Secrets handling

Two concrete rules, both already quoted above in other contexts, that belong
together under this heading:

- **[SPEC]** From the tools page: "Server developers **SHOULD NOT** mark sensitive
  parameters (passwords, API keys, tokens, PII) with `x-mcp-header`, as header
  values are visible to network intermediaries."
- **[SPEC]** From the elicitation page (via `research/spec/` 5.3): servers
  "**MUST NOT** use form mode elicitation to request sensitive information such as
  passwords, API keys, access tokens, or payment credentials" and "**MUST** use
  URL mode for interactions involving such sensitive information".
- **[SPEC]** From the authorization overview: STDIO implementations "**SHOULD
  NOT** follow this specification, and instead retrieve credentials from the
  environment."

### 6.8 Container and package distribution

**[UNVERIFIED] as specification guidance.** I found no page on
modelcontextprotocol.io in the 2026-07-28 documentation set that specifies
container or package distribution practice for MCP servers. The registry defines
package types
(https://modelcontextprotocol.io/registry/package-types) and delegates security
scanning outward. **[OFFICIAL]** From the registry docs, quoted in
`research/spec/` 6.6:

> The MCP Registry delegates security scanning to: **Underlying package
> registries** [...] **Downstream aggregators**

So the supply-chain answer in the official ecosystem is "npm, PyPI and whoever
aggregates us". Do not present a container hardening standard as MCP guidance;
there is not one. Vendor gateway and catalogue approaches (Docker MCP Gateway,
Stacklok ToolHive, IBM Context Forge, Kong, agentgateway) are catalogued with
URLs in `research/scale/mcp-at-scale-architecture-2026-09.md` and are **[VENDOR]**
by construction.

---

## 7. Published reference architectures

Deliberately short, because `research/scale/` covers the gateway and platform
landscape in depth with its own source list. These are the ones that speak
directly to deploying a server against the current revision.

| Source | What it is | Label | URL |
|---|---|---|---|
| AWS Architecture Blog, 2026-09-01, Komandooru, DeVries, Najafzadeh | "MCP went stateless: is your AWS MCP server deployment Well-Architected?" The only major-cloud architecture post written specifically against `2026-07-28`. Names instance loss, broken streams, sticky-routing imbalance, cache-scope tenant disclosure, MCP Apps UI injection. Quantifies the deleted session store at "about $23/month" for two `cache.t4g.micro` nodes and argues the real saving is the eliminated operational class | [VENDOR] first-party, but specific and falsifiable | https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/ |
| AWS ML Blog | "How AgentCore Gateway supports the MCP 2026-07-28 spec" | [VENDOR] | https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/ |
| agentgateway, 2026-08-03 | Gateway-side reading of the new revision | [VENDOR] | https://agentgateway.dev/blog/2026-08-03-new-mcp-spec-revision/ |
| Block engineering, 2025-06-16, Mohammed and Chau | Design retrospective across 60+ internal servers. The Linear server going from 30+ tools to two GraphQL-accepting tools is the most concrete tool-design datum in the corpus. Pre-dates `2026-07-28` | [PRACTITIONER] | https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers |
| Microsoft Learn MCP team, 2026-02-11 | How a public MCP service is actually operated. Source of the "2 to 5% of requests broke" parameter-rename figure. Pre-dates `2026-07-28` | [PRACTITIONER] | https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/ |
| pgEdge, 2026-02-05, Ahmed | Transport failure-mode enumeration | [PRACTITIONER] | https://www.pgedge.com/blog/mcp-transport-architecture-boundaries-and-failure-modes |

**[UNVERIFIED]:** whether any Agentic AI Foundation or MCP-project reference
architecture exists. I found none on modelcontextprotocol.io. The official
documentation set covers building a server, connecting to one, debugging one, and
securing one. It does not publish a deployment architecture. That is a gap worth
naming to this specific audience, and it pairs with the missing migration guide
in 2.1.

---

## 8. Open gaps and everything marked UNVERIFIED

Listed here so nothing marked unverified in the body is lost.

1. **Whether the Tasks extension specifies idempotency or delivery semantics.**
   Section 3.1. Read https://modelcontextprotocol.io/extensions/tasks/overview
   before asserting anything about durable execution guarantees.
2. **Whether any official MCP page states the CORS requirement created by the
   new required headers.** Section 3.4. Only the TypeScript SDK migration guide
   was found to mention it.
3. **Whether each Tier 1 SDK has actually shipped the deprecation annotations
   the lifecycle policy requires.** Section 3.6. Corroborating evidence found for
   C# and Go only.
4. **Container and package distribution guidance.** Section 6.8. None found in
   the official documentation set.
5. **Any AAIF or MCP-project reference architecture.** Section 7. None found.
6. **The full conformance picture per SDK against `2026-07-28`.** The conformance
   suite's `latest` npm tag predates the revision and the 2026-07-28 work is on
   an alpha tag. Per-SDK conformance percentages against the current revision
   were not collected; the PHP SDK publishes badges, Java publishes 40/40 server
   against suite version 0.1.15 which is a `2025-11-25`-era suite. Do not quote a
   cross-SDK conformance number.
7. **Whether Ruby's `2026-07-28` support is complete or partial.** Inferred from
   changelog entries describing `subscriptions/listen` and "a modern client", not
   from a support matrix. Ruby publishes no equivalent of Go's table.

---

## 9. Re-verify the week of the talk, highest exposure first

1. **Has a new revision or RC shipped?** https://modelcontextprotocol.io/specification/versioning
   and https://modelcontextprotocol.io/specification/draft/changelog. Everything
   in Section 1 is keyed to `2026-07-28` being current.
2. **SDK protocol support.** Re-run the release check and re-read the Java
   `CHANGELOG.md` release-line table and the Kotlin `common.kt` constant. Both
   negatives in Section 0.2 are the claims most likely to be corrected from the
   floor, and both are one command to refresh. Java Tier 2's six-month clock runs
   to roughly 2027-01-28.
3. **Has any deprecated feature been removed, or any deprecation added?**
   https://modelcontextprotocol.io/specification/2026-07-28/deprecated. The
   Removed section said "No features have been removed under this policy yet" on
   2026-09-18.
4. **Has a migration guide appeared?** Re-grep https://modelcontextprotocol.io/llms.txt
   for "migrat" and "upgrad". Zero matches on 2026-09-18. If one has shipped, the
   Section 2.1 framing must change.
5. **Conformance suite.** Has `@modelcontextprotocol/conformance` promoted a
   `0.2.x` to the `latest` npm tag? `alpha` was `0.2.0-alpha.11` on 2026-09-18.
6. **The header text itself.** Re-read
   https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http.
   Section 0.1 is quoted on a slide; verify the quote rather than trusting this
   file.
7. **Tier assignments.** https://modelcontextprotocol.io/docs/2026-07-28/sdk.
   An SDK relegated or promoted between now and the talk changes Section 0.2.
