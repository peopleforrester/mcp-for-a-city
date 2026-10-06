---
title: "The inference path: AI gateways as an enterprise control layer"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
audience: "Enterprise platform engineers and MCP maintainers, MCP Dev Summit Toronto 2026-10-06"
brief: "Component research wave, brief A"
---

<!-- ABOUTME: Verified survey of AI gateways as a category, what each actually enforces on the inference path. -->
<!-- ABOUTME: Includes the honest limits, the measured cost figures with methodology, and how this plane relates to MCP. -->

# The inference path: AI gateways as an enterprise control layer

Part A of the component research.

**Scope boundary.** This file covers the **inference** hop: agent to model. The
**tool** hop, agent to MCP server, is already Deep in this repo and is not
re-covered here. For MCP gateways, the registry, server vetting and tool-call
audit see:

- `research/scale/mcp-at-scale-architecture-2026-09.md` (13 MCP gateways compared)
- `research/bestpractice/mcp-gateway-and-registry-operations.md`
- `research/bestpractice/mcp-token-economics-and-tool-consolidation.md` (prompt
  caching economics, the cache-hit arithmetic, tool-definition token cost)
- `research/security/mcp-security-failures-2026-09.md`

Section 5 below is the only place the two planes are deliberately compared, and it
does so from the inference side.

## Sourcing labels

| Label | Meaning |
|---|---|
| **[OFFICIAL]** | Vendor's own product documentation, changelog, release artefact or API. Authoritative for what the product is, not for whether it is good |
| **[PEER-REVIEWED]** | Published at a refereed venue, or an arXiv preprint with a stated method |
| **[VENDOR]** | Marketing copy, blog post or comparison page written to sell. A floor for scepticism |
| **[PRACTITIONER]** | Independent engineer or analyst who measured or read the primary material |
| **[SECONDHAND]** | Reported by someone who did not measure it |
| **[UNVERIFIED]** | Could not be traced to a source making the claim |

Everything below was fetched on **2026-09-18** unless a line states otherwise.
Version numbers came from the GitHub Releases API or the vendor's own docs, not
from recall.

---

## 1. What an AI gateway is, stated precisely

An AI gateway is a reverse proxy that terminates an OpenAI-compatible (or
provider-native) HTTP request, applies policy, and forwards to one or more model
providers. Everything else it does follows from occupying that position:

- It holds the provider credential, so the caller never does.
- It sees the full request and response bodies, so it can cache, log, redact and
  count tokens.
- It chooses the upstream, so it can route, fall back and load balance.
- It can refuse, so it can enforce budgets and rate limits.

That is the entire structural argument. Every capability in the table below is a
consequence of being the single place the request passes through, which is also
why the failure modes in section 4 are shared across the whole category rather
than being specific to any one product.

**The category boundary is blurring.** Four of the twelve entries below now also
terminate MCP traffic in the same data plane. That is section 5.

---

## 2. The projects

Version and licence facts verified 2026-09-18. "Governance home" means who
controls the roadmap, which is the question that matters when standardising a
fleet on something.

### 2.1 LiteLLM

**Current stable: `v1.101.0`, published 2026-09-15.** Newer tags exist
(`v1.102.0-rc.2` and `v1.103.0-dev.2`, both 2026-09-16 to 2026-09-18) but are
flagged prerelease in the API.
Source: GitHub Releases API for `BerriAI/litellm` [OFFICIAL], 2026-09-18.

**Licence is open core with a directory boundary, not plain MIT.** The repository
`LICENSE` file reads verbatim:

> "Portions of this software are licensed as follows:
> * All content that resides under the "enterprise/" directory of this repository,
> if that directory exists, is licensed under the license defined in
> "enterprise/LICENSE".
> * Content outside of the above mentioned directories or restrictions above is
> available under the MIT license as defined below."

Source: `https://raw.githubusercontent.com/BerriAI/litellm/main/LICENSE` [OFFICIAL].
GitHub's licence detector reports `NOASSERTION` for this repo as a result, so any
comparison table that lists LiteLLM as "MIT" without qualification is repeating a
simplification.

**The tier split is the thing to check before adopting.** LiteLLM's own feature
comparison page places the following in Enterprise, not OSS: SSO, OIDC/JWT auth,
custom auth, virtual key rotation, writing keys to a secret manager, user/team/org
management, the admin UI with self-serve access, **budgets and rate limits**,
budget tiers, **guardrails** (per request, default-on, by key or team), Prometheus
metrics and PagerDuty alerting. Free tier covers pass-through endpoints, cost
tracking, logging (Datadog, S3, GCS, Azure Data Lake), end-user tracking, virtual
keys and webhook alerting.
Source: `https://www.litellm.ai/features` [OFFICIAL/VENDOR, it is the vendor's own
comparison table].

This matters because LiteLLM is widely recommended as "the open source option for
budgets and guardrails", and on the vendor's own page those two are the Enterprise
column. Secondary comparison articles disagree with the vendor page on exactly this
point, placing budgets in OSS.
Conflicting secondary claim: [SECONDHAND], search-surfaced comparison articles.
**Treat the tier boundary as something to verify against a current deployment
rather than a settled fact.** Marked [UNVERIFIED] as to which is correct today.

**LiteLLM is mid-rewrite into Rust, and that is an adoption risk right now.** The
repo description reads "The fastest, litest AI Gateway. Rust core with Python SDK."
The Rust gateway is documented as **beta**, with the vendor stating "streaming and
the full feature surface are still landing", and the published roadmap targets the
full server by **2026-12-01**.
Source: `https://docs.litellm.ai/blog/rust-ai-gateway-benchmarks` and
`https://docs.litellm.ai/docs/proxy/rust_gateway` [OFFICIAL].
An enterprise standardising on LiteLLM in September 2026 is standardising on a
product whose data plane is being replaced under it over the next quarter. The
vendor states configs, database, client API and providers are unchanged, which is a
migration promise rather than a measured outcome.

### 2.2 Portkey, now the core of Palo Alto Prisma AIRS

**Acquisition completed 2026-05-29 for $117 million, substantially all cash.**
Source: Palo Alto Networks press release
`https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-completes-acquisition-of-portkey-to-secure-ai-agents`
[OFFICIAL] and Palo Alto Networks Form 10-K FY2026 filed with the SEC
`https://www.sec.gov/Archives/edgar/data/0001327567/000132756726000023/panw-20260731.htm`
[OFFICIAL] for the consideration figure.

This resolves the **UNVERIFIED** flag carried in
`research/scale/mcp-at-scale-architecture-2026-09.md` section 3, which recorded the
acquisition from secondary sources only. It is now verified against both the
acquirer's press release and its annual report.

