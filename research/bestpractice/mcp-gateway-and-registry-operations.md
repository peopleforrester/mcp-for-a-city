---
title: "Operating an MCP Gateway and an MCP Registry at Enterprise Scale"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
audience: "MCP maintainers and enterprise platform engineers, MCP Dev Summit Toronto 2026-10-06"
---

<!-- ABOUTME: What it takes to run an MCP gateway and a private MCP registry at enterprise scale, -->
<!-- ABOUTME: what each one structurally cannot do, and the failure modes people have written about. -->

# Operating an MCP Gateway and an MCP Registry at Enterprise Scale

> **Note added 2026-10-06, on publication:** The MintMCP figure of 100 to 250 ms gateway overhead is no longer at its cited URL; treat it as unsourced until it is found again.

Research input for "Governing MCP for a Workforce the Size of a City", MCP Dev
Summit Toronto, 2026-10-06. The audience knows what a gateway and a registry
are. This document is about running them.

A companion session at the same event names the "Gateway Registry" pattern
outright. Everything here is downstream of that pattern: the operational
surface, the enforcement boundary, and the parts that are still unbuilt.

## How to read the sourcing

| Label | Meaning |
|---|---|
| **[OFFICIAL]** | The MCP specification, an MCP project charter, or MCP project documentation |
| **[STANDARDS]** | IETF, OpenID Foundation, or another standards body's own publication |
| **[PRIMARY]** | First-hand account by the people who built or ran the thing |
| **[MEASURED]** | Measured by this research on 2026-09-18, command and result shown |
| **[VENDOR]** | A vendor's own documentation or marketing about its own product |
| **[PRACTITIONER]** | A named practitioner writing about their own experience, not selling |
| **[UNVERIFIED]** | Could not be traced to a source that makes the claim |

Nothing below is stated from memory. Where a claim could not be verified it is
marked and kept rather than dropped, because the absence is often the finding.

Four em-dashes survive in this document. All four sit inside verbatim quotations
from cited sources and are preserved because altering a quote is worse than the
punctuation. No em-dash appears in this document's own prose.

---

# Part 1: The gateway

## 1. Deployment topology, and the bypass problem

### 1.1 Where it sits, and what the protocol now gives it

The `2026-07-28` revision changed the gateway's job from managing connections
to routing requests. Three transport requirements do the work.

Every POST to the MCP endpoint **MUST** carry `MCP-Protocol-Version`,
`Mcp-Method`, and, for `tools/call`, `resources/read` and `prompts/get`,
`Mcp-Name`. The specification states the reason directly:

> The Streamable HTTP transport mirrors selected JSON-RPC body fields into HTTP
> headers so that intermediaries (load balancers, gateways, observability
> tooling) can route and inspect requests without parsing the body.

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
(verified 2026-09-18). **[OFFICIAL]**

Servers **MUST** reject a request whose headers disagree with the body, with
HTTP `400` and JSON-RPC error `-32020` `HeaderMismatch`. The spec names the
exact failure this prevents:

> This prevents potential security vulnerabilities when different components in
> the network rely on different sources of truth (e.g., a load balancer routing
> on the header value while the MCP server executes based on the body value).

**[OFFICIAL]**, same source.

AWS describes the deployment consequence for its own MCP hosting: where the
pre-stateless design needed "Elastic Load Balancing Application Load Balancer
(ALB) stickiness so each session reaches the same instance", the answer now is
"Plain round-robin. Delete the stickiness configuration", and "instance loss is
a non-event. Retries need no session affinity, and scale-in never drains
sessions." The same post is explicit about the migration hazard: "Your ALB
stickiness rules and session store (DynamoDB/ElastiCache) **must remain in
place** until you stop serving pre-2026-07-28 clients."
Source: https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
(verified 2026-09-18). **[VENDOR]**, but the underlying facts are spec-derived.

### 1.2 Single gateway or per-domain

