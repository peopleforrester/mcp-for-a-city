---
title: "The Microsoft Stack for Governing MCP at Enterprise Scale"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
---

<!-- ABOUTME: What Microsoft actually ships for governing MCP as of September 2026, product by product, -->
<!-- ABOUTME: with GA versus preview marked, and what is still missing against the gateway and registry requirements. -->

# The Microsoft Stack for Governing MCP at Enterprise Scale

Speaker preparation for "Governing MCP for a Workforce the Size of a City", MCP
Dev Summit Toronto, 2026-10-06.

Everything below is **[VENDOR]** unless otherwise labelled. Microsoft
documentation about Microsoft products is the least independent category of
evidence there is. It is used here because the question is what Microsoft ships,
which only Microsoft can answer, and because the one candid limitation in the
set is worth more than the rest of it combined.

## Labels

| Label | Meaning |
|---|---|
| **[VENDOR]** | Microsoft's own documentation, repository, or engineering blog |
| **[OFFICIAL]** | The MCP specification or an MCP project document |
| **[MEASURED]** | Measured by this research on 2026-09-18, command and result shown |
| **[UNVERIFIED]** | Could not be traced to a source that makes the claim |

Status language follows Microsoft's own words. Where a doc carries a preview
banner it is quoted. Where a doc carries no banner and lists service tiers, it
is treated as generally available in those tiers and said so explicitly. A
roadmap sentence is never treated as a shipped feature.

## The one-paragraph version

Microsoft does not have one MCP control plane. It has **two**, built by
different organisations, with different scopes, and a large Microsoft-centric
enterprise will probably have both without anyone having decided to. The Azure
side is Azure API Management plus Azure API Center plus Microsoft Foundry
Toolbox, and it governs servers and agents the platform team builds. The
Microsoft 365 side is Microsoft Agent 365 and its Tooling Gateway, and it
governs what agents and Copilot users can reach inside the tenant. Identity for
both is Microsoft Entra Agent ID. The single strongest control in the whole set
is not on either control plane: it is the VS Code enterprise MCP policy, which
reaches the local stdio servers on developer laptops that no gateway can see.

---

# 1. The control plane pieces

## 1.1 Azure API Management: the gateway

**Status: generally available in the listed tiers.** The overview carries no
preview banner and states availability as "Classic tiers: Developer, Basic,
Standard, Premium" and "v2 tiers: Basic v2, Standard v2, Premium v2". Doc
`ms.date` 2026-09-11.
Source: https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview
(verified 2026-09-18). **[VENDOR]**

Two documented ways to produce an MCP server, which is the distinction worth
carrying into a conversation:

| Source | What it does |
|---|---|
| **REST API as MCP server** | "Expose any REST API managed in API Management as an MCP server, including REST APIs imported from Azure resources. API operations become MCP tools." |
| **Existing MCP server** | "Expose an MCP-compatible server (for example, LangChain, LangServe, Azure Logic Apps, Azure Functions) via API Management." |

The first is the one to be careful about. An automatic REST-to-tools conversion
is exactly the anti-pattern a companion Toronto session is built around
("It's tempting to point your coding agent at your REST API, have it port every
endpoint, and ship it. Don't.", schedule research, 2026-10-06 session on tool
design). APIM makes that conversion a portal operation.

**What it actually enforces**, in Microsoft's own list: rate limiting and quota,
authentication and authorization by JWT validation, IP filtering, and caching.
Plus the one sentence a platform team needs to hear read aloud:

> Currently, policies apply to all API operations exposed as tools in the MCP
> server.

That is the granularity. Not per tool, and certainly not per argument. Section 6
returns to this.

**Two limitations Microsoft states plainly**, both quoted verbatim from the same
page:

> API Management currently supports MCP server tools, but doesn't support MCP
> resources or prompts.

> API Management MCP server capabilities currently aren't supported in
> [workspaces](https://learn.microsoft.com/en-us/azure/api-management/workspaces-overview).

The workspaces exclusion matters more than it looks. Workspaces are how large
APIM estates delegate API ownership to federated teams. An organisation that
adopted workspaces for its API programme cannot use them for its MCP programme
today, which means the MCP estate is centralised whether or not that was the
plan.

There is also an opt-in early-access channel, which is a useful thing to know
exists before someone claims a capability you cannot find:

> You can get early access to new MCP server and AI gateway features and
> capabilities through the *AI Gateway* release channel.

## 1.2 Azure API Center: the registry

**Status: no preview banner.** Doc `ms.date` 2026-05-29, `updated_at`
2026-06-18.
Source: https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server
(verified 2026-09-18). **[VENDOR]**

Covered in depth in the companion gateway and registry research, section 5.4.
Only the additions and the governance-relevant detail are repeated here.

The registry endpoint, which is the reason API Center is worth showing at all,
because it is one of the very few private registries that publishes its shape:

```
https://<your-api-center-name>.data.<region>.azure-apicenter.ms/workspaces/default/v0.1/servers
```

Note the `v0.1`, matching the official registry API version. A client configured
against it does not know it is talking to Azure.

**The metadata mechanism is real and the vocabulary is not.** API Center's own
words:

> The MCP registry stores standard discovery and configuration metadata for MCP
> servers such as the server name, URL, and transport type. You can optionally
> extend the metadata by configuring custom properties that appear in the
> `_meta` section of MCP server responses to tool calls. You can map your API
> center's metadata properties into structured namespaces for MCP clients to
> consume.

This is exactly the `_meta` namespace pattern the official registry docs sanction
for subregistries. So approval status, owning team and data classification are
**expressible** in API Center, under a namespace you invent. Nothing tells
another tool what your namespace means. That is the same gap the companion
research identifies as a naming problem rather than a schema problem, and API
Center does not close it.

There is a per-version **Version lifecycle** field in the registration form,
which is the closest thing to a native approval-status field. Its values are the
API Center version lifecycle values, not an MCP vetting vocabulary.

**Ingestion sources are Azure-shaped.** Sync is documented from exactly two
places: an Azure API Management instance, and a Git repository. There is a
curated "partner MCP servers" list inside the portal covering "MCP servers from
Microsoft services such as Azure Logic Apps, GitHub, and others". **No sync from
the official MCP registry at `registry.modelcontextprotocol.io` is documented.**
Section 6.3 treats that as the federation gap it is.

**New since the companion research was written:** API Center now feeds Foundry.

> MCP servers registered in your API center can now be integrated with Microsoft
> Foundry's tool catalogs, enabling you to govern MCP tools and make them
> available to AI agents.

## 1.3 Microsoft Foundry Toolbox: the aggregating endpoint

This is the piece most likely to be missed, because it was renamed. The page
titled "tool catalog" now canonicalises to **Toolbox**, at
`/azure/foundry/agents/concepts/toolbox-overview`, and "Azure AI Foundry" is now
"Microsoft Foundry". Doc `ms.date` 2026-07-28.
Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/toolbox-overview
(verified 2026-09-18). **[VENDOR]**

Toolbox is an aggregating MCP gateway by another name:

> With Toolbox, you define a curated set of tools once and expose them through a
> single MCP-compatible endpoint that agents can consume across frameworks and
> runtimes.

**Status is split and the split matters.** Toolbox itself carries no preview
banner. Two of its headline capabilities do: **Tool search (preview)** and
**Skills (preview)**. Tool search is the token-economics answer, hiding tools
behind two meta-tools `tool_search` and `call_tool`, and it is the feature an
organisation with hundreds of tools will actually need. It is in preview.

Four GA capabilities, in Microsoft's words: single endpoint, centralized
authentication ("credential injection, token refresh, and policy enforcement at
runtime by using Microsoft Entra ID and OAuth identity passthrough"), "Governance
by default" (Responsible AI guardrails on tool inputs and outputs), and
versioning with promotion of a default version.

It is not Azure-only by design:

> Toolboxes are created and managed in Microsoft Foundry, but they aren't limited
> to Foundry-based agents. Any MCP-compatible runtime or client can use a
> toolbox, including custom agents built with Microsoft Agent Framework,
> LangGraph, or your own code.

**Per-agent controls on the direct MCP tool**, from the how-to page (doc
`ms.date` 2026-08-26,
https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol,
verified 2026-09-18):

- `allowed_tools`, an explicit per-tool allowlist. Microsoft's guidance: "Use an
  allow list of tools by using `allowed_tools`."
- `require_approval`, with `always` demonstrated in the samples, producing an
  `mcp_approval_request` the caller must answer. The sample comment is honest
  about where the work is: "In production, implement your own approval UX and
  policy."
- Authentication types: `custom headers`, `oauth2` (Foundry-managed app or your
  own registration), `user-entra-token`, `project-managed-identity`, and
  `agentic-identity`.
- Long-running operations via MCP tasks are **preview**: "Long-running MCP
  operations are in preview. Preview features are provided without a
  service-level agreement and aren't recommended for production workloads."

Microsoft draws the trust boundary itself, which is a useful sentence to have
ready:

> Foundry Toolboxes are different from third-party MCP servers. Toolboxes are
> organization-governed resources that you create and manage within your
> Microsoft Foundry project. However, you're still responsible for tool
> selection, data handling, and compliance when curating Toolbox contents.

## 1.4 Microsoft Agent 365 and the Tooling Gateway: the Microsoft 365 control plane

This is the piece a Microsoft-centric enterprise is most likely to be running
without the platform team knowing, because it is administered from the Microsoft
365 admin center rather than from Azure.

Sources:
https://learn.microsoft.com/en-us/microsoft-365/admin/manage/manage-tools-for-agent
(doc `ms.date` 2026-07-30) and
https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview
(doc `ms.date` 2026-08-10), both verified 2026-09-18. **[VENDOR]**

The Work IQ MCP overview carries a preview banner covering the page:

> - This is a preview feature.
> - Preview features aren't meant for production use and might have restricted
>   functionality.

The admin surface is `Agents > Tools`, with a **Registry** tab and a **Requests**
tab. Actions on a listed tool are Block and Unblock. Status is Available or
Blocked. Blocking is described as total:

> If an MCP server is blocked, it's blocked for every user and every agent.
> Permissions always take priority over configuration, so IT admins have
> ultimate authority to maintain security and compliance.

**Bring Your Own MCP server is the interesting part, and it is in preview.** The
banner:

> - This feature is a preview feature.
> - Preview features aren't meant for production use and might have restricted
>   functionality.

Microsoft's statement of the problem it solves is unusually direct about the
status quo:

> Large enterprises often build and operate internal MCP servers to power their
> agents across various business workflows. These servers typically run outside
> any organizational governance boundary, with no admin visibility into what
> tools are exposed, no policy enforcement over how they're invoked, and no usage
> of telemetry for security and compliance teams.

The flow is developer registers via CLI, admin reviews and approves in the M365
admin center, admin grants the Entra permissions, approved server becomes usable
in the supported clients, security team monitors in Defender. The four governance
controls, quoted from the table:

| Control | Description |
|---|---|
| Approval/Rejection | "Admin explicitly approves or rejects each BYO MCP server before it can be used." |
| Server-Level Block | "Admin can block approved servers at any time; blocked servers are enforced at runtime." |
| Tools Snapshot | "Admin can view the declared tools exposed by each MCP server for transparency." |
| Runtime Enforcement | "Blocked MCP servers can't be invoked at runtime across any client surface." |

Supported authentication types at registration: `NoAuth`, `APIKey` (header or
query), `ExternalOAuth`, `EntraOAuth`. Note that `NoAuth` is a first-class,
documented option with a working example.

Observability is Microsoft Defender advanced hunting, with Microsoft's own
sample query:

```kusto
CloudAppEvents
| where ActionType in ( "ExecuteToolByGateway")
| where RawEventData contains "tool name"
```

**Three limitations stated outright, all of them operationally sharp:**

> Microsoft doesn't currently support deleting a BYO MCP server.

> BYO MCP server is currently in preview. Republishing new versions of your
> remote MCP server isn't currently supported.

> The ability to allow or disallow tooling and MCP servers in Microsoft 365 admin
> center might not be available in your region yet.

No delete and no republish, together, mean the registry is append-only in
practice and a server cannot be revised. Block is the only lever. And the
regional caveat means "we have this control" needs to be checked against the
tenant's own region before it is believed.

**Client coverage is partial**, quoted from the same page:

> Supported client surfaces are Copilot Studio, Visual Studio Code, Claude Code,
> and GitHub Copilot CLI. Azure AI Foundry and Microsoft 365 Declarative Agents
> aren't yet supported.

Claude Code appearing in a Microsoft governance surface is worth noticing on its
own. The two control planes do not yet cover each other: the Microsoft 365
control plane explicitly does not govern Foundry agents.

## 1.5 Copilot Studio

Doc `ms.date` 2026-08-26, no preview banner on the MCP extension page.
Source: https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-mcp
(verified 2026-09-18). **[VENDOR]**

Supports MCP tools and resources, not prompts: "Copilot Studio currently supports
MCP tools and resources." Requires generative orchestration to be on. Tool and
resource changes propagate automatically, which is the runtime-drift problem the
MCP Security IG has open with no champion:

> When you update or remove tools and resources on the MCP server, Copilot Studio
> dynamically reflects these changes.

Microsoft places the responsibility explicitly on the customer:

> When you connect to a non-Microsoft product, including an external MCP server,
> you're responsible for the tools and resources you access from within Copilot
> Studio.

**Power Platform data policies reach MCP only indirectly**, and the mechanism is
worth understanding because it is easy to overestimate. From the DLP doc
(`ms.date` 2026-05-15, `updated_at` 2026-09-10,
https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-data-loss-prevention,
verified 2026-09-18):

> Blocking Power Platform connectors also blocks access to tools in connected MCP
> servers, which rely on Power Platform connectors for connectivity.

That is a transitive block through the connector, not a native MCP policy object.
Connectors classify into Business, Non-business and Blocked groups, with
tenant-wide or per-environment scope, and enforcement is real time since early
2025 with no exemptions ("Agent data policy enforcement exemption is no longer
supported"). But there is no documented way to write a Power Platform data policy
against a named MCP server, or against a named tool within one.

## 1.6 Microsoft MCP Server for Enterprise (Graph)

**PREVIEW.** Banner quoted verbatim:

> Microsoft MCP Server for Enterprise is currently in PREVIEW. This information
> relates to a prerelease product that may be substantially modified before it's
> released. Microsoft makes no warranties, expressed or implied, with respect to
> the information provided here.

Endpoint `https://mcp.svc.cloud.microsoft/enterprise`. Read-only over Microsoft
Entra directory data. Three tools: `microsoft_graph_suggest_queries`,
`microsoft_graph_get`, `microsoft_graph_list_properties`. Global cloud only, not
available in US Government L4/L5 or 21Vianet. 100 calls per minute per user.
Doc `ms.date` 2025-11-18.
Source: https://learn.microsoft.com/en-us/graph/mcp-server/overview
(verified 2026-09-18). **[VENDOR]**

The genuinely useful operational detail is the audit path, because it is a
concrete answer to "how would we know": every call lands in Microsoft Graph
activity logs under a fixed appId.

```kusto
MicrosoftGraphActivityLogs
| where TimeGenerated >= ago(30d)
| where AppId == "e8c77dc2-69b3-43f4-bc51-3213c9d915b4"
| project RequestId, TimeGenerated, UserId, RequestMethod, RequestUri, ResponseStatusCode
```

That appId is a usable detection signal today for an organisation that has not
decided whether it wants this server in use.

## 1.7 Two open-source Microsoft gateways, neither of them a product

**`microsoft/mcp-gateway`**, MIT, created 2025-05-14, last pushed 2026-09-11.
**[MEASURED]** via `gh repo view`, 2026-09-18.
Source: https://github.com/microsoft/mcp-gateway

Self-described as "a reverse proxy and management layer for MCP servers,
enabling scalable, session-aware routing, authorization and lifecycle management
of MCP servers in Kubernetes environments." It has a data plane, a control plane
with `/adapters` and `/tools` CRUD, a "Tool Gateway Router", and bearer
token/RBAC on both planes. Agents and Sessions are marked Preview in the README.

One thing to notice rather than repeat from the stage: its central design
concept is **"Session-Aware Stateful Routing: Ensures that all requests with a
given `session_id` are consistently routed to the same MCP server instance."**
The `2026-07-28` revision removed sessions from the protocol core precisely so
that session affinity would stop being necessary. This repository is either
serving older clients, or carrying a session concept above the protocol. Either
is defensible; neither is the stateless model the current spec enables. Worth a
question, not an accusation.

**`microsoft/agent-governance-toolkit`**, MIT, 6,281 stars, last pushed
2026-09-17. **[MEASURED]** 2026-09-18. This is the source of the quote in section
4 and is covered there.

**`microsoft/fides-gateway`**, a research prototype: "A research prototype of an
MCP gateway for propagating information-flow control labels and deterministically
enforcing policies in agents." It evaluates Rego via `microsoft/regorus` and
carries labels keyed by RFC 9535 JSONPath into the call, including per-argument
paths such as `"$['arguments']['foo']"`. Last pushed 2026-06-22.
Source: https://github.com/microsoft/fides-gateway (verified 2026-09-18).

Fides is the most interesting thing in the Microsoft set for this talk and the
least usable. Information-flow labels that travel with data across tool calls are
the only published Microsoft approach that even gestures at the composition
problem a gateway structurally cannot see. It is a research prototype and should
be described as exactly that.

## 1.8 The public catalogues

**GitHub MCP Registry**, `https://github.com/mcp`. Listed **252 MCP servers** at
the time of reading, 2026-09-18. **[MEASURED]** Described on the page as "Servers
and tools from the community that connect models to files, APIs, databases, and
more."

**The page publishes no vetting criteria, no publisher verification model, no
relationship to the official MCP registry, and no enterprise administration
story.** **[UNVERIFIED]** for all four. That absence is the finding. It is
relevant because the VS Code `chat.mcp.access` policy value `registry` restricts
developers to "the configured registry", and the default gallery is GitHub's.
An organisation that sets `registry` without also setting
`McpGalleryServiceUrl` has narrowed its developers to a catalogue whose admission
criteria are not published.

**`mcp.azure.com`** returns HTTP 200 and a document whose only server-rendered
content is the title **"MCP Center - Build Your Own Enterprise MCP Registry"**.
The body is client-rendered, so nothing else could be read without executing
JavaScript. **[MEASURED]** 2026-09-18:

```
$ curl -sL https://mcp.azure.com | wc -c
1730
```

A Microsoft Learn search for "MCP Center" returned no documentation page for it.
Its contents, publisher and governance model are **[UNVERIFIED]**. Do not assert
anything about it beyond the title. If someone in Toronto says "Microsoft has an
MCP Center", this is what they mean and this is all that is currently
verifiable about it from outside a browser.

---

# 2. Identity

This is the part that matters most, and it is also the part where the gap between
what is announced and what is shipped is widest.

## 2.1 What Entra Agent ID actually is

Sources:
https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id
(doc `ms.date` 2026-04-14, `updated_at` 2026-08-13) and
https://learn.microsoft.com/en-us/entra/agent-id/what-are-agent-identities
(doc `ms.date` 2025-11-06, `updated_at` 2026-06-15), both verified 2026-09-18.
**Neither page carries a preview banner.** **[VENDOR]**

An agent identity is a **new directory object type**, not a service principal.
Microsoft argues the distinction explicitly:

> Application identities, typically represented as service principals in
> Microsoft Entra ID, were designed for services built and maintained by
> organizations. These identities carry the expectation of long-term stability,
> known ownership, and managed lifecycle.

> An agent might exist for minutes during a specific task, or might be created
> and destroyed thousands of times per day as part of an automated workflow.

The construct has three parts worth knowing by name, because they are what a
platform team will say back:

1. **Agent identity blueprints**, "templates for creating individual agent
   identities with parent-child relationships, enabling consistent security
   policies across large numbers of agents."
2. **Agent identities** themselves, "identity accounts within Microsoft Entra ID".
3. **Agents' user accounts**, "special Microsoft Entra user accounts that
   maintain a one-to-one relationship with their paired agent identity", for
   cases where an agent must "appear and operate as if they're human users".

Both access models are documented:

> **Autonomous access**. Agents can act autonomously, using access rights given
> directly to the agent identity.

> **Delegated access**. Agents can act on behalf of human users, using access
> rights given to the user. The user has control over which rights are delegated
> to the agent identity.

**How an agent gets one.** Two documented automatic paths and one manual one.
Agents built in Copilot Studio get an identity on creation, with "The user who
created the agent is recorded as its sponsor." The Entra Conditional Access
optimization agent gets one when enabled. Third-party agents are onboarded
deliberately: "Organizations can integrate third-party agents from platforms such
as AWS Bedrock and n8n by using the Microsoft Entra ID Auth SDK (sidecar) or
workload identity federation."

The sponsor field is the single most useful thing in this section for a
governance conversation. It is the ownership metadata that `server.json` does not
carry, existing on the identity rather than on the server.

## 2.2 The licensing seam, which is the real finding

Two sentences, adjacent, on both Entra Agent ID pages:

> Agent ID is available for all Microsoft Entra customers.

> Extending Microsoft Entra security features to agents requires Microsoft Agent
> 365. Agent 365 is included with Microsoft 365 E7 and is available as an add-on
> to Microsoft E5/A5/Business Premium (or Microsoft Defender Suite + Microsoft
> Purview Suite).

So the identity object is universal and the governance of it is licensed. An
organisation can be creating agent identities at scale, today, with no Conditional
Access for agents, no Identity Protection risk detection for agents, no identity
governance and no network controls for agents, because those require an Agent 365
licence per user. "We have Entra Agent ID" and "our agents are governed" are
different statements, and the first does not imply the second.

## 2.3 MCP, and the three standards questions

**MCP is named as a supported protocol**, in one sentence, with no further
detail:

> The platform supports standard protocols such as OAuth 2.0, Model Context
> Protocol (MCP), and agent-to-agent (A2A) for authentication and agent-to-agent
> communication.

That is the entire published mapping between Entra Agent ID and the MCP
authorization specification found in this pass. What follows is the specific
verification of the three things that actually determine interoperability.

**RFC 9728, Protected Resource Metadata.** The MCP authorization spec requires a
resource server to publish `/.well-known/oauth-protected-resource`. Azure API
Management's own security page documents inbound auth as subscription keys and
`validate-azure-ad-token` JWT validation. PRM appears **only as sample code**,
under "For more inbound authorization options and samples", pointing at
`github.com/blackchoey/remote-mcp-apim-oauth-prm`, an
`Azure-Samples/AI-Gateway` lab at `labs/mcp-prm-oauth`, and
`Azure-Samples/remote-mcp-apim-functions-python`, the last of which Microsoft's
own link text labels **"(Experimental)"**.
Source: https://learn.microsoft.com/en-us/azure/api-management/secure-mcp-servers
(doc `ms.date` 2026-09-11, verified 2026-09-18). **[VENDOR]**

**No Microsoft product feature implementing RFC 9728 for MCP was found.** If an
APIM-fronted MCP server publishes protected resource metadata today, somebody
built it from a sample. That is a good question to put to a platform team and a
bad thing to assert from a stage.

**RFC 8707, Resource Indicators.** No Microsoft documentation referencing RFC
8707 or `resource` indicators in an MCP context was found in this pass.
**[UNVERIFIED].** Absence of evidence here is weak evidence: Entra's token
endpoint behaviour around audience restriction is documented elsewhere under
different names, and this research did not chase it. Do not claim Microsoft lacks
it. Claim only that it is not documented for MCP.

**Enterprise-Managed Authorization and ID-JAG.** This is the one where the
temptation to overstate is strongest, because a Microsoft answer here would be
genuinely important. The companion gateway research identifies EMA as the only
vendor-neutral mechanism that reaches a laptop stdio server.

The live MCP extension page names Microsoft **only as an illustration**:

> The IdP (such as Okta, Azure AD, or a corporate SSO system) controls which MCP
> servers employees can access, and under what conditions.

Source: https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization
(verified 2026-09-18). **[OFFICIAL]** There is no identity-provider support table
on that page today.

A pull request to add one is **open and unmerged**. PR #3306, "Document identity
provider support for enterprise managed auth", created 2026-08-26, opened by the
`claude` app on behalf of Den Delimarsky. Its own description states the gap and
the intended fix:

> **Before:** The Enterprise-Managed Authorization page names example IdPs only
> (Okta, Azure AD, a corporate SSO system), with no statement of which vendors
> actually support ID-JAG today.

> **After:** The page documents identity provider support for issuing ID-JAGs
> (Okta, Ping Identity, Microsoft Entra ID) and authorization servers accepting
> them on the MCP server side (Auth0, Keycloak, WorkOS AuthKit, Descope,
> Scalekit) ...

Source: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3306
(verified 2026-09-18, state `open`). **[OFFICIAL]** for the PR's existence and
state.

**So: a proposed documentation change asserts Microsoft Entra ID issues ID-JAGs.
It is not merged, and no Microsoft documentation confirming it was found in this
pass. [UNVERIFIED].** The honest formulation for a hallway conversation is "there
is an open PR on the MCP docs that would list Entra as an ID-JAG issuer; I have
not found Microsoft's own doc for it." If someone asserts Entra ships ID-JAG,
ask them for the Microsoft URL. That is a fair question and it is the one this
research could not answer.

---

# 3. The client side

## 3.1 VS Code, which is the strongest control in the entire Microsoft set

Source: https://code.visualstudio.com/docs/enterprise/ai-settings
(verified 2026-09-18). **[VENDOR]**

This deserves to be the headline of the section, because it reaches the place the
companion gateway research says nothing reaches: a developer's laptop, running a
local stdio server, never touching the gateway.

| Control | Policy name | Effect |
|---|---|---|
| `chat.mcp.access` | `ChatMCP` | `all` any source, `registry` only the configured registry, `none` MCP disabled entirely |
| `McpGalleryServiceUrl` | same name | Point the gallery at a private, organization-curated registry instead of the public one |
| `allowedMcpServers` | `ChatAllowedMcpServers` | VS Code 1.130+. When set, only matching servers may be installed or run |
| `deniedMcpServers` | `ChatDeniedMcpServers` | VS Code 1.130+. Matching servers always blocked. **Denial takes precedence** |
| `allowManagedMcpServersOnly` | `ChatAllowManagedMcpServersOnly` | VS Code 1.132+. Restricts to the enterprise-managed allowlist |

Matching is "by configured name, remote URL, or local command invocation", with
wildcards such as `*.example.com` supported. **Matching on the local command
invocation is the part that matters.** That is what lets a policy deny
`npx -y some-server` on a laptop, which is the exact bypass no network gateway
can see.

Delivery is four ways: native MDM (Windows registry, macOS managed preferences),
GitHub server-managed settings configured by a GitHub enterprise or organization
admin, a file-based `managed-settings.json`, and VS Code enterprise policies via
ADMX templates. Managed settings take precedence over VS Code device policies
where both apply.

One experimental marker on the page, quoted: "Experimental **Automatically start
MCP servers** is experimental and might change or be removed."

The MCP servers page states the org-level claim plainly: "Organizations can
centrally manage access to MCP servers via GitHub policies."
Source: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
(verified 2026-09-18).

**Caveat to state honestly.** This is client-enforced. It is defeated by a
developer who uses a different editor, an unmanaged device, or a coding agent
that is not VS Code. It is the best available answer to the local-server problem
and it is not a complete one.

## 3.2 GitHub Copilot organization policy

> The MCP servers in Copilot policy controls use where MCP server support is
> generally available (GA).

Source: https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies
(verified 2026-09-18). **[VENDOR]**

The same page is explicit that this policy does not reach third-party hosts: it
does not control access for the GitHub MCP server in applications such as Cursor,
Windsurf, or Claude. Which surfaces the policy does cover, beyond "where MCP
server support is GA", is not enumerated on that page. **[UNVERIFIED]** for the
precise surface list.

## 3.3 Microsoft 365 Copilot and the admin center

Covered in 1.4. The short version for this section: yes, an administrator can
allowlist and block MCP servers tenant-wide, from `Agents > Tools` in the
Microsoft 365 admin center; blocking is runtime-enforced across client surfaces;
the BYO registration and approval flow is in preview; and the capability "might
not be available in your region yet". The roles that can do it are AI
Administrator or Global Administrator, and the reason is that approval requires
granting tenant-wide consent.

## 3.4 The client coverage matrix, assembled

Pulling the fragments together, because no single Microsoft page states it:

| Client | Central MCP administration available | Mechanism |
|---|---|---|
| VS Code | Yes, strongest | MDM / GitHub-managed / ADMX policies, allow and deny lists, local command matching |
| Copilot Studio | Yes | M365 admin center block; Power Platform DLP transitively via connectors |
| Microsoft 365 Copilot agents | Yes, preview, regional | M365 admin center Agents > Tools |
| GitHub Copilot (first-party surfaces) | Partially | "MCP servers in Copilot" org policy |
| GitHub Copilot CLI | BYO servers only | Agent 365 approved-server list, preview |
| Claude Code | BYO servers only | Agent 365 approved-server list, preview |
| Microsoft Foundry agents | **No** | "Azure AI Foundry and Microsoft 365 Declarative Agents aren't yet supported" |
| Microsoft 365 Declarative Agents | **No** | same |

The last two rows are the ones to carry into a conversation. The Microsoft 365
control plane does not yet govern the Azure agent platform, and a Foundry agent
is governed by Foundry's own `allowed_tools` and Toolbox curation instead.

---

# 4. Microsoft's published operational positions

## 4.1 The sequence-correlation disclosure, sourced and quoted

The companion gateway research cites this and it traces correctly. The source is
Microsoft's developer blog, post titled "Securing MCP: A Control Plane for Agent
Tool Execution", published **2026-04-22**, authored by **Jack Batzner**, about
the **Agent Governance Toolkit (AGT)**, which the post describes as **"Public
Preview"**.

> AGT governs individual tool calls deterministically. It does not yet correlate
> sequences of individually-allowed calls that may form a malicious workflow —
> that's on the roadmap.

Source: https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/
(verified 2026-09-18). **[VENDOR]**

Note the em-dash inside the quotation is preserved because it is Microsoft's
punctuation and altering a quote is worse than the punctuation.

**Three corrections to how this is usually cited, all of which matter if it comes
up in Q and A.** First, the subject is the Agent Governance Toolkit, not Azure
API Management and not Agent 365. Attributing it to "Microsoft's control plane"
generally is a small overreach; attributing it to AGT is exact. Second, AGT is
an MIT-licensed open-source project at `github.com/microsoft/agent-governance-toolkit`,
in Public Preview, not a supported Azure service. Third, the same post is clear
that AGT is not even MCP-specific.

## 4.2 The other candid statements in the same post

These are worth as much as the famous one and are almost never quoted.

> The governance model also isn't MCP-specific: it applies equally to REST APIs,
> function calls, inter-agent messages, or custom protocols.

> AGT governs agent _actions_, not model _outputs_. It doesn't filter what the
> model says — for that, see Azure AI Content Safety.

The post also names **three OWASP Agentic risks as only partially covered**:
Token Mismanagement (MCP01), Intent Flow Subversion (MCP06), and **Shadow MCP
Servers (MCP09)**. MCP09 being partial is the honest admission that the
local-server bypass is not solved by a governance toolkit, which is the same
conclusion the companion gateway research reaches from the vendor-neutral side.

"Workflow-level policies" and "intent declaration" are named as roadmap items,
"not yet available".

What AGT does enforce, quoted from the post, for completeness: tool-definition
scanning "for hidden instructions, typosquatting, and adversarial patterns"
before the agent sees a description; declarative rules "evaluated
deterministically before every tool invocation"; response validation "against
content policies before they're returned to the agent"; cryptographic agent
identities "with trust scores on a 0–1000 scale"; a "four-tier privilege ring
model"; kill switches; and "Append-only, hash-chained audit logs".

The repository's own description claims coverage of "10/10 OWASP Agentic Top 10",
which sits awkwardly beside the blog post's three partial coverages.
**[MEASURED]** from `gh repo view microsoft/agent-governance-toolkit`,
2026-09-18. Do not repeat the 10/10 claim.

## 4.3 The other honest statements, across the stack

Collected because candid vendor limitations are the most useful material here and
they are scattered across five different docs:

| Statement | Product | Source |
|---|---|---|
| "Currently, policies apply to all API operations exposed as tools in the MCP server." | Azure API Management | mcp-server-overview |
| "API Management currently supports MCP server tools, but doesn't support MCP resources or prompts." | Azure API Management | mcp-server-overview |
| "API Management MCP server capabilities currently aren't supported in workspaces." | Azure API Management | mcp-server-overview |
| "Microsoft doesn't currently support deleting a BYO MCP server." | Agent 365 | manage-tools-for-agent |
| "Republishing new versions of your remote MCP server isn't currently supported." | Agent 365 | manage-tools-for-agent |
| "The ability to allow or disallow tooling and MCP servers in Microsoft 365 admin center might not be available in your region yet." | Agent 365 | tooling-servers-overview |
| "Azure AI Foundry and Microsoft 365 Declarative Agents aren't yet supported." | Agent 365 | manage-tools-for-agent |
| "you're still responsible for tool selection, data handling, and compliance when curating Toolbox contents." | Foundry Toolbox | model-context-protocol how-to |
| "When you connect to a non-Microsoft product, including an external MCP server, you're responsible for the tools and resources you access." | Copilot Studio | agent-extend-action-mcp |

All verified 2026-09-18. **[VENDOR]**

---

# 5. Microsoft's MCP vetting and conformance tooling

## 5.1 MCP Interviewer

`github.com/microsoft/mcp-interviewer`, **MIT**, **155 stars**, last pushed
**2026-09-14**. **[MEASURED]** via `gh repo view`, 2026-09-18.

Covered in full in the companion vetting and supply-chain research, section 3.3.
The single fact that matters for this document: its `--fail-on-warnings` flag is
the only explicit CI gate among the MCP vetting tools that research examined. Its
own stated caveats are that it was "developed for research and experimental
purposes", that servers should be run in isolated containers, and that misleading
server metadata can produce inaccurate output. It is a conformance and quality
tool, not a security scanner.

## 5.2 `a365 develop-mcp evaluate`, which is new and is not in the companion research

A second Microsoft MCP vetting tool, shipped inside the Agent 365 CLI. It was not
covered by the vetting research and is worth knowing about.
Source: https://learn.microsoft.com/en-us/microsoft-365/admin/manage/manage-tools-for-agent
(verified 2026-09-18). **[VENDOR]** Requires Agent 365 CLI version
`1.1.165-preview` or greater for the registration flow.

It runs a five-step pipeline: discover tools via `tools/list`, generate a
checklist, run semantic evaluation, analyse, write reports. Checks are of two
kinds, "Deterministic: Rule-based logic in the CLI" and "Semantic: Scored by the
coding agent, with a `reason` string explaining the judgment". Output is an
overall score 0 to 100, a maturity level 0 to 4, per-tool category scores across
tool name, tool description, parameter name, parameter description and schema
structure, and a prioritized action list.

**The architectural choice is the interesting part.** The semantic scoring is not
a Microsoft service:

> The semantic checks are scored by a coding agent CLI (GitHub Copilot CLI or
> Claude Code) that runs *locally on your machine*, under your own account and AI
> subscription. This command doesn't send tool-schema data to Microsoft.

And Microsoft prints a trust warning, which is the correct instinct and the same
one MCP Interviewer documents:

> Only run `evaluate` against MCP servers you trust. The server's tool names,
> descriptions, and parameter schemas are read through a standard MCP
> `tools/list` call and handed to a coding agent running on your machine for
> scoring.

A Microsoft governance CLI whose default scoring engines are "GitHub Copilot CLI
or Claude Code" is a genuinely notable ecosystem fact for a Linux Foundation
audience, and it is a fact rather than a talking point.

**What it is not.** Like MCP Interviewer, it scores tool-definition quality. It
is not a security scanner, it does not attest anything, and a high maturity score
says nothing about whether a description contains an injection.

---

# 6. What is genuinely missing

Measured against the requirements the companion gateway and registry operations
research establishes.

## 6.1 Approval status and ownership metadata: partial, and not portable

**What exists.** API Center carries a per-version "Version lifecycle" field and
arbitrary custom metadata properties that surface in `_meta` under a namespace
the customer defines. Agent 365 carries a real approval state, Available or
Blocked, plus "Requested by" on the request. Entra Agent ID carries a **sponsor**
on every Copilot Studio agent identity.

**What is missing.** No shared vocabulary, which is the same gap the companion
research identifies at the ecosystem level. `com.contoso.apicenter/approval`
means nothing to a Foundry Toolbox, a VS Code policy, or the Agent 365 registry.
Worse, the approval state lives in a **different system** from the metadata: the
approval is in the M365 admin center, the ownership hint is in Entra, and the
classification is in API Center `_meta`. Three systems, three formats, no join
key documented between them.

## 6.2 Revocation: the strongest Microsoft answer, with two sharp edges

**What exists, and it is better than the vendor-neutral baseline.** Agent 365's
"Blocked MCP servers can't be invoked at runtime across any client surface" is a
genuine runtime revocation, not a poll-interval revocation. Compare that with the
official registry, where, per the companion research, "your revocation latency is
your poll interval" and downstream aggregators only "may" remove a deleted
server. And Entra centralised revocation applies to the agent identity itself.

**The two edges.** First, "Microsoft doesn't currently support deleting a BYO MCP
server", so the registry only grows and block is the sole remedy. Second, the
enforcement reaches "any client surface" only within the surfaces Agent 365
supports, which explicitly excludes Foundry agents and Declarative Agents today.
A server blocked in the M365 admin center is not thereby blocked for a Foundry
agent.

## 6.3 Federation: absent

No registry-to-registry federation is documented anywhere in the Microsoft set.
API Center syncs from Azure API Management and from Git. It does not ingest the
official MCP registry, it does not federate with another API Center, and it does
not publish or consume a peer relationship. Agent 365's registry and API Center's
registry are separate stores with no documented sync between them, despite both
being Microsoft registries of MCP servers in the same tenant.

For a city-sized workforce with many business units, this is the gap with the
largest operational consequence: there is no documented Microsoft answer to "each
division runs its own catalogue and the centre needs a view across them."
**[UNVERIFIED]** that such a mechanism exists undocumented.

## 6.4 Tool-argument policy: absent from every GA Microsoft product

The ladder, from coarsest to finest:

| Granularity | Where |
|---|---|
| Whole MCP server allow or block | Agent 365 admin center, VS Code policies, Power Platform DLP transitively |
| All tools on a server, one policy | Azure API Management ("policies apply to all API operations exposed as tools") |
| Per tool | Foundry `allowed_tools`; Agent 365 declared-tools snapshot |
| Per call, declarative | Agent Governance Toolkit, OSS, Public Preview |
| **Per argument** | **Nothing GA.** `microsoft/fides-gateway`, a research prototype, labels individual argument paths via RFC 9535 JSONPath |

The companion research shows why this is structurally hard rather than merely
unbuilt: the spec's `x-mcp-header` mechanism gives a gateway cheap per-argument
visibility, and the spec then advises servers **not** to annotate sensitive
parameters with it, because header values are visible to intermediaries. So
authorizing on the arguments you actually care about requires parsing the body.
Microsoft has not shipped that in a GA product, and neither has anyone else
except Agent Router's `request.mcp.params`.

## 6.5 Sequence correlation: absent, and Microsoft says so

Section 4.1. The only Microsoft artefact that even addresses composition is
`fides-gateway`, a research prototype, and information-flow labelling is a
different and more ambitious mechanism than temporal policy. AWS's Dogwood
session-aware temporal conditions remain the only published engine that reaches
past a single call, and as the companion research notes, that too is bounded to
one session, one gateway, one vendor.

## 6.6 Two gaps the companion research did not anticipate

**The two control planes do not govern each other.** Agent 365 explicitly does
not cover Foundry agents. Foundry Toolbox does not appear in the M365 admin
center registry. An organisation running both has two governance boundaries and
no documented reconciliation. Nobody's slide shows this.

**Preview concentration in exactly the load-bearing features.** The GA parts are
the plumbing: APIM gateway, API Center registry, Toolbox endpoint, agent
identities. The preview parts are the governance: BYO MCP server registration and
approval, tool search, skills, MCP tasks, the Graph enterprise server, the Agent
Governance Toolkit. An enterprise can stand up the GA plumbing today and will be
running its governance on preview terms, which state that preview features
"aren't meant for production use".

---

# 9. Sources

All verified 2026-09-18.

**Microsoft product documentation**
- APIM MCP overview: https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview
- APIM secure MCP servers: https://learn.microsoft.com/en-us/azure/api-management/secure-mcp-servers
- API Center MCP registry: https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server
- Foundry Toolbox: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/toolbox-overview
- Foundry MCP tool: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol
- Entra Agent ID overview: https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id
- Entra agent identities: https://learn.microsoft.com/en-us/entra/agent-id/what-are-agent-identities
- M365 admin, manage tools for agents: https://learn.microsoft.com/en-us/microsoft-365/admin/manage/manage-tools-for-agent
- Agent 365 Work IQ MCP overview: https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview
- Copilot Studio MCP: https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-mcp
- Copilot Studio data policies: https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-data-loss-prevention
- Microsoft MCP Server for Enterprise: https://learn.microsoft.com/en-us/graph/mcp-server/overview
- VS Code enterprise AI settings: https://code.visualstudio.com/docs/enterprise/ai-settings
- VS Code MCP servers: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- GitHub Copilot org policies: https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies

**Microsoft engineering blog**
- Securing MCP, a control plane for agent tool execution: https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/

**Microsoft repositories**
- https://github.com/microsoft/agent-governance-toolkit
- https://github.com/microsoft/mcp-gateway
- https://github.com/microsoft/fides-gateway
- https://github.com/microsoft/mcp-interviewer
- https://github.com/microsoft/mcp

**MCP project**
- Enterprise-Managed Authorization: https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization
- PR #3306, IdP support for EMA: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3306

**Catalogues**
- https://github.com/mcp
- https://mcp.azure.com

## Measurements taken in this research

```
$ gh repo view microsoft/mcp-interviewer --json stargazerCount,pushedAt,licenseInfo
  155 stars, pushed 2026-09-14, MIT

$ gh repo view microsoft/agent-governance-toolkit --json stargazerCount,pushedAt,licenseInfo
  6281 stars, pushed 2026-09-17, MIT

$ gh repo view microsoft/mcp-gateway --json licenseInfo,createdAt,pushedAt
  MIT, created 2025-05-14, pushed 2026-09-11

$ curl -sL https://mcp.azure.com | wc -c
  1730          # title only: "MCP Center - Build Your Own Enterprise MCP Registry"

$ gh issue view 3306 --repo modelcontextprotocol/modelcontextprotocol
  state: OPEN, created 2026-08-26
```

github.com/mcp reported 252 MCP servers listed on 2026-09-18.

## What could not be verified

Kept rather than dropped, because the absence is the finding.

| Claim | Status |
|---|---|
| Microsoft Entra ID issues ID-JAGs for Enterprise-Managed Authorization | **[UNVERIFIED]**. Asserted in an open, unmerged MCP docs PR. No Microsoft source found |
| Any Microsoft product implements RFC 9728 protected resource metadata for MCP as a feature | **[UNVERIFIED]**. Samples and labs only, one labelled Experimental |
| Any Microsoft support for RFC 8707 resource indicators in an MCP context | **[UNVERIFIED]**. No documentation found; absence of evidence only |
| What `mcp.azure.com` contains, who publishes it, its governance model | **[UNVERIFIED]**. Client-rendered; title only |
| GitHub MCP Registry admission criteria, publisher verification, enterprise controls | **[UNVERIFIED]**. Not published on the page |
| Which Copilot surfaces the "MCP servers in Copilot" org policy covers | **[UNVERIFIED]**. Not enumerated |
| Agent Governance Toolkit's "10/10 OWASP Agentic Top 10" repo claim | Contradicted by the project's own blog post naming three partial coverages. Do not repeat |
| Whether any registry federation exists between API Center and Agent 365 | **[UNVERIFIED]**. Not documented either way |
