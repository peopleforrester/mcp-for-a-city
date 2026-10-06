---
title: "Everyone Vets MCP Servers Alone"
subtitle: "Operating MCP at scale, part two: security"
date: 2026-09-21
status: final
prefix: "Research"
series: "Operating MCP at Scale"
part: 2
sources_verified_on: 2026-10-06
---

# Everyone Vets MCP Servers Alone

*Operating MCP at scale, part two: security.*

With one particular MCP server installed, an attacker who can write to your
application logs could take your cluster credentials. No model was jailbroken,
no vault was breached, and every call in the chain was authorized.

A tool called `kubectl_generic` passes user-supplied flags to kubectl without an
allowlist. An attacker who can write a line into an application's own log output
plants one there. An operator, doing something completely ordinary, asks an
agent to look at the logs. The agent reads the planted instruction and calls
`kubectl_generic` with `--server=https://attacker.example.com` and
`--insecure-skip-tls-verify=true`. kubectl does what it is told and sends the
bearer token from the operator's kubeconfig to the attacker as an
`Authorization` header. The attacker replays it with the operator's permissions.

That is CVE-2026-47250, against `mcp-server-kubernetes`. Affected at 3.6.2 and
below, fixed in 3.7.0, CWE-88, CVSS 3.1 score 6.1 as assigned by GitHub as CNA,
advisory GHSA-6mx4-4h42-r8vh. NVD lists that score as secondary and has not
scored it independently. The exfiltration works by redirecting kubectl's API
server address, not by reading a token file off disk, so a control that watches
access to the kubeconfig file sees nothing unusual.

The project assigned a CVE and shipped a fix. It had also documented a safer
configuration before the flaw was reported: the README at 3.6.2 describes
`ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS=true` and lists `kubectl_generic` under
"Commands Disabled in Non-Destructive Mode". A deployment in that mode did not
expose the tool, so whoever read the README chose the blast radius.

The advisory entered the GitHub Advisory Database on 2026-06-05, scoped to npm
`mcp-server-kubernetes` at `<= 3.6.2`. Whether it reached an operator is another
matter. The README's install paths launch the server with `npx` from a client
configuration, outside any project lockfile, so `npm audit` in a repository does
not see it. And an advisory arrives only after a report, says nothing about
whether the server belonged in your deployment, and leaves the official registry
listing unchanged, under a policy the registry publishes.

## Every layer draws a line, and the reviews happen out of sight

Read the Model Context Protocol's own security policy. On server selection it is
unambiguous:

> "Users and administrators are responsible for server selection."

And it scopes out, explicitly, the class of thing the CVE above sits next to:

> "Reports about 'server X can perform action Y' are not vulnerabilities when Y
> is the server's intended purpose."

> "Reports about 'LLM invoked unexpected tool' are not MCP vulnerabilities, as
> they relate to LLM behavior and application-level controls."

That is a defensible boundary for vulnerability reports, and it is not the
project's whole position. The MCP Security Interest Group, chartered in June
2026, lists in scope "Server identity, attestation, and admission" and "Runtime
drift and post-admission change", the second covering whether tool changes after
approval "are versioning, re-approval, or security events." The protocol's
Security Best Practices also put requirements on clients for local servers: a
client that offers one-click local configuration "**MUST** implement proper
consent mechanisms prior to executing commands" and must "Show the exact command
that will be executed, without truncation". So the steward has taken up
admission as a question. It has not yet published an answer.

Now read the official registry's moderation policy:

> "The MCP Registry **does not** make guarantees about moderation, and consumers
> should assume minimal-to-no moderation."

Under the heading **What We Don't Remove**, second item on the list: **servers
with security vulnerabilities.** The policy is direct about where it expects
scrutiny to happen instead:

> "We largely rely on upstream package registries (like NPM, PyPI, and Docker)
> or downstream subregistries (like the GitHub MCP Registry) to do more in-depth
> moderation."

A permissive registry is a legitimate design choice for an ecosystem that wants
to grow, and this policy says so in public. Removal, when it happens, normally
sets a server's `status` to `"deleted"` while its metadata stays live in the API,
and aggregators decide for themselves whether to drop it. "In extreme cases" the
registry may overwrite or erase the metadata.

