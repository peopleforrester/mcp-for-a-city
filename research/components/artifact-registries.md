---
title: "The artifact layers: model registries, prompt registries, and agent registries"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
audience: "Enterprise platform engineers and MCP maintainers. Brief B of the component wave."
---

<!-- ABOUTME: Separates the three things called a registry in an agentic stack and says what each -->
<!-- ABOUTME: actually versions, enforces and omits, with the A2A agent card and MCP server card compared field by field. -->

# The artifact layers

Part B of the component research. Three
things get called a registry, and a fourth, the MCP registry, is already covered
in depth and is not re-covered here.

**Do not read this file for MCP registry mechanics.** Those live in
`research/bestpractice/mcp-gateway-and-registry-operations.md`, Part 2, which
covers the official registry contract, `server.json`, private registry cost,
ingest, freshness, revocation, signing and the absence of federation. This file
references that work and does not repeat it. Prompt cache economics live in
`research/bestpractice/mcp-token-economics-and-tool-consolidation.md`, Section 2,
and are referenced rather than re-derived.

## Sourcing labels

| Label | Meaning |
|---|---|
| **[OFFICIAL]** | A specification, a standards body document, or first-party product documentation from the organisation that owns the thing |
| **[VENDOR]** | Vendor marketing or a vendor engineering blog. Treated as a claim, not evidence |
| **[PEER-REVIEWED]** | Peer-reviewed or preprint with a stated method |
| **[PRACTITIONER]** | A named operator describing something they ran |
| **[SECONDHAND]** | Reported by someone who did not build or measure it |
| **[DERIVED]** | Arithmetic or inference done here, with the inputs named |
| **[UNVERIFIED]** | Could not be traced to a source that makes the claim |

Everything below was fetched and read on **2026-09-18** unless a line says otherwise.

---

# Part 1: Model registries in the MLOps sense

## 1.1 What each one actually versions

| Product | Core object | Versioning | Governance primitives | Source |
|---|---|---|---|---|
| **MLflow Model Registry** | A registered model with named versions | Named model, numbered versions | Aliases (mutable named pointers), tags (key-value on model and version), descriptions, lineage to the producing run | <https://mlflow.org/docs/latest/ml/model-registry/> [OFFICIAL] |
| **SageMaker Model Registry** | A Model Package inside a Model Package Group | New version per registered package | Approval status on a model, Model Cards surfaced in the record, lineage, a "staging construct that models can progress through", Collections, sharing | <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html> [OFFICIAL] |
| **Vertex AI Model Registry** | A model resource with versions | Versions plus aliases | Aliases, labels, deployment linkage, BigQuery ML integration | <https://docs.cloud.google.com/vertex-ai/docs/model-registry/introduction> [OFFICIAL] |
| **Hugging Face Hub** | A git repository holding model checkpoints | Git, so commits and refs | Repository permissions, model cards, organisations | <https://huggingface.co/docs/hub/en/models-the-hub> [OFFICIAL] |
| **Weights and Biases Registry** | A curated collection of artifact versions | Immutable artifact versions | Aliases, lineage graphs to the producing run, lifecycle stage promotion | <https://docs.wandb.ai/models/registry> and <https://wandb.ai/site/registry/> [VENDOR] |

SageMaker's capability list, verbatim, is the fullest statement of what this
class of product claims to do:

> "Catalog models for production. Manage model versions. Associate metadata,
> such as training metrics, with a model. View information from Amazon SageMaker
> Model Cards in your registered models. View model lineage for traceability and
> reproducibility. Define a staging construct that models can progress through
> for your model lifecycle. Manage the approval status of a model. Deploy models
> to production. Automate model deployment with CI/CD. Share models with other
> users."

[OFFICIAL], <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html>, read 2026-09-18.

**Verified versions, 2026-09-18.** MLflow 3.16.1, published to PyPI
2026-09-16T23:14:16Z. `wandb` 0.30.0. `huggingface_hub` 1.32.0. All read from
the PyPI JSON API on 2026-09-18. [OFFICIAL]

## 1.2 The one deprecation that matters

MLflow's Model Stages are deprecated:

> "Model Stages are deprecated and will be removed in a future major release."

[OFFICIAL], <https://mlflow.org/docs/latest/ml/model-registry/workflow>, read
2026-09-18. The recommended replacement is model version tags for status and
model version aliases for deployment pointers. Search results attribute the
deprecation to MLflow 2.9.0; **the MLflow documentation page read in this pass
does not state the version number, so 2.9.0 is [SECONDHAND] and unverified
here.**

This matters beyond MLflow because stages were the mechanism that encoded
promotion and approval. Replacing them with tags and aliases moves promotion
from a first-class, constrained state machine to a convention. An alias named
`production` carries no enforcement, no approver identity, and no timestamp
unless the operator adds them as tags.

## 1.3 What an enterprise uses these for once the consumer is an agent

This is the part of the brief where the honest answer is partly an absence.

**What is verifiable.** Every product above still versions a *trained model
artifact* plus the metadata of the run that produced it. Nothing in the
documentation of any of the five redefines that object for an agentic consumer.
MLflow markets itself as "the open source AI engineering platform for agents,
LLMs, and ML models" (<https://github.com/mlflow/mlflow>, [OFFICIAL], read
2026-09-18), but the agent-facing surface it points to is Tracing, Evaluation,
Monitoring and the separate Prompt Registry, not the Model Registry. The
MLflow GenAI landing page fetched in this pass makes no statement that agents
are registered in the Model Registry.
<https://mlflow.org/docs/latest/genai/> [OFFICIAL], read 2026-09-18.

