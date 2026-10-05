---
title: "Nobody Vets MCP Servers, and Everyone Is Right About Why"
subtitle: "Operating MCP at scale, part two: security"
date: 2026-09-21
status: draft
series: "Operating MCP at Scale"
part: 2
sources_verified_on: 2026-09-21
---

# Nobody Vets MCP Servers, and Everyone Is Right About Why

*Operating MCP at scale, part two: security.*

An attacker who can write to your application logs can take your cluster
credentials. No model was jailbroken, no vault was breached, and every call in
the chain was authorized.

A tool called `kubectl_generic` passes user-supplied flags
to kubectl without an allowlist. An attacker who can write a line into an
application's own log output plants one there. An operator, doing something
completely ordinary, asks an agent to look at the logs. The agent reads the
planted instruction and calls `kubectl_generic` with
`--server=https://attacker.example.com` and `--insecure-skip-tls-verify=true`.
kubectl does what it is told and sends the bearer token from the operator's
kubeconfig to the attacker as an `Authorization` header. The attacker replays it
with the operator's permissions.

That is CVE-2026-47250, against `mcp-server-kubernetes`. Affected at 3.6.2 and
below, fixed in 3.7.0, CWE-88, CVSS 3.1 score 6.1 as assigned by GitHub as CNA, advisory
GHSA-6mx4-4h42-r8vh. NVD lists that score as secondary and has not scored it
independently. The
exfiltration works by redirecting kubectl's API server address, not by reading a
token file off disk, which is the detail that makes it hard to catch with the
controls most teams already have.

The project assigned a CVE and shipped a fix. That is the correct outcome and it
is not the interesting part.

Nor is it true that nobody would have told you. The advisory went into the GitHub
Advisory Database on 2026-06-05, scoped to the npm package `mcp-server-kubernetes`
at `<= 3.6.2`. Anyone running `npm audit` has been warned since June.

The interesting part is what that warning does not do. It arrives only once
somebody reports the flaw, which is months after the tool was written and
whatever happened in between has already happened. It says nothing about whether
that server belonged in your estate to begin with. And the registry that lists
the server keeps listing it either way, which is a policy it publishes rather
than an oversight.

## Every layer says it is somebody else's job

Read the Model Context Protocol's own security policy. On server selection it is
unambiguous:

> "Users and administrators are responsible for server selection."

And it scopes out, explicitly, the class of thing the CVE above sits next to:

> "Reports about 'server X can perform action Y' are not vulnerabilities when Y
> is the server's intended purpose."

> "Reports about 'LLM invoked unexpected tool' are not MCP vulnerabilities, as
> they relate to LLM behavior and application-level controls."

That is a defensible trust boundary. A protocol specification cannot be
responsible for which software an operator chooses to run, and a model picking an
unexpected tool is an application concern. Anyone who has maintained a
specification has drawn this line, in about this place.

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
to grow, and this policy says so in public rather than implying coverage it does
not provide. Removal, when it happens, sets a server's
`status` to `"deleted"` while its metadata stays live in the API, and aggregators
decide for themselves whether to drop it.

The Registry Working Group's charter also rules out the obvious workaround,
which is running your own copy of the thing. Under **Out of Scope**:

> "Any commitment to delivering an enterprise-ready or reusable registry
> implementation. The codebase supports this instance only and is not intended
> for external deployments."

That is a scope decision, written down, by the group responsible. Working groups
are entitled to decide what they are not building, and saying so plainly is
better than the alternative. It does not say anything about vetting, and it
should not be read as though it does. What it says is that the private catalog
is yours to build.

So follow the pointer to the layer the registry names. A package registry
answers **provenance**: where did this artifact come from, and is the signature
valid. It does not answer **payload**: is the code malicious, and is that tool
description an injection. npm's own documentation says provenance does not
guarantee a package contains no malicious code.

The worked example is `postmark-mcp`. A package impersonating Postmark's MCP
server, whose version 1.0.16 added a single line that blind-copied every outbound
email to an attacker-controlled address. It would have carried valid provenance
at every step. Secondary reporting describes an attacker who built trust over
a run of releases. The npm registry's own publish timestamps, read on 2026-09-21,
show **13 versions before the backdoor**, the first at 10:44 on 2025-09-15 and
the last at 12:41 the following day. That is about **26 hours** of history, with
`1.0.16` landing at 08:59 on the 17th. Not a long con, which is worse.

Four layers, four defensible decisions, and the chain terminates at the
enterprise, which is the one layer with nobody left to point at. **Every position
in it holds, and an organization at the end of it still has to invent a security
framework from scratch.**

## What you would be inheriting

The population you are being asked to admit has a shape worth knowing.

The official registry, paginated in full on 2026-09-19, answers **33,366**
distinct servers or **108,042** version records to the same question, depending
on whether you ask for servers or every version. Neither number is wrong. Neither
is a statement about fitness for anything.

