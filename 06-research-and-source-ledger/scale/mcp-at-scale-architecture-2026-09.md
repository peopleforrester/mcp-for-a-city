---
title: Running MCP at Enterprise Scale, Architecture and Tooling
date: 2026-09-17
sources_verified_on: 2026-09-17
status: draft
audience: MCP maintainers and enterprise platform engineers
---

<!-- ABOUTME: Verified survey of what it takes to run MCP across hundreds of servers and -->
<!-- ABOUTME: hundreds of thousands of users: registry, gateway, identity, policy, ops, observability. -->

# Running MCP at Enterprise Scale

> **Note added 2026-10-06, on publication:** The MintMCP figure of 100 to 250 ms gateway overhead is no longer at its cited URL; treat it as unsourced until it is found again.

Research input for the MCP Dev Summit Toronto keynote, 2026-10-06. Every project
claim below carries a source URL. Everything was checked against the live source
on 2026-09-17 unless the line says otherwise. Claims that could not be verified
are marked **UNVERIFIED** inline rather than dropped.

## 0. The finding that reframes the whole stack

The `2026-07-28` MCP specification revision removed protocol-level sessions and
the `initialize` handshake. MCP is now a stateless protocol.

Verbatim from the specification changelog:

> Remove protocol-level sessions and the `Mcp-Session-Id` header from the
> Streamable HTTP transport. List endpoints (`tools/list`, `resources/list`,
> `prompts/list`) no longer vary per-connection. Servers that need cross-call
> state use explicit, server-minted handles passed as ordinary tool arguments.

> Make MCP stateless: remove the `initialize`/`notifications/initialized`
> handshake. Every request now carries its protocol version and client
> capabilities in `_meta`.

Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog
(verified 2026-09-17).

Consequences that matter for the scale question, all of them traceable to the
spec text rather than to vendor commentary:

1. **Session affinity is gone as a protocol requirement.** Sticky sessions were
   the single biggest obstacle to running MCP servers as ordinary horizontally
   scaled HTTP workloads. A server that needs cross-call state now mints its own
   handle and receives it back as a tool argument, which is application state,
   not transport state.
2. **Routing and policy can happen at the HTTP layer.** The transport now
   requires `Mcp-Method` on every POST and `Mcp-Name` on `tools/call`,
   `resources/read` and `prompts/get`. The spec says these exist explicitly "so
   that intermediaries (load balancers, gateways, observability tooling) can
   route and inspect requests without parsing the body". Servers MUST reject a
   request whose headers disagree with the body, with error `-32020`
   `HeaderMismatch`. That closes the split-brain gap where a load balancer routes
   on a header and the server executes on the body.
   Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
3. **List responses became cacheable.** `tools/list`, `prompts/list`,
   `resources/list`, `resources/read` and `resources/templates/list` now carry
   required `ttlMs` and `cacheScope` (`"public"` or `"private"`) fields via a new
   `CacheableResult` interface. At fleet scale this is the difference between
   every agent turn re-listing every tool and a shared intermediary serving it.
4. **Resumability was removed.** `Last-Event-ID` and SSE event IDs are gone. A
   broken response stream loses the in-flight request and the client must
   re-issue it with a new request ID. This is a reliability property platform
   teams have to design around, not a detail.
5. **Server-initiated requests are gone.** Sampling, elicitation and roots are
   now folded into the Multi Round-Trip Requests (MRTR) pattern: the server
   returns an `InputRequiredResult` and the client retries the original request
   carrying `inputResponses`. There is no server-to-client request channel to
   keep open.
6. **Roots, Sampling and Logging are deprecated**, along with HTTP+SSE and OAuth
   2.0 Dynamic Client Registration. The spec adopted a feature lifecycle policy
   with a minimum twelve-month deprecation window and a registry of deprecated
   features. For a platform team, that policy is the planning input.

The talk framing this supports: the protocol moved toward the operational model
large enterprises already have, rather than enterprises building session
infrastructure to accommodate the protocol. AWS describes the same conclusion for
AgentCore Gateway, saying a single tool call is now "fully self-contained" and
that intermediaries can "route, throttle, and meter at the HTTP layer alone".
Source: https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/

**Caveat to state on stage:** statelessness is a property of the current spec
revision. Fleets will run mixed protocol versions for a long time, and
`2025-03-26` through `2025-11-25` servers still use `Mcp-Session-Id`, GET SSE
streams and `Last-Event-ID`. The spec documents the backward-compatibility
behavior (respond `405` to GET/DELETE, ignore `Mcp-Session-Id`, ignore
`Last-Event-ID`). The session-affinity problem is solved going forward and
present in the installed base.

---

## 1. The registry layer

### 1.1 The official MCP Registry

| Fact | Value | Source |
|---|---|---|
| Status | Preview. "Breaking changes or data resets may occur before general availability." | https://modelcontextprotocol.io/registry/about |
| API | REST, with a published OpenAPI spec other registries can implement | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/openapi.yaml |
| API freeze | v0.1 freeze declared, stated as being validated ahead of a v1 GA | https://github.com/modelcontextprotocol/registry |
| Metadata format | `server.json` | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/draft/server.schema.json |
| Backers named | Anthropic, GitHub, PulseMCP, Microsoft | https://modelcontextprotocol.io/registry/about |

Namespacing is reverse-DNS: `io.github.user/server-name` or `com.example/server`.
Ownership is proved by GitHub OAuth for `io.github.*` and by DNS or HTTP challenge
for a domain namespace. The registry deliberately does no security scanning of
server code; it delegates that to the underlying package registries and to
downstream aggregators, and it handles namespace authentication, character-limit
validation and manual takedown.

Four statements from the official registry documentation are load-bearing for any
enterprise architecture, and they are the ones most often missed:

