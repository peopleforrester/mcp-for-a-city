<!--
ABOUTME: Claim-by-claim source ledger for the MCP approval-process criteria behind the keynote's gate slides.
ABOUTME: Every row names the claim, the source, how it was read, the date, and whether the wording is quotation or paraphrase.
-->

# MCP approval process: source ledger

Companion to [approval-process-criteria.md](approval-process-criteria.md).
Built 2026-10-03 for the keynote's gate slides and for this repo.

"How read" says what actually came back: **full text** means the page body was
fetched and read; **fetched summary** means a tool returned a summary of the
page, so wording is paraphrase unless marked as a quote; **search result** means
only the search engine's excerpt was seen; **prior research** means the claim
comes from the September 2026 research for the keynote (read 2026-09-18) and was
not re-opened today.

## A. The six criteria, each against its source

| # | Criterion | Claim | Source | How read | Date | Quote or paraphrase |
|---|---|---|---|---|---|---|
| A1 | Known vendor, relationship | A vetting guide distinguishes official vendor servers from community-built ones and tiers them Gold (fully vetted enterprise vendors), Silver (community servers with verified security practices), Bronze (experimental, sandboxed only) | MintMCP, "MCP Server Security and Vetting: A 2026 Guide for Enterprise Platform Teams", https://www.mintmcp.com/blog/mcp-server-security-vetting, published 2026-05-20 | fetched summary | 2026-10-03 | Paraphrase; tier names as given |
| A2 | Known vendor, relationship | Anthropic's directory submission asks for company name, website and a primary contact, and requires the server to call "your own first-party APIs, or APIs you legitimately proxy" with a server domain that matches the service | Anthropic, "Connector pre-submission checklist", https://claude.com/docs/connectors/building/review-criteria | full text | 2026-10-03 | Quote |
| A3 | Business need, core to the business | None of the MCP-specific sources read today evaluates business need; the criterion comes from ordinary third-party risk intake | Absence across A1, A2, A4 to A9 | n/a | 2026-10-03 | Finding of absence; scope is the sources read, not the world |
| A4 | Server quality and wrapping | A single tool that accepts both safe and unsafe HTTP methods "is rejected"; reviewers run "a functional test of each tool"; every tool "must return a successful response when called with valid parameters" | Anthropic review criteria (as A2) | full text | 2026-10-03 | Quote |
| A5 | Server quality and wrapping | A wrapper must not forward the user's token upstream: the CISO list asks "Does your MCP server ever forward the client's token upstream?" | SSOJet, "12 Questions a CISO Will Ask About Your MCP Server (2026-07-28 Spec)", https://ssojet.com/blog/ciso-mcp-server-security-questions, published 2026-04-30, updated 2026-09-02 | fetched summary | 2026-10-03 | Question wording as returned; treat as near-quote |
| A6 | Server quality and wrapping | The spec forbids token passthrough: "The MCP server MUST NOT pass through the token it received from the MCP client" | MCP specification 2026-07-28, authorization security considerations, https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations | prior research (quoted in the 2026-10-02 review of the architecture slide); not opened today | 2026-10-02 | Quote via secondary; re-open before putting on a slide |
| A7 | Supports 2026-07-28 | The first CISO question is "Which MCP specification revision do you implement?", and the authors say authorization-server discovery, audience validation and client registration can be tested externally without the vendor | SSOJet (as A5) | fetched summary | 2026-10-03 | Paraphrase |
| A8 | Has authorization | Anthropic requires "OAuth 2.0 for authenticated services"; supported modes are OAuth with dynamic client registration, client ID metadata documents, or Anthropic-held client credentials | Anthropic, "Submit a connector to the directory", https://claude.com/docs/connectors/building/submission.md | full text | 2026-10-03 | Quote |
| A9 | Has authorization | External authorization should consider "the agent, the user it acts for, the tool, and the arguments" | Cerbos, "MCP Server Vetting Checklist for Enterprises", https://www.cerbos.dev/blog/mcp-server-vetting-checklist, published 2026-08-16 | fetched summary | 2026-10-03 | Quote as returned |
| A10 | Has authorization | 40.55 percent of 7,973 live remote MCP servers expose tools with no authentication | Zhou et al., arXiv 2605.22333 | prior research; abstract confirmed in the 2026-10-02 ledger | 2026-10-02 | Figure |
| A11 | Vendor compliant | Verify "SOC 2 Type II audited status, not marketing claims"; also documented processing locations, retention policies, encryption | MintMCP (as A1) | fetched summary | 2026-10-03 | Quote as returned |

## B. Claims about who publishes criteria

| # | Claim | Source | How read | Date | Note |
|---|---|---|---|---|---|
| B1 | Anthropic publishes connector review criteria and submission requirements | A2, A8 | full text | 2026-10-03 | Supersedes the 2026-09-18 finding that the review article returned 404 |
| B2 | Anthropic's default review is automated: submissions are scanned "automatically for policy compliance" and listed as Community "with no action from you"; Verified review is escalated automatically and "higher touch and slower" | Anthropic submission page and review criteria (A8, A2) | full text | 2026-10-03 | Quote |
| B3 | The Verified label "doesn't change how your connector runs once connected" | Anthropic review criteria (A2) | full text | 2026-10-03 | Quote |
| B4 | A connector submission carries "Seven policy acknowledgments covering the directory guidelines, first-party API usage, financial transactions, AI media generation, prompt injection, conversation data collection, and public documentation" | Anthropic submission page (A8) | full text | 2026-10-03 | Quote |
| B5 | Cloudflare's governance model is a portal with policy on identity, device conditions and tool scope, and "shadow MCP" means "employees run unmanaged local MCP servers against sensitive internal resources" | Cloudflare, MCP governance, https://developers.cloudflare.com/agents/model-context-protocol/governance | fetched summary | 2026-10-03 | Quote as returned |
| B6 | GitHub Copilot enforces an enterprise MCP allowlist through managed settings, matching by name, URL or command | GitHub Docs, https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-mcp-usage/configure-enterprise-allowlist | search result | 2026-10-03 | Not opened; cite only as "GitHub documents an allowlist" |
| B7 | The MCP project publishes no server review criteria: "Users and administrators are responsible for server selection" | MCP SECURITY.md | prior research | 2026-09-18 | Quote, already on a slide |
| B8 | No standards body (NIST, ISO, CSA, OWASP) has published an MCP server approval checklist | prior research, the September vetting research | prior research | 2026-09-18 | Not re-checked today; say "as of September" or re-verify |
| B9 | The most complete public technical checklist is SlowMist's, from a blockchain security firm | https://github.com/slowmist/MCP-Security-Checklist | prior research | 2026-09-18 | Not re-opened today |

## C. What the slide may say, and what it may not

Safe to put on a slide today, with the source in the notes or on the sources slide:
- The three-gate structure (A1 to A11 together).
- "Anthropic rejects a single tool that mixes read and write" (A4).
- "Which revision do you implement?" as the first server-gate question (A7).
- "OAuth, audience-checked, no token passthrough" (A5, A8; A6 after re-opening the spec page).
- The 40.55 percent base rate (A10).

Not safe without more work:
- Any statement that no one publishes review criteria (B1 contradicts it).
- Any claim about what standards bodies have or have not published, unless phrased "as of September" (B8).
- Quoting SSOJet, MintMCP or Cerbos verbatim; their text came back as summaries (A1, A5, A7, A9, A11). Re-open the pages if a quotation is wanted.

## D. For the landing repo

Every row above has a URL and a read date. Rows marked "fetched summary" or
"search result" are re-read to full text before anything is quoted.

## E. "Why we wrapped them" slide, verified 2026-10-03

| # | Claim on the slide or in its notes | Source | How read | Result |
|---|---|---|---|---|
| E1 | FastMCP does it in one call: `create_proxy()` | https://gofastmcp.com/servers/proxy.md (documents FastMCP 4.x); PyPI: latest 4.0.10, released 2026-09-25 | full text; PyPI JSON | Holds. The slide said "FastMCP"; now "FastMCP 4". The earlier spike cited the v3 page; the API is unchanged in 4.x |
| E2 | ToolHive `MCPRemoteProxy`: OIDC, Cedar, token exchange, audit, tool filtering | https://docs.stacklok.com/toolhive/reference/crds/mcpremoteproxy | fetched summary | Holds |
| E3 | Envoy AI Gateway aggregates, filters tools, enforces OAuth, injects upstream keys | https://aigateway.envoyproxy.io/docs/0.4/capabilities/mcp/ redirects (301) to https://theagentrouter.ai/docs/0.4/capabilities/mcp/, which says "Formerly Envoy AI Gateway — now an Agentic AI Foundation project" | fetched summary after redirect | Holds for the capabilities; the name was stale. Slide and notes now say Agent Router, formerly Envoy AI Gateway |
| E4 | TBXark mcp-proxy: one endpoint, many upstreams, OAuth client support | https://github.com/TBXark/mcp-proxy README via GitHub API; 734 stars, pushed 2026-09-15 | full README text | Holds |
| E5 | mcpwrapped: tool filtering only | https://github.com/VitoLin/mcpwrapped README via GitHub API; last pushed 2026-01-22 | full README text | Holds; note it is a small, quiet project |
| E6 | The spec forbids forwarding the client's token | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations: "The MCP server **MUST NOT** pass through the token it received from the MCP client." Also: proxy servers using static client IDs "**MUST** obtain user consent for each dynamically registered client" | full text | Holds, verbatim |
| E7 | Confused deputy found in production at real companies | Obsidian Security, published 2026-01-29, updated 2026-09-07: Square (mcp.squareup.com) and Wix; "one shared static client_id"; reported July to August 2025, "fixed by vendors in late September" | fetched summary | Holds; notes now name the vendors and say it was fixed |
| E8 | 40 percent of nearly 8,000 live servers have no authentication | arXiv 2605.22333 abstract: "7,973 live remote MCP servers", "40.55% expose tools without authentication"; Zhou, Zhang, Zhang, Zhang, Zhang, Yang; submitted 2026-05-21 | full abstract | Holds |
| E9 | Anthropic's rule: a tool does not do both reads and writes | https://claude.com/docs/connectors/building/review-criteria: a single tool accepting both safe and unsafe HTTP methods "is rejected" | full text (read earlier today) | Holds |
