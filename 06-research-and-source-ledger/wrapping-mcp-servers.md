
# Wrapping an MCP server inside an MCP server: what it is, how it is done, why

## Question

What does it mean, technically, to wrap one MCP server inside another? How
are people doing it, what does it look like in practice, what does it achieve,
and why would anyone bother?

## Summary

A wrapper is an MCP server whose tools are not its own: when a client calls
`tools/list` or `tools/call`, it forwards the request to an upstream MCP
server and relays the answer back, doing something useful on the way through.
People build one for five reasons, in rough order of frequency in the sources:
to add authentication and authorization an upstream server lacks; to hold the
upstream credential so the client never sees it; to filter or rename the tool
list; to bridge transports (a stdio-only server exposed over HTTP, or a remote
HTTP server made available to a stdio-only client); and to log and rate-limit.
The mechanics are a few lines in FastMCP (`create_proxy`) or a Kubernetes
resource in ToolHive (`MCPRemoteProxy`). The hard part is the credential model:
the spec forbids forwarding the client's token upstream, so a correct wrapper
is an OAuth resource server on the client side and an OAuth client on the
upstream side, exchanging tokens in between.

## Surprises and gotchas

- **The wrapper may not pass the user's token through.** The specification
  says the server "MUST NOT pass through the token it received from the MCP
  client." A wrapper that just copies the `Authorization` header upstream is
  non-compliant and is the confused-deputy setup Obsidian Security found in
  the wild (one static `client_id` shared by every caller, consent cached, one
  click to account takeover). Prior keynote research, read 2026-09-18 and
  2026-10-02; spec text re-stated in SSOJet and Security Boulevard sources
  below.
- **FastMCP's proxy opens no upstream connection until a client initializes.**
  "Creating the proxy object and starting the local server do not contact the
  upstream server." A wrapper that appears healthy at startup can still be
  pointed at a dead upstream. Health-check the upstream separately.
- **Each proxied request gets its own upstream session by default**, and
  sharing one session across callers risks "context mixing in concurrent
  scenarios." The default is right; the shortcut for stateless backends
  (reuse one `ProxyClient`) is only safe when the backend really is stateless.
- **A proxied `tools/list` costs 300 to 400 ms against 1 to 2 ms locally** in
  FastMCP's own numbers, which is why it caches component lists (default TTL
  300 seconds). A wrapper that filters the tool list is also the layer that
  decides how stale that list may be.
- **Mixed revisions are now the wrapper's problem.** The 2026-07-28 revision
  removed sessions and the initialize handshake. A proxy fronting several
  upstreams has to negotiate the era per upstream; 1mcp's open issue of
  2026-08-23 scopes exactly that ("let each selected upstream negotiate
  independently while preserving proxy and configured transports") and flags
  credential leakage between inbound and outbound connections as a risk of
  getting it wrong.
- **No Reddit thread surfaced.** Two searches aimed at Reddit returned
  packages, vendor docs and blog posts, not discussion threads. The practice
  is documented by people shipping proxies, not by people asking how.

## Findings

### What "wrapping" is, mechanically

A wrapping server implements the MCP server side toward the client and the MCP
client side toward the upstream. FastMCP's description: "when it receives a
request (like `tools/call` or `resources/read`), it forwards that request to a
backend MCP server, receives the response, and then relays that response back
to the original client." Tools, resources and prompts are mirrored (with
optional name prefixing); sampling, elicitation, logging, progress and roots
are forwarded too, and each can be switched off. Mirrored components are
read-only copies; to change one, copy it locally first.

### Why people do it

| Reason | What the wrapper does | Who documents it |
|---|---|---|
| Authorization the upstream lacks | Validates an inbound OAuth token, evaluates a per-tool policy, then calls upstream with its own credential | ToolHive `MCPRemoteProxy` (OIDC client auth, Cedar policies, token exchange); Security Boulevard; the keynote's own finding that 40.55 percent of live servers measured had no authentication |
| Credential custody | Holds the upstream API key or OAuth refresh token so the client never sees it; "the proxy holding and refreshing the token for every caller" | TBXark mcp-proxy; Envoy AI Gateway ("upstream API key injection") |
| Tool filtering and renaming | Hides tools from `tools/list`, overrides names and descriptions, prefixes to avoid collisions across upstreams | mcpwrapped ("only exposing tools you explicitly want to use"); dpirate mcp-server-wrapper; ToolHive `toolConfigRef` ("filtering and overriding tools from the remote MCP server") |
| Transport bridging | Exposes a stdio server over HTTP, or a remote HTTP server to a stdio-only client | FastMCP (`transport` on `run()`); ToolHive CLI local proxy |
| Aggregation | One endpoint that fronts many upstreams and merges their catalogs | TBXark mcp-proxy; Envoy AI Gateway; 1mcp |
| Logging, audit, rate limiting, transforms | Records every call with inputs and outcome; throttles agent loops; sanitizes inputs | Fast.io middleware article; ToolHive `audit.enabled` |

### What a correct wrapper looks like

From the Security Boulevard piece (Parambir, 2026-04-09) and the ToolHive
resource, the compliant shape is:

1. Validate the inbound token against the authorization server's keys, with
   the wrapper itself as the audience.
2. Decide per tool, with the user, the agent, the tool and the arguments as
   inputs (Cedar in ToolHive, OPA in the article).