The policy points two ways, and both directions are worth following.

**Downstream, the catalogs vet.** Docker's MCP catalog says "Every pull request
requires a review from the Docker team before merging". Anthropic's
connector directory publishes its review criteria, and they reject the exact
shape behind the CVE above: a single tool that accepts both safe and unsafe
methods "is rejected. Don't ship a catch-all `api_request` tool with a `method`
parameter." Descriptions are rejected if they "Contain hidden, obfuscated, or
encoded instructions" or "attempt to override system instructions". Anthropic's
Claude Code documentation is precise about the limit: Anthropic "reviews
connectors against its listing criteria ... but doesn't security-audit or manage
any MCP server."

**The registry is built for private catalogs.** The Registry Working Group's
charter puts out of scope "Any commitment to delivering an enterprise-ready or
reusable registry implementation. The codebase supports this instance only and is
not intended for external deployments." That is about supporting the reference
code. The API is designed to be reimplemented: the registry defines a subregistry
as "an aggregator that also implements the OpenAPI spec defined by the MCP
Registry", and its worked example shows a subregistry adding `security_scan`
results under `_meta`. GitHub's Copilot administration docs describe a registry
as "a set of HTTPS endpoints" following "the v0.1 MCP registry specification",
honored in seven surfaces from VS Code to Xcode, while warning that this
registry setting "is in public preview and is not the recommended method for
restricting access to MCP servers." GitHub points instead to a managed-settings
allowlist, which comes up again below.

**Upstream, a package registry answers provenance.** Where did this artifact come
from, and is the signature valid. It does not answer **payload**: is the code
malicious, and is that tool description an injection. npm's own documentation
says that established provenance "does not guarantee the package has no
malicious code."

The worked example is `postmark-mcp`, a package impersonating Postmark's MCP
server, whose version 1.0.16 added a single line that blind-copied every outbound
email to an attacker-controlled address. Whether any version carried a provenance
statement can no longer be checked: npm unpublished the package on 2025-09-25,
and the record keeps timestamps and no versions. npm only issues provenance for
packages built on a supported cloud CI provider, and a package published from a
laptop gets registry signatures without it. What can be said is that it would
have passed `npm audit signatures`, like every package the registry served. The
record's publish timestamps, re-read on 2026-10-06, show **13 versions before
the backdoor**, the first at 10:44 UTC on 2025-09-15 and the last at 12:41 UTC
the following day. That is about **26 hours** of history, with `1.0.16` landing
at 08:59 UTC on the 17th.

So vetting happens. Docker does it for its catalog, Anthropic for its directory,
Maryland for the state's enterprise systems, and every security team that admits a server
does it for its own organization. Each does it privately, against its own
criteria, and the result stays where it was produced. Nothing about a completed
review travels with the server to the next organization that installs it.

## What you would be inheriting

The population you are being asked to admit has a shape worth knowing.

The official registry, paginated in full on 2026-09-19, answers **33,366**
distinct servers or **108,042** version records to the same question, depending
on whether you ask for servers or every version. Neither number is wrong. Neither
is a statement about fitness for anything. Both grow daily: re-run on
2026-10-05, the same queries returned 39,617 servers and 133,852 version records.

Two things about that set matter more than its size. **Fifteen percent of it
came from three GitHub accounts** (13 percent of the larger set on 2026-10-05).
Sampling eight entries from each on 2026-10-06: one account publishes
single-purpose utilities from a single repository under separate names, and the
other two publish API wrappers with a repository each. The moderation policy removes "Spam,
especially mass-created servers that disrupt the registry"; I have not judged
whether these meet that definition, so read the share as what the registry
currently answers. And **the median server has exactly one published version**,
still true on 2026-10-05, meaning the median server has been published to the
registry once and never updated there. A remote server can still change behind a
stable URL, which is its own problem.

Then the measured security posture of live servers, from three studies that
looked at real deployments rather than surveying practitioners: two arXiv
preprints and one scan published by a security vendor:

| Study | Population | Finding |
|---|---|---|
| Zhou et al. | 7,973 live remote servers | **40.55% expose tools with no authentication.** Every OAuth-using server tested (119) had at least one flaw |
| Padilla, arXiv:2608.00150 | 414 fully audited servers, from a 640-server confirmed pool | **91.8% of the 414 lacked OAuth.** 687 tool instances exposed shell execution with no access control, counted across the 640. Separately, 193 of 464 servers, 41.6%, vanished between runs about three days apart |
| Knostic (vendor scan, July 2025) | 1,862 exposed servers found, 119 verified | **119 of 119** granted internal tool listings without authentication |

These measure different things. "No authentication at all" and "no OAuth
specifically" are not the same claim, and the three should not be stacked into a
trend line. Individually, each is enough.

## The model is not the control, and this is measured

MCPTox (arXiv:2508.14925) built 1,348 tool-poisoning test cases (1,312 in its
first version; the count was revised in September 2026) against **45 live,
real-world MCP servers and 353 authentic tools**, and ran them against 20
agents, using the reference MCP pipeline's system prompt "without modification".
From the abstract:

> "agents rarely refuse these attacks, with the highest refused rate
> (Claude-3.7-Sonnet) less than 3%"

The most vulnerable model tested, o1-mini, showed a 72.8% attack success rate,
and the authors report that "more capable models are often more susceptible, as
the attack exploits their superior instruction-following abilities".

MCPTox tests the models' own alignment with no defensive prompt added, so it does
not measure the common production mitigation of a system prompt telling the
agent not to follow instructions in tool metadata. My inference from it: models
trained to refuse misuse refused under 3% of these cases, so a prompt asking for
the same behavior starts from that floor. The models tested are from 2025, and
the September revision did not change the set.

The specification already tells clients not to trust the metadata:

> "For trust & safety and security, clients **MUST** consider tool annotations
> to be untrusted unless they come from trusted servers."

Which returns the question to what "trusted" means, and who decided. In MCP
terms, it is the admission decision this article is about, and it has to be made
outside the model.

## What a gateway can and cannot do

A gateway is the right architecture and it is not a solution. Being precise about
the boundary is what separates a working control plane from a false sense of one.

Without parsing a request body, a gateway on Streamable HTTP sees the
`Authorization` header, which carries the caller's identity and scopes and is
what most gateway policy keys on. It also sees the protocol version, the
`Mcp-Method` header, the `Mcp-Name` header, and whichever tool arguments a server
author chose to expose through `x-mcp-header`. The 2026-07-28 revision says of
`Mcp-Method` and `Mcp-Name` that "these headers are **REQUIRED** for compliance",
requires `MCP-Protocol-Version` on every POST in a separate rule, and mandates
rejecting a mismatch between header and body with error `-32020`. The
specification states its own reasoning, which is a gateway threat model in the
spec's words:

> "This prevents potential security vulnerabilities when different components in
> the network rely on different sources of truth (e.g., a load balancer routing
> on the header value while the MCP server executes based on the body value)."

On the argument-mirroring mechanism, the specification tells server authors to
keep the interesting things out:

> "Server developers **SHOULD NOT** mark sensitive parameters (passwords, API
> keys, tokens, PII) with `x-mcp-header`, as header values are visible to network
> intermediaries."

So argument-level policy from headers works for routing-shaped arguments like a
region or a tenant, and not for the arguments a reviewer most wants to police.
Anything further requires a full body parse, whose cost depends on the detector:
in AIMultiple's benchmark, ContextForge's pattern matching added about 11
percent, while TrueFoundry's prompt-injection and credential guardrails moved its
added latency from 55 to 172 milliseconds.

Three limits, stated precisely:

**Most gateways evaluate one call at a time.** Writing on Microsoft's developer
blog about the Agent Governance Toolkit, Jack Batzner states it plainly: "AGT
governs individual tool calls deterministically. It does not yet correlate
sequences of individually-allowed calls that may form a malicious workflow". The
same sentence goes on to say that correlation is on the roadmap. Sequence rules
do exist elsewhere: Invariant's guardrails language matches patterns such as a
tool output followed by a `send_email` call, and Invariant Gateway applies it to
MCP over stdio, SSE and Streamable HTTP. Its repository was last updated in
November 2025.