No published source settles this. What the published implementations show is
that everyone builds aggregation, and they build it at different granularities:
agentgateway's "tool federation", Agent Router's `MCPRoute` with multiple
`backendRefs` behind one client `path`, ToolHive's Virtual MCP Server
("aggregates multiple backend MCP servers with centralized authentication,
routing, or tool optimization"), ContextForge's virtual servers, and Kong's
domain-specific bundles, which Kong describes as a future item: "Group related
MCP servers into domain-specific bundles (like 'DevOps' with GitHub, Jira, and
Jenkins)."
Sources: https://github.com/agentgateway/agentgateway ,
https://theagentrouter.ai/docs/capabilities/mcp/ ,
https://docs.stacklok.com/toolhive/ ,
https://ibm.github.io/mcp-context-forge/architecture/ ,
https://konghq.com/blog/product-releases/enterprise-mcp-gateway
(all verified 2026-09-18). **[VENDOR]**

Kong's bundle framing is the honest statement of the tension: one endpoint is
operationally simple and produces a tool list nobody can use. Section 8.6 has
the evidence for why an everything-gateway degrades the agent.

### 1.3 Egress control, and what it actually covers

ToolHive publishes the most specific egress mechanism and, unusually, its
limits. The mechanism is an explicit HTTP proxy, not transparent redirection:

> ToolHive routes outbound traffic from MCP servers through an explicit HTTP
> proxy using standard environment variables.

> ToolHive does not transparently redirect all traffic with iptables or
> nftables rules.

It ships a Squid egress proxy (Envoy optional), a dnsmasq resolver, and an
ingress proxy for SSE/HTTP transports. Isolation is on by default from v0.30.1
for `thv run` and REST-API-created workloads. The permission profile is JSON
with `allow_host` and `allow_port` arrays under `network.outbound`.

The limits are stated plainly, and they matter:

> Network isolation supports HTTP and HTTPS protocols. If your MCP server needs
> to use other protocols (like direct TCP connections for database access), opt
> out.

> If a server bypasses them ... its outbound traffic fails ... Non-compliant
> connections fail.

Source: https://docs.stacklok.com/toolhive/guides-cli/network-isolation
(verified 2026-09-18). **[VENDOR]**

Read that carefully. Proxy environment variables are a convention, not a
kernel-enforced boundary. A server that ignores `HTTP_PROXY` fails closed here
because the container has no other route, which is the right design, but it
means the control is the container network, not the proxy. Any topology that
does not containerise the server does not have this control at all.

The MCP specification itself recommends egress proxies, in the SSRF section,
for server-side client deployments:

> For server-side MCP client deployments, operators **SHOULD** consider using an
> egress proxy that enforces network policies ... Use tools like Smokescreen or
> similar egress proxies that prevent SSRF by design.

Source: https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
(verified 2026-09-18). **[OFFICIAL]**

### 1.4 mTLS and network policy

Out of scope for the MCP project by charter, and worth saying so from the stage
rather than looking for a spec answer. The Security Interest Group charter puts
"Transport wire security: TLS, mTLS, and certificate handling" explicitly out of
scope, assigning it to the Transports WG.
Source: https://modelcontextprotocol.io/community/interest-groups/security.md
(verified 2026-09-18). **[OFFICIAL]**

The practitioner framing that holds up is pgEdge's: stdio for same-host, HTTP
inside a trusted zone ("That zone can be a VPC, a cluster, or a mesh segment.
It is still a network. You still need to plan for failure."), HTTPS across a
trust boundary. Their named failure modes are ordinary distributed-systems
failures that MCP does not exempt you from: "Latency becomes inconsistent under
load", "Streams stall without clear failure signals", "Poor streaming behavior
can hold connections open and exhaust pools", "Misconfigured retries can
amplify load and create cascading availability incidents", and certificate
expiration as "a hard failure case".
Source: https://www.pgedge.com/blog/mcp-transport-architecture-boundaries-and-failure-modes
(verified 2026-09-18). **[PRACTITIONER]**

### 1.5 The bypass problem: local stdio servers that never reach the gateway

This is the central operational fact about gateways and it deserves to be said
without softening.

The clearest published statement is a vendor's, and it is correct:

> A gateway only governs the traffic configured to flow through it. MCP
> connections made directly inside desktop apps and coding agents bypass any
> central policy.

Source: https://www.getmaxim.ai/articles/shadow-mcp-servers-visibility-and-control-at-the-gateway/
(verified 2026-09-18). **[VENDOR]**

The specification treats the local server as a client-side trust problem, not a
network one. Its mitigations are all addressed to the MCP **client**:

> If an MCP client supports one-click local MCP server configuration, it **MUST**
> implement proper consent mechanisms prior to executing commands.

> Show the exact command that will be executed, without truncation (include
> arguments and parameters)

> Execute MCP server commands in a sandboxed environment with minimal default
> privileges

> Warn that MCP servers run with the same privileges as the client

And for server authors: "Use the `stdio` transport to limit access to just the
MCP client."
Source: https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
(verified 2026-09-18). **[OFFICIAL]**

Every one of those is a control the client enforces. None of them is a control
a platform team enforces. A developer who edits a config file and points a
local server at production has stepped outside the gateway before the gateway
was ever asked a question.

**What the published sources actually propose, and what each one can reach.**

| Approach | Reaches a laptop stdio server? | Source | Label |
|---|---|---|---|
| Registry as allowlist, gateway as the only sanctioned path | No. Governs only traffic routed to it | https://zuplo.com/blog/how-to-avoid-shadow-mcp-servers | [VENDOR] |
| Firewall monitoring for "MCP signatures" | Partially, and only for servers that egress over the corporate network | same | [VENDOR] |
| Kubernetes admission control on `MCPServer` resources | No. Governs cluster workloads only | https://docs.stacklok.com/toolhive/guides-k8s/ | [VENDOR] |
| Containerised servers with an egress proxy | Only for servers you run, not servers a developer starts | https://docs.stacklok.com/toolhive/guides-cli/network-isolation | [VENDOR] |
| MDM-deployed endpoint agent that reads AI-app config files | Yes, on managed devices with the agent installed | https://www.getmaxim.ai/articles/shadow-mcp-servers-visibility-and-control-at-the-gateway/ | [VENDOR] |
| Enterprise-Managed Authorization (ID-JAG through the enterprise IdP) | For any server that requires OAuth, yes, regardless of route | https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization.md | [OFFICIAL] |

The last row is the one most gateway discussions miss, and it is the only
vendor-neutral answer in the list. Enterprise-Managed Authorization moves the
allowlist off the network path and into the identity provider:

> The enterprise IdP maintains a registry of approved MCP servers and the access
> policies for each.

> Employees who lack authorization receive an appropriate error — the MCP client
> never receives a token for unauthorized servers.

> Revoking an employee's access to MCP servers happens at the IdP level, taking
> effect immediately across all MCP clients.

Source: https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization.md
(verified 2026-09-18). **[OFFICIAL]**

Three honest caveats to state with it. The extension is opt-in and
client-dependent: "Support for this extension varies by client. Extensions are
opt-in and never active by default." It requires client-level support "from the
organization's IT team in addition to the MCP client application." And it does
nothing about a local server that authenticates with a static API key in a
config file, because no token exchange happens at all.

**The honest conclusion.** No published source closes the local-stdio gap at
the network layer, and the two approaches that reach it are not gateway
approaches. One moves the decision to the identity provider, which works for
servers that do OAuth and needs client cooperation. The other manages the
endpoint, which works on managed devices and needs an agent. A gateway is the
enforcement point for the traffic you can route. Treating it as the enforcement
point for everything is the mistake, and it is a mistake a slide diagram makes
very easy to draw.

---

## 2. The enforcement boundary: what a gateway sees, and what it structurally cannot

### 2.1 What it sees without parsing a body

Exactly four things, all from the transport spec cited in 1.1:

1. `MCP-Protocol-Version`
2. `Mcp-Method`, mirroring `method`
3. `Mcp-Name`, mirroring `params.name` or `params.uri` for `tools/call`,
   `resources/read` and `prompts/get`
4. `Mcp-Param-{Name}` for each tool parameter the **server author** chose to
   annotate with `x-mcp-header` in the tool's `inputSchema`

Plus whatever identity rides in the `Authorization` header.

### 2.2 Per-argument authorization: the spec hands you the mechanism and then warns you off the arguments you want

`x-mcp-header` is genuinely the per-argument hook. A server annotates a
parameter, and the client **MUST** mirror its value into `Mcp-Param-{Name}`:

> While the use of `x-mcp-header` is optional for servers, clients **MUST**
> support this feature.

It is constrained: primitive types only (integer, string, boolean; `number` is
prohibited), statically reachable from the schema root through `properties`
chains only, no `items`, no `oneOf`/`anyOf`/`allOf`, no `if`/`then`/`else`, no
`$ref`, case-insensitively unique within the schema.

And then:

> Server developers **SHOULD NOT** mark sensitive parameters (passwords, API
> keys, tokens, PII) with `x-mcp-header`, as header values are visible to
> network intermediaries.

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
(verified 2026-09-18). **[OFFICIAL]**

That is the boundary in one sentence. The arguments a gateway can authorize on
cheaply are, by the spec's own guidance, the non-sensitive ones. Authorizing on
a sensitive argument means parsing the body, which means the gateway is no
longer a router and is now a full MCP-aware proxy on the critical path of every
call.

A second constraint follows and is easy to miss: a gateway that runs a header
allowlist breaks these tools.

> Intermediate servers that do not recognize an `Mcp-Param-{Name}` header
> **MUST** forward it and otherwise ignore it.

Strip it and the backend returns `-32020`. **[OFFICIAL]**, same source.

### 2.3 Header trust is conditional on protocol version

> Intermediaries that enforce policy based on mirrored headers (e.g., routing or
> rate-limiting by tenant) **SHOULD** verify that the `MCP-Protocol-Version`
> header indicates a version that requires header-body validation. If the
> version is older or the header is absent, the intermediary **SHOULD** reject
> the request rather than trusting unvalidated header values.

Source: streamable-http transport page (verified 2026-09-18). **[OFFICIAL]**

In a mixed fleet, a gateway that routes on `Mcp-Name` without checking the
protocol version is routing on a value nothing validated. The correct behaviour
is to reject, which means the migration to the stateless revision is not
optional for anyone who wants header-based policy.

### 2.4 What it structurally cannot enforce

**Intent.** A gateway evaluates one call. The most candid published
acknowledgement is Microsoft's own, about its own control plane:

> The toolkit governs individual tool calls deterministically. It does not yet
> correlate sequences of individually-allowed calls that may form a malicious
> workflow.

Source: https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/
(verified 2026-09-18). **[VENDOR]**, and the more credible for being a
limitation disclosed by the vendor.

AWS's Policy in AgentCore is the only published engine that reaches past the
single call, via Dogwood's "session-aware temporal conditions that decide based
on what has already happened earlier in the same session — for example,
requiring that an approval was granted before a transfer, blocking an action
after it has run a set number of times, or keeping a running total under a
budget."
Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
(verified 2026-09-18). **[VENDOR]**

That is real and it is bounded: one session, one gateway, one vendor's engine.
It does not reach a sub-agent, a second gateway, or a task that spans days.

**Whether the data returned should have been returned.** Nothing in MCP
attaches a sensitivity classification to a tool result. A gateway can inspect a
response body and pattern-match, which is what Lasso's Presidio-based PII
detection and Microsoft's response validation do, and which is heuristic. The
specification's only normative statements here are addressed to the server
("Sanitize tool outputs") and the client ("Validate tool results before passing
to LLM").
Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
(verified 2026-09-18). **[OFFICIAL]**

**Anything inside a response the model then acts on.** This is where the
boundary is sharpest, and the MCP project states it directly in the context of
programmatic tool calling:

> Cross-server data flow: Tool results from one server are untrusted input to
> another. The broker should apply the same input-review policy to brokered
> calls as to direct ones; output truncation alone does not prevent
> exfiltration.

> Per-call authorization: The broker is still the MCP host for spec purposes ...
> Approving the script does not grant blanket approval for every tool call it
> makes at runtime.

Source: https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md
(verified 2026-09-18). **[OFFICIAL]**

Note who the enforcement point is in that text: the **broker**, which lives in
the host, not the gateway. Anthropic's engineering post on the same pattern
describes the consequence for observability: "intermediate results stay in the
execution environment by default. This way, the agent only sees what you
explicitly log or return."
Source: https://www.anthropic.com/engineering/code-execution-with-mcp
(verified 2026-09-18). **[PRIMARY]**

A gateway still sees every `tools/call` the sandbox makes, because they are
ordinary calls. What it cannot see is the composition: which result fed which
argument, and what the script did in between. The join between calls happens in
a sandbox the gateway has no view into.

**Whether a tool description is what the publisher wrote.** The spec makes the
client responsible and gives it nothing to verify with:

> For trust & safety and security, clients **MUST** consider tool annotations to
> be untrusted unless they come from trusted servers.

**[OFFICIAL]**, tools page. There is no attestation today. SEP-2809, Attested
Tool-Server Admission, is the proposal to change that, and it is a **Draft**
pull request, opened 2026-05-28, authored by an individual contributor and
tracked as a Security IG discussion item. Its own framing of the gap:

> a prompt-injected model can drive a destructive tool on any server it connects
> to

Sources: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2809 ,
https://modelcontextprotocol.io/community/interest-groups/security.md
(verified 2026-09-18). **[OFFICIAL]** for the charter status, **[UNVERIFIED]**
for the SEP's claimed "48 hermetic tests and adversarial validation against
27,000+ evasion attempts", which is an author's claim in a draft PR and should
not go on a slide.

**Runtime drift after approval.** The Security IG carries this as an open
discussion item with no champion, listed as "Runtime drift: `list_changed`
semantics after approval" with status "Open". A server you approved can change
its tool set and its
descriptions afterwards, and the protocol has no opinion on whether that is a
versioning event, a re-approval event, or a security event. The charter says so
in as many words, listing in scope: "treatment of tool, schema, or behavior
changes after a server has been approved, and whether such changes are
versioning, re-approval, or security events."
Source: https://modelcontextprotocol.io/community/interest-groups/security.md
(verified 2026-09-18). **[OFFICIAL]**

### 2.5 The MCP project's own verdict on the gateway landscape

Worth quoting verbatim to a room of maintainers, because it is the project
talking about the ecosystem rather than a vendor talking about a competitor:

> The ecosystem is developing a sprawling landscape of sidecars, proxies, and
> gateways for cross-cutting concerns that are largely non-reusable and
> non-interoperable, creating an M × N integration problem.

That is the Interceptors Working Group mission statement, chartered 2026-04-21,
led by four people from Bloomberg, Saxo Bank and Nordstrom. Its answer is to
make interception a protocol primitive with two types, validators ("inspect and
return pass/fail decisions") and mutators ("transform context payloads"),
deployable in-process, as a sidecar, or as a remote service, with
"priority-based chain ordering" and "audit mode semantics". SEP-1763 is in
Draft. Reference implementations in the Go and C# SDKs are In Progress. No
target dates are given for any work item.
Source: https://modelcontextprotocol.io/community/working-groups/interceptors.md
(verified 2026-09-18). **[OFFICIAL]**

---

## 3. Operating it

### 3.1 Latency budget, and the decision hiding inside it

Two published figures, two orders of magnitude apart, and the gap is the
architecture decision.

| Claim | Figure | Source | Label |
|---|---|---|---|
| Routing gateway under load | "~10ms Latency, Even Under Load"; "Handles 350+ RPS on just 1 vCPU"; "~3–4 ms latency" in comparisons | https://www.truefoundry.com/blog/enterprise-mcp-governance-control-audit-secure-mcp-server-access | [VENDOR], unverified independently |
| Inspecting gateway | compliance scanning and deep inspection add 100 to 250 ms per request | https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp | [VENDOR], unverified independently |

Neither number is independently reproduced anywhere this research found. Do not
put either on a slide as fact. What survives is the shape: a gateway that
routes on headers costs single-digit milliseconds, and a gateway that parses
and inspects bodies costs two orders of magnitude more. Section 2.2 is why you
might have to pay it.

The protocol removed one round trip outright. There is no `initialize`
handshake, so, in AWS's phrasing, "A client's first message can be the actual
tool call."
Source: https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/
**[VENDOR]**

### 3.2 Caching `tools/list`: the highest-value optimisation and the easiest cross-tenant leak

Servers **MUST** include `ttlMs` and `cacheScope` on `resultType: "complete"`
results from `server/discover`, `tools/list`, `prompts/list`, `resources/list`,
`resources/templates/list` and `resources/read`.

`cacheScope: "public"` means: "Any client, shared gateway, or caching proxy
**MAY** store and serve the cached response to any user."

`cacheScope: "private"` means: "Caches **MUST NOT** be shared across
authorization contexts (e.g. a different access token requires a different
cache)."

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
(verified 2026-09-18). **[OFFICIAL]**

Now the trap, stated by the spec itself:

> Servers MUST be aware that responses with a `"public"` `cacheScope` may be
> shared between callers even if the Result is coming from an authenticated
> endpoint. For example, the Result from an authenticated `tools/list` call with
> a `"public"` `cacheScope` may be cached by a client and may be shared outside
> of the initial requests authorization context.

> MUST apply appropriate per-primitive access controls, and MUST NOT rely on
> `cacheScope` alone to prevent unauthorized access to primitives.

**[OFFICIAL]**, same page.

This lands directly on the gateway pattern everyone is building. Per-group tool
scoping and a shared `tools/list` cache are mutually exclusive. The spec
sanctions per-authorization tool lists:

> This set **MAY** be empty and **MAY** change over time ... but **MUST NOT**
> vary per-connection or as a side effect of other requests on the connection.
> The set **MAY** vary by the authorization presented on the request — for
> example, returning only the tools the caller's granted scopes permit — since
> credentials are per-request input, not connection state.

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
(verified 2026-09-18). **[OFFICIAL]**

The moment a gateway filters the list per group, its own responses are
`private` and the shared-cache win is gone. What remains is a per-principal
cache, which still helps, and which is the thing to build. A gateway that
aggregates `public` upstream lists, filters them, and re-emits them as `public`
has built a cross-tenant disclosure of the tool catalogue.

Other caching mechanics a gateway operator needs:

- Pagination: each page carries its own `ttlMs`; "There is no cross-page
  consistency guarantee. If the underlying data changes between page fetches,
  clients may observe duplicates or gaps."
- Servers **MUST** apply the same `cacheScope` to every page of a given list
  request. An aggregating gateway merging backends with mixed scopes must
  therefore collapse to the strictest, which is `private`.
- `list_changed` invalidates a fresh cache immediately.
- Clients **SHOULD NOT** treat TTL as a polling interval; "Implementations that
  do choose to poll **MUST** apply jitter and backoff."

**[OFFICIAL]**, caching page.

### 3.3 Prompt-cache blast radius: the gateway change nobody budgets for

> Most providers cache the prompt prefix, including the `tools` array. Adding or
> removing tool definitions mid-conversation invalidates that cache, and the
> resulting miss can cost more tokens than the definitions you removed.

> Treat server disconnection as a conversation-boundary operation rather than a
> per-turn one.

Source: https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md
(verified 2026-09-18). **[OFFICIAL]**

Servers **SHOULD** return tools in deterministic order, because "Deterministic
ordering enables clients to reliably cache the tool list and improves LLM prompt
cache hit rates when tools are included in model context."
**[OFFICIAL]**, tools page.

For a gateway this is an operational rule with a cost attached. Adding a backend
to an aggregating gateway changes the `tools` array of every client currently
connected, which invalidates the provider-side prompt cache for every in-flight
conversation across the fleet. Merging backend lists in a non-deterministic
order does the same thing on every single call. A gateway that hot-reloads its
backend set is billing the whole organisation for the reload.

### 3.4 Connection and session handling now that sessions are gone

- No `Mcp-Session-Id`. A modern-only server "**SHOULD**" answer `405 Method Not
  Allowed` to GET or DELETE on the MCP endpoint, ignore `Mcp-Session-Id`, and
  ignore `Last-Event-ID`.
- One long-lived stream remains: the `subscriptions/listen` response stream.
  Servers are "encouraged to periodically emit an SSE comment line ... as a
  keep-alive. This keeps the connection from being closed by intermediaries or
  client idle timeouts during quiet periods."
- Servers **SHOULD** send `X-Accel-Buffering: no` on SSE responses so reverse
  proxies do not buffer.
- Closing the SSE response stream **MUST** be treated as cancellation of that
  request.
- "Resumable SSE streams via `Last-Event-ID` are not supported." AWS's
  operational translation: "Make tools idempotent. Clients re-issue broken
  calls."

Sources: streamable-http transport page **[OFFICIAL]**; AWS well-architected
post **[VENDOR]** (both verified 2026-09-18).

The gateway consequence: idle timeouts have to be reconciled across the load
balancer, the gateway and the compute tier for exactly one method, and the
keep-alive that protects it is a **SHOULD** on the server, not a guarantee. A
gateway operator should assume some backends do not emit it and set the
gateway's own keep-alive.

### 3.5 Observability

The spec documents W3C Trace Context propagation in `_meta` (`traceparent`,
`tracestate`, `baggage`) as SEP-414. Every response carries a required
`resultType` of `complete` or `input_required`, which AWS notes enables
"metrics, alarms, and AWS WAF rules without inspecting payloads."
Sources: https://modelcontextprotocol.io/specification/2026-07-28/changelog ,
AWS well-architected post (verified 2026-09-18). **[OFFICIAL]** / **[VENDOR]**

Protocol-level `Logging` is deprecated; AWS's guidance is "Log to `stderr` or
OpenTelemetry instead of protocol-level Logging" and move "log level into
per-request `_meta`". **[VENDOR]**

The OTel GenAI semantic conventions remain in Development with no stable
attribute names, per the companion architecture research. Anyone naming a span
or metric attribute on a slide should verify it against
`open-telemetry/semantic-conventions-genai` first.

The record that answers an audit question is one structured event per
authorization decision. Docker states the shape: "A structured event per
evaluation, tied to user and agent, streamed to your SIEM."
Source: https://www.docker.com/products/mcp-enterprise-gateway/
(verified 2026-09-18). **[VENDOR]**

TrueFoundry enumerates the fields: "timestamp, caller identity, MCP server
identifier, tool name, input parameters, response summary, policy decision".
**[VENDOR]**, same caveat.

### 3.6 HA, failure modes, and whether the gateway is a single point of failure

The honest answer is yes, and there is no published operating account that says
otherwise.

This research found no primary or peer-reviewed source describing an MCP
gateway's behaviour during its own outage, no published SLO, no failover
architecture, and no post-incident writeup. TrueFoundry says the gateway "scales
horizontally with ease" and does not describe failover. Docker, Kong, Agent
Router, agentgateway and ContextForge documentation describe multi-replica
deployment without describing degraded-mode behaviour. **[UNVERIFIED]** across
the board.

ContextForge is the only project publishing peer-failure mechanics, and only
for gateway-to-gateway federation: "Health checking with configurable intervals
(60s default) and failure thresholds". What happens to a request when a peer is
down is not documented.
Source: https://ibm.github.io/mcp-context-forge/architecture/
(verified 2026-09-18). **[VENDOR]**

The gap is officially acknowledged. The MCP Enterprise Interest Group, chartered
2026-04-13, lists in scope:

> **Scalability and Resilience**: Running MCP at enterprise scale across regions
> and availability zones. With the stateless core enabling horizontal scaling
> without sticky sessions, the focus is on failover, load distribution, and
> reliability for mission-critical deployments.

> **Gateway and Proxy Behavior**: ... With the move to a stateless protocol core
> in the 2026-07-28 release, the focus shifts from session affinity to gaps that
> persist in a stateless model: header and context propagation, authorization
> handoff across proxies, and policy enforcement at the gateway.

Its "Gateway Deployment Patterns Document" is listed as **Planned, Q3 2026**,
with champion **TBD**. As of 2026-09-18 it has not been published.
Source: https://modelcontextprotocol.io/community/interest-groups/enterprise.md
(verified 2026-09-18). **[OFFICIAL]**

A further structural note worth making to this room. Both the Enterprise IG
charter and the Interceptors WG charter reference a **"Gateways IG"** as a
related group. No charter page for a Gateways Interest Group appears in the
site index at `https://modelcontextprotocol.io/llms.txt` as of 2026-09-18; the
listed interest groups are auth, enterprise, enterprise-managed-authorization,
financial-services, primitive-grouping, security and tool-annotations, and
`/community/interest-groups/gateways` returns 404. **[MEASURED]**, 2026-09-18.
Two chartered groups are routing gateway questions to a group with no published
charter. That is a concrete, fixable gap and this audience is the group that can
fix it.

---

## 4. Policy enforcement

### 4.1 AuthZEN, and the COAZ profile for MCP tool authorization

The OpenID Foundation's Authorization API 1.0 reached Final Specification on
2026-01-11. It standardises the PEP-to-PDP wire protocol without defining a
policy language.
Sources: https://openid.net/authorization-api-1-0-final-specification-approved/ ,
https://openid.github.io/authzen/ (verified 2026-09-18). **[STANDARDS]**

On 2026-06-15 the WG approved two Working Group Drafts. COAZ, the AuthZEN
Profile for Model Context Protocol Tool Authorization:

> adds a profile for standardizing the mapping from different source information
> models into the AuthZEN Subject-Action-Resource-Context (SARC) structure

> metadata to allow different enforcement points such as API or AI Gateways,
> services meshes or downstream systems to know how to authorize requests
> against a compatible PDP

> enable Model Context Protocol tools to expose the authorization checks
> required to call a tool to bring a control to agentic workflows

AARP, the Access Request and Approval Profile, covers the case where "policy
cannot authorize an action yet, because a prerequisite must first be satisfied",
defining patterns for "requesting, tracking, satisfying, and re-evaluating these
prerequisites". Its framing is precise and useful:

> approval functions as an **input** to a decision; policy remains the
> decision-maker, evaluated at the moment of enforcement.

Source: https://openid.net/openid-foundation-advances-authorization-for-the-agent-era-with-new-authzen-working-group-drafts/
(verified 2026-09-18). **[STANDARDS]**

**Whether COAZ covers per-argument authorization is [UNVERIFIED].** The
announcement page does not say, and the draft specification text was not
retrieved in this pass. Do not assert it. What COAZ demonstrably does is let a
tool declare what authorization check it needs, so a gateway, a mesh and a
downstream service all ask the same PDP the same question. That is the
interoperability half of the M × N problem the Interceptors WG named.

**No published COAZ implementation was found.** **[UNVERIFIED]**

### 4.2 What the implementations actually support today

| Product | Granularity | Mechanism | Source | Label |
|---|---|---|---|---|
| **AWS AgentCore Policy** | User identity and tool input parameters; session-aware temporal conditions; provider signals | Cedar or Dogwood, default-deny, intercepts "all agent traffic through Amazon Bedrock AgentCore Gateways". Natural-language authoring "validates them against the tool schema, and uses automated reasoning to check safety conditions such as identifying policies that are overly permissive, overly restrictive, or contain conditions that can never be satisfied" | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html | [VENDOR] |
| **Agent Router** | Per backend and per tool, plus arbitrary request context | Rule matchers over `target` (backend/tool), `source` (JWT scopes and claims), and CEL over `request.mcp.backend`, `request.mcp.tool`, `request.mcp.params`, `request.headers`, parsed JWT | https://theagentrouter.ai/docs/capabilities/mcp/ | [VENDOR] |
| **agentgateway** | "fine-grained RBAC with CEL policy engine" | CEL, Rust data plane | https://github.com/agentgateway/agentgateway | [VENDOR] |
| **Docker MCP Enterprise Gateway** | "Allow and deny by server, tool, transport, and call, evaluated before anything runs" | Policy evaluated after IdP authentication and group resolution, before credential injection and routing | https://www.docker.com/products/mcp-enterprise-gateway/ | [VENDOR] |
| **Microsoft Agent Governance Toolkit** | Per-call, plus tool-definition scanning and response validation | "Declarative rules ... are evaluated deterministically before every tool invocation"; unified Rego/Cedar/YAML evaluation | https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/ | [VENDOR] |

`request.mcp.params` in Agent Router's CEL context is the clearest published
per-argument authorization available today, and it necessarily costs a body
parse. Section 2.2 is the trade.

AgentCore's automated reasoning over policy sets deserves a mention to this
audience for a reason that is not about AWS: it is the only published attempt to
answer "is this policy set coherent" rather than "does this call pass". At
hundreds of contributing teams that becomes the operative question.

### 4.3 What is not specified

Per-tool scope advertisement is still an open topic, not a specification. The
Authorization Interest Group re-chartered 2026-08-17 and carries as **Active**
threads:

- `#auth-wg-tool-scopes`: "Per-tool scope advertisement, step-up authorization,
  client-side scope accumulation"
- `#auth-wg-fine-grained-authz`: "Rich Authorization Requests (RFC 9396),
  structured denials, remediation hints", tracked as SEP-2643

In scope for the same group: "Delegated and agentic access: use cases for
on-behalf-of token exchange, downstream resource access, audience restriction,
and consent when an MCP client acts through chains of agents or tools."
Source: https://modelcontextprotocol.io/community/interest-groups/auth.md
(verified 2026-09-18). **[OFFICIAL]**

So a gateway authorizing per tool today is doing it with scopes the server did
not advertise for that purpose, or with vendor-specific rule syntax. Both work.
Neither is portable.

The spec is also clear that gateway policy does not discharge the server's
obligation. Servers **MUST** "Validate all tool inputs", "Implement proper
access controls", "Rate limit tool invocations" and "Sanitize tool outputs";
and servers that implement authorization **MUST** "verify all inbound requests"
and **MUST NOT** "treat possession of a state handle as authentication."
Sources: tools page and security best practices (verified 2026-09-18).
**[OFFICIAL]**

---

# Part 2: The registry

## 5. Running a private registry: what it actually costs

### 5.1 The official position, in the project's own words

Three statements, all load-bearing, all [OFFICIAL], all verified 2026-09-18 at
https://modelcontextprotocol.io/registry/about :

> The MCP Registry **does not** support private servers. Private servers are
> those that are only accessible to a narrow set of users. For example, servers
> published on a private network (like `mcp.acme-corp.internal`) or on private
> package registries ... If you want to publish private servers, we recommend
> that you host your own private MCP registry and add them there.

> Note that the official MCP Registry codebase is **not** designed for
> self-hosting, and the registry maintainers cannot provide support for this use
> case. If you choose to fork it, you would need to maintain and operate it
> independently.

> The MCP Registry is not intended to be directly consumed by host applications.
> Instead, host applications should consume other MCP registries, such as
> downstream marketplaces, via a REST API conforming to the official MCP
> Registry's OpenAPI spec.

The Registry Working Group charter, filed 2026-04-08, puts it beyond doubt by
listing it as **out of scope**:

> Any commitment to delivering an enterprise-ready or reusable registry
> implementation. The codebase supports this instance only and is not intended
> for external deployments.

Source: https://modelcontextprotocol.io/community/working-groups/registry.md
(verified 2026-09-18). **[OFFICIAL]**

That charter also shows the WG's own deliverable status. "Registry API v1 GA"
is **Ideating**, target **TBD**. "Cataloging specification support by clients
and sub-registry products" is **Ideating**, Q3 2026, champion TBD. The WG is
four people, led by Radoslav Dimitrov of Stacklok, with members from PulseMCP,
TeamSpark and Ravenmail, meeting 30 minutes weekly. **[OFFICIAL]**

An enterprise plan that says "we will run the official registry internally" is
proceeding against the project's stated guidance and against an explicit
charter exclusion. Say that from the stage; it is not a matter of opinion.

### 5.2 What implementing the contract actually requires

Smaller than people expect. The read contract is three endpoints.

| Endpoint | Method | Required? | Parameters |
|---|---|---|---|
| `/v0.1/servers` | GET | Required | `cursor`, `limit`, `search` (substring on name), `updated_since` (RFC3339), `version`, `include_deleted` (default false) |
| `/v0.1/servers/{serverName}/versions` | GET | Required | `include_deleted` |
| `/v0.1/servers/{serverName}/versions/{version}` | GET | Required | `include_deleted`; `version` accepts `latest` |
| `/v0.1/publish` | POST | Optional, may return `501` | Bearer JWT |
| `/v0.1/servers/{serverName}/versions/{version}` | PUT / DELETE | Optional, may return `501` | Bearer JWT |
| `/v0.1/servers/{serverName}/versions/{version}/status` | PATCH | Optional | Bearer JWT with publish/edit permission |
| `/v0.1/servers/{serverName}/status` | PATCH | Optional | Bearer JWT with publish/edit permission |

`serverName` and `version` **must** be URL-encoded; `io.modelcontextprotocol/everything`
becomes `io.modelcontextprotocol%2Feverything`. Read endpoints are
unauthenticated on the official instance. Auth for writes is "registry-specific
and may vary between implementations".
Sources: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/openapi.yaml ,
https://modelcontextprotocol.io/registry/registry-aggregators (verified
2026-09-18). **[OFFICIAL]**

The payoff for conforming, in the project's words: "Private MCP registries can
implement it as well to benefit from existing host application support."
**[OFFICIAL]**

**Three GET endpoints is not the cost.** Anyone can serve that in an afternoon.
The cost is everything in sections 6 and 7.

### 5.3 What `server.json` carries, and what it does not

Verified against the schema on 2026-09-18 at
https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/draft/server.schema.json
**[OFFICIAL]**

Present: `name` (reverse-DNS, exactly one forward slash), `description`,
`version`, `title`, `icons`, `websiteUrl`, `packages[]`, `remotes[]`,
`repository`, `$schema`, `_meta`.

Inside `packages[]`: `registryType` (npm, pypi, cargo, oci, nuget, mcpb),
`identifier`, `version`, `transport`, `environmentVariables`,
`packageArguments`, `runtimeArguments`, `fileSha256`.

Absent: approval status, owning team, on-call rotation, data classification,
cost centre, criticality, review date, and every other field an enterprise
catalogue needs.

**But status is real, and it is not in `server.json`.** A live probe of the
official API returns it in a registry-owned `_meta` namespace:

```
$ curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?limit=1"
{"servers":[{"server":{...},"_meta":{"io.modelcontextprotocol.registry/official":
{"status":"active","statusChangedAt":"2026-04-13T17:32:20.852269Z",
"publishedAt":"2026-04-13T17:32:20.852269Z","updatedAt":"2026-04-13T17:32:20.852269Z",
"isLatest":false}}}],"metadata":{"nextCursor":"ac.inference.sh/mcp:1.0.0","count":1}}
```

**[MEASURED]**, 2026-09-18.

That is the important architectural detail and it is widely missed. `server.json`
is the publisher's document. Everything operational lives in `_meta` under a
reverse-DNS key owned by whoever is serving the record. The registry docs
sanction exactly this for a subregistry:

> The subregistry OpenAPI spec allows subregistries to inject custom metadata via
> the `_meta` field. For example, a subregistry could inject user ratings,
> download counts, and security scan results ... We recommend that custom
> metadata be put under a key that reflects the subregistry (e.g.,
> `"com.example.subregistry/custom"`).

Source: https://modelcontextprotocol.io/registry/registry-aggregators
(verified 2026-09-18). **[OFFICIAL]**

So the mechanism for approval status, owning team and data classification
exists. What does not exist is a vocabulary. `com.acme.registry/custom` means
nothing to anyone but Acme, so a catalogue is not portable, not auditable
against a standard, and not migratable between platforms. That is the real gap,
and it is a naming problem, not a schema problem, which makes it exactly the
kind of thing a foundation can fix cheaply.

One hard constraint on the publish path: publisher-provided metadata under
`_meta.io.modelcontextprotocol.registry/publisher-provided` has "a 4KB size limit
(4096 bytes of JSON). Publishing will fail if this limit is exceeded."
Source: https://modelcontextprotocol.io/registry/faq.md (verified 2026-09-18).
**[OFFICIAL]**

### 5.4 Published private-registry implementations

| Implementation | Licence | What it gives you | Source | Label |
|---|---|---|---|---|
| **Azure API Center** | Commercial, Azure | MCP registry endpoint at `https://<name>.data.<region>.azure-apicenter.ms/workspaces/default/v0.1/servers`, note the matching `v0.1`. Remote servers (runtime URL plus environment) and local servers (package registry, name, version, runtime hint, runtime args). Per-server version lifecycle metadata. Auto-generated SSE and Streamable definitions. Portal with a built-in test console ("select a tool and then **Run tool**"). Sync from Azure API Management or a Git repository. Access management. Custom metadata mapped "into structured namespaces" that "appear in the `_meta` section of MCP server responses" | https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server (doc dated 2026-05-29, retrieved 2026-09-18) | [VENDOR] |
| **ToolHive Registry Server** | Apache 2.0 core | Self-hosted catalogue that "aggregates entries from Kubernetes clusters, Git repositories, API endpoints, and local files" behind "a standard MCP Registry API". Registry JSON schema "builds on the official MCP server schema and adds skills and publisher-provided metadata". Configurable sync policies. Helm, manual, or Operator deployment. "role-based access control and claims-based authorization", anonymous or OAuth | https://docs.stacklok.com/toolhive/guides-registry/ | [VENDOR] |
| **IBM ContextForge** | Apache 2.0 | Registry inside the gateway. "YAML-based catalog configuration with auto-health checking", 3600s TTL, 100 items per page default, peer federation with mDNS/Zeroconf or configured peers | https://ibm.github.io/mcp-context-forge/architecture/ | [VENDOR] |
| **Docker MCP Catalog** | Mixed | Curated public catalogue plus custom catalogues for a team or organisation; OCI-distributed (`mcp/docker-mcp-catalog`) | https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/ , https://github.com/docker/mcp-gateway | [VENDOR] |

Azure API Center is the only one publishing its registry endpoint shape, which
is why it is worth showing. ToolHive is the only Apache-2.0 self-hostable one
with a documented sync model. Note that the Registry WG is led by Stacklok, who
also build ToolHive; that is not a criticism, it is context a vendor-neutral
room should have.

---

## 6. Registry operations

### 6.1 Ingesting a curated subset from upstream

The documented shape:

> The MCP Registry provides an unauthenticated read-only REST API that
> aggregators can use to populate their data stores. Aggregators are expected to
> scrape data on a regular but infrequent basis (e.g., once per hour), and
> persist the data in their own data store. The MCP Registry **does not provide
> uptime or data durability guarantees**.

Incremental sync is `updated_since` in RFC3339, pagination is cursor-based via
`nextCursor`.
Source: https://modelcontextprotocol.io/registry/registry-aggregators (verified
2026-09-18). **[OFFICIAL]**

The preview caveat is stronger than most plans assume: "This preview of the MCP
Registry is meant to help us improve the user experience before general
availability and does not provide data durability guarantees or other
warranties."
Source: https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/
(verified 2026-09-18). **[OFFICIAL]**

**Scale of a cold mirror, measured.** A full paged walk of the live API at 100
records per page, `version=latest&include_deleted=true`, following `nextCursor`
to exhaustion, returned **33,830 distinct servers over 339 requests in 160.8
seconds**: 32,720 `active`, 761 `deleted`, 349 `deprecated`. A second walk
without the `version=latest` filter, which enumerates every version of every
server, was still advancing after 20,000 records and 200 requests.
**[MEASURED]**, 2026-09-18, commands in section 9.

Three things follow. A distinct-server mirror is a few hundred requests and
finishes in minutes, which is cheaper than most plans assume. A full
every-version mirror is an order of magnitude larger and must be resumable,
because the API carries no uptime or durability guarantee. And 2.2 per cent of
current entries are already `deleted`, with another 1.0 per cent `deprecated`,
so an ingest that does not read status on day one imports known-bad records at a
measurable rate.

### 6.2 Freshness and status propagation

> Server metadata is generally immutable, except for the `status` field which may
> be updated to, e.g., `"deprecated"` or `"deleted"`. We recommend that
> aggregators keep their copy of each server's `status` up to date.

> The `"deleted"` status typically indicates that a server has violated our
> permissive moderation policy, suggesting the server might be spam, malware, or
> illegal. Aggregators may prefer to remove these servers from their index.

**[OFFICIAL]**, aggregators page.

Immutability is genuinely useful and under-appreciated: "Once published, version
metadata is immutable (similar to npm)", and "The version string **MUST** be
unique for each publication of the server."
Sources: https://modelcontextprotocol.io/registry/faq.md ,
https://modelcontextprotocol.io/registry/versioning.md (verified 2026-09-18).
**[OFFICIAL]**

A compromised upstream publisher cannot silently rewrite a version you already
ingested. They must publish a new version string, which your ingest sees as a
new record. Version pinning therefore actually works here.

There is one sharp edge in the versioning rules a mirror must implement:

> If a server uses semantic version strings but publishes a new version that
> does *not* conform to semantic versioning, the new version will be marked as
> "latest" even if it would otherwise be sorted before the semantic version
> strings.

And the aggregator comparison rules are ordered: "latest" wins; then semver
comparison; then published timestamp; then a valid semver beats a non-semver.
**[OFFICIAL]**, versioning page. A mirror that sorts naively will resolve
`latest` differently from upstream, which is a silent divergence nobody notices
until a rollout goes to the wrong version.

### 6.3 Revocation, and what actually happens when an upstream server is withdrawn

This is the weakest link in the chain and it should be stated plainly.

**A publisher cannot withdraw a server.**

> Can I delete/unpublish my server? Currently, no.

**[OFFICIAL]**, registry FAQ, verified 2026-09-18. The referenced discussion,
registry issue #104 "Allow a reverse-publication flow", opened 2025-05-27, is
**closed**. The maintainer discussion notes that "some registries have a limit
(e.g. RubyGems only allows this for 30 days)" and that a separate mechanism
would be needed "for cases where sensitive data goes unnoticed beyond that
window".
Source: https://github.com/modelcontextprotocol/registry/issues/104 (verified
2026-09-18). **[OFFICIAL]**

**Removal is a status flip, and it does not delete anything.**

> When we remove a server, we set the server's `status` to `"deleted"`, but the
> server's metadata remains accessible via the MCP Registry API. Aggregators may
> then remove the server from their indexes.

> In extreme cases, we may overwrite or erase the server's metadata. For example,
> if the metadata itself is unlawful.

**[OFFICIAL]**, moderation policy, verified 2026-09-18.

**The moderation policy explicitly does not cover the case you care about.**

> The MCP Registry **does not** make guarantees about moderation, and consumers
> should assume minimal-to-no moderation.

What is removed: illegal content, malware, spam, non-functioning servers. What
is **not** removed:

> * Low-quality or buggy servers
> * **Servers with security vulnerabilities**
> * Servers that do the same thing as other servers
> * Servers that provide or contain adult content

**[OFFICIAL]**, moderation policy, emphasis added.

Put those together and the answer to "what happens when an upstream server is
withdrawn or compromised after I ingested it" is:

1. If it is malware or illegal, status flips to `deleted`. You learn about it on
   your next poll, which the docs suggest is hourly. There is no push, no
   webhook, no notification. **Your revocation latency is your poll interval.**
2. If it merely has a critical vulnerability, upstream will not change anything
   at all. The registry has explicitly declined that job. Your only signals are
   the underlying package registry's advisories and your own scanning.
3. The publisher has no way to pull it themselves.
4. Aggregators "may prefer" to remove deleted servers. **MAY**, not **MUST**.
   Nothing propagates a removal down a chain of registries, and a
   sub-sub-registry has no defined obligation at all.

The single most useful operational instruction from all of this: poll
`updated_since` frequently for status, because a status change updates
`updatedAt` and is therefore catchable by the incremental sync. An hourly full
scrape is the documented pattern, but a five-minute `updated_since` poll is
cheap and cuts revocation latency by an order of magnitude. That is a concrete
recommendation this research can make that no published source states.

### 6.4 Signing and trust propagation

There is none, in the protocol or the registry, today.

What exists is namespace authentication, which proves who published, not what
the code does. Reverse-DNS names tie to "verified GitHub accounts or domains",
with GitHub OAuth, GitHub OIDC, DNS verification and HTTP verification as the
four methods.
Sources: https://modelcontextprotocol.io/registry/about ,
https://github.com/modelcontextprotocol/registry (verified 2026-09-18).
**[OFFICIAL]**

Security scanning is delegated, deliberately and explicitly:

> The MCP Registry delegates security scanning to: **Underlying package
> registries** ... **Downstream aggregators** ... The MCP Registry focuses on
> namespace authentication and metadata hosting, while relying on the broader
> ecosystem for security scanning of actual server code.

**[OFFICIAL]**, registry about page.

The one integrity primitive that exists is `fileSha256` on a package entry.
**[OFFICIAL]**, server.json schema.

Work in flight, all of it early:

| Item | Status on 2026-09-18 | Source |
|---|---|---|
| SEP-2809, Attested Tool-Server Admission (ATSA): offline-signed clearance assertions at a well-known URI, verified against locally pinned trust roots before a host admits a server | **Draft** PR, opened 2026-05-28 | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2809 |
| Security IG, "Supply-chain integrity: protocol, registry, or companion standard" | **Open**, no champion | https://modelcontextprotocol.io/community/interest-groups/security.md |
| Security IG, "Tool identity across servers" | **Open**, no champion | same |
| SEP-2127, MCP Server Card | **Draft**, target Apr 3 2026, not shipped | https://modelcontextprotocol.io/community/working-groups/server-card.md |

**[OFFICIAL]** for all four.

The Server Card WG is worth watching for registry operators, because its whole
premise is a discoverable, standard-format document describing a server, which
is the natural carrier for attestation. Its charter keeps it deliberately
aligned: "Server Card format should stay as close as possible to a subset of
`server.json`; coordination required to avoid divergence." The Registry WG
charter names the same coordination as an active Q2 2026 work item. As of
2026-09-18 SEP-2127 is still Draft.
Source: https://modelcontextprotocol.io/community/working-groups/server-card.md
(verified 2026-09-18). **[OFFICIAL]**

### 6.5 Federation

**No federation model exists.** The only defined relationship between registries
is one-directional scraping: a downstream aggregator polls upstream and persists
its own copy. There is no defined protocol for trust between registries, no
signing chain, no revocation propagation guarantee, no conflict resolution when
two upstreams disagree, and no freshness contract.

The Registry WG charter claims "the sub-registry ecosystem that further
distributes server metadata" as in scope and lists "Active sub-registry
ecosystem consuming the official registry API" as a success criterion. Consuming
is the operative word. Nothing describes registries talking to each other.
**[OFFICIAL]**, registry WG charter.

The one published gateway-to-gateway federation is ContextForge's, which is a
product feature rather than a protocol: configured peers or mDNS/Zeroconf
auto-discovery, a Federation Sync service, Redis-backed caching for
multi-cluster, 60-second health-check intervals with failure thresholds.
Source: https://ibm.github.io/mcp-context-forge/architecture/ (verified
2026-09-18). **[VENDOR]**

