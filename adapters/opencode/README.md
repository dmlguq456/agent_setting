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

Native Skill projection is materialized under `adapters/opencode/skills/` from
portable `capabilities/*.md`. Native Agent projection is materialized under
`adapters/opencode/agents/` from `roles/README.md`. Native Command projection
is materialized under `adapters/opencode/commands/` from `capabilities/`.
Native guard plugin projection is materialized under `adapters/opencode/plugins/`.
Capability support still keeps explicit `preflight.sh` wrappers as fallback for
guards and tool-contract reporting.

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
| Native skills | `adapters/opencode/skills/` |
| Native agents | `adapters/opencode/agents/` |
| Native commands | `adapters/opencode/commands/` |
| Native guard plugin | `adapters/opencode/plugins/agent-harness-guards.js` |
| Capabilities | `capabilities/README.md` |
| Role profiles | `roles/README.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |
| Selected tool projection | `adapters/opencode/tools/` |
| Selected utility projection | `adapters/opencode/utilities/` |

## Runtime Mapping

| Core Concept | OpenCode Implementation |
|---|---|
| capability | Read `capabilities/README.md` for meaning; run `adapters/opencode/bin/preflight.sh capability-info <capability>` to confirm OpenCode realization; use `adapters/opencode/skills/<capability>/SKILL.md` as OpenCode-native guidance |
| native skill/command/agent surface | Skills are materialized under `adapters/opencode/skills/`; agents are materialized under `adapters/opencode/agents/`; commands are materialized under `adapters/opencode/commands/`. Future output must be generated from portable capability/role sources and verified with OpenCode discoverability (`opencode debug skill`, `opencode debug agent`, `opencode debug config`) |
| native plugin hook surface | `adapters/opencode/plugins/agent-harness-guards.js` uses `chat.message` and `experimental.chat.system.transform` for prompt lifecycle context, `tool.execute.before` to bridge write/edit/patch targets to `adapters/opencode/bin/preflight.sh write`, `command.execute.before` to bridge `autopilot-code`/`autopilot-spec` to `preflight.sh capability` (spec read gate, throws to abort), and `tool.execute.after` to bridge `prd.md` reads to `preflight.sh read` (grounding marker) and design HTML saves to `preflight.sh design`; explicit preflight remains fallback |
| role profile | Use `roles/README.md` for meaning; use `adapters/opencode/agents/<role>/<role>.md` as OpenCode-native role guidance, and use Claude agent files only as compatibility references |
| role mode | Run `adapters/opencode/bin/preflight.sh mode-info <family/mode>` before using a `roles/modes/` fragment; portable modes can be used directly, tool-contract modes require equivalent tools, unsupported modes report `fallback=reference-only` when no OpenCode-native runtime surface exists |
| adapter bootstrap | Add `adapters/opencode/AGENTS.md` to the `instructions` array in `opencode.json`/`opencode.jsonc`; then load `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| permission model | Run `adapters/opencode/bin/preflight.sh permissions`; use OpenCode native `permission` config and plugin hooks, not Claude `allowedTools` |
| MCP config | Run `adapters/opencode/bin/preflight.sh mcp [--check]`; use OpenCode native `opencode mcp`/config surfaces, not Claude `settings.json` MCP payloads |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| workflow start cleanup | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` once per session; run it manually when plugins are unavailable |
| tracked/untracked signal | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`; run it manually when plugins are unavailable |
| harness status snapshot | Run `adapters/opencode/bin/preflight.sh status [cwd] [session-id]` for read-only workflow, artifact, notes, worktree, and git-risk signals. This does not replace OpenCode native model/context/session UI |
| adapter readiness | Run `adapters/opencode/bin/preflight.sh doctor` to check manifest freshness, native projections, and boundary rules in one command |
| tracked/untracked toggle | Portable `utilities/workflow-toggle.sh`; run `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only on explicit user request |
| headless dispatch | Tool-contract check: `adapters/opencode/bin/preflight.sh headless --check <worktree>` verifies the worktree, `opencode run` availability, and installed OpenCode runtime projection (`agent-harness`, native Skills path, native Agents, native Commands, and guard plugin). Use `adapters/opencode/bin/preflight.sh dispatch --dry-run|--register|--start --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <level> [--agent <agent>]` to build the OpenCode command and register open jobs before launch. `--start` reruns the same runtime projection check before launching. Use `adapters/opencode/bin/preflight.sh liveness [jobs.log]` while waiting on dispatched work; it matches open jobs to OpenCode SQLite sessions by `session.directory` and latest session/message/part update time. Use `adapters/opencode/bin/preflight.sh harvest --slug <slug> --mark-done` after main-session harvest to mark registry rows done only; it does not merge or clean worktrees |
| artifact-order gate | `core/HOOKS.md` defines the invariant; run `adapters/opencode/bin/preflight.sh write <file> [session-id]` before writes |
| material browser fetch | Tool-contract check: `adapters/opencode/bin/preflight.sh browser-fetch --check <url>` verifies rendered browser access through the adapter-owned Playwright launcher before using `roles/modes/material/browser-fetch.md`. Exit 69 means the local browser stack is unavailable |
| material data script | Tool-contract check: `adapters/opencode/bin/preflight.sh data-script --check <script.py>` verifies generated Python analysis scripts through the adapter-owned launcher before using `roles/modes/material/data-script.md` |
| material figure generation | Tool-contract check: `adapters/opencode/bin/preflight.sh figure-gen --check <script.py>` verifies generated matplotlib/seaborn figure scripts through the adapter-owned launcher before using `roles/modes/material/figure-gen.md` |
| material PDF extract | Tool-contract check: `adapters/opencode/bin/preflight.sh pdf-extract --check <file.pdf>` verifies local PDF text extraction through the adapter-owned launcher before using `roles/modes/material/pdf-extract.md`. Exit 69 means the local extractor is unavailable |
| material web image search | Tool-contract check: `adapters/opencode/bin/preflight.sh web-image-search --check <query>` verifies that `OPENCODE_WEB_IMAGE_SEARCH_CMD` or `AGENT_WEB_IMAGE_SEARCH_CMD` provides a local image-search command before using `roles/modes/material/web-image-search.md`. Exit 69 means no provider is configured |
| QA security review | Portable read-only persona: `roles/modes/qa/security-review.md` is consumed with OpenCode file and git diff tools. Do not project or invoke Claude `/security-review` |
| QA verification runner | Tool-contract check: `adapters/opencode/bin/preflight.sh verification-runner --check -- <command>` verifies explicit QA/test commands through the adapter-owned runner before using `roles/modes/qa/test.md` |
| research claim verify | Tool-contract check: `adapters/opencode/bin/preflight.sh claim-verify --check <claim>` verifies that `OPENCODE_CLAIM_VERIFY_CMD` or `AGENT_CLAIM_VERIFY_CMD` provides an external verification command before using `roles/modes/research/claim-verify.md`. Exit 69 means no provider is configured |
| design post-write verification | `core/HOOKS.md` defines the invariant; run `adapters/opencode/bin/preflight.sh design <file>` after design HTML writes |
| design visual harness | Tool-contract check: `adapters/opencode/bin/preflight.sh visual-harness <file.html>` runs the adapter-owned render/screenshot/console wrapper. Inspect the reported screenshot before claiming visual completion. Do not project Claude Design MCP files into OpenCode |
| spec read gate | `core/HOOKS.md` defines marker/check semantics; the plugin enforces it automatically (`command.execute.before` → `preflight.sh capability` throws to abort ungrounded `autopilot-code`/`autopilot-spec`; `tool.execute.after` on a `prd.md` read → `preflight.sh read` marker). Run both manually (`preflight.sh read <prd.md>` after reads, `preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities) when plugins are unavailable |
| git safety gate | `core/HOOKS.md` defines the invariant; included in `adapters/opencode/bin/preflight.sh write <file> [session-id]` |
| memory write guard | `core/HOOKS.md` defines the invariant; included in `adapters/opencode/bin/preflight.sh write <file> [session-id]` |
| memory injection | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh memory [cwd]` once per session; run it manually when plugins are unavailable |
| memory recall injection | OpenCode plugin `chat.message` captures prompt text and system transform runs `adapters/opencode/bin/preflight.sh recall <prompt> [cwd]`; run it manually when plugins are unavailable |
| oncall briefing injection | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh briefing [cwd]`; run it manually when plugins are unavailable |
| loop guidance | `adapters/opencode/bin/preflight.sh loop-info <oncall|note|study|drill>` reports whether a loop has an OpenCode manual contract, unsupported executable projection, or missing native implementation; `note` remains an external scheduler loop while the related `autopilot-note` capability is available on demand through OpenCode-native Skill/command projections |
| capability mapping | `adapters/opencode/bin/preflight.sh capability-info <capability>` reports OpenCode's native Skill/command realization and instruction-only or tool-contract status; root Skill compatibility references are not projected and report `compat_reference=not-projected` |
| model role mapping | `adapters/opencode/bin/preflight.sh role <portable-role>` resolves portable model roles through OpenCode adapter environment variables |
| mode mapping | `adapters/opencode/bin/preflight.sh mode-info <family/mode>` reports whether a mode is portable, tool-contract, or unsupported for OpenCode; tool-contract and unsupported adapter-coupled modes include machine-readable `tool_contract`, optional `tool_contract_check`, `runtime_surface`, and `fallback` fields |
| memory distill delta | Supported through `tools/memory/mem.py --source opencode`, backed by `opencode export <session-id>` (captured to a temp file — piped export stdout truncates) |
| memory distill proposal | Implemented — `distill-worker.sh` runs a no-tools `opencode run --pure --agent <distiller>` worker (verified: no shell exec, no hang, timeout-guarded) |
| memory auto-distillation | Enabled by default — plugin `event`/`session.idle` → detached `preflight session-end` (debounced) → worker → apply. Opt out `OPENCODE_DISTILL_ENABLE=0`; set `OPENCODE_DISTILL_MODEL` for quality |
| memory store | `tools/memory/mem.py` is runtime-neutral; detached distillation worker execution remains adapter-specific |
| permission model | OpenCode native `permission` config (`allow`/`ask`/`deny` per tool, per-agent override); adapter documents recommended rules, not a harness guard replacement |
| statusline | OpenCode TUI footer is native; no user shell statusline surface in config schema; harness status signals stay instruction-only/preflight |