1. **The official registry does not accept private servers.** A server on
   `mcp.acme-corp.internal` or in a private Artifactory npm registry is out of
   scope. The documented recommendation is: "we recommend that you host your own
   private MCP registry and add them there."
2. **The official registry codebase is not designed for self-hosting.** The
   documentation says the maintainers "cannot provide support for this use case"
   and that a fork must be maintained and operated independently. An enterprise
   plan that says "we will run the official registry internally" is proceeding
   against the project's own guidance.
3. **Host applications are not supposed to consume the official registry
   directly.** The intended shape is official registry to downstream aggregator
   or private registry to host application.
4. **The OpenAPI spec is the interoperability contract.** Private registries that
   implement it get existing host-application support for free. This is the
   actual mechanism by which an enterprise catalog plugs into IDEs and agents
   without every client needing bespoke integration.

So the vendor-neutral answer to "how do I run a private catalog" is not a fork.
It is: implement the published OpenAPI surface, ingest a curated subset of the
public registry, and add internal entries on top.

### 1.2 What private-registry products actually exist

**Azure API Center** is the most concretely documented enterprise private
registry, and it is worth showing because Microsoft publishes the endpoint shape.
API Center exposes an MCP registry endpoint at:

```
https://<api-center-name>.data.<region>.azure-apicenter.ms/workspaces/default/v0.1/servers
```

Note the `v0.1` in the path, which matches the official registry's frozen API
version. API Center supports registering remote servers (runtime URL plus an
environment) and local servers (package registry, package name, version, runtime
hint, runtime args), carries version lifecycle metadata per server, auto-generates
definitions, provides a portal with a built-in test console, and synchronizes from
Azure API Management or from a Git repository. Custom metadata properties can be
mapped into `_meta` namespaces returned to MCP clients.
Source: https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server
(doc dated 2026-05-29, retrieved 2026-09-17). Commercial, Azure-specific.

**ToolHive Registry Server** (Stacklok) is the open-source equivalent of the same
idea: a catalog for "discoverability, governance, publishing, or team-specific
access", with cluster-wide namespace scanning so one registry deployment can watch
`MCPServer` resources across namespaces for multi-tenant use. Apache 2.0.
Source: https://docs.stacklok.com/toolhive/ (page last updated 2026-09-11).

**Docker MCP Catalog** offers a curated public catalog plus custom catalogs for a
team or organization.
Source: https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/

**IBM ContextForge** ships a registry as part of the gateway rather than as a
separate product, maintaining unified catalogs of tools, prompts and resources.
Source: https://github.com/IBM/mcp-context-forge

### 1.3 The registry design questions an enterprise has to answer

These are not answered by any spec today, which makes them good talk material:

- **Ownership.** `server.json` carries a namespace, not an internal owning team,
  an on-call rotation or a cost center. Every enterprise is bolting this on with
  custom metadata (API Center's custom properties, ToolHive's labels).
- **Approval status.** There is no standard field for "approved for production",
  "approved for a named data classification" or "pending security review". The
  public registry deliberately has no opinion. Every private registry invents its
  own vocabulary, so a catalog is not portable between two enterprises.
- **Versioning and pinning.** `server.json` maps a version to a package. What is
  missing at fleet scale is a supported answer to "which version is this
  population of users allowed to resolve", which is a rollout problem, not a
  metadata problem.
- **Discovery scoping.** The registry API has no notion of "show this user only
  the servers their group may reach". Scoping is currently done either in the
  gateway or in a product-specific portal. Nothing standard.

---

## 2. The MCP gateway layer

### 2.1 Comparison table

Verified 2026-09-17. "Enforces" lists what the project's own documentation claims
it enforces at the MCP layer, not an independent evaluation.