---

## 7. The registry as an organisational object

### 7.1 The counter-evidence first, because it is the strongest evidence available

The largest published enterprise MCP rollout describes no approval gate at all,
and describes friction as the thing that was actually blocking adoption.

Block's account, as reported by All Things Open:

> Block already has 12,000 employees using them across 15 different job
> functions

within two months of operationalisation, and

> Within a month, 75 percent of engineers were saving 8 to 10 hours a week

The named barriers were all friction, not risk. Non-technical users "couldn't
install MCP servers independently", "lacked understanding of API keys", and
"couldn't locate needed tools".

The fixes were all distribution, not gating: Goose added to the internal software
centre for automatic deployment and updates; "They built over 100 internal MCP
servers bundled by default" rather than requiring external tool hunting; OAuth
with IdP integration replacing credential management with familiar SSO; dynamic
server enabling and disabling based on the query.

And on governance style:

> Community support drives adoption faster than mandates. Slack channels and
> consistent education unlocked usage across 15 job functions in just two months.

Block's stated reason for building internal servers was "security and control,
not distrust of open source options".
Source: https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions
(verified 2026-09-18). **[SECONDHAND]**, a conference-organiser write-up of a
Block talk rather than Block's own post.

Block's own engineering blog corroborates the scale and the design philosophy
without describing governance: "more than 60 MCP servers", the Linear MCP
collapsed from "30+ individual tools" to two query tools, three permission
levels in Goose ("Always Allow, Allow Once, and Denied") classified by read
versus write risk, 400kB output caps with actionable error messages.
Source: https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers
(verified 2026-09-18). **[PRIMARY]**

