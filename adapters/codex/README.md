# Codex Adapter

This adapter maps the common agent harness onto Codex-style sessions.

## Status

Experimental. The portable contract is usable, but Codex does not consume Claude Code's `adapters/claude/settings.json`, slash command registry, or hook event schema directly. `adapters/codex/AGENTS.md` is the current Codex-style bootstrap, and wrappers should still run guard scripts as deterministic checks where native hooks are unavailable.

## Entry Points

| Surface | File |
|---|---|
| Adapter bootstrap | `adapters/codex/AGENTS.md` |
| Core contract | `core/CORE.md` |
| Workflow routing | `core/WORKFLOW.md` |
| Shared conventions | `core/CONVENTIONS.md` |
| Git and dispatch operations | `core/OPERATIONS.md` |
| Memory contract | `core/MEMORY.md` |
| Hook invariants | `core/HOOKS.md` |
| Preflight wrappers | `adapters/codex/bin/` |
| Capabilities | `capabilities/README.md` |
| Role profiles | `roles/README.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |

## Runtime Mapping

| Core Concept | Codex Implementation |
|---|---|
| capability | Read `capabilities/README.md` for meaning; run `adapters/codex/bin/preflight.sh capability-info <capability>` to confirm Codex realization; use `skills/*/SKILL.md` only as Claude compatibility detail until Codex-native capability instructions exist |
| role profile | Use `roles/README.md` for meaning; use `roles/modes/` or Claude agent files only as compatibility references until Codex-native role prompts exist |
| role mode | Run `adapters/codex/bin/preflight.sh mode-info <family/mode>` before using a `roles/modes/` fragment; portable modes can be used directly, tool-contract modes require equivalent tools, unsupported modes are reference-only |
| adapter bootstrap | Load `adapters/codex/AGENTS.md`, then `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `/track` semantics and `utilities/workflow-guard-hook.sh`; run `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` when no automatic prompt hook is attached |
| artifact-order gate | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | `core/HOOKS.md` defines marker/check semantics; run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| git safety gate | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory write guard | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory injection | `tools/memory/mem.py inject` is runtime-neutral; run `adapters/codex/bin/preflight.sh memory [cwd]` when no automatic session-start hook is attached |
| memory recall injection | `hooks/mem-recall-inject.sh` is runtime-neutral for prompt text; run `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` when no automatic prompt hook is attached |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` is runtime-neutral for cwd/text output; run `adapters/codex/bin/preflight.sh briefing [cwd]` when no automatic prompt hook is attached |
| capability mapping | `adapters/codex/bin/preflight.sh capability-info <capability>` reports Codex's instruction-only realization and the Claude compatibility reference, if one exists |
| model role mapping | `adapters/codex/bin/preflight.sh role <portable-role>` resolves portable model roles through Codex adapter environment variables |
| mode mapping | `adapters/codex/bin/preflight.sh mode-info <family/mode>` reports whether a mode is portable, tool-contract, or unsupported for Codex |
| memory distill delta | Codex session transcript extraction is available through `adapters/codex/bin/preflight.sh distill-delta <session-id>` |
| memory distill proposal | `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` runs a constrained Codex exec proposal worker; it mutates memory only with explicit `CODEX_DISTILL_APPLY=1` |
| memory store | `tools/memory/mem.py` is runtime-neutral; detached distillation worker execution remains adapter-specific |

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

Codex 쪽 wrapper 를 만들 때는 `AGENT_MODEL_FAST`, `AGENT_MODEL_DEEP`, `AGENT_MODEL_EXTERNAL` 같은 환경변수나 설정 파일로 이 mapping 을 드러내야 한다. `CODEX_DISTILL_MODEL` 은 distillation proposal worker 에만 적용되는 optional override 다. 공통 skill 은 concrete model name 을 요구하지 않고 role 의미만 요구한다.

`adapters/codex/bin/preflight.sh role <portable-role>` is the executable mapping
surface. When no concrete model is configured it reports `codex-default` and
`runtime-default`; for `external adversary`, it reports unavailable unless
`AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured.

## Compatibility

Codex should create new project artifacts under `.agent_reports/`. Use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

Codex should resolve harness-home paths through `AGENT_HOME` or `utilities/agent-home.sh`. `CLAUDE_HOME` is accepted only as a Claude adapter compatibility alias during migration.

Claude Code-specific files remain valid as implementation references, not as Codex bootstrap files:

- `CLAUDE.md` contains Claude Code routing and response rules.
- `adapters/claude/settings.json` registers Claude Code hooks and permissions.
- `adapters/claude/commands/` defines Claude Code slash commands.
- `skills/*/SKILL.md` is still Claude Skill format; start from `capabilities/README.md` for portable meaning.
- `adapters/claude/statusline.sh` targets Claude Code's statusline contract.

When porting a behavior, copy the underlying invariant from `CORE.md`, `WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to Codex's tool, approval, and session model.