**The structural argument, labelled as synthesis rather than sourced.** When an
agent calls a hosted frontier model over an API, the deployed unit is a string
model id plus a set of parameters. There is no weights artifact in the
enterprise's custody, so the registry's core object does not exist for that path.
What remains genuinely load bearing is the set of models an enterprise does hold:
fine-tuned and self-hosted models, embedding models, rerankers, and the
classifier models used in guardrails. This is my reading of the field definitions
above, not a claim any of the five vendors makes. [DERIVED]

**Practitioner accounts: searched and not found.** Multiple searches for named
operators reporting that they stopped using, or downgraded, a model registry once
their consumer became an agent returned vendor content, listicles and
comparison-site articles. **No first-hand practitioner account either way was
located in this pass.** Stated as an absence, not as evidence that the practice
does not exist. Anyone repeating "model registries are legacy in an agentic
stack" should be asked for a source, because one was not found here.

**The regulatory case for keeping them is documented, and is narrower than it
looks.** The appliedAI Institute for Europe's Practical AI Act guide says a model
registry "can be used to correlate post-market monitoring data with specific
model versions" and describes storing models in a versioned manner with metadata
and lineage. <https://practical-ai-act.eu/latest/engineering-practice/model-registry/>
[OFFICIAL, standards-adjacent], read 2026-09-18. **The guide does not address
the case where the system is built on a third-party foundation model API and the
deployer holds no weights.** That silence is the interesting part: the obligation
to correlate monitoring data with a version survives, but the artifact the guide
assumes you are versioning does not.

**Verdict.** Load bearing for the models an enterprise trains or hosts, and for
the audit record. Not load bearing as the thing that governs what an agent may
call, which is the question an MCP or agent registry answers. Treating one as a
substitute for the other is the confusion the component map warns about.

## 1.4 A secondhand framing worth quoting carefully

Atlan, a data governance vendor, published a direct comparison on 2026-09-01:

> "A model registry versions trained model artifacts, tracking
> staging-to-production promotion and experiment lineage."

> "An agent registry catalogs and approves running agents, tools, skills, and MCP
> servers, tracking identity, ownership, and dependencies."

<https://atlan.com/know/ai-agent/agent-registry-vs-model-registry/> [SECONDHAND,
vendor-authored]. The framing is correct and matches the primary sources above.
Its own sourcing is AWS documentation plus analyst research, so cite the AWS
material directly rather than this page.

---

# Part 2: Prompt registries and prompt versioning

## 2.1 What exists and what it versions

**MLflow Prompt Registry.** A separate product surface from the Model Registry.
It uses "Git-inspired commit-based versioning", versions are immutable, and
aliases are "mutable named reference[s] to the prompt" such as `production`. The
documented API is `mlflow.genai.register_prompt()`, `mlflow.genai.load_prompt()`,
`mlflow.genai.set_prompt_tag()` and `mlflow.genai.set_prompt_version_tag()`.
Aliases are stated to allow you to "perform tasks such as A/B testing and
roll-backs." Prompts integrate with Tracing, Evaluation and Monitoring.
**No approval workflow is documented.**
<https://mlflow.org/docs/latest/genai/prompt-registry/> [OFFICIAL], read 2026-09-18.

**Langfuse prompt management.** Version control plus labels for managing
deployments across environments. The product's stated selling point is the
removal of the deploy step:

> "prompt updates deploy instantly, without needing to involve engineering or
> triggering a deployment"

> "Langfuse Prompt Management adds no latency to your application."

<https://langfuse.com/docs/prompt-management/overview> [OFFICIAL], read 2026-09-18.
Rollback and A/B testing are not described on that overview page.

**LangSmith Prompt Hub and Braintrust** are named in the comparison literature as
the other two commonly used options. **Neither was independently verified in this
pass.** Do not cite either from this file.

## 2.2 Prompts as code or as config: the strongest evidence points to code

OpenAI is retiring its managed prompt object and telling developers to move the
content into their own repositories.

> "Prompt creation will be de-emphasized beginning June 3, 2026"

> "`v1/prompts` is scheduled to shut down on November 30, 2026"

> "Move the prompt content out of the managed `prompt` object and into your
> application code."

> "This gives you more control over review, testing, deployment, and versioning."

<https://developers.openai.com/api/docs/guides/prompting/migrate-from-prompt-object>
[OFFICIAL], read 2026-09-18.

This is a model provider, having shipped a prompt registry as an API primitive,
concluding that review, testing, deployment and versioning are better served by
source control. It is the single most load-bearing data point in this part of the
brief, and it cuts directly against the Langfuse positioning quoted above, whose
explicit value proposition is that a prompt change does not go through a
deployment.

Both positions are coherent and they are optimising for different failure modes.
The registry-as-config model optimises for iteration speed by a non-engineer. The
prompt-as-code model optimises for the change being reviewable, testable and
revertable through the same gate as every other change. An enterprise deciding
between them is choosing which of those two it is willing to lose, and neither
vendor frames it that way.

## 2.3 The prompt cache interaction, which nobody documents

Two different caches share the word, and conflating them produces wrong cost
models.

