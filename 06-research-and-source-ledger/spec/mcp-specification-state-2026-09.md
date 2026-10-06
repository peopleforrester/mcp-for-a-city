---
title: "State of the MCP Specification, September 2026"
date: 2026-09-17
sources_verified_on: 2026-09-17
status: draft
---

<!-- ABOUTME: Verified state of the Model Context Protocol specification as of 2026-09-17, for the MCP Dev Summit Toronto keynote on 2026-10-06. -->
<!-- ABOUTME: Every claim carries a primary source URL; unverified items are marked UNVERIFIED inline. -->

# State of the MCP Specification, September 2026

> **Note added 2026-10-06, on publication:** This file treats the March 2026 roadmap as current. The roadmap published on 2026-08-22 replaces it.

All facts below were verified against live primary sources on **2026-09-17** unless a
line says otherwise. Quoted blocks are verbatim spec text. Where the spec says
something that contradicts common assumption, the contradiction is called out.

---

## 0. The one-line answer to "is authorization still optional?"

**Yes, and no, and the distinction is the talk.**

The literal sentence "Authorization is **OPTIONAL** for MCP implementations" is
still in the current specification, unchanged in wording across three revisions
(2025-06-18, 2025-11-25, 2026-07-28). Nothing has made authorization mandatory.

What changed is everything *inside* the conditional. Once an implementation
offers authorization over HTTP at all, the specification now imposes a dense set
of **MUST** requirements on both sides: RFC 9728 on the server, RFC 8707 on the
client, PKCE with S256, RFC 9207 issuer validation, audience validation, and an
absolute prohibition on token passthrough. The optionality is at the door. Past
the door, almost nothing is optional.

See Section 3 for the verbatim text and the full MUST inventory.

---

## 1. Specification revisions

### 1.1 Versioning policy (verbatim)

Source: https://modelcontextprotocol.io/specification/versioning (verified 2026-09-17)

> The Model Context Protocol uses string-based version identifiers following the format
> `YYYY-MM-DD`, to indicate the last date backwards incompatible changes were made.

> The protocol version will *not* be incremented when the
> protocol is updated, as long as the changes maintain backwards compatibility. This allows
> for incremental improvements while preserving interoperability.

Revisions may be marked **Draft**, **Current**, or **Final**.

> The **current** protocol version is [**2026-07-28**](/specification/2026-07-28/).

### 1.2 Every revision that exists

Source: https://github.com/modelcontextprotocol/modelcontextprotocol/releases (verified 2026-09-17)

| Revision | Release date | State as of 2026-09-17 |
|---|---|---|
| `2024-10-07` | 2024-11-06 | Final (pre-launch draft tag) |
| `2024-11-05` | 2025-01-17 (tag), `2024-11-05-final` tagged 2025-03-26 | Final. The launch revision. |
| `2025-03-26` | 2025-03-26 | Final |
| `2025-06-18` | 2025-06-18 | Final |
| `2025-11-25` | 2025-11-25 (RC 2025-11-15) | Final |
| **`2026-07-28`** | **2026-07-28** (RC 2026-05-29) | **CURRENT** |
| `draft` | n/a | Empty. "Changes since the most recent release will accumulate here." Nothing has accumulated yet as of 2026-09-17. Source: https://modelcontextprotocol.io/specification/draft/changelog |

**Speaker note:** there is no revision between 2026-07-28 and today, and the draft
changelog is empty. 2026-07-28 is a fresh, stable, unchallenged current revision
at the time of the talk.

### 1.3 What changed in each revision

#### 2025-03-26 (from 2024-11-05)
Source: https://modelcontextprotocol.io/specification/2025-03-26/changelog

Verbatim major changes:
1. "Added a comprehensive **authorization framework** based on OAuth 2.1"
2. "Replaced the previous HTTP+SSE transport with a more flexible **Streamable HTTP transport**"
3. "Added support for JSON-RPC **batching**"
4. "Added comprehensive **tool annotations** for better describing tool behavior, like whether it is read-only or destructive"

Also added: `message` field on `ProgressNotification`, audio content type, `completions` capability.

**This is the revision that invented MCP authorization.** Before 2025-03-26 there was no auth framework in the spec at all.

#### 2025-06-18 (from 2025-03-26)
The revision that introduced the resource-server split. It is the first to require
RFC 9728 Protected Resource Metadata and RFC 8707 Resource Indicators, and to state
the token passthrough prohibition. Text quoted in Section 3.2.
Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization

#### 2025-11-25 (from 2025-06-18)
Source: https://modelcontextprotocol.io/specification/2025-11-25/changelog

Verbatim major changes:
1. "Enhance authorization server discovery with support for OpenID Connect Discovery 1.0"
2. "Allow servers to expose icons as additional metadata for tools, resources, resource templates, and prompts (SEP-973)"
3. "Enhance authorization flows with incremental scope consent via `WWW-Authenticate` (SEP-835)"
4. "Provide guidance on tool names"
5. "Update `ElicitResult` and `EnumSchema` to use a more standards-based approach and support titled, untitled, single-select, and multi-select enums"
6. "Added support for URL mode elicitation (SEP-1036)"
7. "Add tool calling support to sampling via `tools` and `toolChoice` parameters"
8. "Add support for OAuth Client ID Metadata Documents as a recommended client registration mechanism (SEP-991)"
9. "Add experimental support for tasks to enable tracking durable requests with polling and deferred result retrieval (SEP-1686)"

Governance updates in the same revision: formalized MCP governance structure (SEP-932),
community communication practices (SEP-994), Working Groups and Interest Groups (SEP-1302),
SDK tiering system (SEP-1730).

#### 2026-07-28 (from 2025-11-25), the CURRENT revision
Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog

The release blog calls this "the largest revision of the protocol since launch."
Source: https://blog.modelcontextprotocol.io/posts/2026-07-28/ (published 2026-07-28)

Verbatim major changes:

1. "Remove protocol-level sessions and the `Mcp-Session-Id` header from the Streamable HTTP transport. List endpoints (`tools/list`, `resources/list`, `prompts/list`) no longer vary per-connection. Servers that need cross-call state use explicit, server-minted handles passed as ordinary tool arguments (SEP-2567)."

2. "Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request now carries its protocol version and client capabilities in `_meta` (`io.modelcontextprotocol/protocolVersion`, `io.modelcontextprotocol/clientCapabilities`). Clients SHOULD identify themselves on each request (`io.modelcontextprotocol/clientInfo`), and servers SHOULD identify themselves in each result's `_meta` (`io.modelcontextprotocol/serverInfo`). Version mismatches return `UnsupportedProtocolVersionError` (SEP-2575)."

3. "Add `server/discover`: servers MUST implement this RPC to advertise their supported protocol versions, capabilities, and identity. Clients MAY call it before any other request for up-front version selection, or use it as a backward-compatibility probe on STDIO (SEP-2575)."

4. "Replace the HTTP GET endpoint and `resources/subscribe`/`resources/unsubscribe` with `subscriptions/listen`: a single long-lived POST-response stream for opted-in server-to-client change notifications."

5. "Remove `ping`, `logging/setLevel`, and `notifications/roots/list_changed`. Log level is now set per-request via `io.modelcontextprotocol/logLevel` in `_meta`."

6. "Move experimental tasks out of the core protocol and into an official extension (`io.modelcontextprotocol/tasks`). The redesigned extension replaces the blocking `tasks/result` method with polling via `tasks/get` and a new `tasks/update` for client-to-server input, removes `tasks/list`, and allows servers to return task handles unsolicited (SEP-2663)."