| Project | License / model | Governance | Latest verified version | What it enforces for MCP | Vendor-neutral |
|---|---|---|---|---|---|
| **agentgateway** | Apache 2.0, open source | Agentic AI Foundation (Linux Foundation) | v1.5.0, 2026-08-27 (v1.6.0-alpha.1, 2026-09-14) | JWT / API key / OAuth auth, fine-grained RBAC via CEL policy engine, MCP tool federation, stdio + HTTP + SSE + Streamable HTTP, OpenTelemetry metrics/logs/tracing. Rust data plane. | Yes (foundation-hosted; originated at Solo.io) |
| **Agent Router** (formerly Envoy AI Gateway) | Apache 2.0, open source | Agentic AI Foundation, moved from CNCF/Envoy subproject on 2026-09-10 | v1.1.0, 2026-08-21 | `MCPRoute` and `MCPRouteSecurityPolicy` CRDs at `aigateway.envoyproxy.io/v1beta1`, per-tool authorization via JWT scopes/claims and CEL, tool filtering by exact match and regex, server multiplexing, header forwarding and renaming, OAuth per MCP spec, OTel tracing plus Prometheus metrics, MCP hostname routing | Yes (foundation-hosted) |
| **kgateway** | Apache 2.0, open source | CNCF Sandbox (accepted 2025-03-04), incubation application filed | Not verified in this pass. **UNVERIFIED** | Envoy-based Kubernetes Gateway API implementation; integrates agentgateway for MCP and A2A rather than implementing MCP itself | Yes (CNCF) |
| **IBM ContextForge / mcp-context-forge** | Apache 2.0, open source | IBM-led GitHub project, no foundation | 1.0.0 GA reached; 1.0.10 is the latest referenced release. Exact current tag **UNVERIFIED** | Gateway + registry + proxy in one. Virtual servers over REST/gRPC/A2A, federation with Redis-backed caching, 40+ plugins, JWT / OAuth / Basic / custom auth with user-scoped controls, rate limiting and retries, OTel to Phoenix/Jaeger/Zipkin, multi-replica Kubernetes multi-tenancy, Vault token injection | Open source but single-vendor-led |
| **ToolHive** (Stacklok) | Apache 2.0 core, commercial Stacklok Enterprise around it | Stacklok. No CNCF status found | v0.46.0, 2026-08-27 | Kubernetes Operator managing `MCPServer` lifecycle (pods, services, service accounts, RBAC), uniform security context, network access controls, secrets management, containerized isolation, vMCP aggregating gateway, registry server | Open core |
| **Docker MCP Gateway** | Open source (`docker/mcp-gateway`) | Docker | **UNVERIFIED** | Containerized MCP server orchestration, catalog integration | Open source, single vendor |
| **Docker MCP Enterprise Gateway** | Commercial | Docker | n/a | SSO through your IdP, per-group server and tool scoping, per-call allow/deny by server, tool, transport and call type, credentials injected at call time from your secret store rather than distributed in client configs, structured per-evaluation audit events to SIEM, org-wide revocation honored on next call. Deploys managed-in-your-VPC, air-gapped Kubernetes appliance, or Docker-managed SaaS (stated coming soon) | No, commercial |
| **Kong AI Gateway** | Commercial (paid plugins), Kong Gateway Enterprise or Konnect | Kong Inc. | AI Gateway 2.0 GA 2026-09-01; MCP gateway introduced in 3.12; MCP server bundling as of 3.14 | REST-to-MCP server generation, OAuth 2.1 per MCP spec, MCP server bundling (one route aggregating tools from multiple upstream servers, Kong performs the handshake), identity-aware AI policies, modality-aware cost accounting, tool-usage observability | No, commercial |
| **Microsoft Azure API Center + API Management** | Commercial (Azure) | Microsoft | API Center MCP registry endpoint at `v0.1`; REST-to-MCP exposure in APIM was announced as preview | Registry and discovery, portal, access management, sync from APIM and Git, `_meta` custom metadata; APIM provides the auth, access, logging and governance path | No, commercial |
| **AWS Bedrock AgentCore Gateway + Policy** | Commercial (AWS) | AWS | AgentCore Policy GA March 2026; Gateway supports MCP `2026-07-28` | Gateway speaks MCP and converts APIs and Lambda into MCP tools. Policy intercepts every tool call and evaluates Cedar policies, default-deny, conditions can reference tool parameters and the OAuth token. Multi-version advertisement, per-request version selection | No, commercial |
| **Lasso mcp-gateway** | MIT, open source | Lasso Security | **UNVERIFIED** (repo active, ~388 stars at check) | Plugin-based guardrails in three tiers: basic token/secret masking (GitHub, AWS, Hugging Face tokens), Presidio PII detection (credit cards, emails, phones, SSNs), and Lasso's own prompt-injection and data-leakage detection with custom policy | Open source, single vendor |
| **obot** | MIT core, self-hostable on Kubernetes, plus managed service | Obot AI | **UNVERIFIED** | Vendor claims tool-level (not just server-level) access control and per-invocation audit trails with full context | Open core, single vendor |
| **MintMCP** | Commercial SaaS | MintMCP | n/a | Vendor claims one-click deployment, OAuth protection, SOC 2 Type II attested governance, audit-ready logs, stdio-to-remote conversion. Vendor also states compliance scanning and deep inspection add 100 to 250 ms per request | No, commercial |

**Sources for the table**

- agentgateway: https://github.com/agentgateway/agentgateway ,
  https://github.com/agentgateway/agentgateway/releases ,
  https://agentgateway.dev/blog/2026-08-03-new-mcp-spec-revision/ , https://aaif.io/projects
- Agent Router: https://theagentrouter.ai/docs/capabilities/mcp/ ,
  https://theagentrouter.ai/blog/envoy-ai-gateway-is-now-agent-router/ ,
  https://theagentrouter.ai/release-notes/
- kgateway: https://www.cncf.io/projects/kgateway/ ,
  https://github.com/cncf/sandbox/issues/319 , https://github.com/cncf/toc/issues/1913
- ContextForge: https://github.com/IBM/mcp-context-forge ,
  https://github.com/IBM/mcp-context-forge/releases
- ToolHive: https://docs.stacklok.com/toolhive/ , https://docs.stacklok.com/toolhive/guides-k8s/
- Docker: https://github.com/docker/mcp-gateway ,
  https://www.docker.com/products/mcp-enterprise-gateway/
- Kong: https://konghq.com/blog/product-releases/enterprise-mcp-gateway ,
  https://konghq.com/blog/product-releases/kong-ai-gateway-2-0-agentic-ai
- Azure: https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server
- AWS: https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/ ,
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
- Lasso: https://github.com/lasso-security/mcp-gateway
- obot and MintMCP: vendor blogs, https://obot.ai/blog/best-mcp-gateways-engineering-teams/ ,
  https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp

### 2.2 The governance story is the headline, and it favours the LF room

Three facts that belong together on a slide:

1. **The Linux Foundation formed the Agentic AI Foundation (AAIF)**, anchored by
   Anthropic's MCP, Block's goose and OpenAI's AGENTS.md. Platinum members named
   in the announcement: Amazon Web Services, Anthropic, Block, Bloomberg,
   Cloudflare, Google, Microsoft and OpenAI.
   Source: https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
2. **AAIF now hosts six projects**: MCP, goose, AGENTS.md, agentgateway, A2A and
   Agent Router. Source: https://aaif.io/projects
3. **Envoy AI Gateway became Agent Router and moved from the CNCF Envoy
   subproject into AAIF on 2026-09-10**, keeping its API group
   (`aigateway.envoyproxy.io`), its `aigw` CLI, its container images and its Go
   module path. Only the product name changed.
   Source: https://theagentrouter.ai/blog/envoy-ai-gateway-is-now-agent-router/

So as of September 2026 the two most prominent vendor-neutral MCP gateways sit in
the same foundation as the protocol itself. That is a genuinely new situation and
it is the honest, non-salesy way to tell an LF audience that the governance
question has moved.