Two things about that set matter more than its size. **Fifteen percent of it
comes from three GitHub accounts.** And **the median server has exactly one
published version**, meaning the median server has been published to the registry
once and never updated there. That is not the same as never shipping a fix, since
a remote server can change behind a stable URL, which is its own problem.

Then the measured security posture of live servers, from three independent
studies that looked at real deployments rather than surveying practitioners:

| Study | Population | Finding |
|---|---|---|
| Zhou et al. | 7,973 live remote servers | **40.55% expose tools with no authentication.** Every OAuth-using server tested had at least one flaw |
| Padilla, arXiv 2608.00150 | 414 fully audited servers, from a 640-server confirmed pool | **91.8% of the 414 lacked OAuth.** 687 tool instances exposed shell execution with no access control, counted across the 640. Separately, 193 of 464 servers, 41.6%, vanished within 72 hours between runs |
| Knostic | 1,862 exposed servers found, 119 verified | **119 of 119** granted internal tool listings without authentication |

These measure different things. "No authentication at all" and "no OAuth
specifically" are not the same claim, and the three should not be stacked into a
trend line. Individually, each is enough.

## The model is not the control, and this is measured

The most common mitigation in production today is a system prompt asking the
agent not to do the bad thing. There is now a number for how well that works.

MCPTox (arXiv:2508.14925) built 1,312 tool-poisoning test cases against **45
live, real-world MCP servers and 353 authentic tools**, and ran them against 20
agents. From the abstract:

> "agents rarely refuse these attacks, with the highest refused rate
> (Claude-3.7-Sonnet) less than 3%"

The most vulnerable model tested, o1-mini, showed a 72.8% attack success rate.
And the finding that should end the argument:

> "more capable models are often more susceptible, as the attack exploits their
> superior instruction-following abilities"

Capability makes this worse, not better. Which means waiting for better models is
not a mitigation, it is the opposite of one.

So: **do not use a probabilistic system to enforce a deterministic
requirement.** A system prompt asking an agent not to exfiltrate is a request. An
authorization check is an answer.

Note also that the specification already tells you not to trust the metadata:

> "For trust & safety and security, clients **MUST** consider tool annotations
> to be untrusted unless they come from trusted servers."

Which returns the whole question to what "trusted" means, and who decided.

## What a gateway can and cannot do

A gateway is the right architecture and it is not a solution. Being precise about
the boundary is what separates a working control plane from a false sense of one.

Without parsing a request body, a gateway sees four things: the protocol version,
the `Mcp-Method` header, the `Mcp-Name` header, and whichever tool arguments a
server author chose to expose through `x-mcp-header`. The 2026-07-28 revision says of `Mcp-Method` and `Mcp-Name` that "these headers
are **REQUIRED** for compliance", requires `MCP-Protocol-Version` on every POST
in a separate rule, and mandates rejecting a mismatch between header and body
with error `-32020`. The specification states
its own reasoning, which is a gateway threat model in the spec's words:

> "This prevents potential security vulnerabilities when different components in
> the network rely on different sources of truth (e.g., a load balancer routing
> on the header value while the MCP server executes based on the body value)."

That is useful, and it is bounded. On the argument-mirroring mechanism,
the specification tells server authors to keep the interesting things out:

> "Server developers **SHOULD NOT** mark sensitive parameters (passwords, API
> keys, tokens, PII) with `x-mcp-header`, as header values are visible to network
> intermediaries."

So argument-level policy works for routing-shaped arguments like a region or a
tenant, and not for the arguments a reviewer most wants to police. Anything
further requires a full body parse, and the cost of that depends entirely on what
does the inspecting. The only independent benchmark I found (AIMultiple, Berk
Kalelioğlu, 2026-08-24) measured self-hosted gateways adding between 0.84 and 23
milliseconds for routing. Pattern-matching inspection added about 11 percent,
while turning on two model-based guardrails moved added latency from 55 to 172
milliseconds. So header routing is close to free, and inspection is cheap or
expensive depending on whether a model is in the path.

Three further limits, stated plainly:

**A gateway evaluates one call.** Writing on Microsoft's developer blog about
the Agent Governance Toolkit, Jack Batzner states the limitation plainly: "AGT
governs individual tool calls deterministically. It does not yet correlate
sequences of individually-allowed calls that may form a malicious workflow". The
same sentence goes on to say that correlation is on the roadmap. AGT is an
MIT-licensed open-source project in public preview rather than a supported Azure
service, and the candor is worth more than the limitation costs.

**A gateway cannot judge a result.** Nothing in MCP classifies returned data, so
no intermediary can decide whether what came back should have.

**A gateway governs only the traffic configured to flow through it.** A developer
running a stdio server on a laptop is outside every central control you own.