7. "Multi Round-Trip Requests (MRTR) pattern introduced which replaces the previous approach of sending server-initiated requests, such as `roots/list`, `sampling/createMessage`, or `elicitation/create`. Servers return an `InputRequiredResult` (`resultType: "input_required"`) whose `inputRequests` field carries the requests for the additional information needed to process the request. Clients respond with `inputResponses` on a retry of the original request (SEP-2322)."

8. "All results now carry a required `resultType` field: `\"complete\"` for ordinary results and `\"input_required\"` for multi round-trip request interim results. Clients **MUST** treat results from earlier-protocol servers that omit the field as `\"complete\"`."

9. "Remove SSE stream resumability and message redelivery (the `Last-Event-ID` header and SSE event IDs) from the Streamable HTTP transport. A broken response stream loses the in-flight request; clients **MUST** re-issue it as a new request with a new request ID (SEP-2575)."

Minor changes worth naming from the stage (all verbatim from the same changelog):

- "Require standard MCP request headers (`Mcp-Method`, `Mcp-Name`) on Streamable HTTP POST requests, and add support for custom headers from tool parameters via `x-mcp-header` (SEP-2243)."
- "Require `ttlMs` and `cacheScope` fields on results returned by `tools/list`, `prompts/list`, `resources/list`, `resources/read`, and `resources/templates/list` via a new `CacheableResult` interface."
- "Authorization servers **SHOULD** include the `iss` parameter in authorization responses per RFC 9207, and MCP clients **MUST** validate a present `iss` against the recorded issuer before redeeming the authorization code (SEP-2468)."
- "Require MCP clients to specify an appropriate `application_type` during Dynamic Client Registration to avoid OpenID Connect redirect URI conflicts (SEP-837)."
- "Clarify that client credentials are bound to the authorization server that issued them: clients **MUST** key persisted credentials by the issuer identifier, **MUST NOT** reuse them with a different authorization server, and **MUST** re-register when the authorization server changes (SEP-2352)."
- "Document OpenTelemetry trace context propagation conventions for `_meta` keys (`traceparent`, `tracestate`, `baggage`) (SEP-414)."
- "Change resource not found error code from `-32002` to `-32602` (Invalid Params)."
- Error code allocation policy: `-32000` to `-32019` legacy/implementation-defined, `-32020` to `-32099` reserved for the MCP specification.

---

## 2. Deprecations and the new lifecycle policy

2026-07-28 introduced a formal feature lifecycle. Source:
https://modelcontextprotocol.io/specification/2026-07-28/deprecated (verified 2026-09-17)

> A Deprecated feature remains part of the specification but is scheduled for
> removal: new implementations **SHOULD NOT** adopt it, and existing
> implementations **SHOULD** migrate before the feature's earliest removal.

Deprecation window: minimum twelve months, or ninety days under the expedited-removal exception.

| Feature | Deprecated in | Migration path | Earliest removal |
|---|---|---|---|
| Roots | `2026-07-28` | Pass directories or files via tool parameters, resource URIs, or server configuration | First revision released on or after 2027-07-28 |
| Sampling | `2026-07-28` | Integrate directly with LLM provider APIs | First revision released on or after 2027-07-28 |
| Logging | `2026-07-28` | Log to `stderr` for stdio; use OpenTelemetry for observability | First revision released on or after 2027-07-28 |
| Dynamic Client Registration | `2026-07-28` | Client ID Metadata Documents | First revision released on or after 2027-07-28 |
| `includeContext: "thisServer"` / `"allServers"` | `2025-11-25` | Omit the field or use `"none"` | Follows Sampling |
| HTTP+SSE transport | `2025-03-26` | Streamable HTTP | Three months after SEP-2596 reaches Final |

**"Removed" section of the registry as of 2026-09-17:** "No features have been removed under this policy yet."

**Speaker note, high value:** three of the original client-side primitives (Roots,
Sampling, Logging) are now formally on death row, and Dynamic Client Registration
with them. An audience that built on MCP in 2025 has four deprecations to absorb.

---

## 3. Authorization: the detail

### 3.1 The optionality clause, verbatim and unchanged

Current revision. Source:
https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
(verified 2026-09-17)

> ### Protocol Requirements
>
> Authorization is **OPTIONAL** for MCP implementations. When supported:
>
> * Implementations using an HTTP-based transport **SHOULD** conform to this specification.
> * Implementations using an STDIO transport **SHOULD NOT** follow this specification, and
>   instead retrieve credentials from the environment.
> * Implementations using alternative transports **MUST** follow established security best
>   practices for their protocol.

This exact paragraph appears **word for word** in 2025-06-18, 2025-11-25, and
2026-07-28. All three verified independently on 2026-09-17:

- https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization

The base protocol overview repeats the same posture. Source:
https://modelcontextprotocol.io/specification/2026-07-28/basic/index

> MCP provides an Authorization framework for use with HTTP.
> Implementations using an HTTP-based transport **SHOULD** conform to this specification,
> whereas implementations using STDIO transport **SHOULD NOT** follow this specification,
> and instead retrieve credentials from the environment.
>
> Additionally, clients and servers **MAY** negotiate their own custom authentication and
> authorization strategies.

And the layering statement:

> All implementations **MUST** support the base protocol, versioning,
> and the message patterns. Other components **MAY** be implemented based on the specific needs of the
> application.

Authorization is not in that MUST list.

### 3.2 The Overview requirements, current revision, verbatim

From https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization

> 1. Authorization servers **MUST** implement OAuth 2.1 with appropriate security
>    measures for both confidential and public clients.
>
> 2. Authorization servers and MCP clients **SHOULD** support OAuth Client ID Metadata Documents
>    (draft-ietf-oauth-client-id-metadata-document-00).
>
> 3. Authorization servers and MCP clients **MAY** support the OAuth 2.0 Dynamic Client Registration
>    Protocol (RFC7591). Note that Dynamic Client Registration
>    is deprecated and retained for backwards compatibility with authorization servers that do not support Client ID Metadata Documents.
>
> 4. MCP servers **MUST** implement OAuth 2.0 Protected Resource Metadata (RFC9728).
>    MCP clients **MUST** use OAuth 2.0 Protected Resource Metadata for authorization server discovery.
>
> 5. MCP authorization servers **MUST** provide at least one of the following discovery mechanisms:
>
>    * OAuth 2.0 Authorization Server Metadata (RFC8414)
>    * OpenID Connect Discovery 1.0
>
>    MCP clients **MUST** support both discovery mechanisms to obtain the information required to interact with the authorization server.

### 3.3 The DCR trajectory, revision by revision

This is a clean three-beat arc and it is fully verified.

| Revision | Normative level for Dynamic Client Registration |
|---|---|
| 2025-06-18 | "Authorization servers and MCP clients **SHOULD** support the OAuth 2.0 Dynamic Client Registration Protocol (RFC7591)." |
| 2025-11-25 | "Authorization servers and MCP clients **MAY** support the OAuth 2.0 Dynamic Client Registration Protocol (RFC7591)." Client ID Metadata Documents becomes the SHOULD. |
| 2026-07-28 | Still **MAY**, and now formally **Deprecated** under the lifecycle policy. Earliest removal: first revision on or after 2027-07-28. |

The spec page carries an explicit warning box. Source:
https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration

> Dynamic Client Registration is deprecated. New implementations should use
> Client ID Metadata Documents instead. This option remains available for
> backwards compatibility with authorization servers that do not support Client
> ID Metadata Documents.