3. Exchange the validated token for an upstream credential (RFC 8693), scoped
   to the operation and audience-bound to the upstream, carrying the user as
   subject and the wrapper as actor.
4. Send only that credential upstream. Never the client's token.
5. Log the decision and the call, joined by trace context.

The keynote's "USB wrapped in USB" line is this: the upstream plug did not have
the pins the enterprise needs, so a second plug is fitted around it.

### How it is done in practice, by tool

- **FastMCP (Python).** `create_proxy(url_or_path_or_transport)` returns a
  server; `FastMCPProxy(client_factory=...)` for explicit session control.
  Session isolation per request by default; lazy upstream connection; cached
  component lists. The docs list "Act as a controlled gateway with
  authentication and authorization" as a use but do not show the auth wiring.
- **ToolHive (Kubernetes).** `MCPRemoteProxy` "fronts a remote MCP server
  (reachable over HTTPS) with the same authentication, telemetry, and
  tool-filtering features that the operator applies to containerized servers."
  OIDC via `spec.oidcConfigRef`, Cedar via `spec.authzConfig`, token exchange
  via `spec.externalAuthConfigRef` ("the proxy will exchange validated incoming
  tokens for remote service tokens"), audit via `spec.audit.enabled`, Redis
  session storage for replicas.
- **Envoy AI Gateway.** Aggregates servers behind one endpoint, applies OAuth
  and injects upstream API keys, filters tools (docs 0.4).
- **Small single-purpose wrappers.** mcpwrapped and dpirate's
  mcp-server-wrapper do one thing: proxy an existing server and expose a chosen
  subset of its tools, to keep the model's context small.
- **Nginx in front.** Fast.io's proxy guide shows plain reverse-proxying of the
  MCP and SSE endpoints with routing, rate limits and tenant isolation, which is
  a network proxy rather than an MCP-aware wrapper and cannot filter tools or
  exchange tokens.

### The spec-revision angle

Wrappers were already common before 2026-07-28. That revision raised the
stakes two ways. It made header-based routing possible (`Mcp-Method`,
`Mcp-Name`), so a wrapper can route and rate-limit without parsing bodies. And
it removed sessions, so a wrapper fronting an old-revision upstream now
translates between a stateless client side and a session-based upstream side.
1mcp's issue is the clearest public record of someone working through that.

## Recommendation

If the reason is authorization or credential custody, build the wrapper as a
real resource server with token exchange, using ToolHive or an equivalent
rather than a hand-rolled FastMCP proxy that copies headers. If the reason is
tool filtering or transport bridging only, FastMCP's `create_proxy` with a
filtered tool list is enough, and keep per-request session isolation on. In
either case, the wrapper's test is the keynote's gate-three question: does the
credential that reaches the upstream differ from the one the client sent?

## Caveats

- Sources are vendor documentation and vendor blogs (FastMCP, Stacklok,
  Envoy, Fast.io, Security Boulevard). Each is accurate about its own product
  and self-interested about why you need one.
- The 300 to 400 ms figure is FastMCP's own measurement, conditions unstated.
- No Reddit or forum threads were found with the searches run; the "how are
  people doing it" answer comes from shipped tools, not from discussion.
- The spec's token-passthrough sentence is quoted via secondary sources in
  this session; the spec page itself was last opened in the September research.

## Sources

- [FastMCP v3, Proxy servers](https://gofastmcp.com/v3/servers/providers/proxy.md): the proxy API, forwarding, session isolation, lazy connection, caching, latency figures
- [Stacklok ToolHive, MCPRemoteProxy reference](https://docs.stacklok.com/toolhive/reference/crds/mcpremoteproxy): OIDC, Cedar, token exchange, audit, tool filtering fields
- [Security Boulevard, "Your MCP Server Is a Resource Server Now. Act Like It."](https://securityboulevard.com/2026/04/your-mcp-server-is-a-resource-server-now-act-like-it/): token passthrough, delegation tokens, required proxy capabilities (2026-04-09)
- [1mcp-app/agent issue 478](https://github.com/1mcp-app/agent/issues/478): per-upstream era negotiation for 2026-07-28 (2026-08-23)
- [Fast.io, MCP Server Middleware](https://www.fast.io/resources/mcp-server-middleware.md): reasons for middleware; architectural pattern, no code (reviewed 2026-02-14)
- [Fast.io, MCP Server Proxy Setup](https://fast.io/resources/mcp-server-proxy/): Nginx reverse proxy in front of MCP (search result only)
- [TBXark/mcp-proxy](https://github.com/TBXark/mcp-proxy): aggregating proxy with OAuth client support (search result only)
- [Envoy AI Gateway, MCP capability](https://aigateway.envoyproxy.io/docs/0.4/capabilities/mcp/): aggregation, OAuth, upstream key injection, tool filtering (search result only)
- [mcpwrapped](https://glama.ai/mcp/servers/@VitoLin/mcpwrapped) and [dpirate/mcp-server-wrapper](https://jsr.io/@dpirate/mcp-server-wrapper/doc): single-purpose tool-filtering wrappers (search result only)
- Prior research for the keynote (September 2026): Obsidian Security's confused-deputy finding, Zhou et al.'s 40.55 percent, the spec's passthrough prohibition
