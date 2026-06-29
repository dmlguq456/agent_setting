# Codex Adapter

This adapter maps the common agent harness onto Codex-style sessions.

## Status

Experimental. The portable contract is usable, but Codex does not consume Claude Code's `adapters/claude/settings.json`, slash command registry, or hook event schema directly. `adapters/codex/AGENTS.md` is the current Codex-style bootstrap, and wrappers should still run guard scripts as deterministic checks where native hooks are unavailable.

The target is harness parity on Codex, not Claude surface parity. Use Codex
native features first, including built-in slash commands and `/statusline`; add
adapter wrappers only for harness-specific signals that Codex does not already
surface.

Codex native Skill projection is materialized under `adapters/codex/skills/`
from `capabilities/`. Codex custom agent projections are materialized under
`adapters/codex/agents/` from `roles/`. A Codex plugin projection is materialized under
`adapters/codex/plugins/agent-harness-codex` and exposed through the repo-local
marketplace at `adapters/codex/.agents/plugins/marketplace.json`. Do not
project Claude Skill, Agent, command, hook, or statusline files into Codex.

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
| Role mode inventory | `roles/MODES.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |
| Native skills | `adapters/codex/skills/` |
| Native agents | `adapters/codex/agents/` |
| Native plugin | `adapters/codex/plugins/agent-harness-codex` |
| Native hooks | `adapters/codex/hooks/` |
| Selected tool projection | `adapters/codex/tools/` |
| Selected utility projection | `adapters/codex/utilities/` |

## Runtime Mapping

| Core Concept | Codex Implementation |
|---|---|
| capability | Read `capabilities/README.md` for meaning; run `adapters/codex/bin/preflight.sh capability-info <capability>` to confirm Codex realization; use `adapters/codex/skills/<capability>/SKILL.md` as Codex-native guidance |
| native skill/plugin surface | Skills are materialized under `adapters/codex/skills/`; the installable plugin projection is materialized under `adapters/codex/plugins/agent-harness-codex`. Command-like capability entrypoints use these native Skills/plugin surfaces and are verified with Codex discoverability (`codex debug prompt-input`) |
| native hook surface | `adapters/codex/hooks/hooks.json` registers Codex `PreToolUse` write guards and `PostToolUse` design HTML checks; explicit preflight remains fallback |
| role profile | Use `roles/README.md` for meaning; Codex custom agents are materialized under `adapters/codex/agents/*.toml` and still call `adapters/codex/bin/preflight.sh role <portable-role>` for concrete model/reasoning mapping |
| role mode | Run `adapters/codex/bin/preflight.sh mode-info <family/mode>` before using a `roles/modes/` fragment; portable modes can be used directly, tool-contract modes require equivalent tools, unsupported modes are reference-only |
| adapter bootstrap | Load `adapters/codex/AGENTS.md`, then `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| workflow start cleanup | Run `adapters/codex/bin/preflight.sh start [cwd] [session-id]` when no automatic session-start hook is attached, so stale untracked flags are GC'd |
| tracked/untracked signal | Portable tracked/untracked semantics plus `utilities/workflow-guard-hook.sh`; run `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` when no automatic prompt hook is attached |
| tracked/untracked toggle | Portable `utilities/workflow-toggle.sh`; run `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only on explicit user request |
| artifact-order gate | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| design visual harness | Tool-contract: `adapters/codex/bin/preflight.sh visual-harness` exits 69 until Codex has an adapter-owned render/screenshot/image-inspection harness. Do not project Claude Design MCP files into Codex |
| spec read gate | `core/HOOKS.md` defines marker/check semantics; run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| git safety gate | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory write guard | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory injection | `tools/memory/mem.py inject` is runtime-neutral; run `adapters/codex/bin/preflight.sh memory [cwd]` when no automatic session-start hook is attached |
| memory recall injection | `hooks/mem-recall-inject.sh` is runtime-neutral for prompt text; run `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` when no automatic prompt hook is attached |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` is runtime-neutral for cwd/text output; run `adapters/codex/bin/preflight.sh briefing [cwd]` when no automatic prompt hook is attached |
| capability mapping | `adapters/codex/bin/preflight.sh capability-info <capability>` reports Codex's native Skill/plugin realization, instruction-only or tool-contract status, and the legacy compatibility reference, if one exists |
| model role mapping | `adapters/codex/bin/preflight.sh role <portable-role>` resolves portable model roles through Codex adapter environment variables |
| mode mapping | `adapters/codex/bin/preflight.sh mode-info <family/mode>` reports whether a mode is portable, tool-contract, or unsupported for Codex; tool-contract modes include a named `tool_contract` field |
| memory distill delta | Codex session transcript extraction is available through `adapters/codex/bin/preflight.sh distill-delta <session-id>` |
| memory distill proposal | `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` runs a constrained Codex exec proposal worker; it mutates memory only with explicit `CODEX_DISTILL_APPLY=1` |
| memory store | `tools/memory/mem.py` is runtime-neutral; detached distillation worker execution remains adapter-specific |

## Tool Projection

`codex_setting/tools` intentionally points at `adapters/codex/tools/`, not the
full shared `tools/` directory. The adapter currently exposes only memory tools
that Codex wrappers use directly:

- `memory/mem.py` (Codex-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (Codex-owned launcher for recall)

Harness development tools and Claude-coupled helper surfaces such as
`build-manifest.py`, `design-mcp`, and `web-bundle` stay out of the Codex
projection until Codex has a documented runtime realization for them.

## Utility Projection

`codex_setting/utilities` intentionally points at
`adapters/codex/utilities/`, not the full shared `utilities/` directory. The
adapter currently exposes only utility files that Codex wrappers or docs use:

- `agent-home.sh` (Codex-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Claude-specific helpers such as `dispatch-liveness.sh` stay out of the Codex
projection until Codex has an equivalent transcript/liveness contract.

## Native Skill Projection

`adapters/codex/skills/` contains Codex-native Skill projections generated from
portable `capabilities/*.md` specs:

```bash
adapters/codex/bin/sync-native-skills.py --check
```

Expose them to Codex by symlinking each generated skill directory into
`$CODEX_HOME/skills/`, using `codex_setting/codex-skills` as the projection
source. Do not expose root `skills/` or `adapters/claude/skills/` as Codex
native skills.

## Native Plugin Projection

`adapters/codex/plugins/agent-harness-codex` contains an installable Codex
plugin generated from the same Codex-native Skill projection:

```bash
adapters/codex/bin/sync-native-plugin.py --check
```

Expose the repo-local marketplace through `codex_setting/codex-plugin-marketplace`:

```bash
codex plugin marketplace add "$AGENT_HOME/codex_setting/codex-plugin-marketplace"
codex plugin add agent-harness-codex@agent-harness
```

The plugin copies generated Codex Skill files into plugin-local `skills/` so
Codex discovers them as `agent-harness-codex:<capability>`. Do not build the
plugin from Claude Skill files.

## Native Agent Projection

`adapters/codex/agents/` contains Codex custom agent TOML projections generated
from portable role profiles in `roles/README.md`:

```bash
adapters/codex/bin/sync-native-agents.py --check
```

Expose them to Codex by symlinking each generated `*.toml` file into
`$CODEX_HOME/agents/` for a user/global install, or into project
`.codex/agents/` for a project-scoped install, using
`codex_setting/codex-agents` as the projection source. The TOML files define
the required Codex custom agent fields (`name`, `description`, and
`developer_instructions`) and defer concrete model or reasoning selection to
`adapters/codex/bin/preflight.sh role <portable-role>`. Do not expose
`adapters/claude/agents/` as Codex-native agents.

## Command-Like Entries

Custom prompts are deprecated in Codex. Do not generate a `prompts/` projection
or copy Claude slash-command files into Codex. Reusable command-like capability
entrypoints are represented by Codex-native Skills and the installable
`agent-harness-codex` plugin.

## Native Hook Projection

`adapters/codex/hooks/` contains a Codex-native `hooks.json` plus concrete
adapter-owned hook bridges. The `PreToolUse` bridge runs before write/edit/patch
tools and delegates artifact-order, git-state, and memory-write checks to
`adapters/codex/bin/preflight.sh write`. The `PostToolUse` bridge runs after
write/edit/patch tools and delegates design HTML saves to
`adapters/codex/bin/preflight.sh design`.

Expose it through `codex_setting/codex-hooks`, not through a plain `hooks/`
projection:

```bash
ln -sfn "$AGENT_HOME/codex_setting/codex-hooks/hooks.json" "$HOME/.codex/hooks.json"
```

The pre-write bridge accepts Codex hook stdin JSON and returns a
`decision=block` hook result when the shared guard fails. The design bridge is a
post-write alert path only. Neither bridge consumes Claude `settings.json` or
Claude hook payloads.

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

Codex 쪽 wrapper 는 `AGENT_MODEL_FAST`, `AGENT_MODEL_DEEP`,
`AGENT_MODEL_EXTERNAL`, `AGENT_REASONING_FAST`,
`AGENT_REASONING_DEEP` 같은 환경변수로 이 mapping 을 드러낸다.
`CODEX_DISTILL_MODEL` 은 distillation proposal worker 에만 적용되는
optional override 다. 공통 skill 은 concrete model name 을 요구하지 않고
role 의미만 요구한다.

`adapters/codex/bin/preflight.sh role <portable-role>` is the executable mapping
surface. When no concrete model is configured it reports `codex-default` and
`runtime-default`; for `external adversary`, it reports unavailable unless
`AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured.

## Compatibility

Codex should create new project artifacts under `.agent_reports/`. Use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

Codex should resolve harness-home paths through `AGENT_HOME` or the Codex-owned `utilities/agent-home.sh`. Some shared legacy tools still accept `CLAUDE_HOME` as a migration alias, but Codex-owned wrappers should not use it as their runtime-home fallback.

Claude Code-specific files remain valid as implementation references, not as Codex bootstrap files:

- `CLAUDE.md` contains Claude Code routing and response rules.
- `adapters/claude/settings.json` registers Claude Code hooks and permissions.
- `adapters/claude/commands/` defines Claude Code slash commands.
- `skills/*/SKILL.md` is still Claude Skill format; start from `capabilities/README.md` for portable meaning.
- `adapters/claude/statusline.sh` targets Claude Code's statusline contract.

When porting a behavior, copy the underlying invariant from `CORE.md`, `WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to Codex's tool, approval, and session model.
