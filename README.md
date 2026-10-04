# MCP for a City

The resources behind **Governing MCP for a Workforce the Size of a City**, the
keynote Michael Rishi Forrester gave at MCP Dev Summit Toronto on Tuesday
6 October 2026. The talk is fifteen minutes on what happens when governance
meets people who route around a no. Its thesis fits in one line: if you do not
give them MCP servers, they build their own.

The interactive version lives at **[mcp.michaelrishiforrester.com](https://mcp.michaelrishiforrester.com/)**,
where you can walk an MCP server through the six approval gates and take the
checklist with you.

## What is here

| Path | What |
|---|---|
| [slides/governing-mcp-toronto-2026.pdf](slides/governing-mcp-toronto-2026.pdf) | The deck as delivered, exported 2026-10-03 |
| [script/keynote-spoken.md](script/keynote-spoken.md) | The spoken script, slide by slide, from the speaker notes |
| [gates/approval-gates.md](gates/approval-gates.md) | The six approval gates as a checklist a platform team can use |
| [diagrams/architecture.png](diagrams/architecture.png) | The enterprise architecture diagram, with its [Mermaid source](diagrams/architecture.mmd) |
| [research/approval-process-criteria.md](research/approval-process-criteria.md) | What an enterprise MCP approval process evaluates, against the published record |
| [research/wrapping-mcp-servers.md](research/wrapping-mcp-servers.md) | Wrapping an MCP server inside an MCP server: how, why, and the one test |
| [research/source-ledger.md](research/source-ledger.md) | Every claim on the gate and wrapping slides, its source, how it was read, and the date |
| [sources/sources.md](sources/sources.md) | The sources slide |
| [art/](art/) | The shadow-play scenes, the ship outlines, the cable sketches, the attack scenes. See the note below |
| [film/](film/) | The shadow-play film: the narrated cut and the captions-only cut, as release links |
| [qr/mcp-site-qr.png](qr/mcp-site-qr.png) | The QR code from the closing slides, pointing at the site |

Every figure in the talk has a source; the ledger is where they are checked
claim by claim. Specification facts are stated against the 2026-07-28 revision
and were verified on the dates the ledger records.

## Related repos

- [mcp_best_practices](https://github.com/peopleforrester/mcp_best_practices): a security-first MCP portfolio tracking the 2026-07-28 revision
- [mcp-k8s-observability-argocd-server](https://github.com/peopleforrester/mcp-k8s-observability-argocd-server): an MCP server for Kubernetes observability through Argo CD
- [MCP_Server_Claude_Doc_monitor](https://github.com/peopleforrester/MCP_Server_Claude_Doc_monitor): an MCP server that watches documentation for change
- [mcp-city](https://github.com/peopleforrester/mcp-city): the source of the site

## The person

Michael Rishi Forrester: [michaelrishiforrester.com](https://michaelrishiforrester.com/) ·
[Speaking](https://michaelrishiforrester.com/speaking/) ·
[LinkedIn](https://www.linkedin.com/in/michaelrishiforrester/) ·
[GitHub](https://github.com/peopleforrester) ·
[Email](mailto:michaelrishiforrester@gmail.com)

## A note on the art

The illustrations were generated for the talk in a cut-paper shadow-play style.
The ship outlines in `art/ships/` depict designs that belong to their studios
and are fan art made for a scale comparison, nothing more. The cable sketches
are hand-drawn.

## License

Text, research and generated art: [CC BY 4.0](LICENSE). Quoted sources remain
their authors'.