That last one has an answer, and the answer is not a gateway. The only verified
control that reaches a laptop server is the editor's enterprise policy:
VS Code's `chat.mcp.access` set to `all`, `registry` or `none`, with allow and
deny lists that match on the **local command invocation itself**, delivered
through device management. It can refuse to launch a named binary.

Which is its own version of the same story. The answer to the protocol's bypass
problem currently lives in one vendor's MDM channel.

## A vetting process that survives contact with reality

Guidance exists, and none of it comes from a steward of the protocol. The Cloud
Security Alliance published an "Agentic MCP Security Best Practices Guide" in
March 2026, still marked draft, which calls for a governance process involving
security review and business sign-off. The OWASP GenAI Security Project has "A
Practical Guide for Securely Using Third-Party MCP Servers", covering discovery
and governance workflows. Both are worth reading.

What does not exist is a vetting profile from **the MCP project, the Agentic AI
Foundation, the Linux Foundation or CNCF**: the bodies that own the protocol, the
registry and the schema an approval would have to attach to. NIST SP 800-218A,
the nearest applicable standards document, is a July 2024 secure software
development profile that predates MCP's release.

Nor has any named organization published the criteria it actually uses. Docker
operates a real human review gate and does not publish the rubric. Block runs
more than a hundred internal servers with no published governance. So every
enterprise derives its own, from the same primary sources, in private.

So here is a five-gate process, assembled from primary sources. The design
principle behind it: **automate everything that is mechanical, and spend human
attention only where judgment is irreplaceable.**

**Gate 0, intake. Fully automatable.** Fingerprint the server with
`server/discover`, which is a mandatory RPC as of 2026-07-28. Run MCP Interviewer
with `--fail-on-warnings`, which is the only tool found with a real CI gate. Run
static scanning. Do all of it **inside an isolated container**, because scanning
a stdio server means executing it.

**Gate 1, provenance.** Registry namespace proof, `npm audit signatures` or PyPI
PEP 740, SLSA level 2 as a floor. Record this as an audit trail and **never as a
safety finding**, because every published supply chain control answers a
provenance question and none answers whether a description is an injection
payload.

**Gate 2, blast radius. The only part worth human time.** Read every
`inputSchema` and ask one question: what is the worst outcome if every string
argument is attacker-chosen? Reject free-form CLI pass-through. Enumerate the
credentials reachable by anything that bypasses tenant isolation. **This is what
catches a `kubectl_generic`.** Reading tool descriptions for signs of
manipulation does not.

**Gate 3, descriptions.** Hash the entire `tools/list` and store the hash with
the approval. This became meaningful for the first time in 2026-07-28, which made
the tool set connection-invariant and says servers **SHOULD** return it in
deterministic order. Review the assembled tool set **per agent**, not each server
alone, or cross-server shadowing is structurally invisible.

**Gate 4, continuous.** Pin digests. Re-hash and fail closed on any diff. Gate at
a proxy on the required headers. Make the gateway reject older protocol versions
rather than trust unvalidated header values, which the specification itself warns
about.

Gate 4 exists because a one-time review does not survive a server that updates,
and because revocation today is worse than most people assume. There is no push,
no feed, and no signal to a running agent. A server **cannot be unpublished at
all**. Removal is a status flip whose metadata stays live, aggregators *may*
prefer to drop it, and your revocation latency equals your poll interval. A
personal `io.github.<person>` namespace has no transfer path, so an abandoned
server stays listed under the name of someone who left.

## Three things that do not exist

Everything above is work every large organization is doing separately, from the
same primary sources, without being able to see each other's results. Three
artifacts would end that duplication, and each one needs a steward rather than a
vendor:

1. **A published vetting profile.** A baseline of what a review covers, so
   organizations stop deriving the same few dozen criteria in private.
2. **A machine-readable review attestation** attached to `server.json`. A
   checklist can be written by anyone. A statement that a review happened,
   against a named profile version, with a hash of the reviewed tool set and an
   expiry, can only be defined by whoever owns the schema. If only one of these
   three gets built, it should be this one.
3. **A revocation feed.** So that "this server is compromised" can travel faster
   than an aggregator's polling interval.

There is a door for this already. The MCP roadmap's third priority area is Agent
Identity and Enterprise-Ready Security, with named Core Maintainers and a working
group forming. These belong there.

## The part nobody has done, including me

Every governance recommendation in circulation, this article included, rests on
vendor material, measurement studies and inference. Operational post-mortems
exist: GitHub's [July 2026 availability report](https://github.blog/news-insights/company-news/github-availability-report-july-2026/)
covers a one hour failure of its MCP Server's `web_search` tool, with a time
budget and a circuit breaker as the remediation. Asana says its report on the
2025 cross-tenant exposure is available on request. **I could not find a
published post-mortem of an MCP security incident written by the organization it
happened to.**