### 2.3 What a gateway actually has to do that a server cannot

Distilled from the enforcement columns above, the functions that are structurally
gateway-shaped rather than server-shaped:

- **Credential custody.** Docker Enterprise Gateway's model is the clearest
  statement: credentials are supplied at call time from the org secret store and
  never distributed in client configs. This is the only way to avoid a
  per-developer sprawl of long-lived tokens in `mcp.json` files.
- **Tool-level authorization.** Server-level allow or deny is not sufficient when
  one MCP server exposes both a read tool and a destructive one. Agent Router,
  AgentCore Policy, Docker Enterprise and obot all converged on per-tool
  granularity independently.
- **Aggregation and multiplexing.** agentgateway's tool federation, Agent Router's
  server multiplexing, ToolHive's vMCP, ContextForge's virtual servers and Kong's
  MCP server bundling are four independent implementations of the same shape:
  present one endpoint, aggregate many backends. This exists because context
  window pressure makes it uneconomic for a client to connect to 300 servers.
- **Revocation.** Docker states org-wide revocation is picked up on the next call.
  Revocation is impossible to implement at the server layer when credentials live
  on laptops.
- **Audit at the call, not at the session.** A structured event per tool-call
  evaluation, carrying user identity, agent identity and the rule applied.

---

## 3. The AI gateway layer (governed inference path)

This is a separate hop from the MCP gateway and is often conflated with it. The
MCP gateway governs which tool an agent may call. The AI gateway governs which
model an agent may call, with which credential, at what cost.

| Project | License / model | Current state, verified 2026-09-17 | Source |
|---|---|---|---|
| **Agent Router** | Apache 2.0, AAIF | v1.1.0 (2026-08-21) added token counting across providers, per-request upstream credentials, stream idle timeout with failover, CEL backend selection, optional OTel GenAI tracing, HTTP CONNECT egress. Does both AI gateway and MCP gateway in one data plane. | https://theagentrouter.ai/release-notes/ |
| **agentgateway** | Apache 2.0, AAIF | v1.5.0 (2026-08-27) introduced API-key-scoped budgets and model access, native Gemini APIs | https://github.com/agentgateway/agentgateway/releases |
| **Kong AI Gateway** | Commercial | 2.0 GA 2026-09-01. Split from Kong Gateway 3.x with its own runtime, control plane, admin API and version line. Identity-aware AI policies and modality-aware cost accounting. | https://konghq.com/blog/product-releases/kong-ai-gateway-2-0-agentic-ai |
| **LiteLLM** | Open source (proxy + SDK), commercial Enterprise tier | 100+ providers behind one OpenAI-compatible API. Budgets and virtual keys in open source; SSO/SAML, org and team RBAC, SCIM, audit logs and enterprise guardrails gated behind the Enterprise license. Exact current version **UNVERIFIED**. | Vendor comparisons, not primary. Treat version claims as unverified. |
| **Portkey** | Commercial | **Acquired by Palo Alto Networks, completed May 2026**, being folded into Prisma AIRS. Relevant because a fleet standardizing on Portkey in 2026 is standardizing on a security vendor's platform. Verify before citing on stage. | Secondary sources only. **UNVERIFIED against a primary Palo Alto or Portkey announcement.** |
| **AWS Bedrock AgentCore** | Commercial | Runtime, Gateway and Policy. Policy GA March 2026. | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html |

The architecturally interesting point: agentgateway and Agent Router both collapse
the AI gateway and the MCP gateway into a single data plane. Kong keeps one
governance layer across APIs, events, LLM calls, MCP tool access and A2A. The
industry is converging on one policy enforcement point for both the model hop and
the tool hop, which is the right answer for an enterprise that has to answer
"what did this agent do" as a single question.

**Do not overstate token governance.** Budgets and per-key limits are widely
implemented. What is not solved anywhere is attributing spend to a *person*
through an *agent* through a *delegation chain*, which is section 9.

---

## 4. Identity for agents

### 4.1 What the MCP spec itself now requires

The `2026-07-28` authorization spec is the baseline and it is more prescriptive
than people assume.
Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization

- MCP server is an **OAuth 2.1 resource server**; MCP client is an OAuth 2.1
  client. The authorization server is explicitly out of scope, which is what makes
  enterprise IdP integration possible.
- Servers **MUST** implement RFC 9728 Protected Resource Metadata. Clients **MUST**
  use it for authorization server discovery.
- Authorization servers **MUST** provide RFC 8414 metadata or OpenID Connect
  Discovery 1.0. Clients **MUST** support both.
- Clients **MUST** implement RFC 8707 Resource Indicators, sending `resource` in
  both authorization and token requests, using the canonical MCP server URI, and
  **MUST** send it regardless of whether the AS supports it.
- Servers **MUST** validate that tokens were issued specifically for them as
  audience, and **MUST NOT** accept or transit any other tokens. Token passthrough
  is explicitly forbidden.
- **Client ID Metadata Documents** (`draft-ietf-oauth-client-id-metadata-document-00`)
  are now the preferred registration mechanism. **Dynamic Client Registration
  (RFC 7591) is deprecated** and retained only for backward compatibility.
- RFC 9207 `iss` validation is now **SHOULD** for servers and **MUST** for clients
  when present, with a stated intention to upgrade to MUST in a future revision.
- Step-up authorization via `WWW-Authenticate` with `error="insufficient_scope"`
  and a `scope` parameter, with the client responsible for computing the union of
  previously requested and newly challenged scopes.

The DCR deprecation is the single most under-appreciated operational change. Every
enterprise MCP deployment built in 2025 on dynamic client registration is now on
a deprecated mechanism with a twelve-month minimum window.

### 4.2 Delegation and cross-app access, the real work

