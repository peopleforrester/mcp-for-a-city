---
title: "Operating MCP at Scale: the enterprise checklist for 2026-07-28"
subtitle: "Operating MCP at scale, the companion checklist"
date: 2026-10-05
status: draft
series: "Operating MCP at Scale"
part: checklist
sources_verified_on: 2026-10-05
---

<!--
ABOUTME: One checklist for an enterprise running MCP on the 2026-07-28 revision, across all five pillars of the series.
ABOUTME: Each item names its level (spec MUST/SHOULD, or practice) and where it comes from; spec lines checked against the spec source on 2026-10-05.
-->

# Operating MCP at Scale: the enterprise checklist for 2026-07-28

*The companion to the five-part series.*

Each item says what kind of obligation it is. **MUST** and **SHOULD** are the
specification's own words for revision 2026-07-28, read from its source on
2026-10-05. **Practice** is a recommendation argued in the series, with the
part that argues it. A practice item is a judgment, and the part it points to
gives the evidence.

The specification is linked as `spec:` followed by its page path under
`https://modelcontextprotocol.io/specification/2026-07-28/`.

## 1. Know what you are running

- [ ] **Inventory every server and every client, with the protocol era each
  speaks.** `server/discover` answers the server side directly. Practice,
  [part one](part-1-operational-excellence.md).
- [ ] **Make the side you control dual-era first**, usually the servers, because
  a single-era move against the other population lands in a failing cell of
  the compatibility matrix. Practice, part one; matrix at `spec: basic/versioning`.
- [ ] **Plan for permanent version skew.** Your fleet will hold both eras for
  longer than the migration plan says. Practice, part one.