**A gateway can inspect a result, not judge entitlement to it.** ContextForge
ships a PII filter on its `tool_post_invoke` hook, TrueFoundry scans for
credentials, and the MCP Interceptors Working Group is specifying validators and
mutators for "tool calls, resource reads, prompt gets". What MCP does not carry
is whether this caller was entitled to this data, so result inspection is
pattern matching on content, separate from authorization.

**A gateway governs only the traffic configured to flow through it.** A developer
running a stdio server on a laptop is outside every central control you own.

That last one has an answer in the client. VS Code's `chat.mcp.access` takes
`all`, `registry` or `none`, with allow and deny lists matching "configured name,
remote URL, or local command invocation". Claude Code has the same shape:
`allowedMcpServers` and `deniedMcpServers` keyed by URL, command or name,
`allowManagedMcpServersOnly: true` to stop users broadening the list, and a
`managed-mcp.json` for exclusive control, delivered by "Jamf or a configuration
profile on macOS, Group Policy or Intune on Windows". GitHub's administration
docs call a managed-settings allowlist "The more secure, generally available
method" for Copilot surfaces.

Two cautions. These lists match a command string, not a binary. Claude Code's
documentation says "The `env` block isn't compared" and that "Some environment
variables change what `node` loads at startup", and an allowlisted
`npx -y <package>` runs whatever npm serves at launch. And each client implements
its own list, so a fleet with three clients maintains three policies.

## A vetting process that survives contact with reality

Guidance exists: the protocol's own Security Best Practices, the Cloud Security
Alliance's draft "Agentic MCP Security Best Practices Guide" of March 2026, and
the OWASP GenAI Security Project's "A Practical Guide for Securely Using
Third-Party MCP Servers". The Coalition for Secure AI, an OASIS Open Project, released a "Model
Context Protocol (MCP) Security" white paper in January 2026 with "a well-defined
taxonomy of nearly forty threats and concrete mitigation strategies across twelve
distinct categories"; among them, enterprise clients "should enforce
authenticated server discovery and maintain explicit allowlists". NIST's National
Cybersecurity Center of Excellence asked in a February 2026 concept paper on
agent identity and authorization, "What support are you seeing for new protocols
such as Model Context Protocol (MCP)?"

What I could not find is a vetting profile: a published baseline of what a review
of an MCP server covers, from the MCP project, the Agentic AI Foundation or the
Linux Foundation. The Security Interest Group now has admission in scope, so the
venue exists.

Published criteria are rarer than reviews. Maryland's Department of Information
Technology publishes seven vetting areas and the rule that "No enterprise system
may connect to an MCP server without prior review and approval by the Office of
Security Management (OSM)". Anthropic publishes its directory criteria. Docker
operates a human review gate and does not publish its review criteria. Block has
been reported to run more than a hundred internal servers, with no published
vetting criteria. Most enterprises derive their own, from the same primary
sources, in private.

So here is a five-gate process, assembled from primary sources. The design
principle behind it: **automate everything that is mechanical, and spend human
attention only where judgment is irreplaceable.**

**Gate 0, intake. Fully automatable.** Fingerprint the server with
`server/discover`, a mandatory RPC as of 2026-07-28. Run a scanner with a CI exit
code. Two have one: MCP Interviewer's `--fail-on-warnings`, from a project whose
README says it "was developed for research and experimental purposes", and Snyk
Agent Scan's `--ci`, which exits non-zero "when findings or operational failures
remain" and sends tool names, descriptions and server configurations to Snyk's
API for analysis. Do all of it **inside an isolated container**, because scanning
a stdio server means executing it.

**Gate 1, provenance.** Registry namespace proof, `npm audit signatures` or PyPI
PEP 740, SLSA level 2 as a floor. Record this as an audit trail and **never as a
safety finding**, because a package registry's controls answer where an artifact
came from and none of them reads a tool description for an injection payload.