**Cache one: the prompt registry's own fetch cache.** Langfuse caches prompt
documents client-side in the SDK. "The default cache TTL (Time To Live) is 60
seconds." "When the cache TTL has expired, stale prompts are served immediately
while it revalidates in the background." Configurable via `cache_ttl_seconds`
(Python) or `cacheTtlSeconds` (JS/TS).
<https://langfuse.com/docs/prompt-management/features/caching> [OFFICIAL], read
2026-09-18. This cache saves an HTTP round trip to Langfuse. It has no effect on
what the model provider charges.

**Cache two: the model provider's prompt cache.** Documented in detail in
`research/bestpractice/mcp-token-economics-and-tool-consolidation.md`, Section 2,
including Anthropic's published cache prefix ordering (`tools`, then `system`,
then `messages`) and the invalidation table. That file is the reference; it is not
repeated here.

**The interaction, derived.** A prompt registry whose whole purpose is to swap a
system prompt at runtime is, in cache terms, a mechanism for invalidating the
`system` segment of the provider's cache prefix and everything downstream of it.
Because `tools` sits ahead of `system` in Anthropic's ordering, a prompt swap does
not invalidate the cached tool definitions, which is the expensive segment in an
MCP-heavy deployment. A tool definition change does invalidate everything. So the
two levers have very different blast radii: rotating a prompt through a registry
alias is comparatively cheap, and adding a tool is not. [DERIVED] from the
published ordering documented in the token economics file; the arithmetic inputs
are named there.

**The absence is the finding.** Of the prompt registry documentation read in this
pass, **none mentions provider-side prompt caching at all.** The Langfuse caching
page "makes no mention of LLM provider prompt caching". The MLflow Prompt Registry
page does not raise it. A platform team that adopts a prompt registry to get
instant rollout, and separately adopts prompt caching to control cost, will find
no vendor documentation telling them the two features interact. Verified by
reading both pages on 2026-09-18.

---

# Part 3: Agent registries and A2A agent cards

This is the centre of the brief. The short version: the two card formats are not
merging, and a joint MCP and A2A steering body is building a shared discovery and
trust envelope around both of them instead.

## 3.1 A2A status and governance

| Fact | Value | Source |
|---|---|---|
| Specification version named as latest on the spec page | `1.0.0` | <https://a2a-protocol.org/latest/specification/> [OFFICIAL] |
| Latest GitHub release tag | `v1.0.1`, published 2026-05-28T11:34:36Z | GitHub Releases API for `a2aproject/A2A` [OFFICIAL] |
| `v1.0.0` release date | 2026-03-12T16:34:41Z | same |
| Previous major | `v0.3.0`, 2025-07-30 | same |
| Protobuf package | `lf.a2a.v1` | `specification/a2a.proto` [OFFICIAL] |
| Foundation | Accepted as an AAIF hosted project | <https://aaif.io/blog/a2a-joins-aaif>, post dated 2026-08-17 as read [OFFICIAL] |

**Note the discrepancy.** The specification page declares `1.0.0` as the latest
released version while the repository has shipped `v1.0.1`. Quote `1.0.0` when
citing the specification and `v1.0.1` when citing the release, and do not merge
them into one number.

The AAIF post read in this pass lists five projects (AGENTS.md, goose, MCP,
agentgateway, A2A). `research/scale/mcp-at-scale-architecture-2026-09.md` records
six, adding Agent Router. The two are not necessarily in conflict, since they were
read at different times, but do not assert a project count from this file.

The `aaif.io` post read here **makes no statement about how A2A relates to MCP or
about convergence between them.** A companion post exists at
<https://a2a-protocol.org/latest/blog/2026/08/27/a-new-chapter-for-a2a-joining-the-agentic-ai-foundation/>
and was **not** read in this pass.

## 3.2 The agent card, field by field

Read verbatim from `specification/a2a.proto` on the `main` branch, 2026-09-18.
[OFFICIAL]

`AgentCard`:

| Field | Required | Notes from the proto comments |
|---|---|---|
| `name` | REQUIRED | "A human readable name for the agent." |
| `description` | REQUIRED | |
| `supported_interfaces` | REQUIRED, repeated | "Ordered list of supported interfaces. The first entry is preferred." |
| `provider` | optional | `AgentProvider`, which is exactly two REQUIRED fields: `url` and `organization` |
| `version` | REQUIRED | "The version of the agent." |
| `documentation_url` | optional | |
| `capabilities` | REQUIRED | `AgentCapabilities` |
| `security_schemes` | map | Discriminated union over API key, HTTP auth, OAuth2, OIDC, mTLS, "based on the OpenAPI 3.2 Security Scheme Object" |
| `security_requirements` | repeated | |
| `default_input_modes` | REQUIRED | Media types |
| `default_output_modes` | REQUIRED | Media types |
| `skills` | REQUIRED, repeated | `AgentSkill` |
| `signatures` | repeated | "JSON Web Signatures computed for this `AgentCard`." |
| `icon_url` | optional | |

`AgentSkill`: `id`, `name`, `description`, `tags` all REQUIRED; `examples`,
`input_modes`, `output_modes`, `security_requirements` optional. The proto
comment is careful about what a skill is: "It is largely a descriptive concept but
represents a more focused set of behaviors that the agent is likely to succeed at."

`AgentCapabilities`: `streaming`, `push_notifications`, `extensions`,
`extended_agent_card`, all optional booleans or lists.

