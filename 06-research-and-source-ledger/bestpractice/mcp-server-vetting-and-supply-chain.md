---
title: "Vetting and Approving MCP Servers: What Is Published, What Is Enforced, What Does Not Exist"
date: 2026-09-18
sources_verified_on: 2026-09-18
status: draft
---

<!-- ABOUTME: Evidence base for enterprise vetting and approval of third-party and internal MCP servers, assembled from primary sources. -->
<!-- ABOUTME: Every claim carries a source URL, a source class label, and a verification date; gaps in the published record are stated as findings. -->

# Vetting and Approving MCP Servers

> **Note added 2026-10-06, on publication:** This file says Anthropic's connector review criteria are unpublished. They are now published: https://claude.com/docs/connectors/building/review-criteria

Built for the MCP Dev Summit Toronto keynote, 2026-10-06, delivered to the Agentic AI Foundation. Companion to `06-research-and-source-ledger/security/mcp-security-failures-2026-09.md`, which catalogues the failures this document is about preventing.

**Source class convention.** Every source is labelled:

| Label | Meaning |
|---|---|
| OFFICIAL | The MCP project, a standards body, or the operator of the thing being described |
| PEER-REVIEWED | Published research with a stated method |
| PRACTITIONER | A named engineer or team describing their own work, not selling a product |
| VENDOR | A company describing a problem its product solves |
| SECONDHAND | Reporting about a primary source not read directly |

Everything below was read on **2026-09-18** unless stated otherwise. Claims that could not be confirmed are marked UNVERIFIED and must not be spoken from the stage as fact.

**The headline finding, stated once here and defended throughout.** There is no published vetting framework for MCP servers from the MCP project, the Agentic AI Foundation, the Linux Foundation, CNCF, NIST, or OWASP. What exists is a namespace-ownership check, a set of general software supply chain controls that were not designed for this problem, three scanners, and a large amount of vendor marketing. The MCP project itself assigns the vetting duty to the deployer in writing and declines to do it. An enterprise that wants a defensible process has to assemble one, and this document assembles it.

---

## 1. Published vetting frameworks and checklists

### 1.1 The MCP project does not vet, and says so in normative language

This is the single most citable fact in this document, and it comes from the specification repository's own `SECURITY.md`.

**Source:** OFFICIAL. <https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/SECURITY.md>, read 2026-09-18. Summarised at <https://modelcontextprotocol.io/community/security>.

The trust model, verbatim:

> **MCP clients trust MCP servers they connect to.** When a user or application configures an MCP client to connect to a server, the client trusts that server to provide tools, resources, and prompts. The security of this trust relationship depends on proper server selection and configuration by the user or administrator.

> **Local MCP servers are trusted like any other software you install.** When you run a local MCP server, you are trusting it with the same level of access as any other application or package on your system. Just as you would evaluate the trustworthiness of a library or tool before installing it, you should evaluate MCP servers before running them.

> **Users and administrators are responsible for server selection.**

And the explicit division of responsibility:

> **Operators and users are responsible for:**
> - Connecting only to trusted MCP servers
> - Reviewing server configurations before deployment
> - Understanding the capabilities of servers they enable
> - Configuring appropriate access restrictions for their environment

The same document lists behaviours that are **not** eligible as vulnerability reports. Three of them matter directly to anyone designing a review checklist, because they define the floor below which no upstream fix is coming:

1. **Command execution over stdio is a feature.** "Reports about 'arbitrary command execution' via STDIO transport configuration, whether in MCP client applications or SDKs, are not vulnerabilities. Process spawning is a core feature of the STDIO transport mechanism."
2. **Server capabilities and side effects are features.** "Reports about 'server X can perform action Y' are not vulnerabilities when Y is the server's intended purpose. The appropriate safeguards and permissions for these capabilities are the responsibility of the user or administrator deploying the server."
3. **LLM-driven tool invocation is a feature.** "The LLM may invoke tools in ways the user did not explicitly request ... Reports about 'LLM invoked unexpected tool' are not MCP vulnerabilities, as they relate to LLM behavior and application-level controls."

There is also a stated non-guarantee about isolation: "Deployments that run stdio servers at reduced privilege (containers, sandboxes) are responsible for enforcing isolation at that boundary; the SDK's stdio transport is not a sandbox."

**What this means for the talk.** The protocol's security model is a delegation. Every question an enterprise reviewer asks is, by the project's own text, the enterprise's question to answer. That is a defensible design choice for a protocol, and it is also the reason a vetting gap exists. Saying this from the stage is not an attack on the project; it is quoting the project.

### 1.2 The Security Interest Group is the venue, not a framework

**Source:** OFFICIAL. <https://modelcontextprotocol.io/community/security>, read 2026-09-18.

The MCP project runs a Security Interest Group, described as "the venue for discussing MCP-specific threats, reviewing security-relevant proposals, and routing disclosure questions that don't fit a single repository." It is a coordination body for spec and SDK vulnerabilities. It publishes no server review criteria, no certification, and no approved-server list. Vulnerability handling is GHSA-based, with CVEs assigned through GitHub's CNA, and cross-SDK coordination when a defect is shared.

### 1.3 OWASP: adjacent, useful, not MCP-specific

**OWASP LLM03:2025 Supply Chain.** Source: OFFICIAL (OWASP GenAI Security Project). <https://genai.owasp.org/llmrisk/llm032025-supply-chain/>, read 2026-09-18. Ten mitigations, of which five transfer directly to MCP server acquisition:

- "Carefully vet data sources and suppliers, including T&Cs and their privacy policies, only using trusted suppliers."
- "Maintain an up-to-date inventory of components using a Software Bill of Materials (SBOM) to ensure you have an up-to-date, accurate, and signed inventory."
- "Only use models from verifiable sources and use third-party model integrity checks with signing and file hashes to compensate for the lack of strong model provenance."
- Apply OWASP A06:2021 component controls, including vulnerability scanning and patching.
- "Ensure applications rely on maintained API and model versions" (patching policy).

The word "MCP" does not appear in the mitigation list. This is generic AI supply chain guidance that predates the MCP-specific threat surface.

**OWASP Agentic Security Initiative.** Source: OFFICIAL. "Agentic AI: Threats and Mitigations", published 2026-02-17 by the OWASP Agentic Security Initiative, <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/>. "Securing Agentic Applications Guide 1.0", published 2025-07-27, <https://genai.owasp.org/resource/securing-agentic-applications-guide-1-0/>.

**UNVERIFIED in detail.** Both are PDF downloads behind landing pages. The landing pages carry the titles, dates and framing but not the content, and the PDFs were not retrieved in this session. The threat taxonomy identifiers and the specific controls are therefore **not verified here**. Do not quote a specific OWASP ASI threat number or control from memory. The dates and the existence of the documents are verified; their contents are not.

### 1.4 NIST: the SSDF profile exists and does not reach this problem

**Source:** OFFICIAL. NIST SP 800-218A, "Secure Software Development Practices for Generative AI and Dual-Use Foundation Models: An SSDF Community Profile", published **July 2024**. <https://csrc.nist.gov/pubs/sp/800/218/a/final>, read 2026-09-18.