### 3.4 Resource server vs authorization server split

Verbatim, current revision:

> A protected *MCP server* acts as an OAuth 2.1 resource server,
> capable of accepting and responding to protected resource requests using access tokens.
>
> An *MCP client* acts as an OAuth 2.1 client,
> making protected resource requests on behalf of a resource owner.
>
> The *authorization server* is responsible for interacting with the user (if necessary) and issuing access tokens for use at the MCP server.
> The implementation details of the authorization server are beyond the scope of this specification. It may be hosted with the
> resource server or a separate entity.

This split first landed in 2025-06-18 and is unchanged in shape since.

### 3.5 Protected Resource Metadata (RFC 9728)

Server side is a hard MUST in every revision since 2025-06-18:

> MCP servers **MUST** implement OAuth 2.0 Protected Resource Metadata (RFC9728).
> MCP clients **MUST** use OAuth 2.0 Protected Resource Metadata for authorization server discovery.

2025-11-25 added a fallback path so the `WWW-Authenticate` header is not the only
discovery route. Source:
https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization

> MCP servers **MUST** implement one of the following discovery mechanisms:
>
> 1. **WWW-Authenticate Header**: Include the resource metadata URL in the `WWW-Authenticate` HTTP header under `resource_metadata` when returning `401 Unauthorized` responses [...]
> 2. **Well-Known URI**: Serve metadata at a well-known URI as specified in RFC9728.

> MCP clients **MUST** support both discovery mechanisms and use the resource metadata URL from the parsed `WWW-Authenticate` headers when present; otherwise, they **MUST** fall back to constructing and requesting the well-known URIs in the order listed above.

### 3.6 Resource Indicators (RFC 8707)

Verbatim, current revision:

> MCP clients **MUST** implement Resource Indicators for OAuth 2.0 as defined in RFC 8707
> to explicitly specify the target resource for which the token is being requested. The `resource` parameter:
>
> 1. **MUST** be included in both authorization requests and token requests.
> 2. **MUST** identify the MCP server that the client intends to use the token with.
> 3. **MUST** use the canonical URI of the MCP server as defined in RFC 8707 Section 2.

And the line that closes the "but my AS doesn't support it" escape:

> MCP clients **MUST** send this parameter regardless of whether authorization servers support it.

Valid canonical URIs per spec: `https://mcp.example.com/mcp`, `https://mcp.example.com`,
`https://mcp.example.com:8443`, `https://mcp.example.com/server/mcp`.
Invalid: `mcp.example.com` (no scheme), `https://mcp.example.com#fragment` (fragment).

### 3.7 Token passthrough prohibition

Three separate places say it, all verified 2026-09-17.

Authorization security considerations. Source:
https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations

> MCP servers **MUST** only accept tokens specifically intended for themselves and **MUST** reject tokens that do not include them in the audience claim or otherwise verify that they are the intended recipient of the token.

> If the MCP server makes requests to upstream APIs, it may act as an OAuth client to them. The access token used at the upstream API is a separate token, issued by the upstream authorization server. The MCP server **MUST NOT** pass through the token it received from the MCP client.

Core authorization page:

> MCP clients **MUST NOT** send tokens to the MCP server other than ones issued by the MCP server's authorization server.
>
> MCP servers **MUST** only accept tokens that are valid for use with their
> own resources.
>
> MCP servers **MUST NOT** accept or transit any other tokens.

Security best practices. Source:
https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices

> "Token passthrough" is an anti-pattern where an MCP server accepts
> tokens from an MCP client without validating that the tokens were
> properly issued *to the MCP server* and passes them through to the
> downstream API.

> Token passthrough is explicitly forbidden in the authorization specification [...]

> #### Mitigation
>
> MCP servers **MUST NOT** accept any tokens that were not explicitly
> issued for the MCP server.

**This is the single strongest normative sentence in the MCP security surface and
it is the one most often violated in practice.** UNVERIFIED: any quantitative
claim about how often it is violated in the wild. Do not assert a percentage.

### 3.8 New in 2026-07-28: RFC 9207 issuer validation

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization

> Before redirecting the user-agent, the client **MUST** record the `issuer` value from the selected authorization server's validated metadata document [...] and associate it with the same per-request record used to store the PKCE code verifier (and the `state` value, if used).

> MCP authorization servers **SHOULD** include the `iss` parameter in authorization responses, including error responses, as defined in RFC9207 Section 2. Authorization servers that include the `iss` parameter **MUST** advertise this by setting `authorization_response_iss_parameter_supported` to `true` in their metadata.

> On receiving the authorization response, MCP clients **MUST** apply the validation in RFC9207 Section 2.4 before transmitting the authorization code to any token endpoint

Client action matrix from the spec:

| `authorization_response_iss_parameter_supported` | `iss` in response | Client action |
|---|---|---|
| `true` | present | Compare to recorded issuer, simple string comparison (RFC3986 6.2.1) |
| `true` | absent | Reject the response |
| `false` or absent | present | Compare to the recorded issuer |
| `false` or absent | absent | Proceed |

And a forward-looking sentence worth quoting on stage:

> A future revision of this specification is expected to upgrade authorization server inclusion of `iss` from **SHOULD** to **MUST**. Implementers are encouraged to emit and validate `iss` now to ease that transition

Also:

> This validation applies equally to error responses - on mismatch the client **MUST NOT** act on or display `error`, `error_description`, or `error_uri`.

### 3.9 PKCE

Source: 2026-07-28 authorization security considerations.

> MCP clients **MUST** implement PKCE according to OAuth 2.1 Section 7.5.2 and **MUST** verify PKCE support before proceeding with authorization.

> MCP clients **MUST** use the `S256` code challenge method when technically capable

> **OAuth 2.0 Authorization Server Metadata**: If `code_challenge_methods_supported` is absent, the authorization server does not support PKCE and MCP clients **MUST** refuse to proceed.

> Authorization servers providing OpenID Connect Discovery 1.0 **MUST** include `code_challenge_methods_supported` in their metadata to ensure MCP compatibility.

### 3.10 Client ID Metadata Documents (CIMD), the DCR replacement

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration

Three mechanisms, with a stated priority order:

> Clients supporting all options **SHOULD** use the following priority order:
>
> 1. Use pre-registered client information for the server if the client has it available
> 2. Use Client ID Metadata Documents if the Authorization Server indicates that it supports them (via `client_id_metadata_document_supported` in OAuth Authorization Server Metadata)
> 3. Use Dynamic Client Registration as a fallback if the Authorization Server supports it (via `registration_endpoint` in OAuth Authorization Server Metadata)
> 4. Prompt the user to enter the client information if no other option is available

Client requirements:

> * Clients **MUST** host their metadata document at an HTTPS URL following RFC requirements
> * The `client_id` URL **MUST** use the "https" scheme and contain a path component, e.g. `https://example.com/client.json`
> * The metadata document **MUST** include at least the following properties: `client_id`, `client_name`, `redirect_uris`
> * Clients **MUST** ensure the `client_id` value in the metadata matches the document URL exactly

Authorization server requirements:

> * **SHOULD** fetch metadata documents when encountering URL-formatted client\_ids
> * **MUST** validate that the fetched document's `client_id` matches the URL exactly
> * **SHOULD** cache metadata respecting HTTP cache headers
> * **MUST** validate redirect URIs presented in an authorization request against those in the metadata document
> * **MUST** validate the document structure is valid JSON and contains required fields