`AgentInterface`: `url`, `protocol_binding` ("The core ones officially supported
are `JSONRPC`, `GRPC` and `HTTP+JSON`"), `tenant` ("An opaque string used for
routing requests to a specific agent or tenant when multiple agents are served
behind a single A2A endpoint"), `protocol_version`.

`AgentCardSignature`: `protected`, `signature`, `header`. "This follows the JSON
format of an RFC 7515 JSON Web Signature (JWS)."

**What is not in an agent card.** No owner or contact beyond `provider.organization`.
No approval state. No lifecycle or deprecation marker. No cost or rate information.
No data classification. No internal identifier. Verified by reading the full
message definition, not inferred from a summary.

## 3.3 Where agent discovery lives

The specification names three mechanisms and prescribes only one of them:

> "**Well-Known URI:** Accessing `https://{server_domain}/.well-known/agent-card.json`"
> "**Registries/Catalogs:** Querying curated catalogs of agents"
> "**Direct Configuration:** Pre-configured Agent Card URLs or content"

Section 8.2, <https://raw.githubusercontent.com/a2aproject/A2A/main/docs/specification.md>
[OFFICIAL]. Section 8.1 makes the card itself mandatory: "A2A Servers **MUST**
make an Agent Card available."

The registry option is explicitly unspecified. From the discovery guide:

> "The current A2A specification does not prescribe a standard API for curated
> registries."

and, as the closing line of the same document:

> "The A2A community explores standardizing registry interactions or advanced
> discovery protocols."

<https://raw.githubusercontent.com/a2aproject/A2A/main/docs/topics/agent-discovery.md>
[OFFICIAL], read 2026-09-18.

**Signing is optional.** "Agent Cards **MAY** be digitally signed using JSON Web
Signature (JWS)." Canonicalisation is JCS, RFC 8785, with the `signatures` field
excluded from the signed content. Verification is a six-step MUST list for clients
that choose to verify, and the trust decision is a SHOULD: "Clients **SHOULD**
verify at least one signature before trusting an Agent Card." Sections 8.4 through
8.4.3. [OFFICIAL]

**Caching is HTTP caching.** `Cache-Control` with `max-age`, `ETag` derived from
the card's `version` field or a content hash, conditional requests per RFC 9111.
Section 8.6. [OFFICIAL] This is the same class of mechanism as the MCP caching
utility and is unrelated to model prompt caching.

## 3.4 How agent discovery differs from MCP tool discovery, structurally

Both protocols have to answer the same question: the capability surface varies by
who is asking. They answer it in opposite directions.

**A2A puts the capability list in the static document and adds an authenticated
variant of that document.** `skills` is a REQUIRED field on the card. There is no
runtime "list skills" operation in the A2A operation set (`SendMessage`,
`SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`,
the push-notification config operations, and `GetExtendedAgentCard`). Per-identity
variation is handled by `GetExtendedAgentCard`, which "**MUST** require
authentication" and "**MAY** return different extended card content based on the
authenticated client's identity or authorization level", and may "include
additional skills not present in the public card". Sections 3.1.11 and 13.3.
[OFFICIAL]

**MCP puts the capability list at runtime and deliberately keeps it out of the
static document.** `tools/list` is a protocol operation, and the Server Card
extension refuses to duplicate it. In the SEP's own words:

> "This specification intentionally omits primitive definitions (tools, resources,
> and prompts) from server cards. MCP servers are inherently dynamic: the
> primitives a server exposes can vary by authenticated user, session,
> configuration, feature flags, deployment state, and more. A static document
> cannot reliably represent this surface, and there is currently no viable
> substitute for runtime listing via the protocol's standard operations
> (`tools/list`, `resources/list`, `prompts/list`) with the logged-in user's
> identity."

<https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/sep/mcp-server-cards/seps/2127-mcp-server-cards.md>
[OFFICIAL], read 2026-09-18.

That is the single sharpest difference between the two formats, and it is a
deliberate, documented design decision on the MCP side rather than an oversight.
The practical consequence for a governance layer: an A2A agent's declared skills
can be reviewed offline, from a document, before anything connects. An MCP
server's tool surface cannot, and any approval process that claims to have
reviewed an MCP server's tools has reviewed a snapshot of them.

## 3.5 MCP Server Cards: current status, corrected

`research/bestpractice/mcp-gateway-and-registry-operations.md` recorded SEP-2127
as "Draft, target Apr 3 2026, not shipped" on 2026-09-18, sourced from the Server
Card WG charter page. Checked against the SEP itself and the GitHub API on the
same day, the picture is more specific:

| Fact | Value | Source |
|---|---|---|
| PR state | **open**, not merged, labels `SEP`, `in-review`, `extension`, `roadmap/transport` | GitHub API, `modelcontextprotocol/modelcontextprotocol` PR 2127 [OFFICIAL] |
| PR created / last updated | 2026-01-21 / 2026-09-12 | same |
| Status line inside the SEP document on its branch | `- **Status**: Final` | the SEP file itself [OFFICIAL] |
| Type | Extensions Track, per SEP-2133 | same |
| Extension identifier | `io.modelcontextprotocol/server-card` | same |
| Authors | David Soria Parra, Sam Morrow, Tadas Antanavicius, on behalf of the Server Card Working Group | same |
| Wire format location | `modelcontextprotocol/experimental-ext-server-card`, "graduating to an `ext-server-card` repository on acceptance" | same |

So: the SEP text declares itself Final, the pull request that would land it is
still open and labelled in-review, and the repository holding the normative wire
format is still named `experimental-`. Not merged, not accepted. Anyone citing
"MCP Server Cards are final" is quoting a line inside an unmerged document.