**Prisma AIRS AI Gateway reached GA on 2026-07-16**, roughly seven weeks after
close. Palo Alto describes it as "a unified LLM, MCP, and A2A Gateway with a single
enforcement point for all operational and security controls".
Source: `https://www.paloaltonetworks.com/blog/2026/07/announcing-general-availability-of-prisma-airs-ai-gateway/`
[OFFICIAL/VENDOR].

**The open source Portkey gateway has gone quiet.** `Portkey-AI/gateway` is MIT
licensed with roughly 13,030 stars, and:

- Last release: **`v1.15.2`, 2026-01-12**, eight months before this check.
- Last commit to the default branch: **2026-05-25**, four days before the
  acquisition completed.

Source: GitHub API for `Portkey-AI/gateway`, releases and commits endpoints
[OFFICIAL], 2026-09-18.

That is a finding rather than an inference about intent. No public statement was
found announcing that the OSS gateway is deprecated, unmaintained or end-of-life.
**The absence of such a statement is itself the finding**: an enterprise running
the MIT gateway has neither a maintenance commitment nor a stated sunset, and the
commercial energy is demonstrably in Prisma AIRS. Marked [UNVERIFIED] as to future
intent; the dates are verified.

### 2.3 Kong AI Gateway

**Kong AI Gateway 2.0 reached GA on 2026-09-01**, following private beta from
2026-07-16. It is a separate runtime, control plane, admin API and version line
from Kong Gateway 3.x, treating "Models, MCP Servers, and Agents as first-class
entities".
Sources: `https://konghq.com/blog/product-releases/kong-ai-gateway-2-0-ga` and
`https://konghq.com/blog/product-releases/kong-ai-gateway-2-0-agentic-ai`
[OFFICIAL/VENDOR].

Note the announcement blog stated an intended GA of "end of July 2026" and actual
GA landed 2026-09-01. Cite the GA post, not the announcement post, for the date.

GA added MCP server bundling, identity-aware AI policies, modality-aware cost
accounting, native Kimi / Microsoft Foundry / Amazon SageMaker support, and AWS IAM
authentication for Amazon Bedrock AgentCore. Existing AI plugins remain supported
in Kong Gateway 3.14 LTS and become opt-in at 3.18. [SECONDHAND] for the 3.18
detail, which came from a search summary rather than Kong's own migration guide.

**Semantic caching is Enterprise only.** Kong's plugin documentation states the AI
Semantic Cache plugin is available in the AI Gateway Enterprise tier, minimum Kong
Gateway 3.8, backed by Redis (including Redis Cloud, Valkey 3.14+, AWS ElastiCache,
Azure Managed Redis, Google Cloud Memorystore) or PostgreSQL with pgvector 3.10+.
Source: `https://developer.konghq.com/plugins/ai-semantic-cache/` [OFFICIAL].

Kong publishes its own caveats on that plugin, which is unusual and worth crediting.
Quoted from the plugin docs:

> "When Exact Caching is enabled, the AI Semantic Cache plugin may still return
> results for queries that are similar but not identical"

and it notes AWS MemoryDB has a hardcoded 10-index limit, and that "most AI
services send `no-cache` headers, which bypasses caching when cache control is
enabled". That last one is an operational trap: a semantic cache can be correctly
configured and still never fire.

### 2.4 Cloudflare AI Gateway

Fully managed, not self-hostable, no version number to pin. Feature status is
tracked by changelog rather than release.

**What it enforces**, per Cloudflare's own docs [OFFICIAL]:

- **Caching, exact match only.** The cache key is the SHA-256 hash of provider,
  endpoint, model, provider auth header and full request body. Quoted: "caching is
  based on **exact match** of the entire request. Any difference in the body,
  including messages, tools, or model parameters, will result in a separate cache
  entry." Minimum TTL 60 seconds, maximum one month, default 5 minutes when no TTL
  is configured. Text and image responses only. Cloudflare states "We plan on
  adding semantic search for caching in the future to improve cache hit rates."
  Source: `https://developers.cloudflare.com/ai-gateway/features/caching/`.
  **For an agent workload this is close to useless**: MCP tool definitions sit in
  the request body, so any change to the tool list invalidates every entry, and
  agent turns are rarely byte-identical. See the prompt-cache discussion in
  `research/bestpractice/mcp-token-economics-and-tool-consolidation.md` for why the
  provider-side prompt cache, which is prefix-based, is the one that pays.
- **Rate limiting, dynamic routing with per-node fallback, logging, analytics.**
  Source: `https://developers.cloudflare.com/ai-gateway/`.
- **Guardrails**, which "intercept and evaluate both user prompts and model
  responses for harmful content", covering categories including violence, hate and
  sexual content, with block-or-flag configuration. Cloudflare publishes **no
  latency figure and no stated limitation section** for Guardrails. That absence is
  a finding: the one number an operator needs before putting a synchronous
  classifier in the request path is not published.
  Source: `https://developers.cloudflare.com/ai-gateway/features/guardrails/`.
- **BYOK**, storing provider keys in Cloudflare Secrets Store encrypted at rest.
- **Unified Billing**, one Cloudflare bill across Workers AI and third-party
  providers. Quoted: "A 5% fee is applied to all credits purchased through Unified
  Billing." Source:
  `https://developers.cloudflare.com/ai-gateway/features/unified-billing/`,
  page last updated 2026-09-17.

Recent changelog entries, all 2026 [OFFICIAL]
(`https://developers.cloudflare.com/changelog/product/ai-gateway/`): 2026-09-14
"Prevent Unified Billing fallback for BYOK third-party providers"; 2026-09-09
"custom costs support cache tokens"; 2026-08-07 "Workers AI and AI Gateway unify
model access and billing"; 2026-08-05 "Identity-aware controls now available".

### 2.5 Helicone

**Apache-2.0**, verified from the repository `LICENSE` file [OFFICIAL]. Roughly
6,163 stars.

**You cannot pin a current version, and that is the finding.** The newest tag in
the repository is **`v2025.08.21-1`, published 2025-08-21**, while the default
branch received commits as recently as **2026-09-16**, including a security fix
described in the commit subject as "close platform-admin takeover and HQL
cross-tenant bypass". Complete tag list: `v2025.08.21-1`, `v2025.08.21`,
`v2025.08.20`, `v1.0.0`, `v0.0.1`.
Source: GitHub API for `Helicone/helicone`, releases, tags and commits endpoints
[OFFICIAL], 2026-09-18.

So a self-hosting enterprise is tracking a branch, not a release, and a security
fix landed with no tagged artefact carrying it. For a component sitting in the
inference path holding every provider credential, that is a supply-chain posture
worth stating plainly rather than a packaging detail.