**No approval workflow, registry gate, or review board appears in either
account.** That absence is the finding, and it should be reported as an absence
rather than inflated into a claim that Block has no governance.

### 7.2 What a registry approval can and cannot mean

An approval in a registry is a claim about a `server.json` record at a moment in
time. Section 2.4 established that the protocol has no position on what happens
when the server's tools change afterwards; the Security IG carries "Runtime
drift: `list_changed` semantics after approval" as an **Open** item with no
champion. **[OFFICIAL]**

So approving a registry entry certifies the metadata, not the behaviour. An
approval process that believes otherwise is measuring the wrong thing. The
honest formulation for a slide: a registry approval is a supply-chain control,
and the runtime control is the gateway, and neither substitutes for the other.

### 7.3 Keeping it from becoming a bottleneck

Three published mechanisms, none of them a review queue:

1. **Approval as an input, not a gate.** AARP's framing: "approval functions as
   an **input** to a decision; policy remains the decision-maker, evaluated at
   the moment of enforcement." A registry that records approval state, and a
   policy engine that reads it at call time, decouples the human step from the
   request path. **[STANDARDS]**, Working Group Draft, June 2026.
2. **Default-allow with a curated bundle.** Block's 100+ servers bundled by
   default. **[SECONDHAND]**
3. **Tiering by what the server can reach**, which is the shape that emerges
   from the scope-minimisation guidance: a read-only tool and a destructive one
   in the same server need different treatment, and the spec's "Minimal initial
   scope set (e.g., `mcp:tools-basic`) containing only low-risk
   discovery/read operations" with step-up for the rest is the protocol's own
   version of that idea. **[OFFICIAL]**, security best practices.