**A widely repeated path claim is wrong.** Secondhand summaries state the
discovery path is `/.well-known/mcp/server-card.json`. The extension's own
discovery document lists that placement under "Alternatives considered" and
explicitly does not recommend it:

> "**A `.well-known` URI** (e.g., `/.well-known/mcp/server-card`). `.well-known`
> is for _site-wide_ metadata, whereas an individual server's card is
> _application-level_ metadata."

The reserved location is instead:

> "MCP Servers MAY host their Server Card at `GET <streamable-http-url>/server-card`,
> which we reserve for this purpose, though any unreserved URI (on any domain) is
> valid."

Domain-level discovery is delegated to the AI Catalog at
`/.well-known/ai-catalog.json`. Media type `application/mcp-server-card+json`.
<https://raw.githubusercontent.com/modelcontextprotocol/experimental-ext-server-card/main/docs/discovery.md>
[OFFICIAL], read 2026-09-18.

**The Server Card is explicitly not an authority.**

> "Clients MUST NOT treat Server Card contents as authoritative for security or
> access-control decisions."

> "Clients SHOULD verify a Server Card's claims against the live connection,
> preferring the runtime values where the two disagree."

Same source. A2A's specification contains no equivalent statement subordinating
the agent card to runtime, which follows from there being no runtime skill list to
subordinate it to.

## 3.6 Where the agent card and `server.json` overlap, field by field

`server.json` fields read from the registry schema on 2026-09-18:
<https://raw.githubusercontent.com/modelcontextprotocol/registry/main/docs/reference/server-json/draft/server.schema.json>
[OFFICIAL]. Required: `name`, `description`, `version`. Optional: `$schema`,
`_meta`, `icons`, `packages`, `remotes`, `repository`, `title`, `websiteUrl`.

| Concept | A2A agent card | MCP `server.json` | MCP Server Card |
|---|---|---|---|
| Identity | `name`, free-form | `name`, reverse-DNS with exactly one slash | `name` |
| Human text | `description` | `description`, `title` | `description`, `title` |
| Version | `version`, REQUIRED | `version`, REQUIRED, SHOULD be semver | `version` |
| Endpoint | `supported_interfaces[].url` plus `protocol_binding`, `protocol_version`, `tenant` | `remotes[]` and `packages[]` | `remotes[]` with `headers`, `variables`, `supportedProtocolVersions` |
| Capability surface | **`skills[]`, REQUIRED and enumerated** | **absent** | **deliberately excluded** |
| Auth | `security_schemes` plus `security_requirements`, OpenAPI 3.2 shaped | **absent from the document** | **absent from the document** |
| Publisher | `provider.organization`, `provider.url` | inferred from the reverse-DNS namespace; `repository`, `websiteUrl` | `repository`, `websiteUrl` |
| Local install | **absent by design** | `packages[]` with `registryType`, `identifier`, `transport`, `fileSha256` | **out of scope**, see below |
| Integrity | `signatures[]`, JWS, MAY | `fileSha256` on a package entry only | none in the document |
| Icons | `icon_url` | `icons[]` | `icons[]` |
| Extension slot | `AgentExtension` on capabilities | `_meta`, reverse-DNS namespaced | `_meta`, namespaced, and "not used to advertise MCP capabilities" |

The SEP draws the boundary between the two MCP documents itself:

> "MCP Server Cards describe _remote_ MCP connectivity only. The MCP Registry's
> `server.json` separately describes registry entries, including locally
> installable packages and their runtime configuration. The Registry owns that
> schema; the Server Card extension does not define a `Server` superset or
> package-installation types."

[OFFICIAL], SEP-2127.

**The three real conflicts, as opposed to differences.**

1. **Skills versus tools.** An agent card must enumerate its skills; an MCP server
   document must not enumerate its tools. A single system that is both an A2A agent
   and an MCP server has to describe the same underlying capability twice, once
   statically and once at runtime, with no defined relationship between the two
   descriptions and no rule for what to do when they disagree.
2. **Authentication.** An agent card carries full OpenAPI-shaped security schemes.
   Neither MCP document carries any; MCP auth is discovered through
   `/.well-known/oauth-protected-resource` and the authorization specification. A
   catalogue holding both record types therefore has authentication metadata for
   one and not for the other.
3. **Naming.** `server.json` mandates reverse-DNS with exactly one slash, which
   encodes a namespace claim. `AgentCard.name` is "a human readable name" with no
   structure at all. Deduplicating across the two is a naming problem before it is
   a schema problem, which is the same failure documented in
   `research/bestpractice/mcp-gateway-and-registry-operations.md` section 8.1.

## 3.7 Are they converging? Yes, but not in the way the question implies

The two card formats are not being merged. A joint body is standardising a common
container and a common trust layer around them, and the protocol-specific formats
are explicitly staying as they are.

**The project.** `Agent-Card/ai-catalog`, "Working repository for common AI Card
standard". Created 2025-10-29. 227 stars and last pushed 2026-09-05 as read on
2026-09-18. **Zero GitHub releases.** Published at <https://ai-catalog.io/>.
[OFFICIAL]

> "Members from various AI protocols (MCP, A2A, and others) are collaborating on a
> common AI Catalog standard for discovering heterogeneous AI artifacts across the
> ecosystem."

> "The **AI Catalog** standard does not replace or redefine protocol-specific
> artifact formats. It provides a common discovery and trust layer around them."