**Positioning.** Helicone is observability-first with routing added, not a
gateway-first product. Its own homepage describes customers using it to "route,
debug, and analyze". Pricing: Hobby free (10,000 requests, 1 GB storage), Pro
$79/month, Team $799/month (five orgs, SOC-2 and HIPAA, dedicated Slack),
Enterprise custom (custom MSA, SAML SSO, on-prem deployment).
Sources: `https://www.helicone.ai/` and `https://www.helicone.ai/pricing`
[OFFICIAL/VENDOR]. Self-hosting is documented via manual install, Docker Compose,
Kubernetes Helm and cloud deployment, and the self-host docs state **no licence
restriction or enterprise-licence requirement** for self-hosting.
Source: `https://docs.helicone.ai/getting-started/self-host/overview` [OFFICIAL].

### 2.6 OpenRouter

A hosted routing marketplace, not enterprise infrastructure, and it should not be
compared like-for-like with the rest. **No self-hosting option is documented**;
searching the FAQ and privacy documentation surfaced enterprise plans but nothing
on self-hosted deployment. Marked as an absence finding rather than a confirmed
"does not exist".

**Fees**, quoted from the FAQ [OFFICIAL]: "5.5% ($0.80 minimum)" for Stripe credit
purchases, 5% for crypto, and a 5% fee on BYOK usage above a free allowance
($25,000/month pay-as-you-go, $200,000/month enterprise). No markup on inference
itself.

**Data handling** is the part an enterprise must read. Quoted from the privacy
documentation [OFFICIAL]: "Prompt and completion are not logged by default", and
users can opt into logging for a 1% discount. Critically, the per-provider data
policy filter carries this caveat verbatim:

> "This setting has no bearing on OpenRouter's own policies and what we do with
> your prompts."

Regional routing within the EU and US is available on enterprise terms, with
prompts and completions stated to remain in the selected region.
Source: `https://openrouter.ai/docs/features/privacy-and-logging`.

### 2.7 TrueFoundry

**Commercial, not open source.** The company publishes open source projects
(KubeElasti, CruiseKube) but the AI Gateway is not among them. No public version
number was found for the gateway itself; marked **[UNVERIFIED]**.

Vendor claims, all from `https://www.truefoundry.com/ai-gateway` [VENDOR] and none
independently verified: latency-based routing to the fastest available LLM,
weighted load balancing, automatic failover, geo-aware routing, rate limits per
user/service/endpoint, cost-based and token-based quotas via metadata filters,
budget enforcement that throttles or blocks, RBAC and OAuth 2.0, PII filtering and
toxicity detection, audit logging with SOC 2 / HIPAA / GDPR framing, deployment to
VPC, on-premises, hybrid or air-gapped.

Performance and savings claims, **[VENDOR], unverified**: "Sub-3ms internal
latency", "10B+ requests/month", "99.99% uptime", "30% average cost optimization".
This repo already flags TrueFoundry's separate MCP-side claims ("~10ms Latency,
Even Under Load", "350+ RPS on just 1 vCPU") as vendor-unverified in
`research/bestpractice/mcp-gateway-and-registry-operations.md` line 448. The
pattern is consistent across both product surfaces: round numbers, no methodology,
no test harness published.

### 2.8 Agent Router (formerly Envoy AI Gateway)

**`v1.1.0`, published 2026-08-21.** Apache-2.0. Governance home: **Agentic AI
Foundation**, moved from the CNCF Envoy subproject on 2026-09-10.

**New fact verified here: the GitHub repository itself moved.** `envoyproxy/ai-gateway`
now returns HTTP 301 and resolves to **`theagentrouter/agent-router`** (repository
id 875880554, Apache-2.0, roughly 2,120 stars, pushed 2026-09-18).
Source: GitHub API redirect resolution [OFFICIAL], 2026-09-18.

This refines the statement in `research/scale/mcp-at-scale-architecture-2026-09.md`
section 2.2 that "Only the product name changed." The API group
(`aigateway.envoyproxy.io`), the `aigw` CLI, container images and Go module path
were retained as that file records, but the **GitHub org and repo path did change**,
which is what breaks pinned clone URLs, CI checkouts and any automation that
resolves the repo by path rather than following redirects. GitHub redirects the API
call; it does not redirect forever by contract.

Release cadence for context: `v1.1.0` 2026-08-21, `v1.0.0` 2026-06-23, `v0.7.0`
2026-06-06, `v0.6.0` 2026-05-05.

Inference-side capabilities in v1.1.0, per this repo's existing verified notes:
token counting across providers, per-request upstream credentials, stream idle
timeout with failover, CEL-based backend selection, optional OTel GenAI tracing,
HTTP CONNECT egress.

### 2.9 agentgateway

**`v1.5.0`, 2026-08-27 stable; `v1.6.0-alpha.1`, 2026-09-14.** Apache-2.0, Agentic
AI Foundation. Source: GitHub Releases API for `agentgateway/agentgateway`
[OFFICIAL], 2026-09-18, which confirms the versions already recorded in
`research/scale/`.

Inference-side: v1.5.0 introduced API-key-scoped budgets and model access, plus
native Gemini APIs. Rust data plane.

### 2.10 kgateway

**`v2.4.5`, 2026-09-16** (with `v2.3.9` on the same date maintaining the 2.3 line).
Apache-2.0, roughly 5,689 stars, CNCF Sandbox.
Source: GitHub Releases API for `kgateway-dev/kgateway` [OFFICIAL], 2026-09-18.

**This resolves the `UNVERIFIED` version flag** carried in
`research/scale/mcp-at-scale-architecture-2026-09.md` section 2.1.

kgateway is an Envoy-based Kubernetes Gateway API implementation that maintains two
active release lines concurrently. On the inference path it is a general-purpose
gateway with AI routing rather than an AI-specific product; its own description is
"The Cloud-Native API Gateway and AI Gateway". For MCP it integrates agentgateway
rather than implementing MCP itself, which is the existing finding in `research/scale/`.

### 2.11 Bedrock native routing (Amazon Bedrock Intelligent Prompt Routing)

**GA since April 2025.** Source: AWS what's-new announcement [OFFICIAL],
`https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-bedrock-intelligent-prompt-routing-generally-available/`,
URL confirmed resolving 2026-09-18.

**The constraints are severe and are the story.** Quoted from the current AWS
documentation [OFFICIAL]
(`https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html`):

> "Intelligent prompt routing is only optimized for English prompts."

> "Intelligent prompt routing can't adjust routing decisions or responses based on
> application-specific performance data."