Portability, a genuinely useful enterprise point:

> Client IDs based on Client ID Metadata Documents are portable
> across authorization servers, since they are self-hosted HTTPS URLs
> resolved by the authorization server on demand. No re-registration
> is needed when the authorization server changes.

Contrast with the new binding rule for everything else:

> Clients that use pre-registered credentials, or persist client credentials obtained via Dynamic Client Registration, **MUST** associate those credentials with the specific authorization server that issued them, keyed by the authorization server's `issuer` identifier. [...] clients **MUST NOT** reuse client credentials from a different authorization server and **MUST** re-register with the new authorization server.

### 3.11 Scopes and step-up

> MCP servers **SHOULD** include a `scope` parameter in the `WWW-Authenticate` header as defined in RFC 6750 Section 3 to indicate the scopes required for accessing the resource.

Note that is a **SHOULD**, not a MUST. If a server omits it, clients fall back to
requesting everything in `scopes_supported`, which is the opposite of least
privilege. The spec acknowledges this tension directly in the security best
practices page under Scope Minimization.

> Clients **MUST NOT** assume any particular set relationship between the challenged scope set and `scopes_supported`. Clients **MUST** treat the scopes provided in the challenge as authoritative for the current operation.

> Servers **MUST** account for scope hierarchies, where a broader scope implies narrower ones, when deciding whether a token is sufficient for an operation.

Runtime insufficient scope: server **SHOULD** respond `403 Forbidden` with
`error="insufficient_scope"`, `scope="..."`, and `resource_metadata`.

### 3.12 Complete MUST/MUST NOT inventory for an HTTP MCP deployment

Once you turn authorization on, this is the binding list. All from the
2026-07-28 authorization pages and security best practices.

**MCP server (resource server) MUST:**
- Implement RFC 9728 Protected Resource Metadata
- Include `authorization_servers` with at least one entry
- Validate access tokens per OAuth 2.1 Section 5.2
- Validate that tokens were issued specifically for it as the intended audience (RFC 8707 Section 2)
- Return 401 for invalid or expired tokens
- Only accept tokens valid for its own resources
- Reject tokens that do not include it in the audience claim
- Validate the `Origin` header on all incoming Streamable HTTP connections, 403 on invalid
- Reject requests where header values do not match the body (`-32020 HeaderMismatch`)
- Implement `server/discover`
- Verify all inbound requests if it implements authorization, and **MUST NOT** treat possession of a state handle as authentication

**MCP server MUST NOT:**
- Accept or transit tokens not issued for it
- Pass through the token it received from the MCP client to an upstream API
- Emit `notifications/message` for requests that did not include `io.modelcontextprotocol/logLevel`

**MCP client MUST:**
- Use RFC 9728 for authorization server discovery
- Support both RFC 8414 and OpenID Connect Discovery
- Implement RFC 8707 `resource` parameter in authorization and token requests, regardless of AS support
- Implement PKCE, verify PKCE support, use S256 when capable, refuse to proceed if `code_challenge_methods_supported` is absent
- Record the issuer before redirect and validate a present `iss` (RFC 9207)
- Have redirect URIs registered with the authorization server
- Send `Authorization: Bearer` on every HTTP request
- Key persisted client credentials by issuer, re-register on AS change
- Specify an appropriate `application_type` during DCR
- Include `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` headers on Streamable HTTP POSTs
- Support `x-mcp-header` mirroring, and reject tool definitions violating its constraints
- Only allow `http://` and `https://` authorization URL schemes, rejecting `javascript:`, `data:`, `file:`, `vbscript:`
- Avoid shell execution when opening URLs

**MCP client MUST NOT:**
- Include access tokens in URI query strings
- Send tokens other than those issued by the MCP server's authorization server
- Apply URI normalization before `iss` comparison

**Authorization server MUST:**
- Implement OAuth 2.1
- Provide at least one of RFC 8414 or OIDC Discovery
- Validate exact redirect URIs against pre-registered values
- Rotate refresh tokens for public clients
- Serve all endpoints over HTTPS
- Advertise `authorization_response_iss_parameter_supported` if it emits `iss`
- Clearly display the redirect URI hostname during authorization (CIMD)

---

## 4. Transports

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
and https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http

### 4.1 The standard set

Two standard bindings, plus custom:

1. **stdio**: newline-delimited messages over the standard streams of a client-launched subprocess.
2. **Streamable HTTP**: each message is an HTTP POST to a single MCP endpoint; replies arrive as a JSON object or a request-scoped SSE stream.

> Custom transports that run over a reliable bidirectional byte stream (e.g.,
> Unix domain sockets or TCP) **SHOULD** reuse the stdio framing rather than
> defining a new one

### 4.2 HTTP+SSE: deprecated, with dates

> **Deprecated**: The HTTP+SSE transport from protocol version
> 2024-11-05 has been deprecated since protocol version `2025-03-26` and is
> classified as Deprecated under the feature lifecycle policy
> (SEP-2596). New implementations **SHOULD NOT** adopt it; existing implementations
> **SHOULD** migrate to Streamable HTTP. It is eligible for removal in a future revision

Earliest removal per the deprecated registry: "Three months after SEP-2596 reaches Final."

### 4.3 Statelessness, verbatim

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/index

> The Model Context Protocol (MCP) is a **stateless protocol**: all the
> information needed to process a request is contained in the request itself.
> A server processes each request independently; no state should be inferred
> from previous requests, even those on the same connection or stream.

> * Servers **MUST NOT** rely on prior requests over the same connection to
>   establish context (e.g., capabilities, protocol version, client identity).
>   Every request supplies this metadata in its `_meta` field.
> * Servers **SHOULD** be prepared to handle requests associated with multiple
>   tasks, threads, or conversations.
> * Servers **SHOULD NOT** require that a client reuse the same connection or process to
>   perform related operations.
> * Clients **SHOULD NOT** use an individual task, thread, or conversation as the
>   lifetime boundary for the stdio process.
> * State that needs to span multiple requests (e.g., long-running tasks,
>   application-level handles) **MUST** be referenced by an explicit identifier
>   the client passes on each request.

> This implies that an open connection, such as a STDIO process, is not a
> conversation or session

### 4.4 Session management: gone

`Mcp-Session-Id` is removed. Per the Streamable HTTP page, a modern-only server
receiving legacy traffic:

> * HTTP GET or DELETE to the MCP endpoint: respond with `405 Method Not Allowed`.
> * An `Mcp-Session-Id` header on a request: ignore it, and do not mint or echo session IDs.
> * A `Last-Event-ID` header: ignore it; streams are not resumable.

### 4.5 Resumability: gone

> Resumable SSE streams via `Last-Event-ID` are not supported.

From the changelog:

> A broken response stream loses the in-flight request; clients **MUST** re-issue it as a new request with a new request ID.

**Speaker note:** this is a real regression in capability, traded deliberately for
horizontal scalability. A long-running tool call that loses its stream is
restarted from zero unless the server implements the Tasks extension. That is a
concrete argument for the "optional but load-bearing" thesis in Section 8.

### 4.6 Required per-request metadata

Required `_meta` keys on every client request:

| Key | Required |
|---|---|
| `io.modelcontextprotocol/protocolVersion` | Yes |
| `io.modelcontextprotocol/clientCapabilities` | Yes |
| `io.modelcontextprotocol/clientInfo` | No (but SHOULD) |
| `io.modelcontextprotocol/logLevel` | No |