README, [OFFICIAL], read 2026-09-18.

**The governance is the evidence that this is real.** Four TSC seats:

| Company | Representative |
|---|---|
| Google | Junjie Bu |
| Microsoft | Darrel Miller |
| Anthropic | David Soria Parra |
| PulseMCP | Tadas Antanavicius |

> "At the inception of the Project, four TSC members will be nominated. Two will be
> nominated by MCP Core Maintainers ... and two will be nominated by the the Linux
> Foundation A2A Technical Steering Committee."

`GOVERNANCE.md`, [OFFICIAL]. Meetings run on the Linux Foundation meeting
platform. The repository states its own impermanence: "This is a temporary working
repo maintained by the Linux Foundation" and "This project will be moved to a
permanent location a later date with a permanent governance model."

**The adoption plan, in the project's own words.** This is the sentence that
answers the brief's question directly:

> "When the specification is finalized, A2A and MCP steering committees will vote
> on adoption of the AI Catalog standard, potentially replacing existing
> protocol-specific standards or proposals."

> "Protocol-specific artifacts would remain in their native formats and become
> discoverable through common AI Catalog entries."

> "If adopted, MCP and A2A steering committees will recommend duplicative
> card-adjacent efforts be consolidated, such as Registry, Agent Identity, and
> others."

README, [OFFICIAL], read 2026-09-18. Note the conditionals. The vote has not
happened.

**The mechanism.** Entries are typed by media type. The recognised types are
partitioned by who governs them:

Core, governed by the AI Catalog WG: `application/ai-catalog+json` (a nested
catalog) and `application/agent-card+json`, "reserved for a generic Agent Card
format".

Governed externally: `application/a2a-agent-card+json`,
`application/mcp-server-card+json`, `application/agent-skills+json`,
`application/agent-skills+md`, `application/agent-skills+zip`,
`application/agent-skills+gzip`, `application/agent-plugins+zip`,
`application/agent-plugins+gzip`.

Specification, [OFFICIAL]. Identifiers use `urn:air:{publisher}:{namespace}:{name}`,
"HIGHLY RECOMMENDED" and "MUST be used for open or federated systems". An entry
carries either a `url` to the native artifact or the artifact inlined in `data`.

**The scope split is documented as a real disagreement, not a tidy division.**
ADR-0017, status Accepted, discussed 2026-07-02 and agreed 2026-07-09, records
that the Agentic Resource Discovery group wanted JSON-LD `@context` for rich
federated metadata and the AI Catalog TSC refused, on the grounds that catalog
entries are "least common denominator" pointers rather than data envelopes. The
two specifications were deliberately decoupled so neither blocks the other. The
ADR names thirteen participants including Darrel Miller, David Soria Parra, Pamela
Dingle, Ramanathan Guha and Tadas Antanavicius. [OFFICIAL]

## 3.8 Commercial agent registries that already hold both record types

**AWS Agent Registry.** Generally available 2026-08-31.
<https://aws.amazon.com/about-aws/whats-new/2026/08/aws-agent-registry-generally-available/>
[OFFICIAL]. The accompanying engineering post, dated 31 AUG 2026, states the
record types verbatim:

> "Registry supports four record types: MCP – Model Context Protocol server, its
> tools, resources, and prompts. Agent – Agent2Agent (A2A) agent card defining
> agents and their skills. Skill – agent skill definitions in markdown files and
> associated code/packages. Custom – Custom descriptor which must be valid JSON."

> "The Approver reviews the workflow outcome and takes one of two actions:
> Approves – Record moves to APPROVED state. Rejects – Record moves to REJECTED
> state."

> "Registry exposes each registry instance as an MCP server. MCP compatible IDE,
> including Kiro and Claude Code, can connect to it natively."

> "An admin enables endpoint detection once at the AWS Organization level, and
> Registry automatically detects agents and MCP servers running on AgentCore
> runtime across every account in the organization."

<https://aws.amazon.com/blogs/machine-learning/manage-agents-tools-and-skills-at-scale-with-aws-agent-registry/>
[VENDOR], read 2026-09-18.

Two observations worth carrying forward. First, AWS holds A2A agent cards and MCP
server records as **sibling types in one catalogue rather than merging them**,
which is the same architectural choice the AI Catalog makes. Second, AWS's MCP
record type is described as covering "its tools, resources, and prompts", which is
exactly the primitive enumeration that SEP-2127 refuses to put in a static
document. If that description is accurate, AWS has taken the opposite position to
the MCP specification on the one question the specification argued hardest about,
and a record's tool list will drift from the server's runtime surface. **Not
independently verified against the AWS API schema in this pass.**

**Microsoft.** Agent 365 is becoming the unified registry and Entra Agent ID
remains the identity layer. "**Agent 365** becomes the unified registry and control
plane for agents." "**Microsoft Entra** continues to provide the identity
foundation through Agent ID." Microsoft's own wording for the split is that "the
comprehensive agent inventory, including agents without a Microsoft Entra agent
identity, is available in Agent 365", while the Entra admin center shows only
agents that have an Entra agent identity. Page `ms.date`
2026-04-05, `updated_at` 2026-06-17.
<https://learn.microsoft.com/en-us/entra/agent-id/agent-registry-convergence>
[OFFICIAL]. Entra Agent ID itself, including the directory object type, blueprints
and the sponsor field, is already covered in
`research/ecosystem/microsoft-mcp-control-plane.md` section 2.1 and is not
re-covered here.