The honest summary for the stage: the published evidence that approval gates
produce value in MCP deployments is absent, and the published evidence that
friction blocks adoption is specific and numeric. That asymmetry should shape
where an organisation spends its governance budget. It is not an argument
against having gates. It is an argument for measuring the cost of the ones you
build.

---

# Part 3: Edge cases and failure modes

## 8.1 Tool name collisions

The spec addresses this directly, to proxies, by name:

> Tool name uniqueness is scoped to a single server. Clients or proxies that
> aggregate tools from multiple servers **MAY** encounter naming collisions (for
> example, two servers each exposing a `search` tool) and **SHOULD** implement a
> disambiguation strategy such as prefixing tool names with a server identifier.

> The server `name` (from `serverInfo`) is not guaranteed to be unique across
> servers and **SHOULD NOT** be relied upon for disambiguation.

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
(verified 2026-09-18). **[OFFICIAL]**

Agent Router implements exactly the sanctioned strategy, with a double
underscore: `github__issue_read`, `context7__query-docs`. **[VENDOR]**

Three consequences that follow and that nobody documents:

- Tool names **SHOULD** be 1 to 128 characters. Prefixing spends part of that
  budget, and a long backend name plus a long tool name can exceed it.
- The prefix becomes an API. Rename a backend and every tool the model learned
  changes name, which invalidates prompt caches and breaks any client-side
  allowlist keyed on the old name.