> A request missing any required field is malformed; the server **MUST** reject it with
> JSON-RPC error code `-32602` (Invalid params). On HTTP, the response status **MUST** be
> `400 Bad Request`.

> A server **MUST NOT** rely on capabilities the client has not declared. If
> processing a request requires a capability the client did not include in
> `io.modelcontextprotocol/clientCapabilities`, the server **MUST** return a
> `MissingRequiredClientCapabilityError` (`-32021`)

### 4.7 Header-based routing

> | Header Name | Source Field | Required For |
> |---|---|---|
> | `Mcp-Method` | `method` | All requests |
> | `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` requests |
>
> These headers are **REQUIRED** for compliance.

Plus `MCP-Protocol-Version` on every POST, which **MUST** match the body `_meta` value.

> Servers that process the request body **MUST** reject requests where the
> values specified in the headers do not match the corresponding values in the
> request body. This prevents potential security vulnerabilities when
> different components in the network rely on different sources of truth
> (e.g., a load balancer routing on the header value while the MCP server
> executes based on the body value).

Security caution the spec itself raises:

> Server developers **SHOULD NOT** mark sensitive parameters (passwords, API keys, tokens, PII) with `x-mcp-header`, as header values are visible to network intermediaries.

### 4.8 Streamable HTTP local security

> 1. Servers **MUST** validate the `Origin` header on all incoming connections to prevent DNS rebinding attacks.
> 2. When running locally, servers **SHOULD** bind only to localhost (127.0.0.1) rather than all network interfaces (0.0.0.0).
> 3. Servers **SHOULD** implement proper authentication for all connections.

Note item 3 is a **SHOULD**. See Section 8.

---

## 5. Primitives and recent additions

### 5.1 The core set as of 2026-07-28

Source: https://modelcontextprotocol.io/specification/latest (resolves to 2026-07-28)

> Servers offer any of the following features to clients:
> * **Resources**: Context and data, for the user or the AI model to use
> * **Prompts**: Templated messages and workflows for users
> * **Tools**: Functions for the AI model to execute
>
> Clients may offer the following features to servers:
> * **Elicitation**: Server-initiated requests for additional information from users

**Notice what is absent from that list.** Sampling and Roots are no longer named
as headline client features on the spec landing page; they are deprecated.

### 5.2 Tools

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools

Tool definition fields: `name`, `title` (optional), `description`, `icons`
(optional), `inputSchema`, `outputSchema` (optional), `annotations` (optional).

Annotations, unchanged warning since 2025:

> For trust & safety and security, clients **MUST** consider tool annotations to
> be untrusted unless they come from trusted servers.

Output schema:

> If an output schema is provided:
> * Servers **MUST** provide structured results that conform to this schema.
> * Clients **SHOULD** validate structured results against this schema.

`structuredContent` in 2026-07-28 was loosened to "any JSON value (object, array,
string, number, boolean, or null)", and `inputSchema`/`outputSchema` now allow
any JSON Schema 2020-12 keywords (SEP-2106).

A clarification worth repeating because it is routinely confused:

> `structuredContent` is server-produced result data and is unrelated to LLM
> "structured outputs" (schema-constrained model generation).

Resource links are a content type returned by tools:

```json
{
  "type": "resource_link",
  "uri": "file:///project/src/main.rs",
  "name": "main.rs",
  "description": "Primary application entry point",
  "mimeType": "text/x-rust"
}
```

> Resource links returned by tools are not guaranteed to appear in the results of a `resources/list` request.

New in 2026-07-28, the list-stability rule that makes caching safe:

> This set **MAY** be empty and **MAY** change over time [...] but **MUST NOT** vary
> per-connection or as a side effect of other requests on the connection. The set
> **MAY** vary by the authorization presented on the request

> Servers **SHOULD** return tools in a deterministic order

Stateful tools guidance (non-normative) replaces sessions: mint an explicit
handle, return it, accept it as an ordinary argument, validate authorization
against the handle on every call.

### 5.3 Elicitation

Source: https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation

Two modes: `form` and `url`. URL mode was introduced in 2025-11-25 and carries a
stability caveat:

> **New feature:** URL mode elicitation is introduced in the `2025-11-25` version of the MCP specification. Its design and implementation may change in future protocol revisions.

Capability declaration is per-request now:

> Clients that support elicitation **MUST** declare the `elicitation` capability in
> `_meta.io.modelcontextprotocol/clientCapabilities` on each request

> Clients declaring the `elicitation` capability **MUST** support at least one mode (`form` or `url`).
> Servers **MUST NOT** send elicitation requests with modes that are not supported by the client.

Hard security boundary:

> * Servers **MUST NOT** use form mode elicitation to request sensitive information such as
>   passwords, API keys, access tokens, or payment credentials
> * Servers **MUST** use URL mode for interactions involving such sensitive information

> MCP servers **MUST NOT** rely on URL mode elicitation to authorize users for themselves.

Client URL handling:

> 1. **MUST NOT** automatically pre-fetch the URL or any of its metadata.
> 2. **MUST NOT** open the URL without explicit consent from the user.
> 3. **MUST** show the full URL to the user for examination before consent.
> 4. **MUST** open the URL provided by the server in a secure manner that does not enable the client or LLM to inspect the content or user inputs.

The phishing attack against URL elicitation (Alice generates the URL, tricks Bob
into completing it, tokens bind to Alice) is documented in full on that page and
is a strong three-sentence stage story.

### 5.4 Multi Round-Trip Requests (MRTR), the biggest structural change

Servers no longer initiate JSON-RPC requests at all.

> The server **MUST NOT** send independent JSON-RPC *requests* on this stream.
> Server-to-client interactions (sampling, elicitation, list-roots) are
> embedded as input requests inside an `InputRequiredResult` per MRTR, not
> delivered as separate requests on this or any other stream. This is a change
> from Streamable HTTP in protocol versions `2025-03-26` through `2025-11-25`

And from the transports overview:

> No other message direction exists: per the message patterns, servers do not
> initiate JSON-RPC requests and clients do not send JSON-RPC responses.

Flow: server returns `resultType: "input_required"` with `inputRequests` and an
opaque `requestState`; client gathers input; client retries the original request
with `inputResponses` and the echoed `requestState`, under a **new** JSON-RPC id.

> Note that the JSON-RPC `id` **MUST** be different between the initial request and the retry.

### 5.5 Tasks: moved out of core into an extension

In 2025-11-25 tasks were experimental core. In 2026-07-28 they are
`io.modelcontextprotocol/tasks`, an official extension:

- `tasks/result` (blocking) replaced by `tasks/get` (polling)
- new `tasks/update` for client-to-server input mid-flight
- `tasks/list` removed
- servers may return task handles unsolicited, without per-request opt-in

Source: 2026-07-28 changelog item 6, and
https://modelcontextprotocol.io/extensions/tasks/overview

### 5.6 Caching

New `CacheableResult` interface. `ttlMs` and `cacheScope` are **required** fields
on results from `tools/list`, `prompts/list`, `resources/list`, `resources/read`,
and `resources/templates/list`. `cacheScope` is `"public"` or `"private"` and
controls whether shared intermediaries may cache.

### 5.7 Subscriptions

`resources/subscribe` / `resources/unsubscribe` and the HTTP GET stream are
replaced by a single `subscriptions/listen` long-lived POST-response stream.
Clients opt in to specific notification types: `toolsListChanged`,
`promptsListChanged`, `resourcesListChanged`, `resourceSubscriptions`.

### 5.8 Icons