**Gate 2, blast radius. The only part worth human time.** Read every
`inputSchema` and ask one question: what is the worst outcome if every string
argument is attacker-chosen? Reject free-form CLI pass-through, which is
Anthropic's catch-all rule applied to your own estate of servers. Read the
configuration as well as the code: the safe mode that removed `kubectl_generic`
was a documented environment variable. Enumerate the credentials reachable by
anything that bypasses tenant isolation. **This is what catches a
`kubectl_generic`.** Reading tool descriptions for signs of manipulation does
not.

**Gate 3, descriptions.** Hash the entire `tools/list` and store the hash with
the approval. This is not new: in 2025 mcp-scan detected changes to MCP tools "via hashing"
(it is now Snyk Agent Scan, whose current README, read 2026-10-06, no longer
describes this), and registry issue #82 and SEP-1766 proposed tool fingerprints
and per-tool digests. What 2026-07-28 changed is that a hash became reliable: the tool set is
connection-invariant and servers **SHOULD** return it in deterministic order. The
set may still vary by the authorization presented, so hash it under the
credential the agent will actually use. Review the assembled tool set **per
agent**, not each server alone, or cross-server shadowing is invisible.

**Gate 4, continuous.** Pin digests. Re-hash and fail closed on any diff. Gate at
a proxy on the required headers. Make the gateway reject older protocol versions
rather than trust unvalidated header values, which the specification itself warns
about.

Gate 4 exists because a one-time review does not survive a server that updates,
and because revocation today is pull-only. The registry offers an
`updated_since` query and a `status` field it asks aggregators to keep current,
so your revocation latency equals your poll interval, and nothing reaches a
running agent. Removal is normally a status flip whose metadata stays live, and
aggregators *may* prefer to drop it. A personal `io.github.<person>` namespace
has no transfer path, so an abandoned server stays listed under the name of
someone who left.

## Three things that are not shared yet

Each organization that does this work does it separately, from the same primary
sources, without being able to see each other's results. Three artifacts would
end that duplication. Each has a venue now.

1. **A published vetting profile.** A baseline of what a review covers, so
   organizations stop deriving the same few dozen criteria in private. The
   Security Interest Group's scope covers admission; a profile is the concrete
   thing it could publish.
2. **A machine-readable review attestation** attached to `server.json`, stating
   that a review happened, against a named profile version, with a hash of the
   reviewed tool set and an expiry. The slot exists: `_meta` already carries
   subregistry data. What is missing is a standard key the schema owners bless.
   Registry issue #1273 proposes an optional security scan field, and pull
   request #1404 implements digest-bound, evidence-scoped scan receipts under
   `_meta`; neither had a maintainer response as of 2026-10-06. In May 2025 a
   registry maintainer, Tadas Antanavicius, wrote that attestations about
   "server signing or build proof" and CVE-based risk "could both be very
   useful", with any filter "decidedly vendor-neutral, objective, and not
   subject to context/interpretation". That condition is the reason the field
   has to describe evidence and not deliver a verdict. If only one of these three
   gets built, it should be this one.
3. **A revocation signal that is pushed.** The pull feed exists. What does not
   is a way for "this server is compromised" to reach a client faster than an
   aggregator's polling interval.

If you vet servers today, these are the places to bring what you have learned:
the Security Interest Group for the profile and post-approval drift, registry
issue #1273 and pull request #1404 for the field, and the Enterprise Interest
Group, whose scope includes audit and compliance and "descendant revocation".
The MCP roadmap's third priority area, Agent Identity and Enterprise-Ready
Security, has named Core Maintainers.

## The part nobody has done, including me

Every governance recommendation in circulation, this article included, rests on
vendor material, measurement studies and inference. Operational post-mortems
exist: GitHub's [July 2026 availability report](https://github.blog/news-insights/company-news/github-availability-report-july-2026/)
covers a 2026-07-16 failure of its MCP Server's `web_search` tool, remediated
with a time budget, with a circuit breaker still to come. Asana, as UpGuard
reported, said a post-mortem of its 2025 cross-tenant exposure would be
available on request. **I could not find a published post-mortem of an MCP
security incident written by the organization it happened to.**

The measurement studies above count exposed servers. What has not been published
is an account of what a control plane caught under attack, what went past it, and
what it cost to find out. The Security Interest Group's scope includes
"tamper-evident records of what a tool call did and under what authority, for
compliance and incident review", which is the record such an account would be
written from.