Not one account of what actually happened to an organization running this at
scale, what the control plane caught, what went past it, and what it cost to find
out. The security literature for this protocol is composed of people reasoning
about what should happen.

That is the gap worth closing, and it does not need a specification change or
anyone's permission. It needs somebody to go first.

---

*Part two of five on operating MCP at scale. Part one covers operational
excellence and the revision that moved under everyone. Parts three, four and five
cover reliability, performance and cost.*

*Every figure in this article is sourced below and was verified against the
primary source on 2026-09-21. Where a number is self-reported or vendor-published
rather than measured, the text says so.*

## Sources

All URLs returned HTTP 200 on 2026-09-21 unless noted.

**The protocol and its governance**
1. MCP Security Policy. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/SECURITY.md
2. MCP Registry Moderation Policy. https://modelcontextprotocol.io/registry/moderation-policy
3. MCP Registry Working Group charter. https://modelcontextprotocol.io/community/working-groups/registry
4. MCP Registry FAQ, on unpublishing. https://modelcontextprotocol.io/registry/faq
5. MCP Registry guidance for aggregators. https://modelcontextprotocol.io/registry/registry-aggregators
6. Specification 2026-07-28, Tools. https://modelcontextprotocol.io/specification/2026-07-28/server/tools
7. Specification 2026-07-28, Streamable HTTP. https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
8. Specification 2026-07-28, `server/discover`. https://modelcontextprotocol.io/specification/2026-07-28/server/discover
9. MCP Roadmap. https://modelcontextprotocol.io/development/roadmap
10. Registry API, paginated to exhaustion for the counts. https://registry.modelcontextprotocol.io/v0.1/servers?limit=100&version=latest

**The CVE**
11. GitHub Security Advisory GHSA-6mx4-4h42-r8vh (CVE-2026-47250), 2026-05-22. https://github.com/Flux159/mcp-server-kubernetes/security/advisories/GHSA-6mx4-4h42-r8vh
12. NVD, CVE-2026-47250. https://nvd.nist.gov/vuln/detail/CVE-2026-47250

**Supply chain**
13. npm registry record for `postmark-mcp`, publish timestamps. https://registry.npmjs.org/postmark-mcp
14. Postmark, "Information regarding malicious postmark-mcp package", 2025-09-25. https://postmarkapp.com/blog/information-regarding-malicious-postmark-mcp-package
15. Idan Dardikman, Koi Security, 2025-09-25. The original URL now redirects to a vendor product page, so this is the archived copy. https://web.archive.org/web/20260101202603/https://www.koi.ai/blog/postmark-mcp-npm-malicious-backdoor-email-theft
16. npm Docs, "Generating provenance statements". https://docs.npmjs.com/generating-provenance-statements/
17. npm Docs, "Verifying ECDSA registry signatures". https://docs.npmjs.com/verifying-registry-signatures/
18. PEP 740, index support for digital attestations. https://peps.python.org/pep-0740/
19. SLSA v1.1 security levels. https://slsa.dev/spec/v1.1/levels

**Measurement**
20. H. Zhou et al., "A First Measurement Study on Authentication Security in Real-World Remote MCP Servers", arXiv:2605.22333. https://arxiv.org/abs/2605.22333
21. N. Padilla, "Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale", arXiv:2608.00150. https://arxiv.org/abs/2608.00150
22. Knostic, "Mapping MCP Servers", 2025-07-17. https://www.knostic.ai/blog/mapping-mcp-servers-study
23. Z. Wang et al., "MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers", arXiv:2508.14925. https://arxiv.org/abs/2508.14925
24. Berk Kalelioğlu, AIMultiple, "MCP Gateway Benchmark: Latency and Security of 6 Gateways", 2026-08-24. https://aimultiple.com/mcp-gateway

**Controls and guidance**
25. Jack Batzner, Microsoft, "Securing MCP: A Control Plane for Agent Tool Execution", 2026-04-22. https://developer.microsoft.com/blog/securing-mcp-a-control-plane-for-agent-tool-execution/
26. Microsoft, Agent Governance Toolkit. https://github.com/microsoft/agent-governance-toolkit
27. Microsoft, MCP Interviewer. https://github.com/microsoft/mcp-interviewer
28. Visual Studio Code, Enterprise AI settings. https://code.visualstudio.com/docs/enterprise/ai-settings
29. NIST SP 800-218A, July 2024. https://csrc.nist.gov/pubs/sp/800/218/a/final
30. SlowMist, MCP Security Checklist. https://github.com/slowmist/MCP-Security-Checklist
31. Docker, MCP Registry contributing guide. https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md
32. All Things Open, "Block scaled MCP to 12,000 employees", 2025-12-02. https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions
