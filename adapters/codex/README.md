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
marketplace projection at `adapters/codex/plugin-marketplace/`. Do not
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
| Native mode guides | `adapters/codex/modes/` |
| Native plugin | `adapters/codex/plugins/agent-harness-codex` |
| Native hooks | `adapters/codex/hooks/` |
| Design scaffolds | `adapters/codex/scaffolds/` |
| Selected tool projection | `adapters/codex/tools/` |
| Selected utility projection | `adapters/codex/utilities/` |

## Runtime Mapping

| Core Concept | Codex Implementation |
|---|---|
| capability | Read `capabilities/README.md` for meaning; run `adapters/codex/bin/preflight.sh capability-info <capability>` to confirm Codex realization; use `adapters/codex/skills/<capability>/SKILL.md` as Codex-native guidance |
| native skill/plugin surface | Skills are materialized under `adapters/codex/skills/`; the installable plugin projection is materialized under `adapters/codex/plugins/agent-harness-codex`. Command-like capability entrypoints use these native Skills/plugin surfaces and are verified with Codex discoverability (`codex debug prompt-input`) |
| native hook surface | `adapters/codex/hooks/hooks.json` registers Codex `SessionStart` lifecycle prep, `SessionEnd`/`Stop` memory sync/distill, `UserPromptSubmit` prompt signals and turn nudges, `PermissionRequest` harness status snapshots, `PreToolUse` write guards, `PostToolUse` spec read markers, and `PostToolUse` design HTML checks; explicit preflight remains fallback |
| shell I/O hook boundary | Structured write tools (`Write`, `Edit`, `MultiEdit`, `apply_patch`, `functions.apply_patch`) and structured `Read` are guarded. Shell/Bash/`functions.exec_command` reads and writes are target-ambiguous and unsupported by file-level hooks, so run explicit `preflight.sh write`, `preflight.sh read`, or `preflight.sh design` before using shell I/O on guarded paths |
| role profile | Use `roles/README.md` for meaning; Codex custom agents are materialized under `adapters/codex/agents/*.toml` and still call `adapters/codex/bin/preflight.sh role <portable-role>` for concrete model/reasoning mapping |
| role mode | Run `adapters/codex/bin/preflight.sh mode-info <family/mode>` before using a `roles/modes/` fragment; use the reported `native_mode_path` under `adapters/codex/modes/`; portable modes can be used directly, tool-contract modes require equivalent tools, unsupported modes report `fallback=reference-only` when no Codex-native runtime surface exists |
| native mode surface | Mode guides are generated under `adapters/codex/modes/` from `roles/modes/`; design modes additionally require the Codex visual-harness tool contract before claiming rendered visual completion |
| adapter bootstrap | Load `adapters/codex/AGENTS.md`, then `core/CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| permission model | Run `adapters/codex/bin/preflight.sh permissions`; use Codex native approval policy and sandbox settings, not Claude `allowedTools` |
| MCP config | Run `adapters/codex/bin/preflight.sh mcp [--check]`; use Codex native `codex mcp`/config surfaces, not Claude `settings.json` MCP payloads |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| workflow start cleanup | Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh start [cwd] [session-id]`; run it manually when hooks are unavailable |
| tracked/untracked signal | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`; tracked output includes `routing_contract=core/WORKFLOW.md`, `routing_action=read-workflow-and-select-codex-skill`, and `capability_entrypoints=codex-native-skills-plugin`; run them manually when hooks are unavailable |
| harness status snapshot | Run `adapters/codex/bin/preflight.sh status [cwd] [session-id]` for read-only workflow, artifact, notes, worktree, and git-risk signals. This does not replace Codex `/statusline` for model/context/token/session fields |
| UI boundary | Run `adapters/codex/bin/preflight.sh ui-info` to report the Codex-native UI boundary. Codex `/statusline` and `/title` configure built-in footer/title items; arbitrary Claude-style live statusline scripts are unsupported, so harness signals use `preflight.sh status` and hook `statusMessage`. `/statusline` persists choices in runtime-owned `$CODEX_HOME/config.toml`; `codex_setting/codex-config/tui-statusline.toml` records the harness-recommended footer fragment without projecting the full config file. Run `adapters/codex/bin/preflight.sh tui-config` only when explicitly applying that fragment to the runtime-owned config |
| adapter readiness | Run `adapters/codex/bin/preflight.sh doctor` to check manifest freshness, native skill/plugin/agent/mode projections, hook bridge syntax, and boundary rules in one command. Add `--runtime` to include the installed `$CODEX_HOME` projection check |
| runtime projection install | Run `adapters/codex/bin/install-runtime-projection.sh [--install-plugin]` to wire `$CODEX_HOME` (default `$HOME/.codex`) to the harness projection: `agent-*` pointers, `hooks.json`, native skill/agent symlinks, and the read-only `agent-config` fragment pointer. Idempotent; never touches Codex credentials, sessions, history, logs, caches, `config.toml`, or local databases (a pre-existing real `hooks.json` is backed up to `hooks.json.pre-harness`). Run `adapters/codex/bin/check-runtime-projection.sh`, `adapters/codex/bin/preflight.sh runtime-projection`, or `adapters/codex/bin/preflight.sh doctor --runtime` for a read-only `status=ok|failed` validation of the wiring, linked skills/agents, bootstrap discovery, plugin presence, and hook trust records. `check=hook-trust:review-needed` means run `/hooks` in Codex and trust the changed harness hooks; set `CODEX_REQUIRE_HOOK_TRUST=1` to make missing trust fail runtime checks |
| tracked/untracked toggle | Portable `utilities/workflow-toggle.sh`; run `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only on explicit user request |
| headless dispatch | Tool-contract check: `adapters/codex/bin/preflight.sh headless --check <worktree>` verifies the worktree, `codex exec` availability, and installed Codex runtime projection (`agent-harness`, bootstrap, hooks, native Skills, native Agents, and native Modes). Use `adapters/codex/bin/preflight.sh dispatch --dry-run|--register|--start --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <quick|light|standard|thorough|adversarial>` to build the Codex command and register open jobs before launch. The wrapper validates `capability-info`, `mode-info`, and the portable QA level before writing `.dispatch/jobs.log`, then writes a Codex harness prompt that loads `AGENTS.md`, runs `prompt-signal`/`mode`, checks capability/mode realization, applies spec-read/capability/write gates, and bans Claude-native runtime files. `--start` reruns the same runtime projection check before launching. Use `adapters/codex/bin/preflight.sh liveness [jobs.log]` while waiting on dispatched work; it matches open jobs to Codex session JSONL files by `cwd` and transcript mtime. Use `adapters/codex/bin/preflight.sh harvest --slug <slug> --mark-done` after main-session harvest to mark registry rows done only; it does not merge or clean worktrees |
| autopilot routing | Codex exposes `autopilot-*` as native Skills/plugin entries and can select matching Skills from descriptions, but the adapter does not emulate Claude slash-command routing. `prompt-signal` emits the portable routing contract and Codex-native entrypoint surface on tracked work; for spec-backed work, rely on spec-read/capability gates plus the relevant Skill or explicit dispatch wrapper |
| subagent delegation | Codex supports native subagent workflows, but they are explicit or main-dispatched. Use prompt-directed subagents or `preflight.sh dispatch`; do not treat UI/status state as an automatic delegation trigger |
| artifact-order gate | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| material browser fetch | Tool-contract check: `adapters/codex/bin/preflight.sh browser-fetch --check <url>` verifies rendered browser access through the adapter-owned Playwright launcher before using `roles/modes/material/browser-fetch.md`. Exit 69 means the local browser stack is unavailable |
| material data script | Tool-contract check: `adapters/codex/bin/preflight.sh data-script --check <script.py>` verifies generated Python analysis scripts through the adapter-owned launcher before using `roles/modes/material/data-script.md` |
| material figure generation | Tool-contract check: `adapters/codex/bin/preflight.sh figure-gen --check <script.py>` verifies generated matplotlib/seaborn figure scripts through the adapter-owned launcher before using `roles/modes/material/figure-gen.md` |
| material PDF extract | Tool-contract check: `adapters/codex/bin/preflight.sh pdf-extract --check <file.pdf>` verifies local PDF text extraction through the adapter-owned launcher before using `roles/modes/material/pdf-extract.md`. Exit 69 means the local extractor is unavailable |
| material web image search | Tool-contract check: `adapters/codex/bin/preflight.sh web-image-search --check <query>` verifies that `CODEX_WEB_IMAGE_SEARCH_CMD` or `AGENT_WEB_IMAGE_SEARCH_CMD` provides a local image-search command before using `roles/modes/material/web-image-search.md`. Exit 69 means no provider is configured |
| QA security review | Portable read-only persona: `roles/modes/qa/security-review.md` is consumed with Codex file and git diff tools. Do not project or invoke Claude `/security-review` |
| QA verification runner | Tool-contract check: `adapters/codex/bin/preflight.sh verification-runner --check -- <command>` verifies explicit QA/test commands through the adapter-owned runner before using `roles/modes/qa/test.md` |
| code-test capability | `capability-info code-test` reports `status=tool-contract`, `tool_contract=verification-runner`, `runtime_surface=adapter-owned-verification-runner`, and the `test_logs/` artifact contract before claiming verification support |
| research claim verify | Tool-contract check: `adapters/codex/bin/preflight.sh claim-verify --check <claim>` verifies that `CODEX_CLAIM_VERIFY_CMD` or `AGENT_CLAIM_VERIFY_CMD` provides an external verification command before using `roles/modes/research/claim-verify.md`. Exit 69 means no provider is configured |
| design post-write verification | `core/HOOKS.md` defines the invariant; run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| design visual harness | Tool-contract check: `adapters/codex/bin/preflight.sh visual-harness <file.html>` runs the adapter-owned render/screenshot/console wrapper. Inspect the reported screenshot before claiming visual completion. Do not project Claude Design MCP files into Codex |
| design scaffold assets | Use `<agent-home>/scaffolds/` for reusable HTML scaffold assets. `codex_setting/scaffolds` points at the Codex-owned projection under `adapters/codex/scaffolds/`, not Claude runtime paths |
| spec read gate | `core/HOOKS.md` defines marker/check semantics; Codex `PostToolUse` Read hook records actual `spec/prd.md` reads, and `adapters/codex/bin/preflight.sh read <prd.md> [session-id]` remains the explicit fallback. Run `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| git safety gate | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory write guard | `core/HOOKS.md` defines the invariant; included in `adapters/codex/bin/preflight.sh write <file> [session-id]` |
| memory injection | Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh memory [cwd]`; run it manually when hooks are unavailable |
| memory sync | Codex `SessionEnd` and `Stop` hook bridges run `adapters/codex/bin/preflight.sh session-end [cwd] [session-id]`, which performs `mem sync` and then runs automatic distillation by default (the read-only `codex exec` worker is verified tool-free); opt out with `CODEX_DISTILL_ENABLE=0` |
| memory turn nudge | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh turn-nudge [cwd] [session-id]`; it is deterministic and launches distillation when the configured interval is reached. Automatic distillation is on by default (`CODEX_DISTILL_ENABLE` defaults to `1`); opt out with `CODEX_DISTILL_ENABLE=0` |
| memory recall injection | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh recall <prompt> [cwd]`; run it manually when hooks are unavailable |
| oncall briefing injection | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh briefing [cwd]`; run it manually when hooks are unavailable |
| loop guidance | `adapters/codex/bin/preflight.sh loop-info <oncall|note|study|drill>` reports whether a loop has a Codex manual contract, unsupported executable projection, or missing native implementation; `note` remains an external scheduler loop while the related `autopilot-note` capability is available on demand through Codex-native Skill/plugin projections |
| capability mapping | `adapters/codex/bin/preflight.sh capability-info <capability>` reports Codex's native Skill/plugin realization and instruction-only or tool-contract status; root Skill compatibility references are not projected and report `compat_reference=not-projected` |
| autopilot-code pipeline | `capability-info autopilot-code` and `route autopilot-code` additionally report `pipeline_contract=code-plan>code-execute>code-test>code-report`, optional `code-refine`, required plan artifacts, role mapping, and the dispatch fallback |
| model role mapping | `adapters/codex/bin/preflight.sh role <portable-role>` resolves portable model roles through Codex adapter environment variables |
| mode mapping | `adapters/codex/bin/preflight.sh mode-info <family/mode>` reports whether a mode is portable, tool-contract, or unsupported for Codex; tool-contract and unsupported adapter-coupled modes include machine-readable `tool_contract`, optional `tool_contract_check`, `runtime_surface`, and `fallback` fields |
| QA policy mapping | `adapters/codex/bin/preflight.sh qa-policy <level> [code|research|doc|general]` maps portable QA levels from `core/CONVENTIONS.md` to Codex reviewer roles, external-adversary requirements, max rounds, and inline fallback reporting |
| memory distill delta | Codex session transcript extraction is available through `adapters/codex/bin/preflight.sh distill-delta <session-id>` |
| memory distill proposal | `adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` reports `status=tool-contract` and exits 69 until `CODEX_DISTILL_ENABLE=1` is explicit. Enabled runs use a constrained Codex exec proposal worker; memory mutates only when both `CODEX_DISTILL_APPLY=1` and `CODEX_DISTILL_CONTRACT_ACCEPTED=1` are explicit |
| memory store | `tools/memory/mem.py` is runtime-neutral; detached distillation worker execution remains adapter-specific |

## Tool Projection

`codex_setting/tools` intentionally points at `adapters/codex/tools/`, not the
full shared `tools/` directory. The adapter currently exposes only tools that
Codex wrappers use directly:

- `memory/mem.py` (Codex-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (Codex-owned launcher for recall)
- `material/browser-fetch.sh` (Codex-owned launcher for rendered web page extraction)
- `material/data-script.sh` (Codex-owned launcher for Python data-analysis scripts)
- `material/figure-gen.sh` (Codex-owned launcher for generated matplotlib figure scripts)
- `material/pdf-extract.sh` (Codex-owned launcher for local PDF text extraction)
- `material/web-image-search.sh` (Codex-owned launcher for configured image search providers)
- `qa/verification-runner.sh` (Codex-owned launcher for explicit verification commands)
- `research/claim-verify.sh` (Codex-owned launcher for configured external claim verification providers)
- `design/visual-harness.sh` (Codex-owned launcher for render/screenshot/console checks)

Harness development tools and Claude-coupled helper surfaces such as
`build-manifest.py` and `web-bundle` stay out of the Codex projection until
Codex has a documented runtime realization for them. The shared `design-mcp`
package is not projected wholesale; Codex exposes only the adapter-owned visual
harness launcher.

## Utility Projection

`codex_setting/utilities` intentionally points at
`adapters/codex/utilities/`, not the full shared `utilities/` directory. The
adapter currently exposes only utility files that Codex wrappers or docs use:

- `agent-home.sh` (Codex-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `harness-status.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Claude-specific helpers such as the shared `dispatch-liveness.sh` stay out of
the Codex projection. Codex exposes its adapter-owned liveness command through
`adapters/codex/bin/preflight.sh liveness [jobs.log]`, backed by
`~/.codex/sessions/**/*.jsonl` metadata and mtime.
Codex also exposes `adapters/codex/bin/preflight.sh harvest` for registry-only
status and selected `open` to `done` updates. It intentionally does not merge
branches or delete worktrees.

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