**Identity Assertion JWT Authorization Grant (ID-JAG), informally Cross-App Access
(XAA).** An IETF OAuth working group document,
`draft-ietf-oauth-identity-assertion-authz-grant`. It lets an enterprise IdP
mediate the connection between two applications: the client presents a short-lived
IdP-signed JWT asserting it is authorized to act for a named user at a named
resource app, and exchanges it for an access token using RFC 8693 Token Exchange
and RFC 7523 JWT profile. This is the standards answer to "an agent acts for a
person without a consent screen per app".

- Spec: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-assertion-authz-grant
- Overview: https://oauth.net/cross-app-access/
- Reached draft -04 as an adopted OAuth WG document in May 2026; Okta began rolling
  it out to customers in August 2026. Named requesting apps include Claude, Cursor,
  Docker, VS Code and Zoom; named resource apps include Asana, Atlassian, Canva,
  Datadog, Figma, Glean, Granola, Linear, Serval, Slack, Supabase, Zoom.
  **The draft number, the dates and the app lists come from secondary sources
  (Okta developer blog and a landscape report) and should be re-verified against
  the IETF datatracker page before going on a slide.** Marked **PARTIALLY
  VERIFIED**.
- agentgateway ships a `traffic-cross-app-access` example, which is a useful
  concrete demonstration that this is implementable today:
  https://github.com/agentgateway/agentgateway/tree/main/examples/traffic-cross-app-access

**Workload identity: SPIFFE/SPIRE and WIMSE.** The consensus split is that SPIFFE
answers "what is this workload" and OAuth answers "what may it touch on whose
behalf". SPIFFE/SPIRE is CNCF-graduated and gives attestation-based short-lived
credentials rather than static secrets. SPIRE agents verify environmental
attributes before issuing a SPIFFE ID.
Source: https://spiffe.io/docs/latest/spire-about/spire-concepts/

IETF **WIMSE** (Workload Identity in Multi-System Environments) is the emerging
formal standard, and it is genuinely draft:

| Document | Status | Source |
|---|---|---|
| `draft-ietf-wimse-arch-07` | WG review, March 2026. Architecture, vocabulary, threat model | https://datatracker.ietf.org/doc/draft-ietf-wimse-arch/ |
| `draft-ietf-wimse-workload-creds-02` | July 2026, expires 2027-01-03. Defines the Workload Identity Token (WIT) | https://datatracker.ietf.org/doc/draft-ietf-wimse-workload-creds/ |
| `draft-ietf-wimse-wpt-01` | Workload Proof Token, proof of possession of the WIT private key | https://datatracker.ietf.org/doc/draft-ietf-wimse-wpt/ |
| `draft-ietf-wimse-http-signature-03` | Workload-to-workload auth with HTTP signatures | https://datatracker.ietf.org/doc/html/draft-ietf-wimse-http-signature-03 |

The motivating claim for WIMSE over plain SPIFFE is replay: an X.509-SVID or
JWT-SVID presented as a bearer credential can be replayed by anything that touches
it, and WPT binds proof of possession. Expect architecture to reach RFC across
2026 to 2027. **That timeline is an expectation reported in secondary sources, not
an IETF commitment. UNVERIFIED.**

### 4.3 What is real versus draft, stated plainly

| Thing | Status on 2026-09-17 |
|---|---|
| OAuth 2.1 for MCP (RFC 9728, RFC 8414, RFC 8707, RFC 9207) | **Real and normative in the MCP spec.** Deploy today. |
| Client ID Metadata Documents | IETF draft-00, but already **SHOULD** in the MCP spec |
| RFC 7591 Dynamic Client Registration | **Deprecated** in MCP as of 2026-07-28 |
| RFC 8693 Token Exchange | Published RFC, widely implemented |
| ID-JAG / Cross-App Access | **IETF draft**, adopted WG document, early commercial rollout |
| SPIFFE / SPIRE | **Real**, CNCF graduated, production-proven for workloads |
| WIMSE WIT / WPT | **IETF drafts**, not yet RFC |
| AuthZEN Authorization API 1.0 | **Final OpenID specification, approved January 2026** |
| AuthZEN COAZ (MCP tool authorization profile) | **Working Group Draft**, approved 2026-06-15 |
| AuthZEN AARP (access request and approval) | **Working Group Draft**, approved 2026-06-15 |

---

## 5. Policy and authorization engines applied to tool calls

### 5.1 AuthZEN is the sleeper story

The OpenID Foundation's **Authorization API 1.0 became a Final Specification on
2026-01-11**. It standardizes the wire protocol between a Policy Enforcement Point
and a Policy Decision Point without defining a policy language, so a PEP can talk
to a PDP backed by Cedar, Rego, XACML/ALFA, a Zanzibar-style engine or plain ACLs
without custom integration.
Sources: https://openid.net/authorization-api-1-0-final-specification-approved/ ,
https://openid.github.io/authzen/

On 2026-06-15 the AuthZEN WG approved two new Working Group Drafts:

- **COAZ, the AuthZEN Profile for Model Context Protocol Tool Authorization.**
  It standardizes how information models map into AuthZEN's
  Subject-Action-Resource-Context structure via metadata, so an API gateway, an AI
  gateway, a service mesh or a downstream system all interpret a tool's
  authorization requirements the same way. The stated initial implementation
  target is exactly MCP tool invocation in agentic workflows.
- **AARP, the Access Request and Approval Profile.** It handles the case where a
  decision cannot be reached until a prerequisite is satisfied: approval, consent,
  delegated authority, an attestation, a risk assessment or additional
  justification. It is an asynchronous authorization model analogous to
  Client-Initiated Backchannel Authentication.

Source: https://openid.net/openid-foundation-advances-authorization-for-the-agent-era-with-new-authzen-working-group-drafts/