---

# Part 4: The comparison

## 4.1 What each versions, who owns it, what it enforces

| | Model registry | Prompt registry | MCP registry | Agent registry (A2A cards) | AI Catalog |
|---|---|---|---|---|---|
| **Versioned object** | A trained model artifact plus its training run | A prompt template text plus optional model config | A `server.json` record naming a server and its packages or remotes | An agent card describing identity, interfaces, auth and skills | A typed pointer to any of the above |
| **Who owns it in an enterprise** | ML platform or data science | Application team, sometimes product | Platform engineering | Platform engineering or the agent team | Not yet owned by anyone; the spec has no releases |
| **Who owns the standard** | Nobody. Five vendor-specific products | Nobody. Vendor-specific, and OpenAI is exiting | MCP project, Registry WG | A2A project, LF TSC | Joint MCP and A2A TSC, four seats |
| **What it enforces** | Approval status (SageMaker), stage or alias, immutability of a version | Immutability of a version, alias resolution | Nothing at the protocol layer; the official registry is a metadata service, see the existing registry research | Nothing. The card is a self-description | Nothing. Conformance levels 1 to 3 define what a consumer must verify, not what a publisher must do |
| **Signed?** | Product-specific | No | `fileSha256` per package only | `signatures[]`, JWS, MAY | Trust Manifest `signature`, required only at conformance Level 3 |
| **Runtime authority** | The deployed endpoint | The running application | `tools/list` at runtime, always | The card, plus the authenticated extended card | Delegates entirely to the artifact |

## 4.2 What happens when they disagree

**MCP resolves in favour of runtime, in writing.** "Clients SHOULD verify a Server
Card's claims against the live connection, preferring the runtime values where the
two disagree", and clients "MUST NOT treat Server Card contents as authoritative
for security or access-control decisions." [OFFICIAL]

**A2A has no runtime to defer to for skills.** There is no skill-listing
operation. A stale `skills` array is not detectable by the protocol; the client
discovers the error by sending a message and getting a bad result. The only
corrective mechanism is `GetExtendedAgentCard`, which requires authentication and
is only available when the public card declares `capabilities.extendedAgentCard`.
An unauthenticated client has the static card and nothing else. [OFFICIAL],
sections 3.1.11, 13.3, and the operation list in section 3.1.

**Between a registry record and the thing it describes, nobody arbitrates.** The
existing registry research documents this for MCP: status is real and is not in
`server.json`, it lives in registry-owned `_meta`, and revocation propagation to
downstream aggregators has no guarantee. See
`research/bestpractice/mcp-gateway-and-registry-operations.md` sections 5.3, 6.2
and 6.3. The same hole exists on the A2A side with less machinery around it, since
there is no standard registry API at all.

**Between a model registry and an agent registry, the version skew is silent.** An
agent record approved on the basis of a particular model, prompt version and tool
set has no field in any of the formats above that binds it to those three. The
agent card has `version`; what that version is a version *of* is undefined. This
is the practical form of the Atlan observation quoted in 1.4: "Registry integrity
and context accuracy are different audits."

---

# Part 5: The stated gaps, confirmed or refuted

## 5.1 "No portable approval or ownership metadata"

**CONFIRMED for the wire formats, as of 2026-09-18.**

- The A2A agent card has no approval field, no owner field, no lifecycle state and
  no contact. The closest thing is `provider`, which is two strings: an
  organisation name and a URL. Verified against the full proto message.
- `server.json` has no approval field. The existing registry research already
  establishes that status "is real, and it is not in `server.json`"; it lives in
  registry-owned `_meta`, which by construction does not travel with the record in
  any standard way.
- The MCP Server Card has no approval or ownership field, and its `_meta` is
  explicitly narrowed: "not used to advertise MCP capabilities or negotiated
  extension support."
- Both vendor registries that do carry approval carry it in proprietary fields.
  AWS's `APPROVED` and `REJECTED` states are AWS states. Microsoft's ownership and
  sponsorship live in Entra. Neither serialises into a document another
  organisation's registry can read.

**PARTIALLY REFUTED as a claim about the future.** The AI Catalog Trust Manifest is
precisely a portable approval and provenance envelope, and it is designed not to
touch the artifact:

> "The Trust Manifest does NOT wrap the artifact. It sits alongside the artifact as
> a peer element within a Catalog Entry, keeping the native artifact format
> unmodified."

It requires an `identity` that "SHOULD be a DID, SPIFFE ID, or URL", carries an
`attestations` array (`type` such as "SOC2-Type2", `uri`, optional `digest`,
`size`, `description`), a `provenance` array of link objects (`relation`,
`sourceId`, optional `sourceDigest`, `registryUri`, `statementUri`,
`signatureRef`), a `signature` with `subject` and `issuedAt`, and an optional
`trustSchema`. The Publisher object on the entry carries `identifier`,
`displayName` and an optional `identityType` hint such as "did" or "dns".
Conformance Level 3 requires a signature, a subject binding and an `issuedAt`, and
requires consumers to verify all three before relying on any claim. There is an
explicit anti-theatre rule: a Trust Manifest carrying only non-substantive members
"MUST be omitted entirely rather than included empty". [OFFICIAL], specification,
read 2026-09-18.

**Three caveats that keep this a gap today.** The specification has zero releases
and lives in a repository its own governance document calls temporary. The
adoption vote by the A2A and MCP steering committees has not happened. And the
attestation model is aimed at compliance documents, SOC 2 and ISO 27001 and the
like, rather than at the mundane internal record an enterprise actually needs,
which is "approved for use by this person, on this date, for this population". A
`trustSchema` or a custom attestation `type` could carry that, but no field is
defined for it.

## 5.2 "No federation"

**CONFIRMED for both protocols as they stand.**

- MCP: no federation model exists. One-directional scraping by downstream
  aggregators is the only defined relationship, with no trust protocol, no signing
  chain, no revocation propagation guarantee, no conflict resolution and no
  freshness contract. Established in
  `research/bestpractice/mcp-gateway-and-registry-operations.md` section 6.5 and
  not re-derived here.
- A2A: weaker still, because there is no standard registry API to federate. "The
  current A2A specification does not prescribe a standard API for curated
  registries." [OFFICIAL]

**PARTIALLY REFUTED as a claim about the future, with a caveat about what the word
means.** The AI Catalog names federation as design goal 5:

> "**Scalable Federation**: The catalog format enables partitioning into
> sub-catalogs to manage size, and supports delegation to sub-catalogs managed by
> independent publishers. Nested catalog entries support a federated model where
> each segment of the hierarchy may be authored, hosted, and updated
> independently."

[OFFICIAL], specification. The mechanism is that any entry may have
`type: application/ai-catalog+json` and point at another catalog.

That is hierarchical delegation, which is a real and useful thing, and it is not
the same as peer federation between two registries operated by different
organisations that need to reconcile overlapping records. Nothing read in this
pass defines conflict resolution between two catalogs that both claim the same
`urn:air` identifier, and the specification's own security section lists
"Identifier Typosquatting" and "Catalog Poisoning" as threats rather than as
solved problems. A cross-registry query interface is named as future work, not as
shipped: "The AI Catalog project should also define a common **AI Catalog
Registry** standard that provides a universal interface for clients to interact
with catalog collections." [OFFICIAL], README.

## 5.3 A third gap, not in the brief, worth recording

**Nothing binds an agent record to the model and prompt versions it depends on.**
A model registry versions weights. A prompt registry versions templates. An agent
card versions the agent. No field in any of the five formats compared in 4.1 links
the three, and no vendor registry examined here does it either. The consequence is
that the question "which model and which prompt was this approved agent running
when it was approved" has no standard answer, and an enterprise that needs one has
to invent a convention in `_meta` or in a custom record type. Searched for in this
pass across the A2A proto, the `server.json` schema, the Server Card schema, the
AI Catalog specification and the AWS record-type description; **found in none of
them.**

---

# Verification ledger

Fetched and read directly on 2026-09-18:

- `a2aproject/A2A` `specification/a2a.proto` and `docs/specification.md` on `main`,
  via raw.githubusercontent.com. Sections 8.1 to 8.6, 3.1.11, 13.3, 14, Appendix B.
- `a2aproject/A2A` `docs/topics/agent-discovery.md` on `main`.
- A2A releases via the GitHub API: `v1.0.1` 2026-05-28, `v1.0.0` 2026-03-12,
  `v0.3.0` 2025-07-30.
- <https://a2a-protocol.org/latest/specification/> and
  <https://a2a-protocol.org/latest/topics/a2a-and-mcp/>.
- <https://aaif.io/blog/a2a-joins-aaif>.
- `modelcontextprotocol/modelcontextprotocol` PR 2127 via the GitHub API, and
  `seps/2127-mcp-server-cards.md` on branch `sep/mcp-server-cards`.
- `modelcontextprotocol/experimental-ext-server-card` `schema.ts` and
  `docs/discovery.md` on `main`.
- `modelcontextprotocol/registry` `docs/reference/server-json/draft/server.schema.json`
  on `main`.
- `Agent-Card/ai-catalog` repository metadata via the GitHub API, plus `README.md`,
  `GOVERNANCE.md`, `MAINTAINERS.md`, `specification/ai-catalog.md`,
  `adr/0017-ard-loose-coupling.md` and `docs/implementations.md` on `main`.
- <https://ai-catalog.io/>.
- MLflow: `/docs/latest/ml/model-registry/`, `/docs/latest/ml/model-registry/workflow`,
  `/docs/latest/genai/`, `/docs/latest/genai/prompt-registry/`.
- PyPI JSON API for `mlflow`, `wandb`, `huggingface-hub`.
- <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html>.
- <https://docs.cloud.google.com/vertex-ai/docs/model-registry/introduction>.
- <https://huggingface.co/docs/hub/en/models-the-hub>.
- <https://langfuse.com/docs/prompt-management/overview> and
  `/docs/prompt-management/features/caching`.
- <https://developers.openai.com/api/docs/guides/prompting/migrate-from-prompt-object>.
- <https://aws.amazon.com/about-aws/whats-new/2026/08/aws-agent-registry-generally-available/>
  and the AgentCore engineering post.
- <https://learn.microsoft.com/en-us/entra/agent-id/agent-registry-convergence>.
- <https://practical-ai-act.eu/latest/engineering-practice/model-registry/>.
- <https://atlan.com/know/ai-agent/agent-registry-vs-model-registry/>.

Named but **not** verified in this pass, and not to be cited from this file:
LangSmith Prompt Hub, Braintrust, the a2a-protocol.org AAIF blog post of
2026-08-27, the AWS Agent Registry API schema, and the MLflow version number in
which Model Stages were deprecated.