Expose the repo-local marketplace through `codex_setting/codex-plugin-marketplace`.
That projection is a dedicated marketplace root, not a link to the entire
Codex adapter:

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
`adapters/codex/bin/preflight.sh role <portable-role>`. The generated
instructions also encode role-specific runtime boundaries such as QA
read-only behavior, depth-one delegation, write preflight requirements, and
external-adversary independence. Mixed or variable role profiles include
`Codex role-map inputs` so the concrete role can be selected by mode and QA
policy instead of flattening the profile to one model role. Do not expose
`adapters/claude/agents/` as Codex-native agents.

Current validation is structural plus install-path validation: the boundary
guard verifies generated TOML fields, portable role references, role-map
resolution, role-specific runtime boundaries, and absence of non-Codex adapter
paths. Codex CLI 0.142.x exposes `codex debug prompt-input` for
bootstrap/Skill/plugin discovery, but it does not expose a `codex debug agent` listing surface. Add a runtime discovery test when Codex exposes one.

## Native Mode Projection

`adapters/codex/modes/` contains Codex-owned mode realization guides generated
from `roles/modes/`. These files are not copied from another runtime. They keep
the portable mode source visible while mapping each mode through
`adapters/codex/bin/preflight.sh mode-info <family/mode>`. Each generated guide
also embeds a sanitized projected portable mode contract so Codex sees the
actual procedure, with non-Codex runtime surfaces rewritten to Codex
preflight/tool-contract wording.

