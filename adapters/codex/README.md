# Codex Adapter

This adapter maps the common agent harness onto Codex-style sessions.

## Status

Experimental. The portable contract is usable, but Codex does not consume Claude Code's `settings.json`, slash command registry, or hook event schema directly. `adapters/codex/AGENTS.md` is the current Codex-style bootstrap, and wrappers should still run guard scripts as deterministic checks where native hooks are unavailable.

## Entry Points

| Surface | File |
|---|---|
| Adapter bootstrap | `adapters/codex/AGENTS.md` |
| Core contract | `core/CORE.md` |
| Workflow routing | `core/WORKFLOW.md` |
| Shared conventions | `core/CONVENTIONS.md` |
| Git and dispatch operations | `core/OPERATIONS.md` |
| Memory contract | `core/MEMORY.md` |
| Capabilities | `skills/*/SKILL.md` |
| Role profiles | `agents/*.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |

## Runtime Mapping

| Core Concept | Codex Implementation |
|---|---|
| capability | Read and follow the relevant `skills/*/SKILL.md`; no native slash registry is assumed |
| role profile | Use `agents/*.md` and `agent-modes/` as delegation prompts or review personas |
| adapter bootstrap | Load `adapters/codex/AGENTS.md`, then `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `track-toggle.sh` and `utilities/workflow-guard-hook.sh` semantics; no automatic prompt hook unless wrapped |
| artifact-order gate | `hooks/artifact-guard.sh` can be run as a pre-write check by wrappers or manually |
| spec read gate | `hooks/spec-skill-gate.sh` / `hooks/spec-read-marker.sh` semantics apply when the runtime can emit equivalent events |
| git safety gate | `hooks/git-state-guard.sh` is the portable check; Codex must also honor sandbox and approval state |
| memory store | `tools/memory/mem.py` is runtime-neutral; hook automation is adapter-specific |

## Runtime Home Projection

Target layout:

```text
$HOME/agent_setting/        # neutral repo
$HOME/.codex/               # Codex runtime home
```

Codex runtime state such as `auth.json`, logs, SQLite state, sessions, model caches, and shell snapshots should stay in `$HOME/.codex`. The neutral harness should be referenced from Codex through explicit bootstrap instructions, symlinks, or wrapper configuration. At minimum, the Codex adapter should expose a stable pointer back to the neutral repo, for example:

```text
$HOME/.codex/agent-harness -> $HOME/agent_setting
```

Further Codex-specific files can be added under `adapters/codex/` and symlinked or generated into `$HOME/.codex` as the adapter matures.

## Model Role Mapping

Codex adapter 는 `core/CONVENTIONS.md §2` 의 portable role 을 Codex 런타임에서 동등한 capability tier 로 매핑해야 한다. 현재 adapter 는 experimental 이므로 concrete default 를 고정하지 않는다.

| Portable role | Codex adapter expectation |
|---|---|
| `fast reviewer` / `fast fact-checker` / `fast writer` | 낮은 비용·낮은 지연의 모델 또는 낮은 reasoning effort profile. surface, coverage, format, verbatim matching 중심 |
| `deep reviewer` / `deep maker` | 높은 reasoning effort 또는 더 강한 모델. methodology, domain, architecture, safety 판단 중심 |
| `external adversary` | 가능하면 primary Codex session 과 다른 모델·설정·프로세스. 없으면 explicit unavailable 로 보고하고 thorough 로 fallback |
| `orchestrator` | 도구 호출·artifact merge·한국어 정리 담당. 실제 판단 role 과 분리 가능 |

Codex 쪽 wrapper 를 만들 때는 `AGENT_MODEL_FAST`, `AGENT_MODEL_DEEP`, `AGENT_MODEL_EXTERNAL` 같은 환경변수나 설정 파일로 이 mapping 을 드러내야 한다. 공통 skill 은 concrete model name 을 요구하지 않고 role 의미만 요구한다.

## Compatibility

Codex should create new project artifacts under `.agent_reports/`. Use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

Codex should resolve harness-home paths through `AGENT_HOME` or `utilities/agent-home.sh`. `CLAUDE_HOME` is accepted only as a Claude adapter compatibility alias during migration.

Claude Code-specific files remain valid as implementation references, not as Codex bootstrap files:

- `CLAUDE.md` contains Claude Code routing and response rules.
- `settings.json` registers Claude Code hooks and permissions.
- `commands/` defines Claude Code slash commands.
- `statusline.sh` targets Claude Code's statusline contract.

When porting a behavior, copy the underlying invariant from `CORE.md`, `WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to Codex's tool, approval, and session model.