> "Intelligent prompt routing might not always provide the most optimal routing for
> unique or specialized use cases. How effective the routing is depends on the
> initial training data."

And from the console instructions: "You must choose exactly two models within the
same family."

**Routing is within one model family, between exactly two models.** It is not a
multi-vendor router. It cannot route Claude to Nova to save money.

**The published model pool is stale.** The supported-models table in the live
documentation lists Nova Lite, Nova Pro, Claude 3 Haiku, Claude 3.5 Haiku, Claude
3.5 Sonnet, Claude 3.5 Sonnet v2, and Llama 3.1/3.2/3.3. No Claude 4.x model
appears. The same page still contains the phrase "During preview, you can choose to
use select models in the Anthropic and Meta families" more than a year after GA.
Verified by direct read of the page 2026-09-18.

Compare against Azure's pool in section 2.12, which carries gpt-5.6, Claude Opus
4.8 and Grok 4. **The two hyperscaler native routers are not in the same generation
of capability**, and a comparison that lists both as "native routing, available"
obscures a gap of several model generations.

### 2.12 Vertex / Google native routing

**Google's own model routing is in Public Preview, not GA, as of 2026-08-04, and it
lives in API Gateway rather than in the Vertex or Gemini platform surface.**

Quoted from the Google Developers Blog [OFFICIAL]
(`https://developers.googleblog.com/a-unified-api-for-ai-model-routing/`):

> "Google Cloud API Gateway now offers model routing in Public Preview to solve
> this. It provides a lightweight, serverless ingress layer that accepts
> OpenAI-compatible requests and dynamically routes them to Gemini, Claude, or
> OpenAI OSS-GPT."

Routing tables are declared in the OpenAPI specification via a
`x-google-api-management.ai.models.routing` extension. It enforces authentication
(applications authenticate to the Gateway rather than to model providers), rate
limiting and token tracking, and transcodes payloads to each backend's native
schema. Model pool at preview: Gemini 3.5 Flash Lite, Claude Opus 4.7, GPT OSS 120B.

**Naming caution for the deck and the longer session.** Secondary reporting states
Google announced Gemini Enterprise Agent Platform on 2026-04-22 as the successor to
Vertex AI, and that the Vertex AI console was removed from Google Cloud on
2026-05-21. Source: [SECONDHAND], search-surfaced, including
`https://therouter.ai/news/vertex-ai-sdk-migration-gemini-enterprise-agent-platform/`
and a Wikipedia article. **Marked [UNVERIFIED]**: this was not confirmed against a
Google Cloud release note or official announcement in this pass, and it is exactly
the kind of platform-rename claim that should not be said from a stage without a
primary source. If this material is used, verify first.

### 2.13 Azure AI Foundry model router

**Current version `2025-11-18`, actively maintained in place.** Frozen prior
versions: `2025-08-07` and `2025-05-19`. Source: Microsoft Learn [OFFICIAL],
`https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router`,
page `ms.date` 2026-09-01, updated 2026-09-02.

Microsoft's versioning note is worth quoting because it is unusual:

> "The current version is `2025-11-18` (latest), which is actively maintained: new
> underlying models and features are added to this version over time without
> changing the version identifier."

That is a deliberate trade of reproducibility for freshness. The set of models
behind a given deployment can change without the version identifier changing, and
with auto-update enabled Microsoft states this "could affect the overall
performance of the model and costs".

**It is the most capable of the three hyperscaler native routers.** Routes across
27 models from five vendors (OpenAI, Anthropic, xAI, DeepSeek, Meta), including
gpt-5.6-sol/terra/luna, gpt-5.5, gpt-5.4 family, Claude Opus 4.8/4.7/4.6, Claude
Sonnet 4.5, Claude Haiku 4.5, Grok 4.1 Fast Reasoning, Grok 4, DeepSeek-V3.2 and
Llama-4-Maverick. Claude models must be deployed separately first.

Capabilities [OFFICIAL]: three routing modes (Balanced default, Cost, Quality);
model subset selection; **automatic failover enabled by default**, using the model
subset as the fallback set; Azure Policy governance over which models a developer
may include; prompt caching passthrough; session affinity (preview) to keep
Chat Completions turns on the same model for cache reuse; quota tiers from 1,000
RPM / 1M TPM at Tier 1 to 15,000 RPM / 15M TPM at Tier 6.

**The limitation that will bite.** Quoted:

> "The effective context window is limited by the smallest underlying model."

and

> "an API call with a larger context will succeed only if the prompt happens to be
> routed to the right model."

A context-length failure that depends on which model the router picked is
non-deterministic from the caller's point of view. Agent workloads carry large MCP
tool definitions in every request, which puts them close to the smallest model's
ceiling routinely.

Also stated: routing decisions on image input are based on text only; audio input
is not processed; "It does not store your prompts."

**Microsoft publishes no cost-savings percentage in this documentation.** Billing is
described only as "Model router usage is charged for input prompts at the rate
listed on the pricing page." See section 6 for what figures do circulate and where
they come from.

---

## 3. Comparison table

Verified 2026-09-18. **"Enforces" means what the project's own documentation says
it enforces**, not an independent evaluation. Where a capability is gated behind a
paid tier, the cell says so, because "has budgets" and "has budgets if you buy the
Enterprise licence" are different answers to a procurement question.

Legend: **Y** documented, **Y(E)** documented but Enterprise or paid tier only,
**P** preview or beta, **N** not offered, **?** not documented / unverified.