AARP is the standards shape of human-in-the-loop approval for agent actions, which
is a thing every enterprise is currently building by hand in a chat bot. Worth
flagging to this audience precisely because it is early enough to influence.

### 5.2 Cedar

- **Amazon Bedrock AgentCore Policy reached GA in March 2026** using Cedar. It sits
  inside the Gateway, intercepts every agent-to-tool call, and evaluates against
  Cedar policies that can be authored in Cedar or generated from natural-language
  statements. Default-deny: if no policy matches, Cedar returns DENY. Conditions
  can reference tool parameters and the OAuth token.
  Sources: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html ,
  https://aws.amazon.com/blogs/security/why-policy-in-amazon-bedrock-agentcore-chose-cedar-for-securing-agentic-workflows/
- Cedar's design properties that matter for tool authorization: deliberately
  constrained grammar, default-deny, forbid-wins-over-permit, order-independent
  evaluation, no side effects. Those make policy sets compositionally analyzable,
  which matters when hundreds of teams contribute policy.
  Source: https://cedarpolicy.com/

### 5.3 OPA / Rego and Kyverno

- OPA/Rego is the incumbent and is being applied to agent tool loops as an external
  decision point. Reported policy evaluation overhead is sub-millisecond per call
  for typical rule sets. **That number comes from secondary sources and is
  UNVERIFIED.**
- **Kyverno graduated in the CNCF on 2026-03-24**, announced at KubeCon +
  CloudNativeCon North Europe in Amsterdam. The graduation announcement states
  directly that "Upcoming releases will focus on extending policy enforcement to
  additional control points across the cloud native stack, including support for
  artificial intelligence and Model Context Protocol (MCP) gateways."
  Source: https://www.cncf.io/announcements/2026/03/24/cloud-native-computing-foundation-announces-kyvernos-graduation/

That Kyverno sentence is a good, citable, vendor-neutral data point that MCP
governance is arriving in the CNCF policy layer rather than only in products.

- Microsoft publishes an Agent Governance Toolkit that evaluates Rego files, Cedar
  statements and YAML documents through a single `PolicyEvaluator.evaluate()` call.
  Source: https://microsoft.github.io/agent-governance-toolkit/tutorials/08-opa-rego-cedar-policies/
- Nirmata (Kyverno's commercial sponsor) published an integration of Okta Cross-App
  Access / ID-JAG into its AIControls product, which is one of the few concrete
  ID-JAG-plus-policy implementations in public.
  Source: https://nirmata.com/2026/08/18/okta-cross-app-access-xaa-id-jag/

### 5.4 The division of labour that works

- **Kyverno / OPA Gatekeeper** at Kubernetes admission: which MCP server workloads
  may exist at all.
- **Cedar or Rego behind an AuthZEN PDP** at the gateway: which tool call is
  permitted, for which subject, with which arguments.
- **The MCP server's own authorization**: the spec is explicit that servers "MUST
  verify all inbound requests" and "MUST NOT treat possession of a state handle as
  authentication". Gateway policy does not remove the server's obligation.

---

## 6. Deployment mechanics at scale

### 6.1 Statelessness changed the scaling model

Covered in section 0 and it is the answer to the session-affinity question. On the
current spec revision:

- No `Mcp-Session-Id`, so no sticky routing requirement.
- Every POST is independently routable; `Mcp-Method` and `Mcp-Name` are required
  headers so an L7 proxy can route, throttle and meter without body parsing.
- Header and body must agree, enforced server-side with `-32020`, which removes the
  class of bug where the proxy and the server disagree about what the request is.
- The one long-lived connection left is the `subscriptions/listen` response stream,
  which clients opt into per notification type. Servers are encouraged to emit SSE
  comment keep-alives so intermediaries do not close it.
- Servers SHOULD send `X-Accel-Buffering: no` on SSE responses so reverse proxies
  do not buffer.
- No stream resumability: a dropped stream means the client re-issues the request
  with a new ID. Design idempotency into tools accordingly.

### 6.2 Kubernetes as the substrate

ToolHive's operator is the clearest published pattern: an `MCPServer` custom
resource whose controller provisions pods, services, service accounts and RBAC,
enforces a uniform security context, applies network access controls and secrets
management, and cleans up on delete. Cluster-wide namespace scanning (February 2026
release) lets one registry deployment watch `MCPServer` resources across many
namespaces for multi-tenancy.
Source: https://docs.stacklok.com/toolhive/guides-k8s/

ContextForge documents multi-replica Kubernetes deployment with Redis-backed
federation caching and Vault token injection.
Source: https://github.com/IBM/mcp-context-forge

### 6.3 Admission control and shadow MCP

"Shadow MCP" is the named problem: employees running MCP servers with no platform
oversight, giving agents reach into production systems. The closed-loop pattern
being published is: the registry is the allowlist, and anything not in the registry
is by definition unsanctioned, detected at admission (Kyverno or Gatekeeper) and at
runtime (egress policy at the gateway).
Sources: https://zuplo.com/blog/how-to-avoid-shadow-mcp-servers ,
https://aquilax.ai/blog/mcp-security-shadow-ai-agents (both vendor blogs; the
pattern is well described, the incident claims in them are **UNVERIFIED**).

GitOps for the control plane is standard CNCF practice rather than anything
MCP-specific: Argo CD plus Kyverno, with Kyverno policies as the admission gate on
what Argo is allowed to sync.
Source: https://www.cncf.io/blog/2026/04/02/gitops-policy-as-code-securing-kubernetes-with-argo-cd-and-kyverno/

### 6.4 Secrets

The pattern every serious implementation converged on: **credentials never reach
the client config.** Docker Enterprise Gateway injects from your secret store at
call time. ContextForge supports Vault token injection including for A2A agents
exposed as MCP tools. ToolHive handles secrets through the containerized runtime.
The MCP spec supports this direction by forbidding token passthrough and requiring
audience validation, which means the gateway must mint or exchange, not forward.