- The `serverInfo` name is unusable for this, so the gateway must mint and own a
  stable backend identifier, and that identifier is now a piece of enterprise
  configuration with its own lifecycle.

## 8.2 A gateway that strips or rewrites something the client needed

Three distinct, spec-derived failure modes, all of which produce `-32020` or a
silently wrong result:

1. **Renaming a tool breaks header-body agreement.** The client sends
   `Mcp-Name: github__issue_read` and a body with `params.name` matching. A
   gateway that rewrites the body to `issue_read` for the backend, and forgets
   the header, gets `-32020 HeaderMismatch` from a conforming backend. It must
   rewrite both, consistently, including the Base64 sentinel form
   `=?base64?...?=` when the name is not header-safe. **[OFFICIAL]**
2. **A header allowlist drops `Mcp-Param-*`.** The spec is normative: "Intermediate
   servers that do not recognize an `Mcp-Param-{Name}` header **MUST** forward it
   and otherwise ignore it." Strip it and any tool using `x-mcp-header` fails.
   **[OFFICIAL]**
3. **Re-emitting a filtered list as `public`.** Covered in 3.2. This one does
   not error; it leaks. **[OFFICIAL]**

## 8.3 Version skew between gateway and servers

The compatibility matrix is published and unambiguous.
Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
(verified 2026-09-18). **[OFFICIAL]**

