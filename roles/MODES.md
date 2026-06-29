# Role Mode Inventory

`roles/modes/` contains mode-level persona and procedure fragments used by role
profiles. Claude Code consumes concrete projection files under
`adapters/claude/agent-modes/`, currently kept byte-identical to these fragments
for behavior preservation. Not every fragment is purely portable.

## Status Classes

| Status | Meaning |
|---|---|
| `portable-persona` | Runtime-neutral role behavior. Can be reused by adapters with minimal wrapping. |
| `portable-with-tool-contract` | Mostly portable, but assumes named deterministic tools or external CLIs that an adapter must provide or replace. |
| `adapter-coupled` | Mentions Claude runtime paths, Claude-native MCP names, or Claude-derived command behavior. Needs adapter-native realization before another runtime can claim support. |

## Inventory

| Mode family | Files | Current status | Split requirement |
|---|---|---|---|
| `dev` | `backend`, `frontend`, `new-lib`, `refactor` | `portable-persona` | Keep shared unless runtime-specific tool schemas are added. |
| `editorial` | `translate`, `polish`, `review` | `portable-persona` | Keep shared; adapter only maps invocation and edit tools. |
| `qa` | `code-review`, `data-curate`, `ml-debug`, `plan-review`, `security-review`, `test` | mixed | `security-review` and `test` include Claude-derived `/security-review`, `/verify`, `/run` notes; split those notes when Codex-native verification exists. |
| `research` | `plan-review`, `research-survey`, `fact-check`, `claim-verify` | mixed | `claim-verify` includes Claude deep-research provenance; `plan-review` includes old `~/.claude` topology examples. General review semantics are portable. |
| `material` | `browser-fetch`, `data-script`, `figure-gen`, `pdf-extract`, `web-image-search` | `portable-with-tool-contract` | Requires adapter-provided browser/pdf/script/web fetch tools plus memory wrapper or `<agent-home>` memory CLI resolution. |
| `design` | `_design_rules`, `maker`, `critic`, `verifier` | `adapter-coupled` | Design MCP tool names, `~/.claude/scaffolds`, and Claude Design provenance need adapter-specific implementation notes. |

## Adapter Rule

Adapters may read `roles/modes/` as portability references. Runtime consumption
should go through adapter-owned realizations such as
`adapters/claude/agent-modes/`. An adapter must not claim a mode is natively
supported unless it provides:

- equivalent tools or documented fallbacks;
- runtime-neutral `<agent-home>` path resolution;
- a mapping from any MCP or slash command references to the adapter runtime;
- a clear unsupported report when the mode depends on a missing visual/browser
  or verification harness.