### 6.5 Multi-tenancy

Three separable tenancy questions, and no single project solves all three:

1. **Server tenancy.** One MCP server instance per tenant, or one instance serving
   many tenants. ToolHive's namespace model and ContextForge's multi-replica
   deployment address the first. The second is left to the server author.
2. **Catalog tenancy.** Which tenant sees which servers. Handled per-product
   (API Center access management, ToolHive team-specific access), never portably.
3. **Policy tenancy.** Whose policies apply. Cedar and Rego both support this; the
   MCP layer has no opinion.

---

## 7. Observability

### 7.1 The spec now carries trace context

Minor change 2 in the `2026-07-28` changelog: the spec documents OpenTelemetry
trace context propagation conventions for `_meta` keys, specifically
`traceparent`, `tracestate` and `baggage` (SEP-414). This is the primary,
verifiable fact: distributed tracing across the agent-to-gateway-to-server-to-API
path is now a documented protocol convention rather than a per-vendor hack.
Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog

### 7.2 The OTel GenAI conventions are not stable, and that matters

| Fact | Detail | Source |
|---|---|---|
| Repo split | GenAI conventions moved out of the core semantic-conventions repo into `open-telemetry/semantic-conventions-genai` at v1.42.0, June 2026. MCP conventions moved with them. | https://github.com/open-telemetry/semantic-conventions-genai |
| Stability | Development. As of July 2026, no GenAI-specific span, event, metric or attribute in the dedicated repo is marked Stable. | https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/ |
| Versioning | The dedicated repo has no releases or version tags. The last versioned GenAI release is v1.42.0 from the main repo, which makes pinning a schema URL awkward. | same |
| MCP alignment | There is an open issue to align the MCP semantic conventions with protocol `2026-07-28` and expose peer server implementation metadata. | https://github.com/open-telemetry/semantic-conventions-genai/issues/437 |

The claim that OpenTelemetry defines `mcp.client` and `mcp.server` spans plus four
MCP metrics, and recommends them instead of the RPC semantic conventions, appears
in secondary reporting. The specific span names, attribute names and metric names
are **UNVERIFIED**; the docs path could not be resolved in this pass. Verify
directly against the `docs/` tree of `semantic-conventions-genai` before putting
any attribute name on a slide.

### 7.3 What to actually collect at fleet scale

Synthesized from what the gateways emit, not from a spec:

- **One structured event per tool-call authorization decision**, carrying user
  identity, agent identity, server, tool, decision and the rule that produced it.
  Docker Enterprise Gateway and obot both describe exactly this, and it is the
  record that answers an audit question.
- **Per-tool metrics, not per-server.** Agent Router shipped per-tool
  observability as a stable primitive in v1.0. Server-level aggregates hide the
  one destructive tool inside an otherwise benign server.
- **Trace context propagated through `_meta`** so an agent turn, a gateway hop, a
  tool call and the downstream API call join into one trace.
- **Token and cost attribution** at the AI gateway hop (Agent Router v1.1.0 token
  counting, Kong modality-aware cost accounting, agentgateway API-key-scoped
  budgets).
- **Protocol version distribution across the fleet.** New, and specific to this
  moment: with `MCP-Protocol-Version` required on every POST, a gateway can report
  exactly what fraction of traffic is still on pre-stateless revisions. That is the
  migration dashboard, and it is free.

Practical warning worth saying out loud: the GenAI vocabulary is a moving target,
so pin the version you build on and expect churn.

---

## 8. Reference architectures published by credible parties

| Publisher | What it covers | URL |
|---|---|---|
| Anthropic / MCP project | Registry architecture and the ecosystem diagram: official registry to aggregators and private registries to host applications | https://modelcontextprotocol.io/registry/about |
| MCP project | Security best practices: confused deputy, token passthrough, SSRF, state handle hijacking, local server compromise, mix-up attacks, scope minimization | https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices |
| AWS | AgentCore Gateway on MCP `2026-07-28`, stateless implications for scaling and HTTP-layer routing | https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/ |
| AWS | Why AgentCore Policy chose Cedar for agentic workflows | https://aws.amazon.com/blogs/security/why-policy-in-amazon-bedrock-agentcore-chose-cedar-for-securing-agentic-workflows/ |
| Microsoft | Private MCP registry with Azure API Center, including the registry endpoint shape and APIM integration | https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server |
| Microsoft | Securing MCP, a control plane for agent tool execution | https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/ |
| Microsoft | Agent Governance Toolkit, unified OPA/Rego/Cedar/YAML policy evaluation | https://microsoft.github.io/agent-governance-toolkit/tutorials/08-opa-rego-cedar-policies/ |
| CNCF | Kyverno graduation, with the stated MCP gateway roadmap | https://www.cncf.io/announcements/2026/03/24/cloud-native-computing-foundation-announces-kyvernos-graduation/ |
| CNCF | GitOps policy-as-code with Argo CD and Kyverno | https://www.cncf.io/blog/2026/04/02/gitops-policy-as-code-securing-kubernetes-with-argo-cd-and-kyverno/ |
| OpenID Foundation | Authorization API 1.0 Final, plus COAZ and AARP drafts | https://openid.net/wg/authzen/specifications/ |
| IETF OAuth WG | Identity Assertion JWT Authorization Grant | https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-assertion-authz-grant |
| IETF WIMSE WG | Workload identity architecture, credentials, proof tokens | https://datatracker.ietf.org/doc/draft-ietf-wimse-arch/ |
| Stacklok | Why Kubernetes is the right platform for MCP servers in production, plus the operator guide | https://stacklok.com/blog/why-kubernetes-is-the-right-platform-for-running-mcp-servers-in-production/ |
| IBM | ContextForge architecture | https://ibm.github.io/mcp-context-forge/architecture/ |