It augments SSDF 1.1 for model producers, system producers, and acquirers. It predates MCP's public release by four months and predates the entire tool-poisoning literature. The specific practice identifiers for third-party component acquisition were not extracted from the landing page and are **UNVERIFIED** here; the full PDF was not read.

**The honest framing:** the applicable NIST document is an SSDF profile written before the problem existed. There is no NIST publication on agent tool vetting. If asked from the stage, say that.

### 1.5 CSA: A2A, not MCP

**Source:** OFFICIAL (Cloud Security Alliance). <https://cloudsecurityalliance.org/blog/2025/04/30/threat-modeling-google-s-a2a-protocol-with-the-maestro-framework>, read 2026-09-18.

CSA's MAESTRO threat-modelling framework (published 2026-02-06 per the article's own cross-reference) has been applied to Google's A2A protocol and to the OpenAI Responses API. **No CSA MCP-specific server vetting guidance was located in this session.** Absence of evidence, stated as such.

### 1.6 The most complete published checklist is from a security firm, not a standards body

**Source:** PRACTITIONER, with a vendor affiliation. SlowMist Team, "MCP Security Checklist", <https://github.com/slowmist/MCP-Security-Checklist>, read 2026-09-18. Contributions from FENZ.AI. Items carry High/Medium priority labels.

This is the closest thing to a real review checklist in the public record, and it is worth saying plainly that the most complete artifact comes from a blockchain security firm rather than from any foundation. Its items, grouped:

| Category | Criterion (verbatim where quoted) | Priority |
|---|---|---|
| Tools security | "Strictly validate all inputs from clients" | High |
| Tools security | "Each tool should have only the minimum permissions needed" | High |
| Tools security | "Verify that the returned information from interfaces is as expected; do not directly insert" third-party data into context | High |
| Tools security | Check tool descriptions for potential malicious instructions | Medium |
| Tool and server management | "Verify the authenticity and integrity of registered tools" | High |
| Tool and server management | "Check for name conflicts or malicious overwriting before registering" | High |
| Tool and server management | "Verify whether the updated tools contain any malicious descriptions" | High |
| Tool and server management | Maintain authorized directory of trustworthy MCP servers | Medium |
| Tool and server management | Set explicit function priority rules to prevent hijacking | Medium |
| Supply chain | "Securely manage third-party dependencies" | High |
| Supply chain | "Verify the integrity and authenticity of packages" | High |
| Auth | "Implement role-based access control, limit resource access, and enforce the principle of least privilege" | High |
| Auth | "Securely manage and store service credentials; avoid hard-coded secrets" | High |
| Auth | "Use secure methods when authenticating with third-party services" | High |
| Auth | Automatic API key rotation | Medium |
| API | "Enforce strict validation on all API inputs to prevent injection attacks" | High |
| API | "Implement call rate limits to prevent abuse or DoS attacks" | Medium |
| Monitoring | "Detect and report anomalous activity patterns" | High |
| Monitoring | "Log all service activities and security events" | High |
| Monitoring | "Configure real-time alerts for critical security events" | High |

Note the three items under tool and server management. They are the rug-pull controls, and they are stated as requirements without a stated mechanism. Section 4 supplies the mechanism.

### 1.7 Vendor guidance that says "have a process" without saying what the process is

**Source:** VENDOR. Palo Alto Networks, "Model Context Protocol (MCP): A Security Overview", June 2025, <https://www.paloaltonetworks.com/blog/prisma-cloud/model-context-protocol-mcp-a-security-overview/>, read 2026-09-18.

The operative sentence: "Create a formal approval process for adding new MCP servers to your environment, including security reviews, source verification and documentation." It also recommends an inventory of approved servers and "an internal repository of vetted MCP servers rather than allowing direct installation from public sources." It gives no criteria, no evaluation metrics, and names no organisation that does this.

**Source:** VENDOR. Wiz, "MCP Security Research Briefing", published 2025-04-17, updated 2025-04-21, <https://www.wiz.io/blog/mcp-security-research-briefing>, read 2026-09-18. Nine user-facing recommendations: trusted sources only, audit before use, careful credential handling, client selection, sandboxing, internal registries. One measured data point worth keeping: roughly **100 of the 3,500 servers** listed on glama.ai at the time linked to non-existent repositories. Registry listings drift away from their own source.

This is the shape of most of the corpus. The recommendation "have a formal approval process" is correct and is not a process.

---

## 2. Supply chain controls that exist today

### 2.1 The MCP Registry verifies who published, and nothing else

**Source:** OFFICIAL. <https://modelcontextprotocol.io/registry/about>, <https://modelcontextprotocol.io/registry/authentication>, <https://modelcontextprotocol.io/registry/moderation-policy>, <https://modelcontextprotocol.io/registry/faq>. All read 2026-09-18. The registry is **in preview**, with the note "Breaking changes or data resets may occur before general availability."

**What is enforced: namespace ownership proof.** Server names are reverse-DNS. The namespace determines which proof is required.

| Auth method | Name format | What is actually proven |
|---|---|---|
| GitHub OAuth device flow (`mcp-publisher login github`) | `io.github.username/*` or `io.github.orgname/*` | Control of that GitHub account or org |
| DNS TXT record | `com.example.*/*` | Control of the domain's DNS |
| HTTP well-known file | `com.example.*/*` | Control of content served at that domain |

The DNS record format is a signed-key challenge, not a shared secret:

```
example.com. IN TXT "v=MCPv1; k=ed25519; p=${PUBLIC_KEY}"
```

Supported key types are Ed25519 and ECDSA P-384, with the private key held locally or in Google Cloud KMS or Azure Key Vault. The HTTP variant serves the same `v=MCPv1; k=...; p=...` string at `/.well-known/mcp-registry-auth`.

This is a real cryptographic control and it is worth crediting. It defeats the plain impersonation case: nobody but the controller of `postmarkapp.com` can publish under `com.postmarkapp`. It does not defeat the postmark-mcp case, because that package was published to **npm** under a plausible name, not to the MCP Registry under a claimed domain.

**What is explicitly not enforced.** From the "Trust and Security" section:

> The MCP Registry delegates security scanning to:
> - **Underlying package registries** ... npm, PyPI, Docker Hub, and other package registries perform their own security scanning and vulnerability detection.
> - **Downstream aggregators** ... MCP Registry aggregators and marketplaces can implement additional security checks, ratings, or curation.
>
> The MCP Registry focuses on namespace authentication and metadata hosting, while relying on the broader ecosystem for security scanning of actual server code.

And the moderation policy is blunter still:

> The MCP Registry **does not** make guarantees about moderation, and consumers should assume minimal-to-no moderation.

> We largely rely on upstream package registries (like NPM, PyPI, and Docker) or downstream subregistries (like the GitHub MCP Registry) to do more in-depth moderation.

> This means there may be content in the MCP Registry that should be removed under this policy, but which we haven't yet removed. Consumers should treat scraped data accordingly.