| Project | Licence | Current version | Governance home | Credentials | Routing | Caching | Budgets | Guards | Audit | Self-hostable |
|---|---|---|---|---|---|---|---|---|---|---|
| **LiteLLM** | MIT except `enterprise/`, which has its own licence | `v1.101.0` (2026-09-15); Rust data plane in beta, full server targeted 2026-12-01 | BerriAI, commercial company, no foundation | Y, virtual keys; secret-manager write and key rotation Y(E) | Y, 100+ providers, fallbacks | ? not in the vendor feature table | Y(E) per vendor page; secondary sources say OSS. **Conflicting** | Y(E) per vendor page | Logging Y; audit logs Y(E) | Y |
| **Portkey (OSS gateway)** | MIT | `v1.15.2` (2026-01-12); last commit 2026-05-25 | Palo Alto Networks since 2026-05-29 | Y | Y, 1,600+ models claimed | Y | Y | Y, 50+ guardrails claimed | Y | Y |
| **Prisma AIRS AI Gateway** | Commercial | GA 2026-07-16, no public version line | Palo Alto Networks | Y, credential scoping | Y | ? | Y, budgets and rate limits | Y, prompt and response inspection | Y | N, vendor platform |
| **Kong AI Gateway** | Commercial; six AI plugins free in Kong Gateway | 2.0 GA 2026-09-01, own version line | Kong Inc. | Y | Y, LLM routing and load balancing | Y(E) semantic, Enterprise tier, min KGW 3.8 | Y, token-based rate limiting; modality-aware cost accounting | Y, prompt guarding | Y, analytics and identity-aware policies | Y, self-managed or Konnect |
| **Cloudflare AI Gateway** | Commercial, managed | No version; changelog-tracked | Cloudflare | Y, BYOK via Secrets Store | Y, Dynamic Routing with per-node fallback | Y, **exact match only**, semantic stated as future | Y, rate limiting; budgets via BYOK nodes | Y, Guardrails, block or flag | Y, logs, analytics, User Insights | **N** |
| **Helicone** | Apache-2.0 | **Cannot pin.** Last tag `v2025.08.21-1`; branch active to 2026-09-16 | Helicone Inc. (YC W23) | Y | Y | ? | Rate limiting Y | ? | Y, observability is the product | Y, no stated licence restriction |
| **OpenRouter** | Proprietary, hosted | No version, hosted service | OpenRouter Inc. | Y, plus BYOK | Y, marketplace routing across providers | ? | Credit-based; BYOK allowance caps | ? | Metadata only by default; prompts not logged by default | **N documented** |
| **TrueFoundry** | Commercial | **? unverified** | TrueFoundry | Y, centralised key management | Y, latency-based, weighted, geo-aware, failover | ? | Y, cost and token quotas, throttle or block | Y, PII filtering, toxicity | Y, SOC 2 / HIPAA / GDPR framing | Y, VPC, on-prem, hybrid, air-gapped |
| **Agent Router** | Apache-2.0 | `v1.1.0` (2026-08-21) | **Agentic AI Foundation**, from CNCF 2026-09-10; repo moved to `theagentrouter/agent-router` | Y, per-request upstream credentials | Y, CEL backend selection, stream idle failover | ? | Token counting across providers | Via MCP security policy CRDs on the tool plane | Y, OTel GenAI tracing, Prometheus | Y |
| **agentgateway** | Apache-2.0 | `v1.5.0` (2026-08-27); `v1.6.0-alpha.1` (2026-09-14) | **Agentic AI Foundation** | Y | Y, native Gemini APIs | ? | Y, API-key-scoped budgets and model access | CEL policy engine | Y, OTel metrics/logs/traces | Y |
| **kgateway** | Apache-2.0 | `v2.4.5` (2026-09-16); `v2.3.9` same day | CNCF Sandbox | Y | Y, Envoy-based | ? | ? | ? | Y, Envoy telemetry | Y |
| **Bedrock native routing** | Commercial | GA April 2025; docs still say "During preview" | AWS | AWS IAM | **Two models, same family, English only** | N, separate feature | Via AWS billing, not the router | N, Bedrock Guardrails is separate | CloudTrail | N |
| **Vertex / Google native routing** | Commercial | **Public Preview** 2026-08-04, in API Gateway | Google Cloud | Y, apps auth to gateway not provider | Y, Gemini / Claude / GPT OSS 120B | ? | Rate limiting and token tracking | ? | Token tracking | N |
| **Azure AI Foundry model router** | Commercial | `2025-11-18`, updated in place | Microsoft | Azure identity | Y, 27 models / 5 vendors, 3 modes, **failover default-on** | Prompt caching passthrough; session affinity (P) | Quota tiers, RPM/TPM | Azure Policy on deployable models; content filters separate | Azure Monitor | N |

**Reading the table.** Three clusters, and they are not competing with each other:

1. **Foundation-hosted open source** (Agent Router, agentgateway, kgateway). Apache-2.0,
   no tier gates on the core, and two of the three now sit in the same foundation as
   MCP itself. Weakest on caching, where none of the three documents a semantic or
   response cache on the inference path.
2. **Commercial platforms** (Kong, Prisma AIRS, TrueFoundry, Cloudflare). Broadest
   feature surface, and every interesting control is a purchasing decision.
3. **Hyperscaler native routing** (Bedrock, Google, Azure). Not gateways. They are
   routing features inside one provider's platform, they do not hold third-party
   credentials, and only Azure's is current.

**The open-core pattern is consistent enough to be a rule.** Across LiteLLM, Kong
and Helicone, the capabilities gated behind payment are the same three: identity
integration (SSO/SAML/SCIM), audit logs, and semantic caching. Those are exactly the
three an enterprise needs and a hobbyist does not. Budget for them.

---

## 4. The honest limits

### 4.1 What no inference gateway can do

**It cannot see what the tool returned, or what the agent did with it.** The
gateway terminates the model call. It observes the prompt, the tool definitions in
the request body, and the model's tool-call request in the response. The execution
of that tool, its result, and the agent's next decision happen outside the hop. An
independent analysis states the boundary precisely: the gateway "knows a search
endpoint was called, but it does not know the endpoint returned a customer record,
or that the agent then acted on it." [PRACTITIONER], surfaced via
`https://www.fiddler.ai/blog/ai-agent-control-plane-beyond-proxy` and corroborating
analyses. This is structural, not a product gap, and it is why section 5 exists.

**It cannot attribute spend through a delegation chain.** This repo's existing
finding stands and is reinforced here: per-key and per-team budgets are universally
implemented, and attributing cost to a *person* through an *agent* through a chain
of delegated calls is implemented nowhere. A virtual key identifies the agent, not
the human who asked. See `research/scale/mcp-at-scale-architecture-2026-09.md`
section 9.

**It cannot make a model deterministic, and routing makes this worse.** Azure's
context-window limitation is the clean example: the same request succeeds or fails
depending on which model the router selected. Any router that varies the upstream
per request converts a deterministic class of error into a probabilistic one.

**It cannot enforce anything on a call that does not pass through it.** An SDK
call with a hardcoded key, a developer laptop hitting `api.openai.com` directly, or
a vendor SaaS product calling its own models bypasses the gateway entirely. Central
credential custody is the only control that makes bypass *detectable*, by making the
direct path fail for lack of a key. Gateways that permit BYOK pass-through weaken
their own primary control.

### 4.2 Where guards produce false confidence

This is the most load-bearing part of this file and the sourcing is deliberately
peer-reviewed rather than vendor.