---

*Part two of five on operating MCP at scale. Part one covers operational
excellence and the revision that moved under everyone. Parts three, four and five
cover reliability, performance and cost.*

*Every figure here is sourced below and was verified against the
primary source on 2026-09-21, again on 2026-10-05, and the revised sections on
2026-10-06. Where a number is self-reported or vendor-published rather than
measured, the text says so.*

## Sources

All URLs returned HTTP 200 on 2026-10-06 unless noted. The OWASP page refuses scripted requests (HTTP 403) and opens in a browser.

**The protocol and its governance**
1. MCP Security Policy. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/SECURITY.md
2. MCP Security Interest Group charter. https://modelcontextprotocol.io/community/interest-groups/security
3. MCP Security Best Practices, 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices
4. MCP Enterprise Interest Group charter. https://modelcontextprotocol.io/community/interest-groups/enterprise
5. MCP Interceptors Working Group charter. https://modelcontextprotocol.io/community/working-groups/interceptors
6. MCP Registry Moderation Policy. https://modelcontextprotocol.io/registry/moderation-policy
7. MCP Registry Working Group charter. https://modelcontextprotocol.io/community/working-groups/registry
8. MCP Registry FAQ, on unpublishing. https://modelcontextprotocol.io/registry/faq
9. MCP Registry guidance for aggregators and subregistries. https://modelcontextprotocol.io/registry/registry-aggregators
10. Specification 2026-07-28, Tools. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
11. Specification 2026-07-28, Streamable HTTP. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
12. Specification 2026-07-28, Authorization, for the `Authorization` request header. https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
13. Specification 2026-07-28, `server/discover`. https://modelcontextprotocol.io/specification/2026-07-28/server/discover
14. MCP Roadmap. https://modelcontextprotocol.io/development/roadmap
15. Registry API, paginated to exhaustion for the counts. https://registry.modelcontextprotocol.io/v0.1/servers?limit=100&version=latest
16. Registry issue #31, "Entry Criteria", comment of 2025-05-11. https://github.com/modelcontextprotocol/registry/issues/31
17. Registry issue #82, tool signatures. https://github.com/modelcontextprotocol/registry/issues/82
18. Registry issue #1273, security scan metadata field. https://github.com/modelcontextprotocol/registry/issues/1273
19. Registry pull request #1404, security-scan receipt `_meta` extension. https://github.com/modelcontextprotocol/registry/pull/1404
20. SEP-1766, digest-pinned tool versioning. https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1766

**The CVE**
21. GitHub Security Advisory GHSA-6mx4-4h42-r8vh (CVE-2026-47250), 2026-05-22. https://github.com/Flux159/mcp-server-kubernetes/security/advisories/GHSA-6mx4-4h42-r8vh
22. NVD, CVE-2026-47250. https://nvd.nist.gov/vuln/detail/CVE-2026-47250
23. `mcp-server-kubernetes` README at v3.6.2, non-destructive mode. https://github.com/Flux159/mcp-server-kubernetes/blob/v3.6.2/README.md

**Catalogs and supply chain**
24. Docker, MCP Registry contributing guide. https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md
25. Anthropic, connector review criteria. https://claude.com/docs/connectors/building/review-criteria
26. GitHub, "Configure an MCP registry for your enterprise or organization". https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-mcp-usage/configure-mcp-registry
27. npm registry record for `postmark-mcp`, publish timestamps and unpublish date. https://registry.npmjs.org/postmark-mcp
28. Postmark, "Information regarding malicious postmark-mcp package", 2025-09-25. https://postmarkapp.com/blog/information-regarding-malicious-postmark-mcp-package
29. Idan Dardikman, Koi Security, 2025-09-25. The original URL now redirects to a vendor product page, so this is the archived copy. https://web.archive.org/web/20260101202603/https://www.koi.ai/blog/postmark-mcp-npm-malicious-backdoor-email-theft
30. npm Docs, "Generating provenance statements". https://docs.npmjs.com/generating-provenance-statements/
31. npm Docs, "Verifying ECDSA registry signatures". https://docs.npmjs.com/verifying-registry-signatures/
32. PEP 740, index support for digital attestations. https://peps.python.org/pep-0740/
33. SLSA v1.1 security levels. https://slsa.dev/spec/v1.1/levels