Added in 2025-11-25 (SEP-973), on tools, resources, resource templates, prompts,
and `Implementation`. Clients that render icons **MUST** support `image/png` and
`image/jpeg`, **SHOULD** support `image/svg+xml` and `image/webp`. Icons **MUST**
be fetched without credentials, and clients **MUST** reject `javascript:`,
`file:`, `ftp:`, `ws:` icon URIs.

### 5.9 OpenTelemetry

`traceparent`, `tracestate`, and `baggage` are reserved `_meta` keys, exempt from
the vendor-prefix rule, and **MUST** follow W3C Trace Context and W3C Baggage
formats when present. This is the first time observability has a protocol-level
convention, and it is the stated migration path for the deprecated Logging feature.

---

## 6. The official MCP Registry

Source: https://modelcontextprotocol.io/registry (verified 2026-09-17)

### 6.1 Status: preview, not GA

Verbatim from the current docs page:

> The MCP Registry is currently in preview. Breaking changes or data resets may occur before general availability.

From the registry repository README (verified 2026-09-17,
https://github.com/modelcontextprotocol/registry):

> The Registry API has entered an **API freeze (v0.1)**. For the next month or more, the API will remain stable with no breaking changes

> this is still a preview release and breaking changes or data resets may occur. A general availability (GA) release will follow later

**The registry has been in preview since its September 2025 announcement and is
still in preview as of 2026-09-17.** The API freeze note in the README references
an October 2025 date and reads as stale relative to today; treat the freeze
timing as UNVERIFIED and the preview status as verified. There is **no** GA
announcement on the official blog as of 2026-09-17.

Original announcement: https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/

### 6.2 What it is

> The MCP Registry is the official centralized metadata repository for publicly accessible MCP servers, backed by major trusted contributors to the MCP ecosystem such as Anthropic, GitHub, PulseMCP, and Microsoft.

Provides: a publishing surface, DNS-verified namespace management, a REST API for
discovery, and standardized installation and configuration information.

### 6.3 server.json

Server metadata lives in a standardized `server.json` format containing:

> * The server's unique name (e.g., `io.github.user/server-name`)
> * Where to locate the server (e.g., npm package name, remote server URL)
> * Execution instructions (e.g., command-line args, env vars)
> * Other discovery data (e.g., description, server capabilities)

Schema: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/draft/server.schema.json
(note the path still says `draft`)

### 6.4 Namespaces

Reverse DNS format (`io.github.username/server`, `com.example/server`) tied to
verified GitHub accounts or domains via DNS, GitHub, or HTTP challenges.

> This namespace system ensures that only the legitimate owner of a GitHub account or domain can publish servers under that namespace

### 6.5 Private and enterprise registries: the important part

This is where the enterprise story is weakest, and it is verbatim:

> The MCP Registry **does not** support private servers. Private servers are those that are only accessible to a narrow set of users. For example, servers published on a private network (like `mcp.acme-corp.internal`) or on private package registries [...] If you want to publish private servers, we recommend that you host your own private MCP registry and add them there.

> In addition to a public REST API, the MCP Registry defines an OpenAPI spec that other MCP registries can implement in order to provide a standardized interface for MCP host applications. [...] Private MCP registries can implement it as well to benefit from existing host application support.

> Note that the official MCP Registry codebase is **not** designed for self-hosting, and the registry maintainers cannot provide support for this use case. If you choose to fork it, you would need to maintain and operate it independently.

> The MCP Registry is not intended to be directly consumed by host applications. Instead, host applications should consume other MCP registries, such as downstream marketplaces

**Speaker-ready summary:** an enterprise that wants a private catalogue of internal
MCP servers gets an OpenAPI contract and nothing else. No reference
implementation it is allowed to run, no support, no federation protocol. The
sub-registry model is a specification, not a product.

### 6.6 Security posture

> The MCP Registry delegates security scanning to: **Underlying package registries** [...] **Downstream aggregators**

> The MCP Registry focuses on namespace authentication and metadata hosting, while relying on the broader ecosystem for security scanning of actual server code.

---

## 7. Governance

### 7.1 MCP under the Agentic AI Foundation

Announcement date: **2025-12-09**. Two independent sources, both verified 2026-09-17:

- https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/
- https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation

The AAIF is a directed fund under the Linux Foundation. Founding project
contributions: **MCP** (Anthropic), **goose** (Block), **AGENTS.md** (OpenAI).

Membership at launch:
- Platinum: Amazon Web Services, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft, OpenAI
- Gold: Adyen, Arcade.dev, Cisco, Datadog, Docker, Ericsson, IBM, JetBrains, Okta, Oracle, Runlayer, Salesforce, SAP, Shopify, Snowflake, Temporal, Tetrate, Twilio
- Silver: Apify, Chronosphere, Cosmonic, Elasticsearch, Eve Security, Hugging Face, Kubermatic, KYXStart, LanceDB, Mirantis, NinjaTech AI, Obot.ai, Prefect.io, Pydantic, Shinkai.com, Solo.io, Spectro Cloud, Stacklok, SUSE, Uber, WorkOS, Zapier, ZED

Division of powers, from the MCP blog post:

> The AAIF Governing Board handles "strategic investments, budget allocation, member recruitment, and approval of new projects," while individual projects like MCP retain "full autonomy over their technical direction and day-to-day operations."

> The people making decisions about the protocol are still the maintainers who have been stewarding it, guided by community input through our SEP process.

Jim Zemlin, Executive Director, Linux Foundation:

> Bringing these projects together under the AAIF ensures they can grow with the transparency and stability that only open governance provides.

Ecosystem scale cited in the same announcement: **97 million monthly SDK
downloads, 10,000 active servers**, first-class client support across ChatGPT,
Claude, Cursor, Gemini, Microsoft Copilot, and Visual Studio Code. Those figures
are as of December 2025 and should be presented with that date attached, not as
current numbers. UNVERIFIED: any September 2026 refresh of those figures.

### 7.2 Legal and licensing

Source: https://modelcontextprotocol.io/community/governance (verified 2026-09-17)

> Model Context Protocol has been established as **Model Context Protocol a Series of LF Projects, LLC**.

> Except as described below, all code and specification contributions to the project must be made using the Apache License, Version 2.0

Documentation (excluding specifications) is CC BY 4.0.

> Governance changes approved as per the provisions of this governance document must also be approved by LF Projects, LLC.

### 7.3 The maintainer structure

| Role | Scope |
|---|---|
| Lead Maintainers (BDFL) | Final decision authority |
| Core Maintainers | Overall project direction |
| Maintainers | Working Groups, SDKs, components |
| Contributors | Issues, PRs, discussions |

Together, Maintainers, Core Maintainers, and Lead Maintainers form the **MCP Steering Group**.

**Current Lead Maintainers:** David Soria Parra, Den Delimarsky.

**Current Core Maintainers:** Peter Alexander, Caitie McCaffrey, Kurtis Van Gent,
Clare Liguori, Paul Carleton, Nick Cooper.

**Emeritus:** Justin Spahr-Summers (Co-Inventor, Lead Maintainer Emeritus),
Basil Hosmer, Che Liu, Nick Aldridge.

> Membership in the technical governance process is for individuals, not companies. That is, there are no seats reserved for specific companies, and membership is associated with the person rather than the company employing that person.

Core Maintainers meet every two weeks and vote on proposals; the group aims to
meet in person every three to six months.

**Speaker note for this specific audience:** some of these people will be in the
room. Name-check accurately or not at all.

### 7.4 SEP process

Proposed changes to the specification must be submitted as Specification
Enhancement Proposals. 2026-07-28 formalized the mechanics (SEP-1850):

> Formalize PR-based SEP workflow with markdown files in `seps/` directory, PR-derived numbering, sponsor responsibilities, and status management via PR labels.

Extensions have their own SEP track (SEP-2133), and the bar includes a working
implementation:

> **Implement**: Build at least one reference implementation in an official SDK — this is required before the SEP can be reviewed.

### 7.5 The 2026 roadmap

Source: https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/ (published 2026-03-09, verified 2026-09-17)

The roadmap moved from release-based planning to **priority areas** driven by
Working Groups. Four areas:

1. **Transport Evolution and Scalability**: horizontal scaling, session management, server capability discovery via `.well-known` metadata
2. **Agent Communication**: refining the Tasks primitive with retry semantics and result expiry policies
3. **Governance Maturation**: a contributor ladder and a delegation model so Working Groups can approve SEPs within their domain without full Core Maintainer review
4. **Enterprise Readiness**: audit trails, SSO authentication, gateway behavior, and configuration portability, addressed **through extensions rather than core changes**

Quotes:

> SEPs aligned with the priority areas above will move the fastest.

> We are **not** adding more official transports this cycle but evolve the existing transport.

> Working Groups drive the timeline for their deliverables

"On the Horizon" items with community interest but lower maintainer capacity:
triggers, event-driven updates, and security enhancements.

**Speaker note, load-bearing for the talk:** point 4 is the roadmap explicitly
committing that enterprise readiness will be delivered as **optional extensions**,
not as core requirements. That is a maintainer-stated position, not an inference.

---

## 8. Explicitly OPTIONAL but load-bearing for enterprise deployment

This is the enumeration. Every item is optional or non-binding by the letter of
the specification, and every item is something a serious enterprise deployment
cannot do without. Each has its source cited above.

### Tier 1: optional at the top level

| # | Thing | Normative status | Why it is load-bearing |
|---|---|---|---|
| 1 | **Authorization itself** | "Authorization is **OPTIONAL** for MCP implementations." HTTP implementations **SHOULD** conform. | A SHOULD-conformant server can be fully spec-compliant with no auth at all. There is no conformance level that requires it. |
| 2 | **Authentication on Streamable HTTP** | "Servers **SHOULD** implement proper authentication for all connections." | SHOULD, not MUST, even for the network-exposed transport. |
| 3 | **Custom auth schemes** | "clients and servers **MAY** negotiate their own custom authentication and authorization strategies." | An explicit sanctioned escape hatch from every MUST in Section 3. |

### Tier 2: the extensions, all opt-in by definition

Extensions overview, verbatim:
> Extensions are always disabled by default and require explicit opt-in from the developer.
> SDKs can choose to implement extensions, but it's not required for protocol conformance.

| # | Extension | Identifier | Enterprise function it carries |
|---|---|---|---|
| 4 | **Enterprise-Managed Authorization** | `io.modelcontextprotocol/enterprise-managed-authorization` | Centralized IdP policy, SSO, single-console grant and revoke, auditable authorization trail. The entire enterprise access-control story lives here, outside the core spec. |
| 5 | **OAuth Client Credentials** | `io.modelcontextprotocol/oauth-client-credentials` | Machine-to-machine auth. No user in the loop. |
| 6 | **Tasks** | `io.modelcontextprotocol/tasks` | Long-running work. With resumability removed from the transport, this is now the only durable path for an operation that outlives a stream. |
| 7 | **MCP Apps** | `io.modelcontextprotocol/ui` | Server-rendered interactive UI. |
| 8 | **Skills over MCP** | ext-skills | Structured workflow instructions. |

EMA detail, from https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization:

The extension exists precisely because the core model does not serve enterprises:

> In enterprise environments, this model creates friction and security gaps:
> * Employees shouldn't need to understand the authorization details of every MCP server their organization uses
> * Security teams can't enforce consistent access policies if each user authorizes independently
> * Onboarding new employees requires them to manually authorize dozens of services
> * Offboarding requires revoking access across every service individually

Mechanism: the client obtains an Identity Assertion JWT Authorization Grant
(ID-JAG) from the enterprise IdP and exchanges it for an access token at the MCP
authorization server. Origin: SEP-990.

Client support caveat, verbatim:

> Support for this extension varies by client. Extensions are opt-in and never active by default.

### Tier 3: SHOULDs inside the authorization spec that enterprises depend on

| # | Thing | Status | Consequence if skipped |
|---|---|---|---|
| 9 | `scope` in the `WWW-Authenticate` challenge | Servers **SHOULD** | Clients fall back to requesting every scope in `scopes_supported`. Least privilege collapses by default. |
| 10 | `iss` in authorization responses (RFC 9207) | Authorization servers **SHOULD** | Mix-up attack mitigation "provides no protection against an honest server that does not" emit `iss`. The spec says a future revision is expected to raise this to MUST. |
| 11 | Client ID Metadata Documents | Clients and AS **SHOULD** | The only portable client identity. Without it, every AS change forces re-registration. |
| 12 | `io.modelcontextprotocol/clientInfo` | Clients **SHOULD** | Attribution in logs. And the spec warns it is self-reported and **SHOULD NOT** be relied on for security decisions, so it is unreliable even when present. |
| 13 | `io.modelcontextprotocol/serverInfo` | Servers **SHOULD** | Same. |
| 14 | Deterministic tool ordering | Servers **SHOULD** | Client-side caching and prompt cache hit rates. |
| 15 | Short-lived access tokens | Authorization servers **SHOULD** | Blast radius on token theft. |
| 16 | SSRF mitigations on OAuth metadata fetches | Clients **SHOULD** require HTTPS, **SHOULD** block private IP ranges | Cloud metadata endpoint credential exfiltration. A SHOULD guards the 169.254.169.254 attack. |
| 17 | Human in the loop on tool invocation | "there **SHOULD** always be a human in the loop with the ability to deny tool invocations" | The entire consent model for tool execution is a SHOULD. |

### Tier 4: structural optionality

| # | Thing | Note |
|---|---|---|
| 18 | **Audit trail** | Not in the core specification at all. Named as a 2026 roadmap Enterprise Readiness item, to be delivered "through extensions rather than core changes." OpenTelemetry `_meta` keys are the only protocol-level observability hook, and they are optional. |
| 19 | **Private registry** | No supported implementation. OpenAPI contract only. Official codebase explicitly not designed for self-hosting. |
| 20 | **`x-mcp-header`** | "While the use of `x-mcp-header` is optional for servers, clients **MUST** support this feature." Optional on the side that needs it for gateway routing. |
| 21 | **Extension graceful degradation** | If one side lacks an extension, the other "needs to either fall back to core protocol behavior or reject the request." Fallback is the documented norm, which means a security extension can be negotiated away unless the server refuses. |

**The argument this supports:** MCP's normative core is rigorous about how to do
authorization correctly and silent about whether to do it at all. Every control
an enterprise security team would consider mandatory (centralized policy, SSO,
audit trail, private catalogue, durable execution) sits in an extension, a
SHOULD, or nothing. That is a deliberate design choice, stated in the 2026
roadmap, and it is defensible. It is also the gap a city, a bank, or a hospital
has to close itself.

---

## 9. Quick-reference table for slides

| Question | Verified answer, 2026-09-17 |
|---|---|
| Current spec revision | `2026-07-28` |
| Previous revisions | 2024-10-07, 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25 |
| Draft revision contents | Empty |
| Is authorization mandatory? | No. Still literally "OPTIONAL". |
| Is RFC 9728 mandatory? | Yes, for any server that does authorization. MUST since 2025-06-18. |
| Is RFC 8707 mandatory? | Yes, for clients. MUST, regardless of AS support. |
| Is DCR still recommended? | No. MAY, and Deprecated since 2026-07-28. |
| What replaces DCR? | Client ID Metadata Documents (SHOULD). |
| Is token passthrough allowed? | No. Verbatim 2026-07-28 core authorization text: "MCP servers **MUST** only accept tokens that are valid for use with their own resources." and "MCP servers **MUST NOT** accept or transit any other tokens." (The tidier sentence "MUST NOT accept any tokens that were not explicitly issued for the MCP server" is 2025-06-18 wording. Do not put it on a slide attributed to the current revision.) |
| Are there sessions? | No. Removed in 2026-07-28. |
| Is SSE resumable? | No. Removed in 2026-07-28. |
| Is HTTP+SSE dead? | Deprecated since 2025-03-26, formally Deprecated under the lifecycle policy in 2026-07-28. |
| Can servers send requests? | No. MRTR replaced server-initiated requests in 2026-07-28. |
| Are Sampling/Roots/Logging alive? | Deprecated 2026-07-28, earliest removal on or after 2027-07-28. |
| Is the Registry GA? | No. Preview. |
| Who governs MCP? | AAIF under the Linux Foundation since 2025-12-09. Maintainers retain technical autonomy. |
| Lead Maintainers | David Soria Parra, Den Delimarsky |

---

## 10. Facts to re-verify the week of the talk (week of 2026-09-29)

Priority order, highest exposure first. A wrong answer to items 1 through 4 in
front of MCP maintainers is the expensive kind of wrong.

1. **Is `2026-07-28` still the current revision?** Check https://modelcontextprotocol.io/specification/versioning for the "current protocol version" line. A new RC or revision between now and 2026-10-06 would invalidate a large part of this document.

2. **Has the draft changelog accumulated anything?** https://modelcontextprotocol.io/specification/draft/changelog was empty on 2026-09-17. Anything new there is a signal about what maintainers are shipping next, and it is exactly what this audience will be thinking about.

3. **Is the "Authorization is OPTIONAL" sentence still present, word for word?** https://modelcontextprotocol.io/specification/latest/basic/authorization. This is the spine of the talk. Re-read it, do not trust this file.

4. **Has the `iss` SHOULD been raised to MUST?** The spec says a future revision is expected to do this. If it has happened, the Section 3.8 framing changes.

5. **Has any Deprecated feature been Removed?** https://modelcontextprotocol.io/specification/2026-07-28/deprecated, "Removed" section. It said "No features have been removed under this policy yet" on 2026-09-17.

6. **Has the MCP Registry gone GA?** Check both https://modelcontextprotocol.io/registry for the preview note and https://blog.modelcontextprotocol.io/ for an announcement. This has been "preview, GA to follow" for over a year, so a change is plausible and would be newsworthy to the room.

7. **Has the registry `server.json` schema moved off the `draft` path?** The schema URL still contains `/draft/`.

8. **Current Lead and Core Maintainer list.** https://modelcontextprotocol.io/community/governance. People join and go emeritus. Verify before naming anyone from the stage.

9. **Any new official extension, or any experimental extension graduating?** https://modelcontextprotocol.io/extensions/overview. Enterprise Managed Authorization's status in particular, since it carries the enterprise argument.

10. **Roadmap update.** https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/ was published 2026-03-09. Check the blog index for a mid-year revision or a 2027 roadmap post.

11. **December 2025 ecosystem figures (97M monthly SDK downloads, 10,000 active servers).** These are nine months stale. Either find a dated refresh or present them with "as of December 2025" attached. Do not round or update them by guess.

12. **AAIF membership roster.** The Platinum/Gold/Silver lists are from the 2025-12-09 press release. If a sponsor in the room joined later, the list is incomplete.

### Items marked UNVERIFIED in this document

- The MCP Registry README's "API freeze (v0.1)" date. The README text reads as written in October 2025 and may be stale; the preview status itself is verified current.
- Any quantitative claim about real-world token passthrough violations.
- Any September 2026 refresh of the December 2025 ecosystem figures.

---

## 11. Independent verification by the parent session, 2026-09-17

The claims this talk leans on hardest were re-checked against primary sources by
a second reader, because a research agent's summary is a claim like any other and
this deck is delivered to the people who maintain the specification.

Confirmed verbatim from the live spec on 2026-09-17:

| Claim | Verdict | Source |
|---|---|---|
| Current revision is 2026-07-28 | CONFIRMED. "The **current** protocol version is [**2026-07-28**]" | /specification/versioning |
| "Authorization is **OPTIONAL** for MCP implementations. When supported: Implementations using an HTTP-based transport **SHOULD** conform to this specification." | CONFIRMED verbatim | /specification/2026-07-28/basic/authorization |
| Servers MUST implement RFC 9728; clients MUST use it for authorization server discovery | CONFIRMED | same |
| Clients MUST implement RFC 8707 and "**MUST** send this parameter regardless of whether authorization servers support it" | CONFIRMED verbatim | same |
| Clients MUST apply RFC 9207 issuer validation before transmitting the authorization code | CONFIRMED. Note the asymmetry: authorization servers **SHOULD** include `iss`, clients **MUST** validate it. The spec states a future revision is expected to raise the server side to MUST | same |
| Dynamic Client Registration is deprecated, replaced by Client ID Metadata Documents | CONFIRMED. "Note that Dynamic Client Registration is deprecated and retained for backwards compatibility with authorization servers that do not support Client ID Metadata Documents" | same |
| Roots, Sampling, Logging and DCR all deprecated in 2026-07-28, earliest removal a revision released on or after 2027-07-28 | CONFIRMED against the deprecated features registry | /specification/2026-07-28/deprecated |
| The handshake is gone | CORROBORATED. The versioning page refers to "the handshake-based protocol revisions (`2025-11-25` and earlier)" and links a "Backward Compatibility with initialization-based versions" section | /specification/versioning |
| `server/discover` is a mandatory RPC | CONFIRMED with a nuance worth keeping: the RPC is mandatory for servers, and "Calling it is optional" for clients | /specification/versioning |

Corrections applied to this file as a result:

1. **Section 9 token passthrough quote.** The quick-reference table carried
   "MCP servers MUST NOT accept any tokens that were not explicitly issued for
   the MCP server." That is the 2025-06-18 wording. The 2026-07-28 core
   authorization page reads "MCP servers **MUST** only accept tokens that are
   valid for use with their own resources." and "MCP servers **MUST NOT** accept
   or transit any other tokens." Corrected in place, with a note, because that
   table exists to be lifted onto slides and the older sentence is the tidier
   one, which is exactly how a misquote survives review.

Two details worth carrying into the talk that the summary flattened:

- **The `iss` asymmetry is a better example than a flat MUST.** The spec asks
  clients to validate something servers are only advised to send. That is the
  optional-at-the-door pattern appearing inside the hardened part, and it is
  self-aware: the spec says it expects to raise the server obligation later.
- **The deprecation of Logging names OpenTelemetry as the migration path.** The
  registry's stated path is "Log to `stderr` for stdio transports; use
  OpenTelemetry for observability". The protocol is handing observability to
  OTel by name.