| Client | Server | Outcome |
|---|---|---|
| Modern | Modern | Works |
| **Modern** | **Legacy** | **Fails.** "The server may reject the request with an implementation-defined error, stay silent, or even process an era-ambiguous method under legacy semantics" |
| Dual-era | Modern | Works |
| Dual-era | Legacy | Works |
| **Legacy** | **Modern** | **Fails.** "Legacy clients have no fall-forward mechanism" |
| Legacy | Dual-era | Works |

A gateway fronting a mixed backend fleet must be dual-era on the backend side
and should be dual-era on the client side, because both failure rows are ones a
gateway can absorb.

The trap is in the caching rule:

> The era determination is a property of the server, not of an individual
> request. Clients **SHOULD** cache the result for the lifetime of the server
> process (stdio) or origin (HTTP), and **MAY** persist it across restarts of
> the same server configuration, re-probing if the cached assumption later
> fails.

**[OFFICIAL]**, versioning page.

A gateway that caches era per origin will get it wrong for a backend that
upgrades in place behind a shared hostname, and the wrong-answer mode for
Modern-to-Legacy includes "process an era-ambiguous method under legacy
semantics", which is a silent wrong answer rather than an error. Re-probe on
error is the spec's own escape hatch and a gateway must implement it.

**A live example of the skew.** Agent Router's MCP capabilities documentation,
retrieved 2026-09-18, describes its session handling as "Streamable HTTP with
persistent connections per June 2025 MCP spec", with "Unified sessions encode
multiple backend session IDs" and "'Last-Event-ID' support for SSE streams".
Those are `2025-03-26`-era mechanics that the current revision removed. This is
not a criticism of the project, which ships fast and is AAIF-hosted; it is a
demonstration that gateway documentation and the current spec revision can
diverge, and that a platform team must verify which revision its gateway speaks
rather than assuming the latest.
Source: https://theagentrouter.ai/docs/capabilities/mcp/ (retrieved
2026-09-18). **[VENDOR]**

## 8.4 Cross-server contamination

The spec's statement, again:

> Tool results from one server are untrusted input to another. The broker should
> apply the same input-review policy to brokered calls as to direct ones; output
> truncation alone does not prevent exfiltration.

**[OFFICIAL]**, client best practices.

The specific mechanism the spec worries about at the transport layer is SSRF
during OAuth discovery, where "A malicious MCP server can populate these fields
with URLs pointing to internal resources", including `http://169.254.169.254/`
and `http://localhost:6379/`, and where "The MCP client acts as a proxy,
bypassing network perimeter controls". The recommended mitigations are HTTPS
enforcement, blocking private IPv4 and IPv6 ranges plus `169.254.0.0/16`,
validating redirect targets, egress proxies, and DNS pinning against TOCTOU.
The spec adds a warning that applies to anyone tempted to hand-roll it: "Avoid
implementing IP validation manually. Attackers exploit encoding tricks (octal,
hex, IPv4-mapped IPv6) that custom parsers often miss."
**[OFFICIAL]**, security best practices.

