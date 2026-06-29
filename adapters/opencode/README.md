# OpenCode Adapter

This adapter maps the common agent harness onto OpenCode.

## Status

Experimental. OpenCode has a richer native surface than an instruction-only
runtime: it ships native commands, skills, agents, MCP, a JS/TS plugin hook
system, and a permission model. The portable contract is usable through
instruction-first preflight wrappers. OpenCode does not consume Claude Code's
`adapters/claude/settings.json`, slash command registry, hook event schema, or
statusline contract directly. `adapters/opencode/AGENTS.md` is the current
OpenCode bootstrap, loaded through the `instructions` array in
`opencode.json`/`opencode.jsonc`.

The target is harness parity on OpenCode, not Claude surface parity. Use
OpenCode native features first, including native commands, skills, agents, MCP,
permission config, and plugin hooks; add adapter wrappers only for
harness-specific signals that OpenCode does not already surface.

Native skill, command, agent, and plugin materialization is future work. Until
then, capability support is instruction-first through `preflight.sh` wrappers,
matching the Codex adapter's safe default.

## Entry Points

| Surface | File |
|---|---|
| Adapter bootstrap | `adapters/opencode/AGENTS.md` |
| Core contract | `core/CORE.md` |
| Workflow routing | `core/WORKFLOW.md` |
| Shared conventions | `core/CONVENTIONS.md` |
| Git and dispatch operations | `core/OPERATIONS.md` |
| Memory contract | `core/MEMORY.md` |
| Hook invariants | `core/HOOKS.md` |
| Preflight wrappers | `adapters/opencode/bin/` |
| Capabilities | `capabilities/README.md` |
| Role profiles | `roles/README.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |
| Selected tool projection | `adapters/opencode/tools/` |
| Selected utility projection | `adapters/opencode/utilities/` |

## Runtime Mapping

| Core Concept | OpenCode Implementation |
|---|---|
| capability | Read `capabilities/README.md` for meaning; run `adapters/opencode/bin/preflight.sh capability-info <capability>` to confirm OpenCode realization; use `skills/*/SKILL.md` only as Claude compatibility detail until OpenCode-native capability instructions exist |
| native skill/command/agent surface | Not materialized yet; OpenCode has native `.opencode/skill/`, `.opencode/command/`, `.opencode/agent/` surfaces. If added, generate adapter-owned output from portable capability/role sources and verify OpenCode discoverability (`opencode debug skill`, `opencode debug agent`) |
| native plugin hook surface | Not materialized yet; OpenCode has JS/TS plugin hooks (`tool.execute.before`, etc). If added, bridge to shared shell guards and keep preflight as fallback |
| role profile | Use `roles/README.md` for meaning; use `roles/modes/` or Claude agent files only as compatibility references until OpenCode-native role prompts exist |
| role mode | Run `adapters/opencode/bin/preflight.sh mode-info <family/mode>` before using a `roles/modes/` fragment; portable modes can be used directly, tool-contract modes require equivalent tools, unsupported modes are reference-only |
| adapter bootstrap | Add `adapters/opencode/AGENTS.md` to the `instructions` array in `opencode.json`/`opencode.jsonc`; then load `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| workflow start cleanup | Run `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` when no automatic session-start hook is attached, so stale untracked flags are GC'd |
| tracked/untracked signal | Portable tracked/untracked semantics plus `utilities/workflow-guard-hook.sh`; run `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]` when no automatic prompt hook is attached |
| tracked/untracked toggle | Portable `utilities/workflow-toggle.sh`; run `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only on explicit user request |
| artifact-order gate | `core/HOOKS.md` defines the invariant; run `adapters/opencode/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | `core/HOOKS.md` defines the invariant; run `adapters/opencode/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | `core/HOOKS.md` defines marker/check semantics; run `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/opencode/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| git safety gate | `core/HOOKS.md` defines the invariant; included in `adapters/opencode/bin/preflight.sh write <file> [session-id]` |
| memory write guard | `core/HOOKS.md` defines the invariant; included in `adapters/opencode/bin/preflight.sh write <file> [session-id]` |
| memory injection | `tools/memory/mem.py inject` is runtime-neutral; run `adapters/opencode/bin/preflight.sh memory [cwd]` when no automatic session-start hook is attached |
| memory recall injection | `hooks/mem-recall-inject.sh` is runtime-neutral for prompt text; run `adapters/opencode/bin/preflight.sh recall <prompt> [cwd]` when no automatic prompt hook is attached |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` is runtime-neutral for cwd/text output; run `adapters/opencode/bin/preflight.sh briefing [cwd]` when no automatic prompt hook is attached |
| capability mapping | `adapters/opencode/bin/preflight.sh capability-info <capability>` reports OpenCode's instruction-only or tool-contract realization and the Claude compatibility reference, if one exists |
| model role mapping | `adapters/opencode/bin/preflight.sh role <portable-role>` resolves portable model roles through OpenCode adapter environment variables |
| mode mapping | `adapters/opencode/bin/preflight.sh mode-info <family/mode>` reports whether a mode is portable, tool-contract, or unsupported for OpenCode |
| memory distill delta | Tool-contract: OpenCode session source reader not yet implemented in the shared memory CLI |
| memory distill proposal | Disabled by default; requires both a session source reader and a verified no-tools worker contract before it can be enabled |
| memory store | `tools/memory/mem.py` is runtime-neutral; detached distillation worker execution remains adapter-specific |
| permission model | OpenCode native `permission` config (`allow`/`ask`/`deny` per tool, per-agent override); adapter documents recommended rules, not a harness guard replacement |
| statusline | OpenCode TUI footer is native; no user shell statusline surface in config schema; harness status signals stay instruction-only/preflight |

## Tool Projection

`opencode_setting/tools` intentionally points at `adapters/opencode/tools/`,
not the full shared `tools/` directory. The adapter currently exposes only
memory tools that OpenCode wrappers use directly:

- `memory/mem.py` (OpenCode-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (OpenCode-owned launcher for recall)

Harness development tools and Claude-coupled helper surfaces such as
`build-manifest.py`, `design-mcp`, and `web-bundle` stay out of the OpenCode
projection until OpenCode has a documented runtime realization for them.

## Utility Projection

`opencode_setting/utilities` intentionally points at
`adapters/opencode/utilities/`, not the full shared `utilities/` directory.
The adapter currently exposes only utility files that OpenCode wrappers or
docs use:

- `agent-home.sh` (OpenCode-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Claude-specific helpers such as `dispatch-liveness.sh` stay out of the
OpenCode projection until OpenCode has an equivalent transcript/liveness
contract.

## Runtime Home Projection

Target layout:

```text
$HOME/agent_setting/        # neutral repo
$HOME/.config/opencode/     # OpenCode global config home
$HOME/.local/share/opencode/  # OpenCode data home (DB, logs, snapshots)
```

OpenCode runtime state such as `auth.json`, `opencode.db`, logs, snapshots,
and tool output should stay under `$HOME/.local/share/opencode` and
`$HOME/.config/opencode`. The neutral harness should be referenced from
OpenCode through explicit bootstrap instructions and the `instructions` array
in the config. At minimum, the OpenCode adapter should expose a stable pointer
back to the neutral repo:

```text
$HOME/.config/opencode/agent-harness -> $HOME/agent_setting
```

The `instructions` array in `opencode.json`/`opencode.jsonc` should include the
projected bootstrap file:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "$HOME/agent_setting/opencode_setting/AGENTS.md"
  ]
}
```

Further OpenCode-specific files can be added under `adapters/opencode/` and
symlinked or generated into the config home as the adapter matures.

## Model Role Mapping

OpenCode adapter maps `core/CONVENTIONS.md §2` portable roles to OpenCode
runtime model/variant tiers. OpenCode uses `provider/model-id` strings and a
`variant` field for reasoning profile selection; there is no numeric
reasoning-effort config field.

| Portable role | OpenCode adapter expectation |
|---|---|
| `fast reviewer` / `fast fact-checker` / `fast writer` | 낮은 비용·낮은 지연의 모델 또는 `small_model` + 낮은 variant. surface, coverage, format, verbatim matching 중심 |
| `deep reviewer` / `deep maker` | 높은 variant 또는 더 강한 모델. methodology, domain, architecture, safety 판단 중심 |
| `external adversary` | 가능하면 primary OpenCode session 과 다른 모델·설정·프로세스. 없으면 explicit unavailable 로 보고하고 thorough 로 fallback |
| `orchestrator` | 도구 호출·artifact merge·한국어 정리 담당. 실제 판단 role 과 분리 가능 |

OpenCode wrapper 를 만들 때는 `AGENT_MODEL_FAST`, `AGENT_MODEL_DEEP`,
`AGENT_MODEL_EXTERNAL` 같은 환경변수나 설정 파일로 이 mapping 을 드러내야
한다. 공통 skill 은 concrete model name 을 요구하지 않고 role 의미만
요구한다.

`adapters/opencode/bin/preflight.sh role <portable-role>` is the executable
mapping surface. When no concrete model is configured it reports
`opencode-default` and `runtime-default`; for `external adversary`, it reports
unavailable unless `AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is
configured.

## Compatibility

OpenCode should create new project artifacts under `.agent_reports/`. Use
`utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`;
use `.claude_reports` only if it already exists and `.agent_reports` does not.

OpenCode should resolve harness-home paths through `AGENT_HOME` or the
OpenCode-owned `utilities/agent-home.sh`. Some shared legacy tools still accept
`CLAUDE_HOME` as a migration alias, but OpenCode-owned wrappers should not use
it as their runtime-home fallback.

Claude Code-specific files remain valid as implementation references, not as
OpenCode bootstrap files:

- `CLAUDE.md` contains Claude Code routing and response rules.
- `adapters/claude/settings.json` registers Claude Code hooks and permissions.
- `adapters/claude/commands/` defines Claude Code slash commands.
- `skills/*/SKILL.md` is still Claude Skill format; start from
  `capabilities/README.md` for portable meaning. OpenCode auto-loads
  `~/.claude/skills/` as a compat convenience, but the adapter must not depend
  on it.
- `adapters/claude/statusline.sh` targets Claude Code's statusline contract.

For native OpenCode surface checks, disable the Claude compatibility autoload:

```bash
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 opencode debug skill --pure
```

When porting a behavior, copy the underlying invariant from `CORE.md`,
`WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to OpenCode's
tool, permission, agent, and session model.