**Measurement**
34. H. Zhou et al., "A First Measurement Study on Authentication Security in Real-World Remote MCP Servers", arXiv:2605.22333. https://arxiv.org/abs/2605.22333
35. N. Padilla, "Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale", arXiv:2608.00150. https://arxiv.org/abs/2608.00150
36. Knostic, "Mapping MCP Servers", 2025-07-17. Verified 2026-10-05; on 2026-10-06 every knostic.ai page, including the home page, returned HTTP 404. https://www.knostic.ai/blog/mapping-mcp-servers-study
37. Z. Wang et al., "MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers", arXiv:2508.14925, v2 of 2026-09-29. https://arxiv.org/abs/2508.14925
38. Berk Kalelioğlu, AIMultiple, "MCP Gateway Benchmark: Latency and Security of 6 Gateways", 2026-08-24. https://aimultiple.com/mcp-gateway

**Controls and guidance**
39. Jack Batzner, Microsoft, "Securing MCP: A Control Plane for Agent Tool Execution", 2026-04-22. https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/
40. Microsoft, Agent Governance Toolkit. https://github.com/microsoft/agent-governance-toolkit
41. Invariant Labs, guardrails language. https://github.com/invariantlabs-ai/invariant
42. Invariant Labs, Invariant Gateway. https://github.com/invariantlabs-ai/invariant-gateway
43. IBM, ContextForge PII guardian plugin configuration. https://github.com/IBM/mcp-context-forge/blob/main/plugins/config-pii-guardian-policy.yaml
44. Microsoft, MCP Interviewer. https://github.com/microsoft/mcp-interviewer
45. Snyk Agent Scan, formerly mcp-scan. https://github.com/snyk/agent-scan
46. mcp-scan README as of 2025-07-29, hashing and whitelist. https://github.com/snyk/agent-scan/blob/ffc2363e/README.md
47. Visual Studio Code, "Manage AI settings". https://code.visualstudio.com/docs/enterprise/manage-ai-settings
48. Claude Code, managed MCP configuration. https://code.claude.com/docs/en/managed-mcp
49. SlowMist, MCP Security Checklist. https://github.com/slowmist/MCP-Security-Checklist
50. All Things Open, "Block scaled MCP to 12,000 employees", 2025-12-02. https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions
51. Cloud Security Alliance, "Agentic MCP Security Best Practices Guide", draft, 2026-03-27. https://labs.cloudsecurityalliance.org/agentic/agentic-mcp-security-best-practices-v1/
52. OWASP GenAI Security Project, "A Practical Guide for Securely Using Third-Party MCP Servers" 1.0, 2025-11-04. https://genai.owasp.org/resource/cheatsheet-a-practical-guide-for-securely-using-third-party-mcp-servers-1-0/
53. OASIS Open, "Coalition for Secure AI Releases Extensive Taxonomy for Model Context Protocol Security", 2026-01-27. https://www.oasis-open.org/2026/01/27/coalition-for-secure-ai-releases-extensive-taxonomy-for-model-context-protocol-security
54. Coalition for Secure AI, "Model Context Protocol (MCP) Security" white paper. https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf
55. NIST NCCoE, "Accelerating the Adoption of Software and AI Agent Identity and Authorization", concept paper, February 2026. https://www.nccoe.nist.gov/sites/default/files/2026-02/accelerating-the-adoption-of-software-and-ai-agent-identity-and-authorization-concept-paper.pdf
56. Maryland Department of Information Technology, "Guidance for Responsible and Safe Usage" (MCP servers), v2.0, last revised 2026-09-08. https://doit.prod.maryland.gov/guidance-responsible-and-safe-usage

**Incidents**
57. GitHub, "GitHub availability report: July 2026". https://github.blog/news-insights/company-news/github-availability-report-july-2026/
58. UpGuard, "Asana discloses data exposure bug in MCP server". https://upguard.com/blog/asana-discloses-data-exposure-bug-in-mcp-server