The removal list covers illegal content, malware, spam, and non-functioning servers. The **do not remove** list is the one to put on a slide:

> We therefore **won't** remove:
> - Low-quality or buggy servers
> - **Servers with security vulnerabilities**
> - Servers that do the same thing as other servers
> - Servers that provide or contain adult content

A registry that explicitly does not remove servers with security vulnerabilities is not a vetting layer, and it does not claim to be. Removal sets `status: "deleted"` while metadata stays readable via the API, so aggregators must act on the status themselves.

**Two operational facts that matter for pinning.** From the FAQ: servers **cannot currently be deleted or unpublished** (open discussion at registry issue #104), and "Once published, version metadata is immutable (similar to npm)." Immutability is the property that makes version pinning meaningful. Inability to unpublish means a withdrawn server keeps resolving.

**What a reviewer actually receives.** `server.json` carries name, version, title, description, repository URL, package identity and registry type (npm, PyPI, NuGet, Cargo, OCI), transport configuration, environment variables including which are secret, package arguments, runtime hints, and remote endpoint templates. Integrity is **selective, not universal**: a `fileSha256` field exists for MCPB bundle packages. There is no universal digest or signature field binding a registry entry to a specific artifact across all package types. Source: OFFICIAL, <https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md>, read 2026-09-18.

Custom publisher metadata lives under `_meta.io.modelcontextprotocol.registry/publisher-provided`, capped at 4096 bytes.

**Security history of the registry itself.** Three advisories in 2026: CVE-2026-44427 (open redirect), CVE-2026-44428 (GitHub OIDC token bound only to a global audience string, so a token minted for one registry was accepted by any other), CVE-2026-44429 (stored XSS in the public catalogue via `server.websiteUrl` in any published `server.json`). Verified in the companion security document on 2026-09-17. The namespace verification layer is itself young code.

### 2.2 Docker MCP Catalog: the only curation with a human review gate and published entry requirements

**Source:** OFFICIAL. <https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/> and <https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md>, both read 2026-09-18.

Two tiers, and the difference is the whole point:

- **Docker-built servers.** Docker builds the image from your repository's Dockerfile. The resulting image "will include cryptographic signatures, provenance tracking, SBOMs, and automatic security updates."
- **Bring-your-own-image and remote servers.** You supply a prebuilt image or an externally hosted HTTPS endpoint. The signing, provenance and SBOM guarantees attach to Docker's build, so they do not transfer to an image Docker did not build.

Published submission requirements, verbatim:

- "Make sure that the license of your MCP Server allows people to consume it. (MIT or Apache 2 are great, GPL is not)."
- A `servers/<name>/server.yaml` entry, generated by `task wizard` or `task create`.
- "Ensure that CI passes, if it fails, fix the failures."
- "Every pull request requires a review from the Docker team before merging."
- Test credentials shared through a Google Form when the server needs them to be exercised.
- On approval, commits are squashed and the server is live "within 24 hours" across the catalog, Docker Desktop's MCP Toolkit, and Docker Hub's `mcp` namespace.

**What is enforced versus claimed.** Enforced and verifiable: a license check, CI, a human review by a named team, and for Docker-built images a signed artifact with provenance and an SBOM. Not published: the security criteria that human review applies. There is no written rubric, no threat-model requirement, no tool-description review standard, and no stated re-review trigger. The gate is real. Its contents are undisclosed.

### 2.3 Anthropic's directory: reviewed for "quality and security", criteria unpublished

**Source:** OFFICIAL. <https://www.anthropic.com/engineering/desktop-extensions>, read 2026-09-18. A submission form, cross-platform testing on Windows and macOS, and team review described only as focused on "quality and security". Secrets go to the OS keychain; extensions auto-update; users can audit what is installed. Enterprise controls named: blocklists, pre-installation of approved extensions, and private extension directories.

No signing requirement, no published audit procedure, no stated re-review trigger. The support article at `support.claude.com/en/articles/11596040-connectors-directory-review-process` returned **404** on 2026-09-18; treat any recollection of its contents as UNVERIFIED.

The enterprise controls are the genuinely useful part and they are the model for section 6: a private directory plus a blocklist is an admission-control system, and it is available today.

### 2.4 Build provenance: npm, PyPI, Sigstore, SLSA

These are the mature controls. They were built for a different threat and they are worth adopting anyway, provided nobody is told they solve this one.

**npm provenance.** OFFICIAL, <https://docs.npmjs.com/generating-provenance-statements>, read 2026-09-18. Two attestation types: a provenance attestation linking a package to its source repository and build instructions, and a publish attestation generated by the registry. Sigstore issues a short-lived signing certificate containing the build information and logs it to an immutable transparency ledger. Supported build environments are **GitHub Actions and GitLab CI/CD only**; self-hosted and on-premises runners are not supported. Consumers verify with `npm audit signatures`.

The sentence to quote:

> provenance does not guarantee the package has no malicious code

It establishes a verifiable audit trail so a developer can go and look. It is an input to review, not a substitute for it. The postmark-mcp backdoor would have carried perfectly valid provenance: it was genuinely built by its genuine author from its genuine source, and the source contained the backdoor.

**PyPI digital attestations (PEP 740).** OFFICIAL, <https://docs.pypi.org/attestations/>, read 2026-09-18. Each distribution is bound to a cryptographic digest of its contents. Publishing identities are limited to Trusted Publishers: GitHub Actions, GitLab CI/CD, Google Cloud, ActiveState. Built on the in-toto Attestation Framework with two predicate types, SLSA Provenance and PyPI Publish. Limits: at most two attestations per file, one per predicate type.

**SLSA build levels.** OFFICIAL, <https://slsa.dev/spec/v1.1/levels>, read 2026-09-18.

| Level | Requirement | Threat addressed |
|---|---|---|
| Build L1 | Consistent build process; the platform automatically generates provenance. Provenance "may be incomplete and/or unsigned" | Mistakes during release, such as building from the wrong commit. Not intentional attack |
| Build L2 | Hosted build platform generates **and signs** the provenance; consumers validate authenticity | Tampering after the build completed |
| Build L3 | Platform prevents runs from influencing one another and prevents signing key material from being accessible to user-defined build steps | Tampering during the build, insider threat, compromised credentials |

SLSA's scope is build integrity. It makes no claim about source code quality, dependency safety, or whether the software does something harmful on purpose. A malicious MCP server built at SLSA L3 is a malicious MCP server with excellent provenance.

**The synthesis, and it is the point of this whole section.** Provenance answers "did this artifact come from that source, built by that pipeline". Every published supply chain control answers a variant of that question. **Not one of them answers "is this tool description an injection payload".** The controls are necessary, they are cheap, they defeat typosquatting and post-build tampering, and they leave the MCP-specific attack surface entirely untouched.

### 2.5 Sigstore

OFFICIAL, referenced from both the npm and PyPI documentation above. Keyless signing with short-lived certificates bound to an OIDC identity, logged to a public append-only transparency log. It is the machinery under npm provenance and PyPI attestations rather than a separate control to adopt. Verified indirectly through those two sources on 2026-09-18; the Sigstore project documentation was not read directly in this session.

---

## 3. Automated scanning

Three tools exist. Together they cover static description analysis, adversarial probing, and schema and behaviour conformance. None covers code-level vulnerability discovery in the server implementation, which remains a job for ordinary SAST.

### 3.1 mcp-scan, now Snyk

**Source:** OFFICIAL (project README). Original: <https://github.com/invariantlabs-ai/mcp-scan>. Pre-acquisition README read at tag `v0.3.0` on 2026-09-18 via `raw.githubusercontent.com`.

**Provenance note worth stating.** mcp-scan was built by Invariant Labs, the team that disclosed tool poisoning, rug pulls and tool shadowing in April 2025. It is now a **Snyk** product, surfaced as "Agent Scan" and integrated with Snyk Evo. The independent tool that found the class became a commercial product of a security vendor within about eighteen months. That is a fact about the ecosystem, not a criticism of either party.

Two modes:

1. **`mcp-scan scan`.** Static. Reads file-based client configurations (Claude, Cursor, Windsurf and others), connects to each configured server, retrieves tool descriptions, and analyses them for prompt injection, tool poisoning, cross-origin escalation, rug pulls and toxic flows.
2. **`mcp-scan proxy`.** Dynamic. Temporarily injects a local Invariant Gateway into the client's MCP server configurations to intercept traffic, then removes it on exit. Enforces guardrails on calls and responses: PII detection, secrets detection, tool restrictions, and custom policies written in the Invariant policy language.

The rug-pull mechanism, which is the single most important line in the README for section 4:

> detect and prevent [MCP rug pull attacks], i.e. mcp-scan detects changes to MCP tools via hashing

State is kept in `--storage-file`, "Path to store scan results and whitelist information (default: `~/.mcp-scan`)". So the mechanism is: hash the tool description at approval time, store it, compare on every subsequent scan, and flag any change. That is the approval-pinning primitive, implemented.

**What it misses, from the README's own text.** Static scanning "connects to these servers and retrieves tool descriptions" and analyses those. It reviews the **advertised description**, not the server's code, so a server whose description is clean and whose implementation is malicious passes. A server that serves a benign description to a scanner and a poisoned one to a real client passes. Scanning requires connecting to and starting the server, which for a stdio server means executing it; the current Snyk-era build adds interactive consent prompts before starting stdio servers for exactly this reason.

**A privacy condition that will matter to an enterprise reviewer**, verbatim from the v0.3.0 README:

> For this, tool names and descriptions are shared with invariantlabs.ai. By using MCP-Scan, you agree to the invariantlabs.ai terms of use and privacy policy.

> Invariant Labs is collecting data for security research purposes (only about tool descriptions and how they change over time, not your user data). Don't use MCP-scan if you don't want to share your tools.

Guardrails and proxying are stated to operate entirely locally with no external API calls; the static scan's description analysis is the part that leaves the building. Whether this holds under Snyk is **UNVERIFIED**.

The current documentation lists "15+ security risks" across MCP servers and Agent Skills in v0.6+: prompt injection, dangerous words, untrusted content, private data, destructive capabilities, suspicious download URLs, malicious code patterns, insecure credential handling, hardcoded secrets. CLI output is marked experimental in both lines: "We do not recommend building production workflows that depend on specific CLI output fields."

### 3.2 MCPSafetyScanner

**Source:** PEER-REVIEWED (arXiv preprint). Radosevich and Halloran, "MCP Safety Audit: LLMs with the Model Context Protocol Allow Major Security Exploits", arXiv:2504.03767, submitted 2025-04-02, revised 2025-04-11. <https://arxiv.org/abs/2504.03767>, read 2026-09-18.

Described as "the first agentic tool to assess the security of an arbitrary MCP server". Three phases: automatically generate adversarial samples from the server's declared tools and resources, search for related vulnerabilities and remediations, produce a security report. Detects exposure to malicious code execution, remote access control, and credential theft.

**Limitation to state honestly:** the abstract does not publish quantitative detection rates or a false-negative analysis, and the full paper was not read in this session. Do not attribute a hit rate to it.

Its method is the interesting part for a keynote: it generates attacks from the server's own declared surface. That is the automatable half of a review, and it is the half a human reviewer does worst.

### 3.3 MCP Interviewer

**Source:** OFFICIAL (Microsoft). <https://github.com/microsoft/mcp-interviewer>, read 2026-09-18. Surfaced via Microsoft's own engineering blog on the Learn MCP server, <https://devblogs.microsoft.com/engineering-at-microsoft/how-we-built-the-microsoft-learn-mcp-server/>.

A Python CLI that "helps you catch MCP server issues before your agents do". Four check classes:

1. **Constraints.** Provider limits, for example OpenAI's 128-tool ceiling and name-length restrictions.
2. **Schema and metadata.** Tool definitions, descriptions, structural compliance.
3. **Functional behaviour.** Optionally executes tools and observes what happens.
4. **LLM compatibility.** Uses a model to judge whether tools work well with agents. Marked experimental.

Outputs Markdown and JSON: server info, capabilities, tool statistics, constraint violations, execution results. **It has a `--fail-on-warnings` flag intended for CI/CD**, which makes it the only one of the three with an explicit pipeline gate.

Stated caveats: "developed for research and experimental purposes", servers should be run in isolated containers, and misleading server metadata can produce inaccurate output.

It is a conformance and quality tool, not a security scanner. In a vetting pipeline it belongs at the intake step, because a server that violates its host's constraints or ships 200 undocumented tools is a governance problem before it is a security problem.

### 3.4 Semgrep and CodeQL

**UNVERIFIED.** The Semgrep blog URL tried in this session returned 404. No MCP-specific Semgrep ruleset or CodeQL query pack was confirmed. Generic rules for the underlying CWEs plainly apply, and the companion security document establishes that these dominate the CVE corpus: OS command injection CWE-78 at 41 occurrences, command injection CWE-77 at 29, SSRF CWE-918 at 59, path traversal CWE-22 at 21, out of 333 MCP-related CVEs.

The relevant research finding is that generic SAST is structurally insufficient here. Hasan et al. (arXiv:2506.13538, PEER-REVIEWED, verified 2026-09-17 in the companion document) scanned 1,899 open-source MCP servers and found 7.2% with general vulnerabilities and 5.5% with MCP-specific tool poisoning, across eight vulnerability classes **of which only three overlap with traditional software vulnerabilities**. Five of eight classes are invisible to a conventional scanner by construction. Run Semgrep, and do not report its clean result as a clean server.

---

## 4. The tool description problem

This is the part of the review that has no good answer, and saying so precisely is more useful than pretending otherwise.

### 4.1 Why it resists review

The tool description is simultaneously the documentation a human reads, the specification an LLM acts on, and attacker-controlled input. Invariant Labs demonstrated on 2025-04-01 that instructions embedded in a description are invisible to the user in the clients they tested and fully visible to the model (<https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks>, verified 2026-09-17).

A human reviewer reading a description for injection is doing a task the MCPTox benchmark measured models failing at. From the companion document: across 20 agents on 1,312 malicious cases built from 45 live servers and 353 authentic tools, the **highest refusal rate observed was under 3%**, from Claude-3.7-Sonnet, and more capable models were often more susceptible (arXiv:2508.14925). Nothing establishes that a human reviewer, skimming the fortieth description of the afternoon, does better.

### 4.2 The one mechanical control that exists: hash and diff

The only published, implemented approach is to treat the description as a versioned artifact:

1. **Capture** the full tool list at approval: name, description, and `inputSchema` for every tool.
2. **Hash** it and store the hash with the approval record.
3. **Re-fetch and compare** on a schedule and before each deployment.
4. **Fail closed** on any diff. A changed description is an unapproved server until re-reviewed.

Implemented by mcp-scan via `--storage-file` and its whitelist, described in its own words as detecting "changes to MCP tools via hashing" (section 3.1). This is the mechanism behind SlowMist's three unexplained requirements: "Verify the authenticity and integrity of registered tools", "Check for name conflicts or malicious overwriting before registering", "Verify whether the updated tools contain any malicious descriptions".

**The 2026-07-28 revision makes this materially easier, and this is a genuinely good-news finding for the talk.** From the changelog, major change 1:

> List endpoints (`tools/list`, `resources/list`, `prompts/list`) no longer vary per-connection.

And minor change 3:

> Servers **SHOULD** return tools from `tools/list` in a deterministic order to enable client-side caching and improve LLM prompt cache hit rates.

A list that does not vary by connection and comes back in a deterministic order is a **hashable artifact**. Under the session-based revisions, a server could legitimately return different tools to different connections, so a hash mismatch was ambiguous between "rug pull" and "normal behaviour". Under 2026-07-28 a mismatch means something changed. Source: OFFICIAL, <https://modelcontextprotocol.io/specification/2026-07-28/changelog>, read 2026-09-18.

### 4.3 What hashing does not solve

Four gaps, all real:

1. **A first-look poisoned description passes.** Hashing detects change, not malice. The initial review still has to catch a payload that was there from version one.
2. **A legitimate update is indistinguishable from a malicious one** without re-reading the diff. The control converts a silent compromise into a review queue, which is progress and is not a solution.
3. **Remote servers can serve different content to different callers.** Nothing in the protocol prevents a hosted server from returning a clean list to a scanner's IP and a poisoned one to production. The hash is only as good as the vantage point it was taken from.
4. **Cross-server shadowing needs the whole set, not one server.** Invariant's shadowing attack has server A's description alter the agent's behaviour toward server B. Reviewing each server in isolation cannot see it. The reviewable unit is the **assembled tool set for a given agent**, not the individual server. This is the strongest argument for a gateway that owns the composition.

### 4.4 Allowlisting arguments beats reviewing prose

CVE-2026-47250 is the worked example, verified in the companion document. `kubectl_generic` passed user-supplied flags to `kubectl` with no allowlist, and `--server` plus `--insecure-skip-tls-verify` were reachable, which sent the operator's bearer token to an attacker endpoint. No amount of description review catches that. Reading the `inputSchema` for free-form pass-through parameters does.

**The reviewable question is therefore structural, not literary:** what is the worst thing this tool can be made to do if every string argument is attacker-chosen? That question has an answer a reviewer can actually produce. "Is this description trying to manipulate a model" does not.

---

## 5. Runtime and continuous controls

A one-time review does not survive a server that updates, and the ecosystem updates fast. The companion document's measurement of internet-facing servers found **41.6% disappeared within 72 hours** between consecutive runs (Padilla, arXiv:2608.00150v1, PEER-REVIEWED, verified 2026-09-17). Approval is a statement about a moment.

### 5.1 Version pinning is available and the registry supports it

Registry version metadata is immutable once published (OFFICIAL, registry FAQ, read 2026-09-18). npm, PyPI and OCI all support digest pinning. For a containerised server, pin the image digest rather than the tag; for npm, pin the exact version and verify with `npm audit signatures`; for PyPI, pin and verify the PEP 740 attestation.

**The counter-fact that must be stated alongside it.** Servers cannot currently be deleted or unpublished from the MCP Registry, and removal only sets `status: "deleted"` while metadata stays readable through the API. A pinned, withdrawn, known-malicious version keeps resolving unless the consuming system acts on `status` itself. Pinning without a revocation check is a pin to a known-bad artifact.

### 5.2 The 2026-07-28 revision makes proxy-level gating substantially more practical

This is the most useful technical finding in the document and it belongs in the talk. Source for all of it: OFFICIAL, <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http>, read 2026-09-18.

The transport now mirrors selected body fields into HTTP headers, with the stated purpose that "intermediaries (load balancers, gateways, observability tooling) can route and inspect requests without parsing the body."

| Header | Source field | Required for |
|---|---|---|
| `MCP-Protocol-Version` | `_meta` protocol version | Every POST |
| `Mcp-Method` | `method` | All requests |
| `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` |
| `Mcp-Param-{Name}` | Tool parameters annotated `x-mcp-header` | When the server annotates them |

"These headers are **REQUIRED** for compliance."

The control that makes them trustworthy is header-body validation:

> Servers that process the request body **MUST** reject requests where the values specified in the headers do not match the corresponding values in the request body. This prevents potential security vulnerabilities when different components in the network rely on different sources of truth (e.g., a load balancer routing on the header value while the MCP server executes based on the body value).

Failure returns HTTP 400 with JSON-RPC error `-32020` `HeaderMismatch`.

**Why this matters for admission control.** Before this revision, a gateway wanting to allow `read_file` and deny `execute_sql` had to parse every JSON-RPC body. Now it reads one header. The policy becomes an L7 rule. And `x-mcp-header` lets a server promote a security-relevant argument into a header, so a gateway can enforce on the argument's value: the spec's own example promotes `region` on an `execute_sql` tool, which is exactly a data-residency control expressible at the proxy.

**Two traps the spec names, both worth a sentence on stage.**

First, the spec anticipates downgrade abuse:

> Intermediaries that enforce policy based on mirrored headers (e.g., routing or rate-limiting by tenant) **SHOULD** verify that the `MCP-Protocol-Version` header indicates a version that requires header-body validation. If the version is older or the header is absent, the intermediary **SHOULD** reject the request rather than trusting unvalidated header values.

A gateway that trusts `Mcp-Method` without checking the protocol version can be walked past by a client claiming an older version. **A gateway is only a control if it rejects the legacy path.**

Second, identity in `_meta` is decorative. From the base spec (OFFICIAL, <https://modelcontextprotocol.io/specification/2026-07-28/basic/index>, read 2026-09-18):

> `io.modelcontextprotocol/clientInfo` and `io.modelcontextprotocol/serverInfo` are self-reported by the sender and are not verified by the protocol. They are intended for display, logging, and debugging. Implementations **SHOULD NOT** use them to change the behavior of the client or server, and **SHOULD NOT** rely on them for security decisions.

Any policy keyed on client identity needs a real credential. The protocol tells you in normative language not to use the field that looks like one.

### 5.3 What else 2026-07-28 changes for a reviewer

| Change | Effect on review and gating |
|---|---|
| Stateless core; no `initialize` handshake; no `Mcp-Session-Id` | Every request is independently inspectable and independently deniable. A gateway no longer needs to track session state to make a decision. Session hijacking as a class is replaced by **state handle hijacking**, with the spec requiring servers to verify all inbound requests and **MUST NOT** treat possession of a handle as authentication |
| `server/discover` is a mandatory server RPC | A single call yields supported versions, capabilities and identity. This is a **free intake step**: a scanner can fingerprint a server in one request before running anything |
| Deterministic, connection-invariant `tools/list` | Makes description hashing meaningful. See 4.2 |
| Required `ttlMs` and `cacheScope` on list and read results | `cacheScope: "public"` permits shared intermediaries to cache. A reviewer must confirm a server does not mark user-scoped data `public`, which would be a cross-tenant leak through the gateway's own cache |
| Extensions are opt-in via the `extensions` capability map | Extensions are negotiated, not assumed. If one party does not support an extension the other "**MUST** either revert to core protocol behavior or reject the request". Tasks and MCP Apps are separately advertised and separately deniable at the proxy |
| Sampling, Roots and Logging deprecated (SEP-2577) | Three server-to-client capabilities leave the default surface. Sampling in particular was the "server asks the client's model to generate content" path. Its deprecation shrinks what a reviewer must reason about, over a minimum twelve-month window |
| OAuth Dynamic Client Registration deprecated in favour of Client ID Metadata Documents | DCR is a precondition of the confused-deputy attack (spec: "MCP proxy server allows MCP clients to dynamically register"). Moving off it removes one of the four required conditions |
| `$ref` network dereferencing **MUST** be disabled by default | Closes an SSRF path through tool schemas. An opt-in mode "**MUST** be disabled by default" and **SHOULD** enforce a host allowlist |
| Composition-keyword bounds | Servers **SHOULD** bound schema depth and subschema count so a malicious schema is not a DoS against the validator |

Sources: changelog, versioning page, base spec, security best practices page, all OFFICIAL, all read 2026-09-18.

**The honest net assessment.** 2026-07-28 makes MCP servers easier to **gate** and marginally easier to **review**. It makes nothing about tool-description trust better. Statelessness plus required headers is a genuine gift to anyone building admission control. Deprecating Sampling and DCR removes two attack preconditions. The description remains attacker-controlled input to a model that refuses it under 3% of the time.

### 5.4 Runtime enforcement and revocation

Continuous controls that are implemented today rather than proposed:

- **Interception with policy.** `mcp-scan proxy` with guardrails, blocking on secrets, PII, or custom policies over call and result sequences (OFFICIAL, section 3.1).
- **Admission control at a gateway.** Now expressible on `Mcp-Method` and `Mcp-Name` per 5.2.
- **Change detection.** Re-hash `tools/list` on a schedule; fail closed on diff.
- **Blocklists and private directories.** Anthropic's enterprise controls (OFFICIAL, section 2.3): blocklists, pre-installed approved extensions, private directories.
- **Egress control.** The spec recommends an egress proxy such as Stripe's Smokescreen for server-side MCP client deployments, blocking RFC1918, loopback and link-local ranges including `169.254.0.0/16`, and warns against hand-rolled IP validation because "attackers exploit encoding tricks (octal, hex, IPv4-mapped IPv6) that custom parsers often miss" (OFFICIAL, security best practices, read 2026-09-18).

**What happens when an approved server ships a malicious update.** Following the published record end to end: the MCP Registry will not remove it for having a vulnerability, cannot unpublish it at all, and marks malware with `status: "deleted"` while leaving metadata served. The upstream package registry is where a takedown actually happens; postmark-mcp was unpublished from npm, and its download history became unavailable along with it. Downstream aggregators must poll and act on status themselves; the registry's own guidance expects aggregators to pull "on a regular but infrequent basis (for example, once per hour)".

So the revocation path is: upstream package registry takedown, then aggregator refresh, then your own pin update. **There is no push, no revocation feed, and no signal to a running agent.** An enterprise that wants revocation to work in minutes rather than days has to own the polling and the kill switch itself. That is a concrete, defensible thing to say from the stage.

---

## 6. Internal servers versus third party

**This is the weakest-evidenced section in the document, and the weakness is the finding.** No published internal MCP publishing pipeline from a named organisation was located in this session.

### 6.1 What is genuinely different

Derived from the controls established above rather than from a published source, and labelled as synthesis:

| Dimension | Third-party server | Internal server |
|---|---|---|
| Source access | Often none. Review is of the artifact and the advertised surface | Full. Ordinary code review applies |
| Provenance | Must be verified from outside: npm or PyPI attestation, signed image | Produced by your own CI, so SLSA L2 or L3 is achievable directly |
| Tool description authorship | Attacker-controlled by assumption | Authored by a colleague, still reviewable as a text artifact and still capable of being wrong |
| Change control | Detect after the fact by hashing | Gate before merge in CI |
| Identity and lifecycle | Namespace proof only. No ownership record beyond a domain or GitHub account | Assignable to a team, with the ordinary consequences when nobody owns it |
| Revocation | Poll an upstream registry and hope | Your own deploy pipeline, immediate |

The asymmetry worth naming: for internal servers every control in this document moves **left**, from detection to prevention. Description hashing becomes a CI check that diffs `tools/list` against the committed manifest on every pull request. Provenance becomes a build-pipeline property rather than something to verify. Argument allowlisting becomes a code review comment.

An internal server is not automatically safer. It is subject to controls at a point where they are cheaper and more reliable.

### 6.2 What the published record actually contains

- **Block.** PRACTITIONER. "They built over 100 internal MCP servers bundled by default instead of making people hunt for external ones" (<https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions>, read 2026-09-18). Block's own engineering playbook (<https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers>, read 2026-09-18) covers workflow-first design, token budgets and authentication. **Neither describes a review gate, an approval workflow, a publishing pipeline, or an ownership model.** The closest governance content is end-user permissions in Goose: "Always Allow", "Allow Once", "Denied".

  The interesting and quotable fact is the strategy rather than the process. Bundling 100+ internal servers by default is itself a vetting decision: it makes the curated set the path of least resistance. That is admission control implemented as developer experience, and it is the only at-scale approach in the published record.

- **Microsoft.** PRACTITIONER. The Learn MCP server engineering post describes architecture, three tools, and six operational lessons, and contains **no internal review, security gate, or approval process**. Its only governance-adjacent content points outward, to tool-space-interference research and to MCP Interviewer.

- **Anthropic.** OFFICIAL. Enterprise blocklists, pre-installed approved extensions, private extension directories (section 2.3). These are the mechanisms for running a private directory. No account of anyone operating one.

### 6.3 What happens when the author leaves

**No published guidance exists on MCP server ownership lifecycle.** Not from the MCP project, not from any of the practitioner accounts read. The registry's namespace model actively complicates it: a server published under `io.github.alice/*` is bound to Alice's personal GitHub account, and an organisation namespace requires the org, so a server published under an individual's namespace has no transfer path short of republishing under a new name. Combined with the inability to unpublish, an abandoned server stays listed, stays resolvable, and stays attributable to someone who has left.

This is a real, concrete, unaddressed gap and it is worth thirty seconds from the stage.

---

## 7. A concrete review checklist, with every criterion attributed

Assembled from the sources above. This is a **synthesis**: no single published source contains it, and it is presented as my own assembly per source-fidelity discipline. Each row cites the source that establishes the criterion, and rows marked SYNTHESIS are derived rather than quoted.

### Gate 0: Intake, automatable, no human time

| # | Criterion | Source and class |
|---|---|---|
| 0.1 | Call `server/discover`. Record supported protocol versions, capabilities, declared extensions, self-reported identity. Reject anything that cannot answer | OFFICIAL, spec 2026-07-28 versioning: servers **MUST** implement `server/discover` |
| 0.2 | Run MCP Interviewer with `--fail-on-warnings`. Reject on constraint violations, malformed schemas, tool-count breaches | OFFICIAL, <https://github.com/microsoft/mcp-interviewer> |
| 0.3 | Run mcp-scan (Snyk Agent Scan) static scan. Reject on tool poisoning, cross-origin escalation, or toxic flow findings | OFFICIAL, mcp-scan README |
| 0.4 | Run ordinary SAST over source where available. Do **not** treat a clean result as a clean server | PEER-REVIEWED, Hasan et al. arXiv:2506.13538: five of eight MCP vulnerability classes do not overlap traditional ones |
| 0.5 | Execute every step of intake in an isolated container. Scanning a stdio server means running it | OFFICIAL, MCP Interviewer guidance; MCP SECURITY.md, "the SDK's stdio transport is not a sandbox" |

### Gate 1: Provenance and identity

| # | Criterion | Source and class |
|---|---|---|
| 1.1 | Verify the registry namespace proof matches the vendor you believe you are dealing with: GitHub account, or DNS TXT `v=MCPv1; k=...; p=...`, or the `/.well-known/mcp-registry-auth` file | OFFICIAL, MCP Registry authentication guide |
| 1.2 | Verify build provenance at the package registry: `npm audit signatures`, or the PyPI PEP 740 attestation, or a Docker-built signed image | OFFICIAL, npm and PyPI docs |
| 1.3 | Record the SLSA build level achieved. Require L2 or better for anything touching production credentials | OFFICIAL, <https://slsa.dev/spec/v1.1/levels> |
| 1.4 | Do **not** record provenance as a safety finding. "provenance does not guarantee the package has no malicious code" | OFFICIAL, npm docs, verbatim |
| 1.5 | Obtain an SBOM. Docker-built catalog images carry one; otherwise require one | OFFICIAL, Docker MCP Catalog; OWASP LLM03:2025 |
| 1.6 | Confirm the license permits use. Docker's own bar: "MIT or Apache 2 are great, GPL is not" | OFFICIAL, Docker mcp-registry CONTRIBUTING.md |
| 1.7 | Confirm the repository the listing points at exists and matches the artifact | VENDOR, Wiz: ~100 of 3,500 glama.ai listings pointed at non-existent repositories |

### Gate 2: Capability and blast radius, the part that repays human attention

| # | Criterion | Source and class |
|---|---|---|
| 2.1 | For every tool, read the `inputSchema` and ask: what is the worst outcome if every string argument is attacker-chosen? | SYNTHESIS, from CVE-2026-47250 (`kubectl_generic` flag pass-through) |
| 2.2 | Reject free-form pass-through to a CLI or shell. Require an argument allowlist, not a blocklist | OFFICIAL, GHSA-6mx4-4h42-r8vh; SlowMist "strictly validate all inputs from clients" (High) |
| 2.3 | Enumerate the credentials the server requires from `server.json` env vars, including which are marked secret. Reject any credential that bypasses row-level or tenant isolation | OFFICIAL, server.json reference; worked example: the Supabase `service_role` leak |
| 2.4 | Require least-privilege scopes. Reject `*`, `all`, `full-access`, or a server that publishes its entire catalogue in `scopes_supported` | OFFICIAL, spec security best practices, "Common Mistakes" |
| 2.5 | Confirm the server does not accept tokens issued for anything else. "MCP servers **MUST NOT** accept any tokens that were not explicitly issued for the MCP server" | OFFICIAL, spec, normative |
| 2.6 | Confirm state handles are non-deterministic and bound server-side to the authenticated user, keyed as `<user_id>:<handle>`. Possession of a handle **MUST NOT** be treated as authentication | OFFICIAL, spec 2026-07-28, State Handle Hijacking |
| 2.7 | If the server proxies a third-party API: confirm per-client consent stored server-side and checked **before** the third-party flow, exact-string `redirect_uri` matching with no wildcards, and single-use `state` stored only after consent approval | OFFICIAL, spec confused deputy section, all **MUST** |
| 2.8 | Confirm `cacheScope` is never `"public"` on user-scoped data | OFFICIAL, SEP-2549. SYNTHESIS for the leak conclusion |
| 2.9 | Confirm the server binds loopback when local, validates `Origin`, and has DNS rebinding protection enabled | OFFICIAL, Streamable HTTP transport: servers **MUST** validate `Origin`, 403 on invalid |
| 2.10 | Confirm no schema uses a network `$ref`, and that the client will not dereference one | OFFICIAL, spec: implementations **MUST NOT** automatically dereference network `$ref`s |

### Gate 3: Tool descriptions

| # | Criterion | Source and class |
|---|---|---|
| 3.1 | Human-read every tool description for embedded instructions. Record that this is a weak control and do not rely on it alone | PEER-REVIEWED, MCPTox arXiv:2508.14925: best observed refusal rate under 3% |
| 3.2 | Hash the complete `tools/list` output, names, descriptions and schemas, and store the hash with the approval record | OFFICIAL, mcp-scan: "detects changes to MCP tools via hashing", `--storage-file` |
| 3.3 | Review the **assembled tool set** for the target agent, not each server alone, to catch cross-server shadowing | OFFICIAL (Invariant disclosure) for the attack; SYNTHESIS for the review-unit conclusion |
| 3.4 | Check for tool name collisions with already-approved servers | PRACTITIONER, SlowMist: "Check for name conflicts or malicious overwriting before registering" (High) |
| 3.5 | Capture the hash from the same network vantage point production will use. A remote server can serve different content to different callers | SYNTHESIS |

### Gate 4: Continuous, because approval is a statement about a moment

| # | Criterion | Source and class |
|---|---|---|
| 4.1 | Pin an exact version or image digest. Registry version metadata is immutable, so a pin is meaningful | OFFICIAL, MCP Registry FAQ |
| 4.2 | Re-fetch and re-hash `tools/list` on a schedule and before every deployment. Fail closed on any diff; a changed description is an unapproved server | OFFICIAL (mechanism), SYNTHESIS (fail-closed policy) |
| 4.3 | Poll the upstream package registry for takedown and the MCP Registry for `status: "deleted"`. Do not assume a signal will reach you | OFFICIAL, moderation policy: status is set, metadata stays served; FAQ: no unpublish |
| 4.4 | Enforce admission control at a gateway on `Mcp-Method` and `Mcp-Name` | OFFICIAL, Streamable HTTP: headers are "REQUIRED for compliance" |
| 4.5 | Make the gateway reject requests whose `MCP-Protocol-Version` predates header-body validation, rather than trusting unvalidated headers | OFFICIAL, spec note to intermediaries, verbatim |
| 4.6 | Never key a policy decision on `clientInfo` or `serverInfo`. They are self-reported and the spec says **SHOULD NOT** rely on them for security decisions | OFFICIAL, spec base page |
| 4.7 | Run an egress proxy that blocks RFC1918, loopback and link-local including `169.254.0.0/16`. Do not hand-roll IP validation | OFFICIAL, spec SSRF mitigation, names Smokescreen |
| 4.8 | Log every tool invocation with the W3C trace context propagated in `_meta` | OFFICIAL, SEP-414; SlowMist "Log all service activities and security events" (High) |
| 4.9 | Set a re-review trigger: any version change, any description hash change, any new capability or extension advertised, any scope change | SYNTHESIS |

### Gate 5: Internal servers, additional

| # | Criterion | Source and class |
|---|---|---|
| 5.1 | CI diffs `tools/list` against a committed manifest on every pull request, so 4.2 becomes prevention rather than detection | SYNTHESIS |
| 5.2 | Build at SLSA L2 minimum, L3 for anything with production credentials | OFFICIAL, SLSA levels |
| 5.3 | Publish under an **organisation** namespace, never an individual's `io.github.<person>`, because there is no transfer path and no unpublish | OFFICIAL, registry authentication and FAQ; SYNTHESIS for the conclusion |
| 5.4 | Record a named owning team, and a review trigger on owner departure | SYNTHESIS. No published guidance exists on this |
| 5.5 | Bundle the approved internal set by default so the curated path is the easy path | PRACTITIONER, Block: 100+ internal servers bundled by default |

---

## 8. What organisations actually do: the evidence is close to absent, and that is the finding

Stated plainly, because an audience that stewards MCP will know it and will respect it being said.

**What was searched.** The MCP project's own documentation and specification repository, the MCP Registry documentation set, Docker's catalog and contributing guides, Anthropic's extension and connector documentation, OWASP GenAI and the Agentic Security Initiative, NIST CSRC, Cloud Security Alliance, the practitioner engineering blogs of Block and Microsoft, and the vendor security literature from Wiz and Palo Alto Networks.

**What was found, in full:**

| Organisation | What is published | What is not |
|---|---|---|
| Docker | A real human review gate, a license bar, a CI requirement, signing, provenance and SBOM on Docker-built images | The security criteria the review applies |
| Anthropic | A submission form, cross-platform test requirement, review for "quality and security", enterprise blocklists and private directories | Any criteria, any audit procedure, any re-review trigger |
| MCP Registry | Cryptographic namespace ownership proof, a moderation policy | Security review of any kind, stated as a deliberate delegation |
| Block | 100+ internal servers bundled by default; a server design playbook | Any review, approval, catalogue, or ownership process |
| Microsoft | An engineering account of one server; MCP Interviewer as a public tool | Any internal approval process for that server |

**Nobody has published their MCP server review checklist.** Not a bank, not a hyperscaler, not a government. Not one named organisation has written down the criteria it applies before approving a third-party MCP server for production.

**What that absence means, and what it does not.** It does not mean nobody is doing this. Enterprises rarely publish control documents, and the tooling vendors selling MCP gateways plainly have customers. It does mean that a team standing up this process in 2026 has no worked example to copy, no peer benchmark to measure against, and no regulator-recognised baseline to point at. Every organisation is deriving the same checklist independently from the same primary sources, which is the condition a foundation exists to fix.

**The ask that follows.** The MCP Registry's own documentation names the gap and assigns it: security scanning belongs to "downstream aggregators", and moderation belongs to "subregistries". Those layers have been designated and, on the published record, largely not built. A vetting profile, a machine-readable review attestation attached to a `server.json`, and a revocation feed are three artifacts that do not exist and that only a steward can credibly create. The talk can make that ask specifically, to a room that could act on it.

---

## 9. Claims held back

Not to be spoken as fact:

- **Specific OWASP ASI threat identifiers or control names.** Both relevant documents are PDFs behind landing pages and were not retrieved. Titles and dates are verified; contents are not.
- **Specific NIST SP 800-218A practice identifiers.** Only the landing page was read.
- **Any Semgrep or CodeQL MCP-specific ruleset.** The Semgrep URL tried returned 404. No ruleset confirmed.
- **MCPSafetyScanner detection rates.** The abstract publishes none and the full paper was not read.
- **Whether mcp-scan still transmits tool descriptions to a third party under Snyk.** The pre-acquisition README said it did for static scanning. Current behaviour unconfirmed.
- **Anthropic's connectors directory review criteria.** The support article returned 404 on 2026-09-18.
- **CSA MCP-specific guidance.** None located. Claim absence, not existence.
- **Any named enterprise's internal MCP vetting process.** None found. This is stated as a finding in section 8, not hedged into a claim that one exists.

---

## 10. Research provenance

All fetched 2026-09-18 unless noted.

- modelcontextprotocol.io: `llms.txt`, `/registry/about`, `/registry/authentication`, `/registry/moderation-policy`, `/registry/faq`, `/community/security`, `/docs/2026-07-28/tutorials/security/security_best_practices`, `/specification/2026-07-28/changelog`, `/specification/2026-07-28/basic/index`, `/specification/2026-07-28/basic/versioning`, `/specification/2026-07-28/basic/transports/streamable-http`
- GitHub raw: `modelcontextprotocol/modelcontextprotocol/SECURITY.md`, `modelcontextprotocol/registry` server.json reference, `docker/mcp-registry/CONTRIBUTING.md`, `invariantlabs-ai/mcp-scan` README at tag `v0.3.0` and at `main`
- docs.docker.com MCP catalog; docs.npmjs.com provenance; docs.pypi.org attestations; slsa.dev v1.1 levels
- genai.owasp.org LLM03:2025, ASI landing pages; csrc.nist.gov SP 800-218A landing page; cloudsecurityalliance.org MAESTRO/A2A
- github.com/microsoft/mcp-interviewer; github.com/slowmist/MCP-Security-Checklist; arxiv.org/abs/2504.03767
- engineering.block.xyz playbook; allthingsopen.org Block scale article; devblogs.microsoft.com Learn MCP server
- wiz.io MCP security research briefing; paloaltonetworks.com MCP security overview
- Cross-referenced against `06-research-and-source-ledger/security/mcp-security-failures-2026-09.md`, verified 2026-09-17

This session used WebFetch only; the WebSearch budget was exhausted before it began. Every URL was seeded from the existing corpus or from `modelcontextprotocol.io/llms.txt` and followed outward.