**Commercial prompt-injection detectors have been evaded at up to 100%.**
"Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks against Prompt
Injection and Jailbreak Detection Systems", arXiv 2504.11168 (v3, 2025-07-14)
[PEER-REVIEWED, arXiv preprint with stated method]. The paper tests character
injection (zero-width characters, homoglyphs) and algorithmic adversarial machine
learning evasion against six production detection systems: Microsoft Azure Prompt
Shield, Meta Prompt Guard, ProtectAI v1 and v2, NeMo Guard Jailbreak Detect, and
Vijil Prompt Injection. Both technique families reached **up to 100% evasion in
some instances**. Source: `https://arxiv.org/abs/2504.11168`.

Read that alongside section 2.4: Cloudflare ships Guardrails and publishes no
efficacy figure and no limitations section. Neither does any other vendor surveyed
here. **Not one of the twelve products publishes a detection rate, a false-positive
rate, or an evaluation method for its guards.** That absence is the finding. An
operator buying "prompt injection filtering" is buying an unmeasured control, and
the independent measurements that do exist are not flattering.

**Over-defence is the other half of the failure.** Detectors including InjecGuard
and PromptGuard maintain high recall on attacks while collapsing on benign prompt
classification, with reported accuracy between 5% and 35%, and AUC inflated by up
to 8.4 points when evaluated on standard splits rather than leave-one-dataset-out.
[PEER-REVIEWED / SECONDHAND: these figures were surfaced via search across arXiv
results including 2502.15427 and 2606.05566 and were **not** verified against the
paper PDFs in this pass. Marked **[UNVERIFIED]** pending a direct read.] The
directional claim, that guards fail in both directions and the false-positive cost
is real, is well supported; the specific percentages are not yet confirmed here.

**Semantic caching is an attack surface, and this one is fully verified.** "When
Cache Poisoning Meets LLM Systems: Semantic Cache Poisoning and Its
Countermeasures", Wu, Wang, Zhang, Zhang, Niu, Wu and Zhang (SUSTech and ByteDance),
NDSS Symposium 2026 [PEER-REVIEWED, refereed venue]. Text extracted directly from
the paper PDF on 2026-09-18. From the abstract:

> "This paper is the first to show that semantic caching is vulnerable to cache
> poisoning attacks, where an attacker injects crafted cache entries to cause others
> to receive attacker-defined responses. We demonstrate the semantic cache poisoning
> attack in diverse scenarios and confirm its practicality across all three major
> public clouds."

Measured attack success rates, quoted from the paper:

> "our attack achieves an attack success rate of 88% on the text-to-text case in
> GPTCache, 81% on the text-to-image case, and 82%, 89%, and 87% on AWS, Azure, and
> Alibaba, respectively, where all three public cloud evaluations are conducted
> under the black-box setting."

And on blast radius: "On average, 95.7% similar queries are poisoned in the
black-box" setting. Best single prompt-construction result in the paper's table was
prompt injection templates at 98% on one cloud target.

On defences, quoted:

> "we evaluate existing adversarial prompting defenses and find they are ineffective
> against semantic cache poisoning"

and the failure shape:

> "We observe that these defenses can reach extreme outcomes of either 100% precision
> or 100% recall. Under a strict configuration, a defense flags nearly all inputs as
> suspicious and reaches 100% recall, while a loose configuration treats all inputs
> as safe and reaches 100% precision."

The paper proposes a new defence and states plainly that "complete mitigation remains
challenging".

**This is the single most important finding in this file for an enterprise.**
Semantic caching is sold as a pure cost win. It is a cross-user response-reuse
mechanism, so a poisoned entry serves an attacker-chosen answer to every subsequent
semantically similar query, from any user, until someone notices. The attack is
demonstrated against AWS, Azure and Alibaba production infrastructure under
black-box conditions. Kong's own documentation independently corroborates the
benign version of the same failure ("may still return results for queries that are
similar but not identical").

Cloudflare's exact-match-only cache, criticised in section 2.4 as nearly useless for
agent workloads, is immune to this class of attack. That is the trade being made,
and it is rarely stated as a trade.

### 4.3 What breaks at high concurrency

**Honest answer: almost nothing is published, and that is the finding.** No vendor
surveyed here publishes a saturation point, a degradation curve, a connection-pool
exhaustion threshold, or a post-incident writeup for its AI gateway. The same gap
was recorded for MCP gateways in
`research/bestpractice/mcp-gateway-and-registry-operations.md` line 610. It repeats
on the inference side.

What can be said structurally:

- **Streaming changes the resource model.** A gateway proxying SSE holds a
  connection open for the full generation, commonly 500 ms to 5 seconds and often
  far longer. Concurrency is bounded by held connections, not by requests per
  second, and an RPS benchmark measures the wrong quantity.
- **Semantic caching adds a vector search to the hot path.** Kong states the plugin
  "requires significant storage and computing resources for vector storage and
  similarity searches" [OFFICIAL]. Under load this is a second datastore that can
  saturate independently of the gateway.
- **Synchronous guards serialise a classifier in front of every request.** Since no
  vendor publishes guard latency, the concurrency cost of enabling them is unknown
  before deployment.

### 4.4 Latency per hop, with the measured figures and their caveats

Published gateway-overhead figures span roughly five orders of magnitude, from 11
microseconds to 257.7 milliseconds. **That spread is a methodology artefact, not a
performance difference.**

| Claim | Figure | Test conditions | Label |
|---|---|---|---|
| LiteLLM Rust, p99 added latency | **0.7 ms** | Local deterministic mock upstream, 4 vCPU / 16 GB single host, **no logging callbacks, spend tracking or persistence** | [OFFICIAL/VENDOR], vendor's own benchmark |
| LiteLLM Python v1, same test | **257.7 ms** | Same harness | [OFFICIAL/VENDOR] |
| Portkey, same test | 2.3 ms | Same harness, run by LiteLLM | [VENDOR], competitor-run |
| Bifrost, same test | 4.5 ms | Same harness, run by LiteLLM | [VENDOR], competitor-run |
| Bifrost, self-reported | 11 microseconds | Bifrost-only stress test, ~10 KB payloads, mock upstream, excludes upstream response time | [VENDOR] |
| Kong | P95 24.07 ms, P99 30.35 ms | WireMock upstream, not a real provider | [PRACTITIONER] reporting of a Kong benchmark |
| Envoy AI Gateway (now Agent Router) | **~2 ms** | **Real H100 GPU inference, streaming enabled** | [PRACTITIONER], described as the only real-provider measurement in the set |
| TrueFoundry | "sub-3ms internal latency" | No methodology published | [VENDOR], unverified |
| Kong AI Gateway | "2-5 ms overhead", "under 10ms", "28,000+ RPS" | No methodology published | [VENDOR]/[SECONDHAND], unverified |

Sources: `https://docs.litellm.ai/blog/rust-ai-gateway-benchmarks` [OFFICIAL] for
the LiteLLM harness and figures; `https://www.deepinspect.ai/blog/ai-gateway-latency-benchmarks`
[PRACTITIONER] for the cross-vendor critique and the Kong and Envoy figures.

**The critique and the vendor agree, which is unusual and worth noting.** The
independent analysis argues that "almost all of them measure proxy forwarding
against a mock upstream, which deletes the largest real-world variable."
LiteLLM's own benchmark post states the same caveat about its own numbers, quoted:

> "Because the upstream is a local mock, the absolute latencies are the gateway's
> isolated slice, not real-world request latencies."

The vendor published the caveat. Comparison articles quote the number and drop it.

**The number that actually matters.** Real inference runs 500 ms to 5 seconds. A
gateway hop of 1 to 30 ms is a low single-digit percentage of total request time.
Optimising from 4 ms to 0.7 ms is invisible to a user and is not a sound basis for
choosing a gateway. **Choose on credential custody, governance home, audit quality
and tier boundaries. Latency is not the differentiator the benchmarks imply**, with
one exception: LiteLLM's Python data plane at 257.7 ms p99 is in a different
category and is the reason the Rust rewrite exists.

Two caveats on these figures that no source states and should be assumed:
benchmarks run with callbacks, spend tracking and persistence **disabled** do not
describe a governed deployment, which has all three on by definition. And none of
these figures include a synchronous guard in the path.

---

## 5. How the inference path relates to the MCP tool path

**They are different planes with different owners, and the split is real.**

| | Inference path | MCP tool path |
|---|---|---|
| The hop | Agent to model provider | Agent to MCP server to system of record |
| Question answered | Which model may this agent call, with whose credential, at what cost | Which tool may this agent invoke, on whose behalf, against what data |
| Typical owner | Platform or FinOps. Cost is the driver | Security and application owners. Blast radius is the driver |
| Unit of policy | Virtual key, model, token budget | Tool name, tool parameters, user identity, OAuth scope |
| What it sees | Prompt, tool definitions, completion, token counts | Tool call, arguments, result, the system it touched |
| What it cannot see | What the tool returned, what the agent decided | Model choice, token spend, provider credential |

**The honest answer to "does anything govern both coherently": partially, and only
recently.** Four products now terminate both in one data plane. That is a genuine
architectural convergence and not vendor noise, because it happened independently
four times.

1. **agentgateway**, Apache-2.0, Agentic AI Foundation. Both planes, one Rust data
   plane, one CEL policy engine. [OFFICIAL]
2. **Agent Router**, Apache-2.0, Agentic AI Foundation. Both planes. `MCPRoute` and
   `MCPRouteSecurityPolicy` CRDs on the tool side, provider routing and token
   counting on the model side. [OFFICIAL]
3. **Kong AI Gateway 2.0**, commercial. GA 2026-09-01, treating "Models, MCP
   Servers, and Agents as first-class entities" in one runtime, with MCP server
   bundling and identity-aware AI policies. [OFFICIAL/VENDOR]
4. **Prisma AIRS AI Gateway**, commercial. GA 2026-07-16, described by Palo Alto as
   "a unified LLM, MCP, and A2A Gateway with a single enforcement point for all
   operational and security controls". [OFFICIAL/VENDOR]

**Two qualifications, and they matter more than the convergence.**

**First, one data plane is not one policy model.** Every one of the four expresses
model policy and tool policy in separate constructs. Agent Router uses provider
routing config for one and `MCPRouteSecurityPolicy` CRDs for the other. Nothing
found in this pass lets an operator write a single rule of the form "this agent,
acting for this user, may spend up to X and may touch these tools", evaluated once.
**No product surveyed publishes a unified policy language spanning both planes.**
Marked as an absence finding, verified by reading the capability documentation of
all four.

**Second, the correlation problem is unsolved even inside one product.** Answering
"what did this agent do" as a single question requires joining a model call to the
tool calls it caused, through the delegation chain, back to the human. That needs a
propagated trace and agent identity, not a shared data plane. OpenTelemetry GenAI
conventions are the candidate mechanism and are covered in this repo's existing
operations research. **No vendor surveyed claims to have solved the join.**

The structural conclusion, stated without overclaiming: **co-locating the planes
removes a hop and a second credential store. It does not by itself produce coherent
governance, because the policy model and the identity propagation are the hard
parts and both remain unsolved.** An enterprise that buys a unified gateway and
assumes it has answered the attribution question has bought convenience and called
it governance.

For the tool-plane side of this comparison, including per-tool authorization,
revocation and call-level audit, see
`research/scale/mcp-at-scale-architecture-2026-09.md` sections 2.1 to 2.3, which
already treat it in depth.

---

## 6. Cost control that is real

Published savings figures, with methodology, ranked by how much the method can be
inspected.

### 6.1 AWS, the best-documented figure in the category

AWS publishes savings **and** its method, which none of the other vendors do.
Source: `https://aws.amazon.com/blogs/machine-learning/use-amazon-bedrock-intelligent-prompt-routing-for-cost-and-latency-benefits/`
[OFFICIAL].

| Model family | Cost saving | Latency benefit |
|---|---|---|
| Nova | 35% | 9.98% |
| Anthropic | 56% | 6.15% |
| Meta | 16% | 9.38% |

**Methodology, quoted.** AWS states it "conducted several internal tests with
proprietary and public data". The metric is "average response quality gain under
cost constraints (ARQGC), a normalized (0-1) performance metric" where "0.5
represents random routing and 1 represents optimal oracle routing performance".
Latency is "estimated latency benefit based on average recorded time to first token
(TTFT)".

**The caveat AWS publishes and everyone drops**, quoted: results are "only meant for
comparing against random routing within the family... and not across families".

**Read that carefully. The baseline is random routing, not the strong model.** A
56% saving against randomly picking between Claude 3.5 Haiku and Claude 3.5 Sonnet
is not a 56% saving against your current bill. Nobody routes randomly. Anyone
quoting these figures as achievable savings has changed the baseline and should not
be followed.

A separate AWS RAG case study reports "average 63.6% cost savings because of a
higher percentage (87%) of prompts being routed to Claude 3.5 Haiku while still
maintaining the baseline accuracy" [OFFICIAL]. This one has a usable baseline
(all-Sonnet) and is the more honest number, though it is a single workload.

### 6.2 Azure, where the circulating figures are not Microsoft's

**Microsoft publishes no cost-savings percentage for model router** in its official
concept documentation, verified by direct read 2026-09-18.

Figures that circulate: 4.5% saving in Balanced mode, 4.7% in Cost mode, 14.2% in
Quality mode. Source: a Microsoft Community Hub blog post
(`https://techcommunity.microsoft.com/blog/azuredevcommunityblog/optimising-ai-costs-with-microsoft-foundry-model-router/4494776`)
[PRACTITIONER, community-authored, hosted on a Microsoft property but not Microsoft
documentation]. **The methodology could not be retrieved**: the page body did not
return on fetch, so prompt count, dataset and baseline are unknown. Marked
**[UNVERIFIED]**.

A separate "up to 60% cost savings" claim attached to a GPT-5 launch is
[SECONDHAND], from a news aggregator, with no methodology. **Do not use it.**

Note the direction of the surprise: if the 4.5% to 14.2% range is right, Azure's
router saves an order of magnitude less than AWS's headline, and the counterintuitive
result that Quality mode saves the most is exactly the kind of finding that needs a
method before it is repeated.

### 6.3 Caching

**Kong.** Claims of "150% faster on the first prompt and 255% faster on the second"
and "28,000+ RPS" were surfaced through secondary comparison articles rather than a
Kong benchmark with a published harness. [SECONDHAND], **[UNVERIFIED]**, no
methodology. Do not cite.

**Cloudflare.** Publishes the mechanism (exact-match SHA-256 over the full request
body, 60 second to one month TTL) and **no hit-rate or savings figure**
[OFFICIAL]. Honest, and correspondingly unhelpful for a business case.

**The arithmetic that is trustworthy is already in this repo.** A cache hit costs
roughly one tenth of a cache miss, derived from published provider prices, in
`research/bestpractice/mcp-token-economics-and-tool-consolidation.md` section 1.3.
That is prompt caching at the provider, which is prefix-based and deterministic, not
gateway semantic caching. **For agent workloads the provider prompt cache is the
larger and safer win**, and it is degraded by exactly the thing gateways do: an
unstable tool-definition prefix. The same file documents why tool-list ordering and
naming stability drive prompt-cache hit rate.

Given section 4.2, the recommendation here is specific: **prompt caching yes,
gateway semantic caching only for workloads where cross-user response reuse is
explicitly safe**, and never for anything user-specific, permission-scoped or
authoritative.

### 6.4 Budget enforcement

The only control in this file with no measurement problem, because it is arithmetic
rather than prediction. LiteLLM's documented model is representative: hard budgets
per key, team, org and model, with daily and monthly resets, and requests stop at
the cap. Kong enforces token-based rate limiting with modality-aware cost
accounting. agentgateway enforces API-key-scoped budgets. Azure enforces quota tiers
(RPM and TPM per subscription tier).

No published figures on savings from budget enforcement were found, from any vendor.
**That absence is unsurprising and slightly telling**: budgets prevent overruns
rather than reduce steady-state spend, so there is no saving to advertise. It is the
control most worth having and the one with the least marketing attached.

### 6.5 What to actually do, ordered by verified return

1. **Central credential custody.** Not a cost control. It is the precondition for
   every other control on this list, because spend you cannot see you cannot cap.
2. **Hard budgets per key and per team.** Deterministic, no methodology dispute, no
   security downside.
3. **Provider prompt caching, with a stable tool-definition prefix.** Roughly 10x on
   the cached portion, arithmetic in this repo, and it is already paid for.
4. **Routing to cheaper models**, but measured against your own current baseline
   rather than a vendor's random-routing baseline. AWS's RAG case (63.6%, all-Sonnet
   baseline) is the shape of an honest test.
5. **Semantic caching last, and scoped.** The measured cost saving is unpublished and
   the measured attack success rate is 82% to 89% on production cloud
   infrastructure.

---

## 7. Findings this file contributes back

Corrections and resolutions against existing files in this repo:

1. **Portkey acquisition is now verified** against the Palo Alto press release and
   the FY2026 10-K ($117 million, completed 2026-05-29). Resolves the
   **UNVERIFIED** flag in `research/scale/mcp-at-scale-architecture-2026-09.md`
   section 3.
2. **LiteLLM version resolved**: `v1.101.0`, 2026-09-15. Resolves the
   **UNVERIFIED** flag in the same file. Licence is more precisely "MIT except the
   `enterprise/` directory", not MIT.
3. **kgateway version resolved**: `v2.4.5`, 2026-09-16. Resolves the
   **UNVERIFIED** flag in `research/scale/` section 2.1.
4. **Refinement, not a correction**: `research/scale/` section 2.2 states of the
   Agent Router rename that "Only the product name changed." The API group, CLI,
   images and Go module path were retained as stated, and the **GitHub repository
   also moved**, from `envoyproxy/ai-gateway` to `theagentrouter/agent-router`,
   which is a break for pinned clone URLs.
5. **New**: the Portkey OSS gateway has had no commit since 2026-05-25 and no
   release since 2026-01-12, with no public deprecation statement.
6. **New**: Helicone has no taggable current version; a security fix landed on the
   branch 2026-09-16 with the newest tag dated 2025-08-21.
7. **New**: Bedrock native routing has a stale model pool with no Claude 4.x, is
   limited to two models within one family, is English-only, and its documentation
   still reads "During preview" more than a year after April 2025 GA.
8. **New**: no vendor in this category publishes a guard detection rate, false
   positive rate, or evaluation method, while the independent peer-reviewed
   measurement reaches up to 100% evasion against six commercial detectors.
9. **New**: semantic cache poisoning is demonstrated at 82% to 89% attack success
   rate against AWS, Azure and Alibaba under black-box conditions, with existing
   adversarial-prompting defences reported ineffective (NDSS 2026).
10. **New**: no product surveyed publishes a unified policy language spanning the
    inference plane and the MCP tool plane, including the four that share a data
    plane.

## 8. Open items, stated rather than hidden

- **LiteLLM tier boundary for budgets and guardrails.** The vendor's feature page
  and secondary comparisons disagree. Verify against a running instance before
  relying on either.
- **Azure model router savings methodology.** The page carrying the 4.5 / 4.7 /
  14.2 percent figures did not return its body. Unknown prompt count, dataset and
  baseline.
- **The Vertex to Gemini Enterprise Agent Platform transition.** Sourced only
  secondhand in this pass. Must be confirmed against a Google Cloud release note
  before it is said anywhere public.
- **Over-defence percentages for InjecGuard and PromptGuard** (5% to 35% benign
  accuracy, 8.4 point AUC inflation). Surfaced via search, not read from the paper
  PDFs. The directional claim is well supported; the figures are not yet confirmed.
- **TrueFoundry gateway version.** No public version identifier found.
- **Concurrency behaviour for every product in the table.** Nobody publishes a
  saturation point or a degradation curve. This gap is identical to the one already
  recorded on the MCP gateway side.
