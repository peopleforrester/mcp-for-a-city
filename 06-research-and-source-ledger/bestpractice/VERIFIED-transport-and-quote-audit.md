---
title: "Parent session verification: transport headers, and one quote that did not survive"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: verified
---

<!-- ABOUTME: Independent verification of the 2026-07-28 transport header claims and an audit of the roadmap quote. -->
<!-- ABOUTME: One widely used quote in this repo is now UNVERIFIED and must not reach a slide until located. -->

## VERIFIED: the routing headers, quoted from the specification

Source: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
Read 2026-09-18. Section "Standard Request Headers".

| Header Name | Source Field | Required For |
| --- | --- | --- |
| `Mcp-Method` | `method` | All requests |
| `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` requests |

> These headers are **REQUIRED** for compliance.

The stated purpose, verbatim:

> The Streamable HTTP transport mirrors selected JSON-RPC body fields into HTTP
> headers so that intermediaries (load balancers, gateways, observability
> tooling) can route and inspect requests without parsing the body.

Enforcement: servers that process the body **MUST** reject header and body
mismatches with `400 Bad Request` and JSON-RPC error `-32020` (`HeaderMismatch`).
A missing required header is itself a listed failure condition.

The specification gives the reason, and it is the gateway threat model stated by
the spec itself:

> This prevents potential security vulnerabilities when different components in
> the network rely on different sources of truth (e.g., a load balancer routing
> on the header value while the MCP server executes based on the body value).

And the trap for anyone enforcing policy at a gateway:

> Intermediaries that enforce policy based on mirrored headers (e.g., routing or
> rate-limiting by tenant) **SHOULD** verify that the `MCP-Protocol-Version`
> header indicates a version that requires header-body validation. If the version
> is older or the header is absent, the intermediary **SHOULD** reject the
> request rather than trusting unvalidated header values.

## VERIFIED and underused: `x-mcp-header` puts tool ARGUMENTS in headers

This did not feature in the research summaries and it is the most consequential
part of the section for a gateway argument.

A server **MAY** annotate a tool parameter with `x-mcp-header` in its
`inputSchema`, and the client then mirrors that argument value into a
`Mcp-Param-{Name}` HTTP header. Clients **MUST** support this:

> While the use of `x-mcp-header` is optional for servers, clients **MUST**
> support this feature.

The spec's own example annotates the `region` parameter of an `execute_sql`
tool, producing `Mcp-Param-Region: us-west1` on the wire.

Why this matters for the talk: as of 2026-07-28 a gateway can route, rate limit
and authorize on **a tool argument** at layer 7, without parsing a body and
without understanding the tool. Combined with the mandatory header-body
validation, argument-level policy becomes an ordinary HTTP concern.

Constraints worth knowing before claiming too much: primitive types only,
integer and string and boolean, no `number`; the property must be statically
reachable through `properties` keys only, so nothing behind `items`, `oneOf`,
`anyOf`, `allOf`, `not`, `if`/`then`/`else` or `$ref`; and non-ASCII values ride
as `=?base64?...?=`, which an intermediary **MUST** decode before comparing.

So it is real and it is bounded. It does not give a gateway argument-level
policy over arbitrary nested arguments, only over primitives the server chose to
expose.

## RESOLVED: the "hundred tools" quote is real, and the short version is a misquote

First pass of this audit marked the quote unverified after reading
https://modelcontextprotocol.io/development/roadmap, which does not contain it.
That was the wrong page. The quote lives in the announcement blog post, which is
the source the token economics research cited correctly.

**Verified 2026-09-18** from https://blog.modelcontextprotocol.io/posts/mcp-roadmap/
"The New MCP Roadmap", David Soria Parra and Den Delimarsky, Lead Maintainers,
published 2026-08-22, under "Improved primitives". Verbatim:

> "Connecting to a server with a hundred tools means the model pays for that
> entire surface before the user has asked a single question, and tool selection
> tends to get worse as the list grows. We're starting a progressive discovery
> effort so a server can offer a small entry point and reveal more of its catalog
> as the conversation narrows."

**The shortened form is a misquote.** "A server with a hundred tools means the
model pays for that entire surface before the user has asked a single question"
drops the opening clause and changes the subject of the sentence. It appears in
`06-research-and-source-ledger/ops/mcp-operations-at-scale-2026-09.md` and has been flagged there.

If this goes on a slide, put the whole sentence up and attribute it to both lead
maintainers by name and to the post by date. Both of them are speaking at this
event, and Den Delimarsky keynotes on the Monday.

Note for anyone re-verifying: there are two distinct roadmap surfaces, the
documentation page at modelcontextprotocol.io/development/roadmap and the
announcement post at blog.modelcontextprotocol.io. They carry the same date and
overlapping but differently worded content. Check the blog post for quotations.