**Gap in this list:** no large non-vendor enterprise has published its own MCP
platform reference architecture with operating numbers. Every architecture above
is from a vendor or a foundation describing its own product or project. A named
bank, retailer or government department publishing "here is how we run 400 MCP
servers for 200,000 people" does not appear to exist in public as of 2026-09-17.
That absence is itself worth stating from the stage, and it is the gap the keynote
can credibly fill from lived experience.

---

## 9. Gaps: what nothing solves yet

Ordered by how exposed an enterprise is if it assumes the gap is filled.

**1. Agent identity as a first-class principal.** OAuth 2.1 in MCP gives you a user
acting through a client. SPIFFE gives you a workload. ID-JAG gives you an app
acting for a user. None of them give you a durable, revocable, auditable identity
for *an agent instance* that persists across a multi-step task, survives a handoff
to a sub-agent, and can be reasoned about in policy. Cedar policies today
authorize on the OAuth token and tool parameters, which is the user's identity
wearing the agent's request. The delegation chain is the missing primitive, and
every layer currently approximates it.

**2. Portable approval and ownership metadata.** `server.json` has no field for
approval status, owning team, data classification, on-call, or cost center. Every
private registry invents its own. The consequence is that an enterprise catalog
cannot be exchanged, audited against a standard, or migrated between platforms.
AuthZEN COAZ addresses the authorization-metadata half of this and is a Working
Group Draft.

**3. Human-in-the-loop approval as infrastructure.** AARP is the first standards
attempt and it is a June 2026 Working Group Draft. Until it lands, every enterprise
builds its own approval workflow in a chat tool, with no interoperability and no
common audit shape. An agent that must wait for a human to approve a $50,000
transaction is an authorization state nothing standard represents.

**4. Tool-description trust.** The registry explicitly delegates security scanning
to package registries and aggregators. Nothing in the MCP protocol attests that the
tool description an agent reads is the one the publisher wrote, or that it has not
been rewritten to manipulate the model. Gateways bolt on prompt-injection
detection (Lasso, MintMCP, obot all claim it), which is heuristic, and none of it
is standardized or independently benchmarked in public.

**5. Cross-server transaction semantics.** With protocol sessions removed, state
that spans calls is a server-minted handle passed as a tool argument. The spec
warns about state handle hijacking and requires servers to bind handles to the
authenticated principal. What does not exist is any notion of a transaction
spanning *two different MCP servers*. An agent that writes to one system and must
roll back a write to another has no protocol support and no gateway support.

**6. Cost attribution through a delegation chain.** AI gateways meter per API key
and per model. MCP gateways meter per tool call. Nothing joins "this person asked
for this outcome" to the full tree of model calls and tool calls that resulted,
across agents and sub-agents. Budgets exist; attribution does not.

**7. Stable observability vocabulary.** The OTel GenAI conventions, MCP included,
are Development, unreleased from their new repo, and have an open issue to align
with the current protocol revision. Anyone building fleet-wide dashboards today is
building on a moving schema and should say so in their runbook.

**8. Registry federation.** The official registry publishes an OpenAPI contract
that private registries "can implement", and the codebase is explicitly not
designed for self-hosting. What is missing is a defined federation protocol:
trust, signing, freshness, revocation propagation and conflict resolution between
an upstream registry and a downstream private one. Today "ingest a curated subset"
is a pattern people describe, not a specification anyone implements compatibly.

**9. Migration tooling for the stateless transition.** The largest revision in
MCP's history landed on 2026-07-28. Deprecated in it: Roots, Sampling, Logging,
HTTP+SSE and Dynamic Client Registration, with a twelve-month minimum window. No
project publishes a fleet-wide conformance scanner that answers "which of my 300
servers still require an initialize handshake, mint session IDs, or depend on a
deprecated feature". A gateway can report protocol version distribution from the
required `MCP-Protocol-Version` header, which gets you part of the way, and the
rest is unbuilt.

**10. Independent evaluation.** Every capability claim in section 2 comes from the
project or vendor that makes the product. There is no CNCF-style conformance suite
for MCP gateways, no published benchmark of policy evaluation overhead at scale,
and no third-party security audit of any MCP gateway that this research surfaced.
For a room of maintainers, that is a concrete, actionable gap.

---

## 10. Verification ledger

**Verified against primary sources on 2026-09-17:** the entire `2026-07-28` spec
changelog, the Streamable HTTP transport requirements, the authorization spec, the
security best practices document, the MCP Registry about page, agentgateway's
repository and releases, Agent Router's MCP capabilities page and rename
announcement, ContextForge's repository, ToolHive's documentation, Docker MCP
Enterprise Gateway's product page, Kong's Enterprise MCP Gateway announcement,
Azure API Center's MCP documentation, the AWS AgentCore Gateway spec-support post,
the Kyverno graduation announcement, the AAIF project list, the OpenID Foundation
AuthZEN drafts announcement, and the Lasso mcp-gateway repository.

**Verified against secondary sources only, re-check before use on stage:** the
ID-JAG draft revision number and rollout dates, the Okta and Auth0 availability
dates, the XAA app lists, Kong AI Gateway version numbers and the 2.0 GA date, the
Palo Alto acquisition of Portkey, LiteLLM version and tier boundaries, ToolHive
v0.46.0's date, Envoy AI Gateway release dates prior to the rename, kgateway's
current version and incubation state, OTel MCP span and metric names, sub-millisecond
OPA evaluation overhead, MintMCP's stated 100 to 250 ms inspection overhead, and
the WIMSE RFC timeline.

**Could not be retrieved in this pass:** the OTel MCP semantic convention
documents themselves (404 on two attempted paths), agentgateway's feature
documentation pages (404), and the MCP Registry's live API documentation endpoint
(returned a title only). The web search budget for the session was exhausted
before these could be resolved by an alternate route.