A gateway that terminates and re-originates OAuth discovery on behalf of many
clients is the correct place to implement all of that once. That is a real,
concrete argument for the gateway that is stronger than the usual ones, and it
does not appear in any vendor's marketing.

## 8.5 Metering and cost attribution through a delegation chain

Unsolved, and the pieces that exist do not join.

- AgentCore logs "every enforcement decision ... through CloudWatch metrics and
  logs". **[VENDOR]**
- Kong captures "prompt and completion sizes flowing through MCP interactions,
  surfacing the context bloat that drives unnecessary LLM expenses". **[VENDOR]**
- agentgateway v1.5.0 added API-key-scoped budgets; Agent Router v1.1.0 added
  token counting across providers. **[VENDOR]**, per the companion architecture
  research.

What none of them does is join "this person asked for this outcome" to the whole
tree of model calls and tool calls that followed, across agents and sub-agents.
Budgets exist. Attribution does not. The Authorization IG has the underlying
primitive in scope as "Delegated and agentic access: use cases for on-behalf-of
token exchange, downstream resource access, audience restriction, and consent
when an MCP client acts through chains of agents or tools", and the Enterprise IG
names it as "identity lineage, least-privilege for child agents, descendant
revocation, and auditability across multi-agent chains". Both are Interest
Groups producing problem statements, not specifications.
Sources: auth IG and enterprise IG charters (verified 2026-09-18). **[OFFICIAL]**

Programmatic tool calling makes this harder rather than easier, because the
composition happens inside a sandbox and only `console.log` output crosses back.
**[OFFICIAL]**, client best practices.

## 8.6 What happens at rollout when hundreds of servers arrive at once

Three published findings that collide.

1. **The client cannot hold them.** Anthropic's figure for loading everything
   upfront versus progressive discovery: "This reduces the token usage from
   150,000 tokens to 2,000 tokens." The MCP client best practices page carries
   the same comparison and recommends switching to progressive discovery once
   tool definitions cross "a threshold as a percentage of the context window. For
   example, 1%-5%."
   Sources: https://www.anthropic.com/engineering/code-execution-with-mcp
   **[PRIMARY]**, client best practices **[OFFICIAL]**.
2. **The model cannot choose among them.** RAG-MCP's stress test, candidate pool
   scaled from 1 to 11,100: retrieval success above 90% for the first ~30
   positions, degrading through 31 to 70 from semantic overlap, degrading
   substantially beyond ~100. arXiv 2505.03275. **[PEER]**, via the companion
   operations research, which also documents that the widely circulated "43% to
   14% collapse" version of this finding reverses the paper's direction.
3. **The organisation still needs them available.** Block's answer was over 100
   internal servers bundled by default, with "dynamic server enabling/disabling
   based on queries". **[SECONDHAND]**

The synthesis, which is the operationally useful part: at rollout scale,
aggregation and filtering are the same problem. A gateway that presents 400
servers as one `tools/list` has produced a catalogue the agent measurably cannot
use. The gateway's job at that size is not to aggregate, it is to answer
`search_tools` well, and the spec's progressive-discovery pattern puts that
capability in the **host**, not the gateway. A platform team that has invested
in a gateway and finds the host doing the filtering has found a real
architectural question, not a bug.

Note also that progressive discovery's "Dynamic Server Management" pattern has
the host "Maintain a registry of available servers and their high-level
descriptions" and connect on demand. That registry is the private registry from
Part 2, consumed by the host. The two halves of the pattern meet there.
**[OFFICIAL]**, client best practices.

## 8.7 Ingest-time failure modes for a private registry

Collected from sections 5 and 6, stated as operational rules:

| Failure | Cause | Mitigation |
|---|---|---|
| Importing known-bad entries | `include_deleted` defaults to `false` on read but a cold mirror that ignores status still imports `deprecated` | Read `_meta["io.modelcontextprotocol.registry/official"].status` on every record |
| Revocation latency of hours | Hourly scrape is the documented pattern; there is no push | Poll `updated_since` every few minutes for status changes, scrape fully far less often |
| Divergent `latest` resolution | Non-semver versions are always marked latest; the documented comparison order is latest, then semver, then timestamp | Implement the published aggregator comparison rules exactly, do not sort naively |
| Silent metadata loss | Status and timestamps live in registry-owned `_meta`, not `server.json` | Preserve the upstream `_meta` namespace verbatim and add your own under your own key |
| Publish rejected at 4KB | `_meta.io.modelcontextprotocol.registry/publisher-provided` limit | Keep enterprise metadata in your registry's namespace, not the publisher's |
| Upstream unavailable mid-mirror | "does not provide uptime or data durability guarantees" | Resumable, cursor-checkpointed ingest; never a fresh full scrape as the only path |

**[OFFICIAL]** for every underlying fact; the table is this research's synthesis.

---

## 9. Verification ledger

**Measured on 2026-09-18.** The live registry probe:

```bash
curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?limit=1"
```
returned the `_meta["io.modelcontextprotocol.registry/official"]` block shown in
5.3. A paging loop following `nextCursor` to exhaustion over
`/v0.1/servers?limit=100&version=latest&include_deleted=true` returned 33,830
distinct servers across 339 requests in 160.8 seconds, with status counts
`active` 32,720, `deleted` 761, `deprecated` 349. The same loop without
`version=latest`, which enumerates every version of every server, was still
advancing after 20,000 records and 200 requests in 94.5 seconds and was stopped
at that cap, so 20,000 is a lower bound on total version records rather than a
total.

`https://modelcontextprotocol.io/community/interest-groups/gateways` returned
HTTP 404, and no Gateways IG charter appears in `llms.txt`, while both the
Enterprise IG and Interceptors WG charters reference a "Gateways IG".

**Verified against primary sources on 2026-09-18:** the Streamable HTTP
transport page including request metadata, `x-mcp-header`, server validation and
backward compatibility; the caching utility page; the tools page including
security considerations, tool names and `x-mcp-header`; the versioning page and
compatibility matrix; the security best practices page; the client best
practices page; the Enterprise-Managed Authorization extension page; the
registry about, FAQ, versioning, moderation-policy and aggregators pages; the
registry OpenAPI spec and `server.schema.json`; the Registry WG, Server Card WG,
Interceptors WG, Security IG, Enterprise IG and Authorization IG charters;
registry issue #104; SEP-2809's pull request; the OpenID Foundation AuthZEN
announcement; AWS AgentCore Policy documentation; the AWS well-architected
stateless post; Docker MCP Enterprise Gateway's product page; the Docker
MCP Gateway repository; Azure API Center's MCP documentation; ToolHive's
overview, registry-server and network-isolation docs; ContextForge's
architecture page; Agent Router's MCP capabilities page; Kong's Enterprise MCP
Gateway post; agentgateway's repository and spec-revision blog post; pgEdge's
transport-boundaries post; the Zuplo and Maxim shadow-MCP posts; TrueFoundry's
governance post; and the All Things Open and Block engineering accounts.

**Could not be verified in this pass, do not put on a slide as fact:**
- Whether AuthZEN COAZ covers per-argument authorization. The announcement page
  does not say and the draft text was not retrieved.
- Any COAZ implementation. None found.
- TrueFoundry's ~10ms / 350 RPS and MintMCP's 100 to 250 ms figures. Vendor
  self-reported, not independently reproduced.
- SEP-2809's "48 hermetic tests" and "27,000+ evasion attempts". Author's claim
  in a Draft PR.
- Any MCP gateway's behaviour during its own outage, any published SLO, and any
  failover architecture. Nothing found, from any source.
- ToolHive, ContextForge, Docker MCP Gateway and kgateway current version
  numbers. Not re-checked in this pass; see the companion architecture research.

**Absences worth stating from the stage, each verified as an absence:**
- No Gateways IG charter, while two chartered groups route work to it.
- No published Gateway Deployment Patterns Document; Planned for Q3 2026,
  champion TBD.
- No registry federation protocol, and none in any charter's scope.
- No unpublish mechanism, and the issue asking for one is closed.
- No standard vocabulary for approval status, owning team or data
  classification, though `_meta` is the sanctioned mechanism for carrying them.
- No conformance suite, benchmark, or third-party security audit for any MCP
  gateway.
- No named non-vendor enterprise has published its own MCP platform architecture
  with operating numbers.