## Also unresolved: the `cacheScope` hazard

The claim is that filtering `tools/list` by credential and marking the result
`cacheScope: "public"` can let a shared intermediary serve one caller's tool list
to another, and that the security-correct value `"private"` surrenders the shared
cache saving.

`cacheScope` is real: the roadmap confirms "The most recent protocol revision
made strides toward caching, adding `ttlMs` and `cacheScope` to list results and
resource reads ([SEP-2549])". The hazard text was not on the Streamable HTTP
page read on 2026-09-18 and has not yet been located in the specification.

**Status: mechanism plausible and partially corroborated, exact wording
UNVERIFIED.** Locate it in SEP-2549 or the tools or basic index pages before
using it. It is the most original technical claim in the corpus and therefore
the one most worth getting exactly right.

---

## RESOLVED 2026-09-18: the `cacheScope` hazard is real and the spec states it

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching
Section "Security Considerations". Verbatim:

> "Servers MUST be aware that responses with a `"public"` `cacheScope` may be
> shared between callers even if the Result is coming from an authenticated
> endpoint. For example, the Result from an authenticated `tools/list` call with
> a `"public"` `cacheScope` may be cached by a client and may be shared outside
> of the initial requests authorization context. (i.e. different access tokens
> can leverage the same cache)."

And:

> "MUST apply appropriate per-primitive access controls, and MUST NOT rely on
> `cacheScope` alone to prevent unauthorized access to primitives."

The scope table, verbatim:

> `"public"`: The response does not contain user-specific data. Any client,
> shared gateway, or caching proxy **MAY** store and serve the cached response to
> any user.
>
> `"private"`: The response contains private data that is not meant to be shared
> between callers. Cached responses **MAY** be reused for the same authorization
> context. Caches **MUST NOT** be shared across authorization contexts (e.g. a
> different access token requires a different cache).

**Important correction to how this was first framed.** The specification does
*not* leave this as a trap. Under "Choosing a Cache Scope" it says `"public"` is
appropriate for tool lists "when they are identical for all users", and
`"private"` is appropriate for "filtered list results that vary per user". A
filtered list is not identical for all users, so the spec already gives the right
answer.

The honest framing for the stage is therefore narrower and better:

The specification anticipated this, named it, and told you which value to use.
What it does not do is price the trade. Filtering `tools/list` by credential is
the single control that cuts tokens, lifts selection accuracy and shrinks the
reachable surface at the same time. Choosing it correctly forces
`cacheScope: "private"`, which surrenders the shared-cache saving that a gateway
in front of many users would otherwise get. The cost control and the access
control are the same field, and doing the right thing costs money.

Do not say the spec created a footgun. Say the spec made you choose, and that the
cheap answer and the safe answer are different.

Related and verified on the tools page: `tools/list` **MUST NOT** vary per
connection, but the set **MAY** vary by the authorization presented on the
request, "since credentials are per-request input, not connection state". That is
what makes credential-filtered tool lists legal in the first place.

## VERIFIED: the bound on `x-mcp-header`, correcting an earlier overclaim

Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
Section "x-mcp-header". Verbatim:

> "Server developers **SHOULD NOT** mark sensitive parameters (passwords, API
> keys, tokens, PII) with `x-mcp-header`, as header values are visible to network
> intermediaries."

This materially bounds the earlier claim in this repository that argument-level
gateway policy became an ordinary layer 7 concern in 2026-07-28. It did, for
routing-shaped arguments such as a region or a tenant, which is what the spec's
own `execute_sql` example shows. It did not for the arguments a security reviewer
most wants to police, because the spec tells server authors to keep those out of
headers.

So a gateway sees: the protocol version, `Mcp-Method`, `Mcp-Name`, and whichever
non-sensitive arguments a server author chose to expose. Anything further
requires parsing the body.

## VERIFIED: tool annotations are untrusted, with the qualifier intact

Source: same tools page. Verbatim:

> "For trust & safety and security, clients **MUST** consider tool annotations to
> be untrusted unless they come from trusted servers."

The trailing qualifier "unless they come from trusted servers" matters and was
dropped in one research summary. Quote the whole sentence.

## VERIFIED: the Registry working group rules out building you one

Source: `docs/community/working-groups/registry.mdx`, modelcontextprotocol
repository, read through the GitHub API 2026-09-18. Under the heading
**Out of Scope**, verbatim:

> "Any commitment to delivering an enterprise-ready or reusable registry
> implementation. The codebase supports this instance only and is not intended
> for external deployments."

The same list also rules out "Hosting, distributing, or executing MCP server code
or binaries", with the clarifying line that "the registry is a metadata catalog,
not a package registry".

This is the strongest single sentence in the corpus for the delegation chain
argument, because it is not an omission or an oversight. It is a scope decision,
written down, by the working group responsible. Present it that way.
