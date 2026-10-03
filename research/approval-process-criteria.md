
# What an enterprise MCP server approval process actually evaluates

## Question

When an organization decides whether to allow an MCP server, what does it
evaluate? Specifically: is the vendor known and is there a relationship; what
is the business need and is it core; how well built and wrapped is the server;
does it support the 2026-07-28 revision; does it carry authorization; is the
vendor itself compliant (SOC 2, ISO 27001). Who has published criteria, and
are the keynote's criteria in line with them?

## Summary

the keynote's six criteria are the standard shape of a third-party risk review
applied to MCP, and each one appears in at least one published source. Nobody
publishes a single rubric that covers all six: the vendor and business-need
questions come from third-party risk management practice and from one gateway
vendor's guide, while the technical questions (spec revision, authorization,
token handling, tool design) come from a CISO question list keyed to 2026-07-28
and from Anthropic's own connector review criteria. The one thing no published
source does is weigh business need; every public checklist assumes the request
is already justified.

## Surprises and gotchas

- **Anthropic now publishes its review criteria.** The September 2026 research
  for the keynote found the connector review article returning 404 and recorded
  Anthropic's criteria as unpublished. As of 2026-10-03, claude.com carries a
  pre-submission checklist and review criteria page. The keynote's older claim
  that "no named organization has published the criteria it reviews against"
  is no longer true for Anthropic's directory, and should not be said on
  stage. (It remains true that no enterprise has published the criteria it uses
  for its own internal approvals.)
- **Anthropic rejects a single tool that mixes read and write.** "A single tool
  that accepts both safe HTTP methods ... and unsafe methods ... is rejected."
  That is the Block principle (one tool, one risk level) now enforced by a
  directory reviewer, which makes it a checkable criterion rather than advice.
- **The spec revision question is first on the CISO list and is testable
  without the vendor.** SSOJet's twelve questions open with "Which MCP
  specification revision do you implement?" and the authors note that
  authorization-server discovery, audience validation and client registration
  can be probed externally.
- **Anthropic's own process is mostly automated.** A submission is scanned
  automatically and listed as Community by default; only listings flagged as
  highly useful get a human Verified review. The label "doesn't change how your
  connector runs." A Community listing is therefore not evidence of a human
  security review.
- **No source weighs business need or "core to our business."** That criterion
  is standard in third-party risk management and in the keynote's process, and it
  is absent from every MCP-specific checklist found.

## Findings

### Who publishes what, as of 2026-10-03

| Source | Kind | What it evaluates | Vendor relationship | Business need | Spec revision | Authorization | Vendor compliance |
|---|---|---|---|---|---|---|---|
| Anthropic, connector review criteria and submission requirements (claude.com docs, read 2026-10-03) | Platform operator, binding on its directory | Read/write tool separation, `title` and `readOnlyHint`/`destructiveHint` on every tool, narrow accurate descriptions, no prompt-injection patterns, functional test of every tool, first-party API ownership, OAuth 2.0 for authenticated services, privacy policy, public docs, seven policy acknowledgments | Company name and primary contact; API must be first-party or legitimately proxied | No | Not stated | OAuth 2.0 required; DCR, client ID metadata documents, or Anthropic-held credentials | No |
| SSOJet, "12 Questions a CISO Will Ask About Your MCP Server" (Apr 30, 2026, updated Sep 2, 2026) | Vendor blog, identity vendor | Spec revision, authorization server discovery, client registration, PKCE, audience validation, token passthrough, agent vs human identity, scopes, human in the loop, audit trail, token lifetimes and revocation, incident response. Scored 0 to 2 each; 20 to 24 proceeds, 8 to 13 "not ready" | No | No | Yes, keyed to 2026-07-28 | Yes, in detail | No |
| MintMCP, "MCP Server Security and Vetting" (May 20, 2026) | Vendor blog, gateway vendor | Authentication method (prefer OAuth), vendor reputation (official vs community), compliance documentation ("SOC 2 Type II audited status, not marketing claims"), data handling (processing locations, retention, encryption), provenance and maintainer reputation, dependency update frequency. Tiers: Gold (fully vetted enterprise vendor), Silver (community server with verified practices), Bronze (sandbox only) | Yes | No | No | Yes | Yes, SOC 2 Type II |
| Cerbos, "MCP Server Vetting Checklist for Enterprises" (Aug 16, 2026) | Vendor blog, authorization vendor | Inventory with a named owner per server, dedicated scoped credentials, tool-surface review including descriptions, external authorization on agent, user, tool and arguments, downstream data reach, audit evidence, lifecycle and revocation | No | No | No | Yes | No |
| Cloudflare, MCP governance docs (read 2026-10-03) | Platform operator | Centralized portal; policy on identity (who), conditions (device posture), scope (which tools); logging of all requests; prefer remote over local servers; "shadow MCP" is employees running unmanaged local servers | No | No | No | Via portal identity | No |
| SlowMist MCP Security Checklist (prior research) | Security firm | Technical controls, High/Medium priority | No | No | No | Partial | No |
| MCP project SECURITY.md, Security Interest Group, registry moderation policy (prior research) | Steward | None. "Users and administrators are responsible for server selection." | n/a | n/a | n/a | n/a | n/a |