```bash
adapters/codex/bin/sync-native-modes.py --check
```

`mode-info` reports `native_mode_path=adapters/codex/modes/<family>/<mode>.md`.
For tool-contract modes, run the reported `tool_contract_check` or report the
unavailable contract before claiming support. Design modes report
`realization=codex-native-mode-with-tool-contract` and require
`adapters/codex/bin/preflight.sh visual-harness <file.html>` before claiming
rendered visual verification.

## Command-Like Entries

Custom prompts are deprecated in Codex. Do not generate a `prompts/` projection
or copy Claude slash-command files into Codex. Reusable command-like capability
entrypoints are represented by Codex-native Skills and the installable
`agent-harness-codex` plugin.

## Native Hook Projection

`adapters/codex/hooks/` contains a Codex-native `hooks.json`, a validated
`run-hook.sh` launcher, and concrete adapter-owned hook bridges. The
`SessionEnd` and `Stop` bridges run `mem sync` and automatic distillation (on by
default; opt out with `CODEX_DISTILL_ENABLE=0`). The `UserPromptSubmit` bridge extracts
prompt text from top-level and nested message/content payloads for recall, and
also runs the deterministic N-turn distill nudge under the same default. The
`PermissionRequest` bridge reports the read-only harness status snapshot while
Codex owns approval and sandbox decisions. The
`PreToolUse` bridge runs before write/edit/multiedit/patch tools, including
qualified `functions.apply_patch` payloads, and delegates
artifact-order, git-state, and memory-write checks to
`adapters/codex/bin/preflight.sh write`. The `PostToolUse` Read bridge records
actual `spec/prd.md` reads through `adapters/codex/bin/preflight.sh read`. The
`PostToolUse` design bridge runs after write/edit/multiedit/patch tools,
including qualified `functions.apply_patch` payloads, and delegates
design HTML saves to `adapters/codex/bin/preflight.sh design`.

