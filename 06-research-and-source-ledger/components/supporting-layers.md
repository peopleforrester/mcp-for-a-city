---
title: "The supporting layers: evaluation and observability, secrets brokering, execution sandboxing"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
---

<!-- ABOUTME: Research brief C of the component wave. Covers the three layers an enterprise MCP deployment needs and treats as a footnote. -->
<!-- ABOUTME: The composition question, what each layer sees that the others cannot, is the point of the brief and lives in section 5. -->

## Scope, and what this deliberately does not re-cover

The following are covered in depth elsewhere and are referenced rather than
repeated:

| Already covered | Where |
|---|---|
| MCP gateway projects, 13 compared, and what a gateway enforces | `scale/mcp-at-scale-architecture-2026-09.md`, `bestpractice/mcp-gateway-and-registry-operations.md` |
| Server vetting, supply chain, registry attestation | `bestpractice/mcp-server-vetting-and-supply-chain.md` |
| The code-execution-with-MCP pattern, its effect sizes and its security section | `bestpractice/mcp-token-economics-and-tool-consolidation.md` 4.4 and 5.3, `ops/mcp-operations-at-scale-2026-09.md` |
| SPIFFE/SPIRE, WIMSE, ID-JAG cross-app access, OAuth 2.1 for MCP | `scale/mcp-at-scale-architecture-2026-09.md` 4.1 to 4.3 |
| The spec's own sandboxing SHOULDs for local servers | `bestpractice/mcp-server-deployment-and-migration.md` 6.4 |
| MCP secrets rules in the spec (`x-mcp-header`, elicitation, stdio from environment) | `bestpractice/mcp-server-deployment-and-migration.md` 6.7 |

One thing this brief does close rather than reference. `scale/` 7.2 recorded that
the OTel MCP span names, attribute names and metric names were **UNVERIFIED**
because the docs path could not be resolved. The path is
`docs/gen-ai/mcp.md` in `open-telemetry/semantic-conventions-genai`. Section 1.1
below reports it from the file.

---

## 1. Evaluation and observability

### 1.1 The OTel MCP semantic conventions, read from the source

**Source:** OFFICIAL.
<https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md>,
retrieved 2026-09-18, 1,332 lines.

Document status: **Development**. Every MCP-specific span, metric and attribute
in the file carries the Development badge. This confirms and extends the
stability finding already in `scale/` 7.2.

**Two spans.** `mcp.client` and `mcp.server`.

- Span name SHOULD follow `{mcp.method.name} {target}`, where target SHOULD match
  `{gen_ai.tool.name}` or `{gen_ai.prompt.name}` when applicable. With no
  low-cardinality target available, the span name SHOULD be `{mcp.method.name}`
  alone.
- Client span kind SHOULD be `CLIENT`.
- Instrumentations MAY let users opt into `{mcp.resource.uri}` as the target, but
  SHOULD NOT include it by default, to avoid high-cardinality span names.
- If MCP instrumentation can reliably detect that outer GenAI instrumentation is
  already tracing the tool execution, it SHOULD NOT create a separate span and
  SHOULD instead add MCP attributes to the existing `execute_tool` span.

**Four metrics.** All Histograms, unit `s`, all Development:

| Metric | What it measures |
|---|---|
| `mcp.client.operation.duration` | Request or notification duration observed on the sender, from send to response or ack |
| `mcp.server.operation.duration` | The server-side equivalent |
| `mcp.client.session.duration` | Session duration, client side |
| `mcp.server.session.duration` | Session duration, server side |

The operation-duration metrics specify `ExplicitBucketBoundaries` of
`[0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]`. The top
bucket at 300 seconds is a statement about what the authors expect tool calls to
cost.

**The conventions displace RPC and HTTP conventions, explicitly:**

> When instrumenting MCP calls, it's RECOMMENDED to follow MCP conventions
> instead of RPC semantic conventions since MCP spans and metrics provide
> domain-specific context and record details that are not covered by the RPC
> conventions such as message exchanges within streaming calls.

and

> HTTP conventions (when HTTP is used as transport) do not adequately cover MCP
> requests and notifications either, given that multiple MCP requests could be
> sent over a single HTTP request in the corresponding request and response
> streams.

**The attribute that decides what observability is worth.** Requirement levels
on the client span:

| Attribute | Stability | Requirement level |
|---|---|---|
| `mcp.method.name` | Development | Required |
| `error.type` | **Stable** | Conditionally required, if and only if the operation fails |
| `gen_ai.tool.name` | Development | Conditionally required, when the operation relates to a specific tool |
| `mcp.resource.uri` | Development | Conditionally required |
| `jsonrpc.request.id` | Development | Conditionally required |
| `rpc.response.status_code` | Release Candidate | Conditionally required, if the response contains an error code |
| `mcp.session.id` | Development | Recommended |
| `mcp.protocol.version` | Development | Recommended |
| `server.address`, `server.port`, `network.transport` | **Stable** | Recommended |
| **`gen_ai.tool.call.arguments`** | Development | **Opt-In** |
| **`gen_ai.tool.call.result`** | Development | **Opt-In** |

The last two rows are the load-bearing ones for section 5. A conformant
implementation at default settings records that a tool was called, by whom, on
what session, over what transport, how long it took and whether it failed. It
does not record what was passed in or what came back. Content capture is
opt-in, per attribute, and nothing in the conventions makes it a default.

**Error mapping worth knowing.** When `CallToolResult` returns with `isError`
set to `true`, `error.type` SHOULD be set to `tool_error`. A tool that fails
inside a successful JSON-RPC response is therefore distinguishable from a
transport failure, which is the distinction an on-call engineer needs and which
the RPC conventions alone would not give.

**Transport is deducible from attributes,** per the file's own table:

| MCP transport | `network.transport` | `network.protocol.*` | `mcp.protocol.version` |
|---|---|---|---|
| stdio | `pipe` | none | any |
| Streamable HTTP | `tcp` or `quic` | `http`, version `2` | `2025-06-18` or newer |
| HTTP with SSE | `tcp` or `quic` | `http`, version `1.1` or `2` | `2024-11-05` or older |
| Custom websockets | `tcp` | `websocket` | any |
| Custom gRPC | `tcp` | `http`, version `2` | any |

The comment column notes that `mcp.protocol.version` is what distinguishes
Streamable HTTP from SSE, because the two are otherwise identical at the network
layer.