- [ ] **Schedule the four 2026-07-28 deprecations**: Roots, Sampling, Logging and
  Dynamic Client Registration. The registry lists the earliest removal of each
  as the first revision on or after 2027-07-28, and earliest removal means
  eligible, with the removal itself a Core Maintainer decision. Twelve months is
  the floor, with one exception: a feature with an active security risk can be
  removed after at least ninety days. Do not plan on the full year for anything
  security-sensitive. `spec: deprecated`; the
  [feature lifecycle policy](https://modelcontextprotocol.io/community/feature-lifecycle).
- [ ] **Retire the HTTP+SSE transport** (deprecated since 2025-03-26) in favor of
  Streamable HTTP. `spec: deprecated`.

## 2. Server conformance

- [ ] **Implement `server/discover`.** MUST. `spec: server/discover`.
- [ ] **Drop protocol sessions and `Mcp-Session-Id`.** State that must outlive a
  call goes in explicit, server-minted handles passed as tool arguments.
  `spec: changelog` (SEP-2567).
- [ ] **Reject a request missing required `_meta`** (`protocolVersion`,
  `clientCapabilities`) with `-32602`, and HTTP 400. MUST.
  `spec: basic/transports/streamable-http`.
- [ ] **Reject a request whose headers disagree with its body**, with
  `-32020 HeaderMismatch`. MUST, and the reason it exists is a load balancer
  routing on the header while the server executes the body.
  `spec: basic/transports/streamable-http`.
- [ ] **Validate `Origin` on every connection.** MUST. When local, bind to
  127.0.0.1, not 0.0.0.0. SHOULD. `spec: basic/transports/streamable-http`.
- [ ] **Return `ttlMs` and `cacheScope` on every list and read result.** Required
  by the `CacheableResult` interface. `spec: server/utilities/caching`.
- [ ] **Return tools in a deterministic order.** SHOULD. It is also what makes a
  hash of `tools/list` stable enough to approve against (section 5).
  `spec: server/tools`.
- [ ] **Keep secrets out of `x-mcp-header`.** SHOULD NOT mark passwords, keys,
  tokens or personal data, because header values are visible to
  intermediaries. `spec: basic/transports/streamable-http`.
- [ ] **Stop relying on `ping` and `logging/setLevel`.** Both are removed. Log
  level travels per request in `_meta`. `spec: changelog`.

## 3. Clients, gateways and probes

- [ ] **Send `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` on every
  Streamable HTTP POST.** MUST. `spec: basic/transports/streamable-http`.
- [ ] **Treat a result without `resultType` from an older server as complete.**
  MUST. `spec: changelog`.
- [ ] **Re-issue a request whose stream broke as a new request with a new ID.**
  MUST, because resumability is gone. `spec: changelog` (SEP-2575).
- [ ] **Write down your own idempotency convention.** The specification defines
  none, and every retry is a new call. Practice, parts
  [one](part-1-operational-excellence.md) and [three](part-3-reliability.md).
- [ ] **Do not health-check with `ping`.** Production servers already answer it
  with `-32601`. Practice, part three.
- [ ] **Count any protocol answer as proof of life**, including a JSON-RPC error.
  Practice, part three.
- [ ] **Make sure a `server/discover` probe cannot be answered from a cache.**
  If you own the server, return `ttlMs: 0`; otherwise probe the backend
  directly. Practice, part three.
- [ ] **Read your gateway's defaults, not its feature list.** Retry, reactivation
  and circuit breaking may be present and switched off. Practice, part three.

## 4. Authorization, on every HTTP server you run

Authorization is **OPTIONAL** in the specification (`spec: basic/authorization`).
Making it mandatory is an estate decision, and once you do, the lines below
bind.

- [ ] **Server: publish Protected Resource Metadata (RFC 9728)** with at least
  one authorization server. MUST. `spec: basic/authorization`.
- [ ] **Server: accept only tokens issued for it**, checking the audience
  (RFC 8707), and return 401 on an invalid or expired token. MUST.
  `spec: basic/authorization`.
- [ ] **Server: never pass the client's token through to an upstream API.**
  MUST NOT. This is also the test for a correctly built wrapper: the
  credential that reaches the upstream differs from the one the client sent.
  `spec: basic/authorization/security-considerations`.
- [ ] **Client: PKCE with `S256`**, and refuse to proceed when support cannot be
  verified. MUST. `spec: basic/authorization`.
- [ ] **Client: record the issuer before redirecting and validate a returned
  `iss` (RFC 9207).** MUST, new in 2026-07-28. `spec: basic/authorization`.
- [ ] **Client: key stored credentials by issuer**, and re-register when the
  authorization server changes. MUST. `spec: changelog` (SEP-2352).
- [ ] **Client: never put an access token in a query string.** MUST NOT.
  `spec: basic/authorization/security-considerations`.
- [ ] **Move client registration from Dynamic Client Registration to Client ID
  Metadata Documents** before DCR's earliest removal. `spec: deprecated`.

## 5. Admission: deciding a server may enter the estate

The five gates argued in [part two](part-2-security.md). The six approval gates
from the keynote, with every verify step, are the business-side companion:
[approval-gates.md](../04-approval-gates-checklist/approval-gates.md).

- [ ] **Gate 0, intake, automated.** Fingerprint with `server/discover`, run a
  conformance tool with warnings failing the build, scan statically, all inside
  an isolated container, because scanning a stdio server means running it.
- [ ] **Gate 1, provenance.** Registry namespace proof, package signatures,
  SLSA level 2 as a floor. Record it as an audit trail, never as a safety
  finding: provenance does not tell you whether a description is an injection.
- [ ] **Gate 2, blast radius, human.** Read every `inputSchema` and ask what
  happens if every string argument is attacker-chosen. Reject free-form command
  pass-through.
- [ ] **Gate 3, descriptions.** Hash the whole `tools/list` under the credential
  the agent will actually use, store the hash with the approval, and review the
  assembled tool set per agent, not each server alone.
- [ ] **Gate 4, continuous.** Pin digests, re-hash, fail closed on any
  difference, and gate at a proxy on the required headers.
- [ ] **Know your revocation latency.** A registry entry cannot be unpublished,
  only flagged, and nothing pushes the change to a running agent. Your
  revocation latency is your poll interval. Practice, part two.

## 6. Observability

- [ ] **Instrument the result body, not the status code.** A tool failure
  arrives as `isError: true` inside a successful response, so status-code
  monitoring reports health that is not there. `spec: server/tools`; practice,
  part one.
- [ ] **Propagate `traceparent`, `tracestate` and `baggage` in `_meta`.**
  `spec: changelog` (SEP-414).
- [ ] **Log to `stderr` on stdio and to OpenTelemetry otherwise**, as the Logging
  feature's migration path. `spec: deprecated`.

## 7. Reliability

- [ ] **Set your own objective at the MCP boundary.** The hosted servers you
  depend on almost certainly publish none, so an end-to-end number you did not
  define measures something nobody promised you. Practice, part three.
- [ ] **Throttle connection setup, not only tool calls.** That is where measured
  rate limiting happened. Practice, part three.

## 8. Performance

- [ ] **Defer tool loading before trimming by hand**, and measure the discovery
  hop that replaces the loaded surface. Practice, [part four](part-4-performance.md).
- [ ] **Count the tools the model sees at the start of a turn.** Vendor guidance
  runs from under 20 to 50; stay toward the low end. Practice, part four.
- [ ] **Make `tools/list` byte-stable** (sorted, a positive `ttlMs` where stable,
  `public` only when every caller gets the same list), **and treat any change as
  a cache event**: a `listChanged` notification or a new server costs a
  prompt-cache miss. Practice, part four; `spec: server/utilities/caching`.
- [ ] **Know how your gateway merges cache hints.** In a federated list, one
  private or zero-TTL upstream can make the whole list private or uncacheable.
  For per-user lists, cache upstream and filter at the edge. Practice, part four.
- [ ] **Route on headers, and label every request that gets inspected**, so a
  newly enabled detector shows up as a dimension on latency rather than as an
  unexplained p99. Keep secrets off `x-mcp-header` (section 2). Practice,
  part four.
- [ ] **Measure the protocol-version mix at the gateway**, because traffic from
  earlier revisions carries no routing header you should trust. Practice,
  part four.
- [ ] **Check your SDK's response mode, and measure it.** Practice, part four.
- [ ] **Keep a hosted MCP control plane in the client's region.** It sits on
  every tool call. Practice, part four.
- [ ] **Separate a slow server from a slow path** with traces, finer histogram
  buckets, or client duration minus server duration per call. Practice,
  part four.
- [ ] **Keep MCP out of loops with no model in them.** If code already knows the
  endpoint, call the endpoint. Practice, part four.

## 9. Cost

- [ ] **Find out whether each client defers tools.** A client that loads every
  definition on every call carries the full surface; one that defers loads a
  search tool and a handful of definitions. An LLM gateway in front of a client
  can turn deferral off. Practice, [part five](part-5-cost.md).
- [ ] **Price the surface you carry:** definition tokens per call, times model
  calls, times tasks, at your cache-read rate, in front of whoever owns the AI
  budget. It is billed as input tokens under whoever's key made the call.
  Practice, part five.
- [ ] **Cut the surface before tuning anything else:** per-role servers, then
  tool search or code execution where the client supports it. Practice, parts
  four and five.
- [ ] **Keep the prompt prefix stable.** Sort tools in the client, require
  deterministic `tools/list` from the servers you admit, and pin versions.
  Per-caller tool lists are allowed by the specification and are the likeliest
  way off the all-cache-reads floor. Practice, part five.
- [ ] **Treat `list_changed` from an approved server as a review trigger**
  (section 5, gate 4), not only as a cache reset. Practice, part five.
- [ ] **Enter prices for tools that wrap paid APIs** in the gateway, so those
  calls appear in its spend data. Practice, part five.
- [ ] **Check `idempotentHint` and `destructiveHint`, from servers you trust,
  before restarting a task a budget stopped**, and record which tool calls had
  already run. Practice, part five.
- [ ] **Derive the payer from the authenticated token** at each hop, and carry
  `baggage` in `_meta` only as a correlation key. Practice, part five;
  `spec: changelog` (SEP-414).
- [ ] **Measure tool calls per model call before signing an observability
  contract**, and compare vendors at the retention you will buy. Practice,
  part five.
- [ ] **Count review hours from the first vetted server**, including every
  re-review a post-approval tool change triggers. Practice, part five.

---

*The companion checklist to the five-part series on operating MCP at scale.
Specification lines were read from the specification's source for revision
2026-07-28 on 2026-10-05. Practice items carry the evidence in the part they
cite.*