### the keynote's criteria against the published record

| Criterion | Published support | Verdict |
|---|---|---|
| Known vendor, existing relationship | MintMCP vendor reputation and official-vs-community tiering; Anthropic requires company identity and first-party API ownership | Standard; in line |
| Business need, core to the business | None of the MCP sources; this is ordinary third-party risk management intake | Reasonable; no MCP-specific source to cite, and it is the gate that stops "everyone wants Canva" |
| Server quality and how it is wrapped | Anthropic functional test, read/write split, narrow descriptions; Cerbos tool surface; SSOJet Q6 token passthrough (a wrapper must exchange tokens, never forward the user's) | In line; the wrapper's token handling is the concrete test |
| Supports 2026-07-28 | SSOJet Q1, with Q2 to Q5 testable externally | In line; one of the few criteria a reviewer can verify without the vendor |
| Carries authorization | Anthropic OAuth 2.0 requirement; SSOJet Q2 to Q8; Cerbos external authorization; Zhou et al. measured 40.6 percent of live servers with no authentication (prior research) | In line; the measured base rate justifies making it a hard gate |
| Vendor compliant (SOC 2, ISO 27001) | MintMCP "SOC 2 Type II audited status, not marketing claims" | In line for the vendor; note it says nothing about the server |

### What a slide-sized version looks like

Three gates, in the order a request moves through them, each with the question
asked and who answers it:

1. **Vendor gate** (procurement answers): do we know them, do we have a
   contract, are they SOC 2 Type II or ISO 27001 audited.
2. **Need gate** (the business answers): what job does this do, is it core,
   what is the cost of no (the workaround the user will build instead).
3. **Server gate** (the platform team answers, mostly by test): speaks
   2026-07-28; OAuth with audience checks and no token passthrough; one risk
   level per tool with annotations; descriptions carry no instructions; wrapped
   where it falls short, with an exchanged token; a named owner and a
   revocation path.

The third gate is the one a reviewer can verify. The first two are judgment.

## Recommendation

Use the keynote's six criteria as the process; they are in line with the published
record and more complete than any single source. On the slide, show them as
three gates with the questions, not as the five abstract rollout items. Cite
Anthropic's connector review criteria for the tool-design tests and the
SSOJet question list for the spec and authorization tests, and say plainly
that the business-need gate has no published MCP source because it is ordinary
vendor risk practice.

Retire the "no named organization has published its review criteria" line
wherever it survives in the keynote material; Anthropic has.

## Caveats

- Three of the five MCP-specific sources are vendor blogs (SSOJet, MintMCP,
  Cerbos) and each sells the control it recommends. Their criteria lists are
  usable; their framing is marketing.
- Anthropic's criteria govern its public directory, not an enterprise's
  internal approvals, and its default review is automated.
- No standards body (NIST, ISO, CSA, OWASP) has published an MCP server
  approval checklist as of this date; the prior research's finding stands.
- The claim that Anthropic's connectors review article returned 404 on
  2026-09-18 and is live on 2026-10-03 reflects two reads on two dates; the
  page may have moved rather than been newly published.
- Searched: enterprise MCP approval checklists, third-party risk and MCP,
  Cloudflare governance, GitHub Copilot and VS Code allowlists, Anthropic
  directory requirements. Not searched: Gartner or Forrester vendor assessment
  guidance, ISO 42001 mappings, bank or government procurement standards.

## Sources

- [Anthropic, Submit a connector to the directory](https://claude.com/docs/connectors/building/submission.md): submission requirements, authentication modes, compliance acknowledgments, Community vs Verified
- [Anthropic, Connector pre-submission checklist and review criteria](https://claude.com/docs/connectors/building/review-criteria): read/write split, annotations, prompt-injection patterns, functional test, API ownership
- [SSOJet, 12 Questions a CISO Will Ask About Your MCP Server](https://ssojet.com/blog/ciso-mcp-server-security-questions): spec revision and authorization questions with a scoring rubric, keyed to 2026-07-28
- [MintMCP, MCP Server Security and Vetting](https://www.mintmcp.com/blog/mcp-server-security-vetting): vendor reputation, SOC 2 Type II, data handling, gold/silver/bronze tiers
- [Cerbos, MCP Server Vetting Checklist for Enterprises](https://www.cerbos.dev/blog/mcp-server-vetting-checklist): inventory, ownership, authorization, audit, revocation
- [Cloudflare, MCP governance](https://developers.cloudflare.com/agents/model-context-protocol/governance): portal-based approval, shadow MCP
- [GitHub, Configure the enterprise MCP allowlist](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-mcp-usage/configure-enterprise-allowlist): how an approved list is enforced on the client
- Prior research for the keynote (2026-09-18): steward positions, SlowMist checklist, Docker catalog, scanning tools