**The version lag is visible in the file itself.** The context-propagation
section links the `_meta` property bag at spec revision `2025-11-25`, the
`mcp.session.id` attribute links transports at `2025-06-18`, and the
`mcp.protocol.version` example value is `2025-06-18`. The current MCP revision is
`2026-07-28`. This is the concrete form of the open alignment issue
(<https://github.com/open-telemetry/semantic-conventions-genai/issues/437>)
recorded in `scale/` 7.2. Anyone pinning a schema URL today is pinning to a
document that has not caught up to the protocol revision it describes.

Context propagation itself matches the spec: inject into `params._meta`, write
the W3C keys `traceparent`, `tracestate` and `baggage` **unprefixed** despite the
general DNS-prefix convention for `_meta`, per SEP-414. The server SHOULD use the
extracted context as the parent and SHOULD link the ambient context. The file
notes that MCP and transport contexts are independent, because one MCP request
can be served by multiple HTTP requests on retry and one streamable HTTP request
can carry more than one MCP message.

### 1.2 The platforms

Versions retrieved live from the GitHub releases API on 2026-09-18.

| Platform | License | Current version | Deployment | Source |
|---|---|---|---|---|
| **Langfuse** | MIT core, separate commercial licence for a smaller EE set | **v4.38.0**, published 2026-09-17T15:26:11Z | Self-host or cloud | OFFICIAL, <https://api.github.com/repos/langfuse/langfuse/releases/latest> |
| **Arize Phoenix** | Open source | **v20.14.0**, published 2026-09-18 | Self-host or cloud | OFFICIAL, <https://github.com/Arize-ai/phoenix/releases> |
| **Braintrust** | Commercial | n/a | Cloud, with on-prem or hosted for Enterprise only | VENDOR, <https://www.braintrust.dev/pricing> |
| **LangSmith** | Commercial | n/a | Cloud, Enterprise self-host | VENDOR, <https://www.langchain.com/pricing-langsmith> |
| **Datadog LLM Observability** | Commercial | n/a | SaaS | VENDOR |

**Correction to a widely repeated secondary claim.** Search results from May 2026
state that Langfuse v4 is cloud-preview only and that self-hosters use the 3.x
line. That is now stale. The self-hosting documentation carries "Version: v4" and
the v4 line is the one shipping releases. [OFFICIAL,
<https://langfuse.com/self-hosting>, read 2026-09-18.]

**Langfuse ownership changed in January 2026.** ClickHouse acquired Langfuse,
announced 2026-01-16, alongside a $400M Series D that valued ClickHouse at $15
billion. ClickHouse states Langfuse "remains committed to open source and
self-hosting". [VENDOR,
<https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability>;
corroborated SECONDHAND by
<https://siliconangle.com/2026/01/16/database-maker-clickhouse-raises-400m-acquires-ai-observability-startup-langfuse/>.]
The commitment is a vendor statement about future behaviour, not a licence term,
and should be read as such. The MIT licence on the core is the enforceable part.

Vendor-reported adoption figures from the same post, presented as the vendor's
claim rather than as fact: "more than 2,000 paying customers, 26M+ SDK installs
per month, trusted by 19 of the Fortune 50 and 63 of the Fortune 500."

**Arize Phoenix and OpenInference.** Phoenix consumes OpenInference traces, an
instrumentation convention Arize also authors, which is a different vocabulary
from the OTel GenAI conventions in 1.1. An enterprise standardising on OTel GenAI
and an enterprise standardising on OpenInference are not emitting the same
attribute names. That both ride OpenTelemetry transport does not make them
interchangeable at the query layer. [Instrumentation relationship: VENDOR,
<https://arize.com/phoenix/>, read 2026-09-18. The specific degree of attribute
overlap between OpenInference and the OTel GenAI registry was not measured in
this pass: **UNVERIFIED**.]

### 1.3 What it costs to store, at fleet scale

The published prices, quoted exactly.

**Braintrust** [VENDOR, <https://www.braintrust.dev/pricing>, read 2026-09-18]:

| Tier | Price | Included data | Overage | Scores | Retention |
|---|---|---|---|---|---|
| Starter | $0/month | 1 GB processed | +$4/GB | 10k, then $2.50/1k | 14 days |
| Pro | $249/month | 5 GB processed | +$3/GB | 50k, then $1.50/1k | 30 days, then $0.50/GB/mo |
| Enterprise | custom | custom | custom | custom | custom |

Seats are unlimited on all tiers. On-prem is Enterprise-only.

**LangSmith** [VENDOR, <https://www.langchain.com/pricing-langsmith>, read
2026-09-18]: Developer $0 for 1 seat with up to 5k base traces per month; Plus
$39 per seat per month with up to 10k base traces; Enterprise custom. Beyond the
included volume both say "then pay-as-you-go".

**The per-trace overage rate is not published anywhere official.** Three vendor
pages were checked: the pricing page, `/pricing`, and
`docs.langchain.com/langsmith/usage-and-billing`. The docs page carries a pricing
table whose price column reads "See pricing page", and the pricing page does not
itemise it. The commonly cited $2.50 per 1,000 base traces and $5.00 per 1,000
extended traces are **SECONDHAND** (multiple third-party pricing explainers) and
could not be confirmed against a LangChain-controlled page on 2026-09-18.

**The two LangChain pages also disagree with each other on retention.** The
documentation table states extended traces retain for **180 days**
[<https://docs.langchain.com/langsmith/usage-and-billing>]. The pricing page FAQ
states **400 days** [<https://www.langchain.com/pricing-langsmith>]. Both read on
2026-09-18. This is a vendor contradicting itself on a number that determines
whether the platform satisfies a retention policy. Resolve it in writing with the
vendor before it goes into a control document.

**Datadog LLM Observability.** Free tier up to 40k LLM spans per month; Pro from
$160 per month including 100k LLM spans; retention add-ons extending to 30, 60 or
90 days billed per 10,000 LLM spans. [SECONDHAND, multiple pricing explainers
read 2026-09-18.] The on-demand rate above 100k spans and the per-10k retention
add-on price are **not published** on the Datadog pricing page or in the LLM
Observability cost documentation, both of which were checked directly. A new
pricing model reportedly took effect 2026-05-01 [SECONDHAND]. Get the rate in
writing from an account team; do not model a fleet on a third-party figure.

**Self-hosting is not free, and the floor is concrete.** Langfuse's own minimum
production footprint, before a single trace lands [OFFICIAL,
<https://langfuse.com/self-hosting/configuration/scaling>, read 2026-09-18]:

| Component | CPU | Memory |
|---|---|---|
| Web container | 2 | 4 GiB |
| Worker container | 2 | 4 GiB |
| PostgreSQL | 2 | 4 GiB |
| Redis/Valkey | 1 | 1.5 GiB |
| ClickHouse | 2 | 8 GiB |
| Blob storage (MinIO) | 2 | 4 GiB |

Eleven CPUs and 25.5 GiB across six components, four of which are stateful. S3 or
compatible blob storage is exempted as serverless. The guidance recommends at
least 16 GiB for ClickHouse on larger deployments, and names queue-depth
saturation (`langfuse.queue.ingestion.depth`, worker CPU above 50% on a 2-CPU
container) as the scaling signal.

**The unit mismatch is the cost story, not the unit price.** From Langfuse's own
engineering write-up [VENDOR,
<https://langfuse.com/resources/engineering/clickhouse-at-agent-scale>, read
2026-09-18]:

> A single agent trace can contain hundreds or thousands of operations. Every LLM
> call, tool execution, retrieval, and intermediate step becomes its own
> observation.

Every platform in 1.2 bills per trace, per span, or per GB of processed data. An
agent trace is not a request. A per-span price multiplied by a request count
understates the bill by the average step count of an agent run, which is a
number most enterprises have not measured. That is the arithmetic to do before
signing, and the input to it is a measurement of your own traces, not a vendor
figure.

Three more numbers from the same post, all VENDOR and all about Langfuse Cloud
rather than a general finding:

- 2025 data processed grew **19x** while ClickHouse node sizes grew **15x**.
- As of March 2026, "roughly 60% of all observations in Langfuse Cloud arrive via
  the OpenTelemetry endpoint". OTel is the majority ingestion path for at least
  one large platform, which is an argument for instrumenting to the conventions
  in 1.1 rather than to an SDK.
- A single ClickHouse shard "scales to multiple terabytes of tracing data".

A per-million-traces storage figure of 1 to 2 GB, and a claim that 80 to 90% of
storage is trace inputs and outputs, circulate in third-party guides. Neither
appeared on the two Langfuse pages checked for them (the ClickHouse
infrastructure page and the reduce-disk-size FAQ). **UNVERIFIED.** The directional
point stands on the official guidance that retention policy is the primary lever,
but do not put the number in a capacity plan without measuring your own traces.

### 1.4 What signals actually drive action

Synthesis, not a cited claim. Of everything the conventions in 1.1 permit, four
signals change behaviour and the rest are context:

1. **`error.type = tool_error` rate per `gen_ai.tool.name`.** A tool failing
   inside successful JSON-RPC is invisible to transport monitoring and is the
   most common real failure. This is the one signal the conventions make cheap
   and that the RPC conventions would have lost.
2. **`mcp.client.operation.duration` p95 and p99 per tool.** The 300 second top
   bucket exists because agents wait. A tool at the top bucket is a tool that
   will time out under load.
3. **Tool-call count per trace,** derived rather than defined by the conventions.
   It is the token bill, the latency budget and the cost driver in one number.
   See `bestpractice/mcp-token-economics-and-tool-consolidation.md`.
4. **Authorization decisions, which the conventions do not carry at all.** The
   one structured event per tool-call authorization decision described in
   `scale/` 7.3 comes from the gateway, not from OTel MCP instrumentation. No
   attribute in `docs/gen-ai/mcp.md` records who was allowed to do what or which
   rule decided it.

Point 4 is a gap, stated plainly: **the OTel MCP semantic conventions define no
identity, principal, or authorization-decision attribute.** `mcp.session.id`
identifies a session, not a person or an agent. An enterprise joining "which
human caused this tool call" to a trace is doing so with `baggage` or a private
attribute, and neither is conventional.

### 1.5 Evals as a gate before an MCP server is approved

**There is no official MCP guidance on evaluation. This is a finding, and it is
falsifiable.** The `modelcontextprotocol.io` sitemap carries 347 pages on
2026-09-18. Filtering every URL for `eval`, `test`, `observab`, `telemetry`,
`sandbox` or `secret` returns exactly one page:
`https://modelcontextprotocol.io/seps/2484-conformance-tests-required-for-final-seps`,
which governs conformance tests for SEPs, not evaluation of servers.
[OFFICIAL, sitemap retrieved 2026-09-18.]

The method proves absence of a URL slug, not absence of a paragraph, so state it
at that strength: **no page in the official documentation set is named for
evaluating or gating a server.** Whether a paragraph on the subject is buried
inside a page named for something else was not checked, and a full-text sweep of
all 347 pages would be needed to close that. The claim as written is that an
enterprise looking for evaluation guidance in the obvious place does not find it.

The registry delegates security scanning outward (already quoted in
`bestpractice/mcp-server-deployment-and-migration.md` 6.8) and delegates
evaluation to nobody at all. An enterprise gate is therefore something the
enterprise builds. What exists to build it with:

| Tool | Licence | What it does | Source |
|---|---|---|---|
| **mcp-eval** (lastmile-ai) | Apache 2.0 | Acts as a real MCP client against a real server with a real model. Asserts on content (substring, regex), tool calls, sequences, success rates, response-time and iteration caps, LLM-judge rubrics, and path efficiency including backtracking detection. Ships GitHub Actions, GitLab CI, PR comments, JSON/HTML/Markdown output. | PRACTITIONER/OFFICIAL project, <https://github.com/lastmile-ai/mcp-eval>, read 2026-09-18 |
| **MCPBench** (modelscope) | Open source | Benchmark over MCP servers | PRACTITIONER, <https://github.com/modelscope/MCPBench> |
| **DeepEval** | Open source | MCP-specific metrics for single and multi-turn | VENDOR, <https://deepeval.com/docs/evaluation-mcp> |
| **MCP Inspector** | Official MCP project | Interactive testing of a server. A debugging tool, not a gate. | OFFICIAL |

mcp-eval is small (37 stars, 9 forks, 163 commits at the read). Do not present
it as an industry standard. It is the most complete open harness found, which is
a different claim.

**Braintrust's published gating guidance** [VENDOR,
<https://www.braintrust.dev/articles/ultimate-guide-mcp-testing-evals>, read
2026-09-18] is worth recording because it declines to give a universal number:

- Dataset size **40 to 60 carefully selected cases**, **3 to 5 trials per case**.
- "Set a separate release threshold for each failure class according to its
  impact."
- Zero tolerance for permission violations and destructive actions. Bounded
  advisory budgets for efficiency issues such as redundant read calls.
- "Permission violations and unsafe side effects can block a merge, with latency,
  token use, and redundant calls tracked under advisory efficiency budgets."
- Filtered experiment views so "a higher overall score cannot hide new failures in
  permission-boundary or side-effect cases."

That last point is the one that generalises. A single aggregate pass rate lets a
safety regression hide behind an accuracy improvement, and a gate built on one
number will eventually approve a server that got worse at the thing that matters.

A widely circulated set of specific thresholds (95% pass for tools with stable
descriptions, 99% for tools a PR did not touch, 200 to 500 traces from the last
week of production) comes from third-party guides rather than from a vendor or
project page. **SECONDHAND and UNVERIFIED.** The shape is reasonable; the numbers
are somebody's example.

**The harness configuration point, which is the practical one.** The eval harness
should connect over the same transport, the same authentication path and the same
exposed tool list as production. A harness that skips OAuth or trims the tool
list is measuring a different server than the one being approved. [SECONDHAND,
practitioner guides read 2026-09-18, but it follows directly from the tool-count
and context findings already in
`bestpractice/mcp-token-economics-and-tool-consolidation.md`.]

---

## 2. Secrets and credential brokering for non-human identities

The question is narrow: how does an agent get a credential without a human
pasting one, and where do the published patterns break when the consumer is an
agent rather than a service?

### 2.1 The standards that exist

| Standard | Status | Verified |
|---|---|---|
| **RFC 8693, OAuth 2.0 Token Exchange** | Internet Standards Track, **Proposed Standard**, January 2020 | OFFICIAL, <https://datatracker.ietf.org/doc/rfc8693/>, read 2026-09-18 |
| RFC 9728, RFC 8414, RFC 8707, RFC 9207 | Normative in the MCP spec | See `scale/` 4.3 |
| ID-JAG / Cross-App Access | IETF OAuth WG draft | See `scale/` 4.2 |
| SPIFFE/SPIRE | CNCF graduated | See `scale/` 4.2 |
| WIMSE (WIT, WPT, HTTP signatures) | IETF drafts | See `scale/` 4.2 |

RFC 8693 is the only piece of this that is a published RFC, and it has been one
for over six years. The delegation problem an agent poses is not a new problem at
the token layer. What is new is who holds the token and for how long.

### 2.2 Vault, the reference implementation, and what it does not say

HashiCorp Vault is the vendor that has moved furthest on agent identity, so it is
the best available read on the published pattern.

**Vault agentic IAM reached GA in Vault Enterprise 2.1**, announced 2026-09-01.
[VENDOR, <https://www.hashicorp.com/en/blog/hashicorp-vault-agentic-iam-is-now-generally-available>,
read 2026-09-18.] The mechanism, as the vendor describes it:

- **Rich Authorization Requests.** Agents present OAuth JWTs carrying
  `authorization_details` claims defining the access requested.
- **RFC 8693 token exchange** for delegated workflows, allowing "an agent to act
  on behalf of a user while preserving the user's identity and permissions", via
  "delegated OAuth JWTs that identify the user as the subject and the agent as
  the actor".
- **An agent registry** mapping agent identities to Vault Identity entities
  before OAuth credentials are used.
- **Per-request access evaluation** with request-scoped tokens that "exist only
  for the lifetime of the request and do not persist".
- A **"three-way intersection"** of user permissions, agent ceiling policies, and
  the constraints in `authorization_details`.

The three-way intersection is the genuinely useful idea and it is worth naming
as a pattern independent of the product: an agent's effective permission is the
intersection of what the user may do, what the agent is ever allowed to do, and
what this specific request asked for. Any two of those without the third
produces a known failure. User and request without an agent ceiling is confused
deputy. Agent and request without user scope is an agent acting beyond its
principal.

**MCP is not mentioned anywhere in that announcement.** The companion product
page for agentic runtime security also does not mention MCP, tool calls as a
protocol concept, or any named standard, and instead makes general claims:
"Authorization is verified at every API call and tool invocation, not assumed
from a prior session", and "Every action an agent takes is traceable to the
person who initiated it or owns the automation". [VENDOR,
<https://www.hashicorp.com/en/products/vault/use-cases/agentic-runtime-security>,
read 2026-09-18.]

**This is the gap, stated plainly.** The leading secrets vendor's agent identity
product and the MCP specification's authorization model have no published join.
Vault describes an agent registry and RFC 8693 exchange; MCP describes OAuth 2.1
resource servers, resource indicators, and (for stdio) credentials retrieved from
the environment. Neither document references the other. An enterprise wiring
Vault agentic IAM to an MCP gateway is building an integration that neither
vendor has published, and should expect no reference implementation.

Vault 2.0 reportedly represents IBM's versioning and support model following the
acquisition, and added Workload Identity Federation for secret syncing without
static credentials plus SCIM 2.0 provisioning. [SECONDHAND, InfoQ,
<https://www.infoq.com/news/2026/04/vault-2-0-ibm-identity/>, read 2026-09-18.
The IBM acquisition of HashiCorp closed 2025-02-27 per the same class of source;
treat the date as SECONDHAND.]

### 2.3 External Secrets Operator, and a correction

ESO is how a large share of Kubernetes deployments get a cloud secret store's
contents into a pod, which makes it load-bearing for any containerised MCP server
fleet.

| Fact | Value | Source |
|---|---|---|
| Current release | **v2.11.0**, published 2026-09-18T14:38:00Z | OFFICIAL, GitHub releases API, read 2026-09-18 |
| CNCF maturity | **Sandbox.** "external-secrets was accepted to CNCF on July 26, 2022 at the Sandbox maturity level." | OFFICIAL, <https://www.cncf.io/projects/external-secrets/>, read 2026-09-18 |

**Correction.** Secondary sources, including a 2026 CNCF blog-adjacent write-up
surfaced in search, describe ESO as "CNCF Incubating". The CNCF project page says
Sandbox. An incubation application exists (cncf/toc#1486) but the project page
has not been updated to reflect a level change, and no announcement of one was
found. Treat ESO as **Sandbox** until the CNCF project page says otherwise.

**The health review matters more than the level.** CNCF TOC issue #1819, opened
2025-08-13, is a health and governance review of ESO. The trigger, quoted from
the project's own community announcement in that issue:

> we've made the difficult decision to pause all official SemVer releases...
> until we can form a larger, sustainable maintainer team.

The pause covered new feature releases, **security patches**, image publishing
and official version releases. The issue includes an archiving checklist. It is
now **closed and marked Done**, and the release cadence has resumed, which
v2.11.0 on 2026-09-18 demonstrates. [OFFICIAL,
<https://github.com/cncf/toc/issues/1819>, read 2026-09-18.]

Recorded not to disparage the project, which recovered, but because the component
that delivers secrets into a fleet's pods stopped shipping security patches for a
period on maintainer capacity, and a deployment that took a dependency on it
would not have been told. Maintainer capacity is a supply-chain property of a
secrets component in the same way a CVE is. See
`bestpractice/mcp-server-vetting-and-supply-chain.md` for the same argument
applied to servers.

A CVE identifier, CVE-2026-22822, surfaced in search alongside ESO. It could not
be resolved on 2026-09-18: the NVD detail page returned only the NVD homepage to
retrieval, and a GitHub advisory query returned no result. **UNVERIFIED, neither
confirmed nor dismissed.** Do not cite it without resolving it first.

### 2.4 Where the published patterns break for agents specifically

Synthesis from the above and from the existing research. Four breakages, each
with the mechanism named.

**1. Secret delivery is per-workload; agent authorization is per-request.**
External Secrets Operator, cloud secret stores and Kubernetes Secrets all deliver
a credential to a running workload, on a refresh interval, as a file or an
environment variable. Vault's agentic model evaluates access per request and
issues tokens that "exist only for the lifetime of the request". An MCP server
holding a synced secret in its environment has a standing credential regardless
of which user's request it is currently serving. The delivery layer and the
authorization layer are operating on different time units, and the gap between
them is a standing privilege.

**2. The MCP spec sends stdio servers to the environment, by name.** The
authorization overview states stdio implementations "SHOULD NOT follow this
specification, and instead retrieve credentials from the environment" (quoted in
`bestpractice/mcp-server-deployment-and-migration.md` 6.7). That is a reasonable
engineering decision and it is also an explicit exemption of local servers from
every brokering mechanism in 2.1 and 2.2. A local stdio server gets an
environment variable. There is no token exchange, no audience restriction, no
per-request evaluation, and no expiry shorter than the process lifetime.

**3. Workload identity attests the workload, not the request's principal.**
SPIFFE and cloud workload identity federation answer "what is this workload",
which is the right question for a service and an incomplete one for an agent
serving many users. The consensus split recorded in `scale/` 4.2, SPIFFE for
"what is this workload" and OAuth for "what may it touch on whose behalf",
remains the correct framing, and it means workload identity alone never
satisfies the three-way intersection in 2.2. Two mechanisms are required, and
joining them is the enterprise's work.

**4. No published pattern covers a credential an agent needs and a human has
not anticipated.** Every mechanism above presumes the scope is known in advance:
`authorization_details` is constructed, a policy is written, a secret is synced.
An agent that discovers mid-task that it needs a credential has, in the published
patterns, exactly two options, fail or use a broader standing credential it
already holds. The MCP elicitation primitive can ask a human, and the spec
forbids using form-mode elicitation for credentials, requiring URL mode
(`bestpractice/mcp-server-deployment-and-migration.md` 6.7). **No published
guidance was found for just-in-time credential acquisition driven by an agent's
own discovery of need.** That absence is the honest state of the art on
2026-09-18.

---

## 3. Execution sandboxing as its own control

### 3.1 The engine classes and their current versions

Versions retrieved live from the GitHub releases API on 2026-09-18. [OFFICIAL.]

| Engine | Class | Current release | Published |
|---|---|---|---|
| **Firecracker** | microVM | v1.17.0 | 2026-09-10 |
| **gVisor** | userspace kernel | release-20260914.0 | 2026-09-16 |
| **Wasmtime** | Wasm runtime | v48.0.2 | 2026-09-10 |
| **Deno** | V8 isolate host | v2.9.7 | 2026-09-17 |

The MCP code-execution spec names Deno and `isolated-vm` for JavaScript, Monty
(experimental) for Python, pctx (early-stage) for TypeScript, and Wasmtime for
anything via Wasm, framed as "example runtimes rather than endorsements". Already
recorded in `bestpractice/mcp-token-economics-and-tool-consolidation.md` 4.4;
repeated here only because it is the list a reader of this section will want.

### 3.2 The one comparative study, and what it concludes

**Source:** arXiv preprint, so PEER-REVIEWED status is **not** established.
Andronchik, G. and Lokhmakov, P., "AI Code Sandboxes: A Comparative Security
Study. Part 1 of 2: Engine-Level Properties (Attack Surface, Leakage,
Stackability, CVE History, Patch Cadence, Fuzzing)", submitted 2026-06-07,
<https://arxiv.org/abs/2606.08433>, CC BY 4.0, companion code Apache 2.0. Read
2026-09-18. Five AI-sandbox products across six measurement axes.

Three findings, quoted from the abstract:

1. "engine classes (microVM, userspace kernel, OCI container) separate cleanly on
   every architectural axis, but products within a class do not".
2. "product pin policy is the dominant operator-facing variable: engine-side
   patch latency aggregates to ~0 days for coordinated disclosures, while
   downstream lag spans 0 days to 471+ days to 'opaque' to infinity".
3. Fuzzing investment splits into three tiers, and "the strongest combination,
   microVM x continuous public fuzzer, is unoccupied in this set".

The authors explicitly decline to rank: "no overall ranking is proposed", and
"No single axis is a sufficient basis for a comparative judgement".

Finding 2 is the one that changes a procurement conversation. The engine
maintainers patch on disclosure; the products that embed the engine may not, and
some will not tell you. The question to ask a sandbox vendor is not which engine
they use, it is what version of it they pin and how fast they move it. A
471-day lag on an engine whose upstream patched in zero days is a product
decision, not an engine property.

### 3.3 What a sandbox catches, stated by the sandbox

gVisor publishes its own threat model, which is the most useful single source
here because it is a vendor saying what its product does not do. [OFFICIAL,
<https://gvisor.dev/docs/architecture_guide/security/>, read 2026-09-18.]

**What it targets:** System API exploitation, meaning bugs in kernel system calls
that untrusted code could use for privilege escalation. The Sentry handles
syscalls in userspace so that only a vetted subset reaches the host kernel.

**What it explicitly does not protect against, quoted:**

> gVisor does not provide protection against hardware side channels, although it
> may make exploits that rely on direct access to the host System API more
> difficult to use.

> While direct interactions are not possible, indirect interactions are still
> possible. For example, a read on a host-backed file in the Sentry may
> ultimately result in a host read system call.

> A sandbox is not a substitute for a secure architecture.

The middle quote is the one to keep. A userspace kernel narrows the syscall
surface; it does not eliminate host syscalls, because the sandbox's own I/O still
becomes host I/O. The Sentry is itself code that can be compromised.

The class distinctions, drawn from practitioner comparisons and consistent with
the arXiv paper's architectural separation [SECONDHAND, Fly.io and Northflank
comparisons, read 2026-09-18; treat the performance figures as vendor-adjacent]:

| Class | Isolation boundary | Cost of escape |
|---|---|---|
| OCI container | Shared host kernel, namespaces and cgroups, seccomp filter | One kernel bug |
| Userspace kernel (gVisor) | Sentry intercepts syscalls, vetted subset reaches host | Sentry bug plus a host bug, or an unvetted indirect path |
| microVM (Firecracker) | Dedicated guest kernel under KVM, minimal device emulation | Guest kernel escape plus hypervisor escape |
| Wasm | Capability-based, no ambient authority, no syscalls by default | Runtime bug, or a capability that was granted |

Commonly cited Firecracker figures (roughly 125 ms boot, under 5 MiB overhead per
VM, up to 150 VMs per second per host, 5 to 30 ms snapshot restore) are
**SECONDHAND** across several 2026 comparison posts and were not confirmed
against Firecracker's own documentation in this pass.

### 3.4 Network egress control, which is the part that matters for MCP

A sandbox that isolates the filesystem and the kernel but permits arbitrary
outbound network traffic does not stop exfiltration. Cloudflare's Sandbox product
publishes the most specific egress model found, and the specifics include a limit
worth knowing. [OFFICIAL vendor documentation,
<https://developers.cloudflare.com/sandbox/guides/outbound-traffic/>, read
2026-09-18.]

The controls, in evaluation order: `deniedHosts`, then `allowedHosts`, then
instance-level rules, then per-host handlers, then catch-all handlers, then the
default egress policy. `enableInternet = false` disables public internet access
entirely. `allowedHosts` is deny-by-default.

The credential property is the same one the MCP code-execution spec describes,
implemented:

> No token is exposed to the sandbox. The secret lives in the Worker's
> environment and is never passed into the sandbox.

Outbound handlers run in the Workers runtime, outside the sandbox. The sandbox
issues an unauthenticated request; the handler attaches credentials and forwards
it. This is credential brokering at the sandbox boundary, and it is the concrete
join between section 2 and section 3.

**The limit, quoted:**

> Traffic on ports other than 80 and 443 is never routed through `outbound` or
> `outboundByHost`.

Interception and header injection cover HTTP and HTTPS only. DNS routes to
Cloudflare's servers as the sole exception. Anything on another port is outside
the interception model, and a policy written as "all egress is inspected" would
be wrong. Isolation is container-tier on Cloudflare Containers, meaning a shared
kernel, so this is an egress control layered on the weakest isolation class in
3.3. [Isolation tier: SECONDHAND,
<https://mcp.directory/blog/cloudflare-sandbox-vs-modal-vs-e2b-vs-daytona-2026>,
read 2026-09-18. Cloudflare's own docs say "its own isolated container with a
full Linux environment" without naming the kernel-sharing property.]

Other hosted sandboxes, characterised SECONDHAND from 2026 practitioner
comparisons read 2026-09-18 and not verified against vendor docs in this pass:
E2B on Firecracker microVMs with dedicated kernels; Daytona on Docker containers
with a shared host kernel, and reported to have moved its production codebase to
closed source in June 2026 citing security concerns. Cloudflare Sandbox billing
is reported at $0.000020 per vCPU-second and $0.0000025 per GiB-second,
scale-to-zero. Verify all of these against vendor documentation before use.

### 3.5 What running generated code in a sandbox changes about the threat model

The effect sizes, the spec's security section, and the gateway blind spot are
already covered in
`bestpractice/mcp-token-economics-and-tool-consolidation.md` 4.4 and 5.3 and in
`bestpractice/mcp-gateway-and-registry-operations.md`. Three additions specific
to sandboxing as a control.

**1. The sandbox becomes the enforcement point for data minimisation, and that is
a property of the sandbox, not of the model.** Intermediate results staying in
the execution environment is what makes the injection surface smaller. That
property holds only while the sandbox actually contains them, which means the
egress controls in 3.4 are not a hardening extra, they are the mechanism the
security claim rests on. A code-execution deployment with an unrestricted
sandbox network has the token savings and none of the security benefit.

**2. The threat actor changes from the model to the code.** Direct tool calling
is attacked by getting the model to call the wrong tool. Code execution is
attacked by getting generated code to do something the approving human did not
read. That is a code-execution vulnerability class, and the spec says so:
"Programmatic tool calling introduces a code execution surface that requires
careful sandboxing." The relevant CVE history is now the sandbox engine's, per
3.2, which is a body of risk an MCP deployment did not previously carry. The
worked example already in this repo is CVE-2026-53710 against MCP Context Forge,
CVSS 10.0, a sandbox escape via raw `getattr` in `safe_builtins` and dunder name
construction (`security/mcp-security-failures-2026-09.md`). A hand-rolled Python
sandbox inside a gateway is the failure mode, and it is not hypothetical.

**3. Approval granularity inverts, and the sandbox cannot restore it.** A human
approving a script approves calls they will not individually see. The spec
compensates by requiring the broker to evaluate each call at runtime. The sandbox
does not help with this and cannot: it constrains what the code may reach, not
whether each reach was authorized. That check lives in the host's broker. Section
5 treats this as the defining blind spot of the sandbox layer.

---

## 4. Absences, recorded as findings

Each of these was looked for and not found on 2026-09-18.

1. **No page in the official MCP documentation is named for evaluating or gating
   a server.** 347 pages in the `modelcontextprotocol.io` sitemap, none with an
   evaluation slug. Scoped as in section 1.5.
2. **No identity or authorization-decision attribute in the OTel MCP semantic
   conventions.** Section 1.4.
3. **No published join between MCP authorization and any secrets vendor's agent
   identity product.** Vault's GA announcement does not mention MCP; MCP does not
   mention credential brokering beyond "use the environment" for stdio. Section
   2.2.
4. **No published pattern for just-in-time credential acquisition driven by an
   agent discovering a need mid-task.** Section 2.4.
5. **No published per-trace overage price for LangSmith, and no published
   per-span on-demand rate for Datadog LLM Observability.** Both checked on
   vendor-controlled pages. Section 1.3. Fleet-scale observability cost cannot be
   modelled from public pricing for either.
6. **No sandbox product in the studied set occupies microVM plus continuous
   public fuzzing.** The strongest available combination is unoccupied, and that
   intersection is "structurally unmeasured". Section 3.2.
7. **No official MCP guidance on secrets management or on sandboxing as a
   deployment topic**, beyond the local-server SHOULDs already recorded in
   `bestpractice/mcp-server-deployment-and-migration.md` 6.4 and the
   credential rules in 6.7.

---

## 5. Composition: what each layer sees that the others cannot

This is the point of the brief. Four layers are in play, because the gateway is
one of them even though it is covered elsewhere.

### 5.1 The matrix

| Question | Gateway | Observability | Secrets broker | Sandbox |
|---|---|---|---|---|
| Was this call authorized, and by which rule | **Yes**, it decided | No. No attribute for it exists | Partially, for the credential only | No |
| Which tool was called, when, how long it took | Yes | **Yes**, and it is the only layer that keeps the history | No | No |
| What arguments were passed | Yes, in flight | Only if `gen_ai.tool.call.arguments` is opted in | No | **Yes**, it executes them |
| What the tool returned | Yes, in flight | Only if `gen_ai.tool.call.result` is opted in | No | **Yes** |
| How results composed into the next call | **No** | No | No | **Yes**, exclusively |
| Which human is ultimately responsible | Yes, at the edge | Only via non-conventional `baggage` | **Yes**, it is the subject of the exchange | No |
| Whether the credential should exist at all | No | No | **Yes**, exclusively | No |
| What the code tried to reach and was refused | No | No | No | **Yes**, exclusively |
| Whether behaviour changed between versions | No | Partially, by comparing over time | No | No. The eval harness answers this |
| Whether a syscall or egress attempt was hostile | No | No | No | **Yes**, exclusively |

### 5.2 What each layer sees that no other layer can

**The observability layer is the only one with history.** A gateway makes a
decision and forgets it. A secrets broker issues a credential and expires it. A
sandbox tears down. Only the trace store can answer "has this tool always been
slow", "when did this failure rate change", and "what did the last thousand runs
of this agent actually do". Every regression question is a comparison across
time, and one layer holds time.

It also sees across servers in a way nothing else does. A gateway sees calls
transiting it; a trace sees the whole agent run including model calls, retrievals
and the reasoning steps between tool calls, and the join between them. The trace
is the only artifact where "the agent called `search`, then called `send_email`
with something from the search result" is a single object. That the arguments and
results are opt-in (1.1) is therefore the most consequential default in this
entire brief: at default settings the layer that could answer the exfiltration
question records the shape of the path and not its contents.

**The secrets broker is the only layer that can say no in advance.** Every other
layer evaluates a call that has already been constructed. The broker is the only
one that decides whether the capability exists at all, before any request is
formed. It holds the three-way intersection from 2.2, and in particular it is the
only layer that knows the human principal as a first-class subject rather than as
a header to be forwarded. A gateway can check a token; only the broker minted it
knowing whose it was and what it was for.

It is also the only layer with a view across protocols. An agent reaching a
database directly, calling a REST API, and calling an MCP server all draw on the
same broker. The gateway sees only the MCP path. If the question is "what can
this agent reach", the MCP gateway answers it for MCP and the broker answers it
for everything.

**The sandbox is the only layer inside the execution.** This is the
irreducible one. From `bestpractice/mcp-gateway-and-registry-operations.md`:

> A gateway still sees every `tools/call` the sandbox makes, because they are
> ordinary calls. What it cannot see is the composition: which result fed which
> argument, and what the script did in between. The join between calls happens in
> a sandbox the gateway has no view into.

Extending that: the sandbox is also the only layer that sees the **attempts that
never became calls**. A generated script that tries to open `/etc/shadow`, resolve
an unexpected hostname, or spawn a process produces no tool call, no gateway
event, no trace span and no credential request. It produces a refused syscall or a
blocked egress attempt inside the sandbox, and if the sandbox does not log it, no
layer in the stack ever knew it happened.

That is the single strongest argument for treating sandboxing as its own control
rather than a deployment detail. The other three layers are all positioned on the
path of successful, well-formed requests. Only the sandbox observes the
malformed, the refused, and the exploratory. An attacker probing what is reachable
is, to every other layer, silent.

**The gateway is the only layer that enforces policy across servers uniformly.**
Covered in depth elsewhere, restated here for completeness: it is the choke point
where a rule written once applies to every server, and the only place an org-wide
revocation takes effect on the next call regardless of what any client cached.

### 5.3 The four blind spots, and which layer covers each

| Blind spot | Blind to | Covered by |
|---|---|---|
| Composition inside generated code | Gateway, observability, broker | Sandbox, and only if it logs |
| Refused syscalls and blocked egress | Gateway, observability, broker | Sandbox, and only if it logs |
| Authorization decisions in the trace record | Observability (no attribute exists) | Gateway, emitting its own structured event |
| Argument and result content in the trace record | Observability at default settings | Observability, but only after opting in per attribute |
| Behaviour change between server versions | All four | The eval harness, which is not a runtime layer |

The last row is why section 1.5's absence matters more than it first appears.
None of the four runtime layers answers "is this version of this server worse than
the last one". The gateway enforces the policy it was given. The trace shows what
happened, not what should have. The broker does not model behaviour. The sandbox
contains, it does not compare. A regression in a tool description, which is the
attack in the poisoning literature already covered in `security/`, passes every
runtime control cleanly because nothing at runtime holds a baseline. The gate has
to run before deployment, and the MCP project publishes nothing about how.

### 5.4 Two places the layers overlap, and the overlap is not redundant

**Credential brokering happens twice, at different boundaries.** The secrets
broker decides whether an agent may hold a capability. The sandbox's outbound
handler, per 3.4, injects the credential at the network boundary so that the
executing code never holds it. These are the same word describing different
controls. An enterprise that implements only the first has an agent process
holding a live token in memory alongside generated code. An enterprise that
implements only the second has a credential nobody authorized. Both are required,
and the MCP code-execution spec's "API keys and tokens are held by the host"
describes the second, not the first.

**Egress is controlled twice, and the gateway's version is weaker than it looks.**
A gateway controls which MCP servers an agent may reach. A sandbox controls which
network destinations executing code may reach. The gateway's control is
irrelevant to code running inside a sandbox that has unrestricted network access,
because that code does not need an MCP server to exfiltrate. Per 3.4, even a
well-configured sandbox egress policy may cover only ports 80 and 443. The
composition failure to watch for is an organisation that believes its gateway
controls where data can go.

### 5.5 Deployment implication, stated once

Brief D assembles the reference architecture and owns the ordering question. The
one input this brief contributes to it: the three layers here are not
substitutable for each other, and the matrix in 5.1 has no column that dominates
another. An enterprise choosing to deploy two of the three is choosing which
class of event it will never see, and the honest version of that decision names
the class. Skipping the sandbox means never seeing a refused probe. Skipping
observability means never seeing a trend. Skipping the broker means every
credential decision was made at provisioning time by someone who is no longer in
the loop.

---

## 6. Source list

| # | Source | Label | Read |
|---|---|---|---|
| 1 | <https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md> | OFFICIAL | 2026-09-18 |
| 2 | <https://github.com/open-telemetry/semantic-conventions-genai/issues/437> | OFFICIAL | via `scale/` 7.2 |
| 3 | <https://api.github.com/repos/langfuse/langfuse/releases/latest> | OFFICIAL | 2026-09-18 |
| 4 | <https://langfuse.com/self-hosting> | OFFICIAL | 2026-09-18 |
| 5 | <https://langfuse.com/self-hosting/configuration/scaling> | OFFICIAL | 2026-09-18 |
| 6 | <https://langfuse.com/resources/engineering/clickhouse-at-agent-scale> | VENDOR | 2026-09-18 |
| 7 | <https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability> | VENDOR | 2026-09-18 |
| 8 | <https://siliconangle.com/2026/01/16/database-maker-clickhouse-raises-400m-acquires-ai-observability-startup-langfuse/> | SECONDHAND | 2026-09-18 |
| 9 | <https://github.com/Arize-ai/phoenix/releases> | OFFICIAL | 2026-09-18 |
| 10 | <https://arize.com/phoenix/> | VENDOR | 2026-09-18 |
| 11 | <https://www.braintrust.dev/pricing> | VENDOR | 2026-09-18 |
| 12 | <https://www.braintrust.dev/articles/ultimate-guide-mcp-testing-evals> | VENDOR | 2026-09-18 |
| 13 | <https://www.langchain.com/pricing-langsmith> | VENDOR | 2026-09-18 |
| 14 | <https://docs.langchain.com/langsmith/usage-and-billing> | VENDOR | 2026-09-18 |
| 15 | <https://docs.datadoghq.com/llm_observability/monitoring/cost/> | VENDOR, did not answer the question asked | 2026-09-18 |
| 16 | <https://github.com/lastmile-ai/mcp-eval> | PRACTITIONER | 2026-09-18 |
| 17 | <https://github.com/modelscope/MCPBench> | PRACTITIONER | 2026-09-18 |
| 18 | <https://modelcontextprotocol.io/sitemap.xml> | OFFICIAL | 2026-09-18 |
| 19 | <https://datatracker.ietf.org/doc/rfc8693/> | OFFICIAL | 2026-09-18 |
| 20 | <https://www.hashicorp.com/en/blog/hashicorp-vault-agentic-iam-is-now-generally-available> | VENDOR | 2026-09-18 |
| 21 | <https://www.hashicorp.com/en/products/vault/use-cases/agentic-runtime-security> | VENDOR | 2026-09-18 |
| 22 | <https://www.infoq.com/news/2026/04/vault-2-0-ibm-identity/> | SECONDHAND | 2026-09-18 |
| 23 | <https://www.cncf.io/projects/external-secrets/> | OFFICIAL | 2026-09-18 |
| 24 | <https://github.com/cncf/toc/issues/1819> | OFFICIAL | 2026-09-18 |
| 25 | <https://api.github.com/repos/external-secrets/external-secrets/releases/latest> | OFFICIAL | 2026-09-18 |
| 26 | <https://arxiv.org/abs/2606.08433> | PREPRINT, not peer-reviewed | 2026-09-18 |
| 27 | <https://gvisor.dev/docs/architecture_guide/security/> | OFFICIAL | 2026-09-18 |
| 28 | <https://developers.cloudflare.com/sandbox/guides/outbound-traffic/> | OFFICIAL vendor docs | 2026-09-18 |
| 29 | <https://developers.cloudflare.com/sandbox/> | OFFICIAL vendor docs | 2026-09-18 |
| 30 | GitHub releases API for firecracker, gvisor, wasmtime, deno | OFFICIAL | 2026-09-18 |
| 31 | <https://fly.io/learn/firecracker-vs-gvisor/> | VENDOR | 2026-09-18 |
| 32 | <https://northflank.com/blog/how-to-sandbox-ai-agents> | VENDOR | 2026-09-18 |
| 33 | <https://mcp.directory/blog/cloudflare-sandbox-vs-modal-vs-e2b-vs-daytona-2026> | SECONDHAND | 2026-09-18 |

### Claims carried as UNVERIFIED

1. LangSmith per-trace overage of $2.50 per 1,000 base traces and $5.00 per 1,000
   extended. SECONDHAND only; absent from three LangChain-controlled pages.
2. LangSmith extended-trace retention. The vendor's own docs say 180 days and the
   vendor's own pricing FAQ says 400 days. Unresolved contradiction.
3. Datadog LLM Observability free tier at 40k spans, Pro at $160/month for 100k
   spans, and a pricing change effective 2026-05-01. SECONDHAND.
4. Langfuse ClickHouse growth of 1 to 2 GB per million traces, and 80 to 90% of
   storage being trace inputs and outputs. SECONDHAND; not on the two Langfuse
   pages checked.
5. CVE-2026-22822, surfaced in search alongside External Secrets Operator.
   Neither confirmed nor dismissed. NVD retrieval failed; no GitHub advisory
   match.
6. Firecracker performance figures (125 ms boot, under 5 MiB per VM, 150 VMs per
   second, 5 to 30 ms snapshot restore). SECONDHAND across comparison posts.
7. E2B on Firecracker, Daytona on Docker containers and its June 2026 move to
   closed source, Cloudflare Sandbox per-second billing rates. SECONDHAND.
8. Degree of attribute overlap between OpenInference and the OTel GenAI registry.
   Not measured.
9. IBM's acquisition of HashiCorp closing on 2025-02-27. SECONDHAND.
10. Third-party eval thresholds (95% and 99% pass rates, 200 to 500 production
    traces). SECONDHAND; not traceable to a vendor or project page.