## Tool Projection

`opencode_setting/tools` intentionally points at `adapters/opencode/tools/`,
not the full shared `tools/` directory. The adapter currently exposes only
tools that OpenCode wrappers use directly:

- `memory/mem.py` (OpenCode-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (OpenCode-owned launcher for recall)
- `material/browser-fetch.sh` (OpenCode-owned launcher for rendered web page extraction)
- `material/data-script.sh` (OpenCode-owned launcher for Python data-analysis scripts)
- `material/figure-gen.sh` (OpenCode-owned launcher for generated matplotlib figure scripts)
- `material/pdf-extract.sh` (OpenCode-owned launcher for local PDF text extraction)
- `material/web-image-search.sh` (OpenCode-owned launcher for configured image search providers)
- `qa/verification-runner.sh` (OpenCode-owned launcher for explicit verification commands)
- `research/claim-verify.sh` (OpenCode-owned launcher for configured external claim verification providers)
- `design/visual-harness.sh` (OpenCode-owned launcher for render/screenshot/console checks)

Harness development tools and Claude-coupled helper surfaces such as
`build-manifest.py` and `web-bundle` stay out of the OpenCode projection until
OpenCode has a documented runtime realization for them. The shared `design-mcp`
package is not projected wholesale; OpenCode exposes only the adapter-owned
visual harness launcher.

## Utility Projection

`opencode_setting/utilities` intentionally points at
`adapters/opencode/utilities/`, not the full shared `utilities/` directory.
The adapter currently exposes only utility files that OpenCode wrappers or
docs use:

- `agent-home.sh` (OpenCode-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `harness-status.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Claude-specific helpers such as the shared `dispatch-liveness.sh` stay out of
the OpenCode projection. OpenCode exposes its adapter-owned liveness command
through `adapters/opencode/bin/preflight.sh liveness [jobs.log]`, backed by
`~/.local/share/opencode/opencode.db` session metadata and update times.
OpenCode also exposes `adapters/opencode/bin/preflight.sh harvest` for
registry-only status and selected `open` to `done` updates. It intentionally
does not merge branches or delete worktrees.

## Native Skill Projection

`adapters/opencode/skills/` contains OpenCode-native Skill projections generated
from `capabilities/*.md`:

```bash
adapters/opencode/bin/sync-native-skills.py --check
```

Expose them to OpenCode through `opencode_setting/opencode-skills`, not through
a `skills/` projection. The plain `skills/` name is reserved for historical
Claude compatibility references.

## Native Agent Projection

`adapters/opencode/agents/` contains OpenCode-native Agent projections
generated from portable role profiles in `roles/README.md`. They declare
`mode: subagent` and defer concrete model/variant selection to
`adapters/opencode/bin/preflight.sh role <portable-role>`:

```bash
adapters/opencode/bin/sync-native-agents.py --check
```

Expose them to OpenCode by symlinking each generated `*.md` file into
`$HOME/.config/opencode/agent/` or a project `.opencode/agent/` directory,
using `opencode_setting/opencode-agents` as the projection source. Do not expose
`adapters/claude/agents/` as OpenCode-native agents.

## Native Command Projection

`adapters/opencode/commands/` contains OpenCode-native command projections
generated from portable `capabilities/*.md` specs. Each command includes
OpenCode's `$ARGUMENTS` placeholder so runtime command arguments are visible to
the portable capability contract:

```bash
adapters/opencode/bin/sync-native-commands.py --check
```

Expose them to OpenCode by symlinking each generated `*.md` file into
`$HOME/.config/opencode/command/` or a project `.opencode/command/` directory,
using `opencode_setting/opencode-commands` as the projection source. Do not
expose `adapters/claude/commands/` as OpenCode-native commands.

## Native Guard Plugin Projection

`adapters/opencode/plugins/agent-harness-guards.js` contains an OpenCode-native
JS plugin that runs adapter preflight guards around tool and command execution.
`tool.execute.before` delegates write safety checks to `preflight.sh write`;
`command.execute.before` enforces the spec read gate for `autopilot-code` /
`autopilot-spec` via `preflight.sh capability` (throwing to abort an ungrounded
command); `tool.execute.after` drops the spec read marker via `preflight.sh
read` on a `prd.md` read and delegates design HTML saves to `preflight.sh
design`:

```bash
node --check adapters/opencode/plugins/agent-harness-guards.js
```

Expose it to OpenCode by symlinking the generated projection into a project or
global plugin directory:

```bash
mkdir -p .opencode/plugins
ln -sfn "$AGENT_HOME/opencode_setting/opencode-plugins/agent-harness-guards.js" .opencode/plugins/agent-harness-guards.js
```

The plugin bridges to `adapters/opencode/bin/preflight.sh`; it does not copy or
invoke Claude hook files. Keep explicit `preflight.sh` calls as the fallback
path for runtimes or invocations where plugins are disabled. When a runtime
loads a copied plugin file instead of a symlinked projection, set `AGENT_HOME`
to the harness repo so the plugin can resolve `adapters/opencode/bin/preflight.sh`.

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

OpenCode wrapper 는 `AGENT_MODEL_FAST`, `AGENT_MODEL_DEEP`,
`AGENT_MODEL_EXTERNAL`, `AGENT_MODEL_ORCHESTRATOR`,
`AGENT_VARIANT_FAST`, `AGENT_VARIANT_DEEP`,
`AGENT_VARIANT_EXTERNAL`, `AGENT_VARIANT_ORCHESTRATOR` 같은 환경변수로
이 mapping 을 드러낸다. 공통 skill 은 concrete model name 을 요구하지
않고 role 의미만 요구한다.

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
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
OPENCODE_CONFIG_CONTENT='{"skills":{"paths":["/path/to/agent_setting/opencode_setting/opencode-skills"]}}' \
  opencode debug skill --pure
```

When porting a behavior, copy the underlying invariant from `CORE.md`,
`WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to OpenCode's
tool, permission, agent, and session model.