Shell/Bash/`functions.exec_command` I/O is outside current file-target hook
coverage. Treat shell reads/writes to guarded paths as an explicit tool
contract: run `preflight.sh write`, `preflight.sh read`, or
`preflight.sh design` manually before the shell command.

Expose it through `codex_setting/codex-hooks`, not through a plain `hooks/`
projection:

```bash
ln -sfn "$AGENT_HOME/codex_setting/codex-hooks/hooks.json" "$HOME/.codex/hooks.json"
```

The pre-write bridge accepts Codex hook stdin JSON across top-level and nested
tool payload shapes (`tool_name`/`tool_input`, `tool` + `input`, or
`toolUse.input`) and resolves `cwd` / `session_id` from top-level or nested
runtime payloads. It returns a `decision=block` hook result when the shared
guard fails. The read bridge is a marker path only, and the design bridge is a
post-write alert path only.
Neither bridge consumes Claude `settings.json` or Claude hook payloads.

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
`AGENT_MODEL_EXTERNAL`, `AGENT_MODEL_ORCHESTRATOR`,
`AGENT_REASONING_FAST`, `AGENT_REASONING_DEEP`,
`AGENT_REASONING_EXTERNAL`, `AGENT_REASONING_ORCHESTRATOR` 같은
환경변수로 이 mapping 을 드러낸다.
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
