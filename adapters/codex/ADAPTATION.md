# Codex Adaptation

This adapter is not a Claude Code surface clone. It defines the required mapping
so Codex can reproduce the portable harness invariants through Codex-native
surfaces, tool contracts, and explicit fallbacks without copying Claude-specific
assumptions into the common core.

## Design Principle

Codex adaptation targets harness parity on Codex, not Claude surface parity.
Start from the portable invariant in `core/`, then map it onto Codex-native
features where they exist. Claude files are implementation references, not files
to port wholesale.

Use Codex-native surfaces first for model/session/context/status, approvals,
sandboxing, skills/plugins, and built-in slash commands. Add adapter wrappers
only for harness-specific signals that Codex does not provide directly.

## External Reference Lessons

GSD Core (`https://github.com/open-gsd/gsd-core`) is a useful cross-runtime
installer reference pattern, not a source to copy. The relevant lesson is the
seam:

- keep the workflow/capability meaning canonical;
- describe each runtime's artifact layout and config surface as data;
- convert canonical files into runtime-native artifacts;
- prove the runtime discovers those artifacts;
- fail closed when a runtime feature is undocumented or missing.

For this adapter, that means Codex support should not be measured by whether
Claude files are visible under `codex_setting/`. It should be measured by
whether Codex has a native entrypoint or an explicit wrapper for the portable
invariant.

## Native Codex Surfaces

| Codex runtime surface | Adapter source | Projection |
|---|---|---|
| Session bootstrap | `adapters/codex/AGENTS.md` | `codex_setting/AGENTS.md` |
| Adapter guide | `adapters/codex/README.md` | `codex_setting/README.md` |
| Common contract | `core/` | `codex_setting/core` |
| Capability catalog | `capabilities/` | `codex_setting/capabilities` |
| Role catalog | `roles/` | `codex_setting/roles` |
| Preflight wrappers | `adapters/codex/bin/` | `codex_setting/bin` |
| Skills | `adapters/codex/skills/<name>/SKILL.md` generated from `capabilities/` | `codex_setting/codex-skills` |
| Custom agents | `adapters/codex/agents/<role>.toml` generated from `roles/README.md` | `codex_setting/codex-agents` |
| Mode guides | `adapters/codex/modes/*/*.md` generated from `roles/modes/` with Codex mode-info contracts | `codex_setting/codex-modes` |
| Plugin marketplace | `adapters/codex/plugin-marketplace/.agents/plugins/marketplace.json` plus `adapters/codex/plugin-marketplace/plugins/agent-harness-codex` | `codex_setting/codex-plugin-marketplace` |
| Hook bridge | `adapters/codex/hooks/hooks.json`, `adapters/codex/hooks/pretooluse-write-guard.py`, `adapters/codex/hooks/posttooluse-design-check.py` | `codex_setting/codex-hooks` |
| Permission/sandbox contract | `adapters/codex/bin/preflight.sh permissions` | `codex_setting/bin/preflight.sh permissions` |
| MCP contract | `adapters/codex/bin/preflight.sh mcp` | `codex_setting/bin/preflight.sh mcp` |
| Design scaffold assets | `adapters/codex/scaffolds/` Codex-owned projection of shared scaffold HTML assets | `codex_setting/scaffolds` |
| Shared helper tools | selected `tools/`, selected `utilities/` | `codex_setting/tools`, `codex_setting/utilities` |
| Selected tools | `adapters/codex/tools/` adapter launchers plus selected portable tool projections | `codex_setting/tools` |
| Selected utilities | `adapters/codex/utilities/` adapter wrappers plus selected portable utility projections | `codex_setting/utilities` |

## Native Skill And Plugin Surface

Current Codex support includes generated native Skill projections:
`adapters/codex/skills/<name>/SKILL.md` is generated from
`capabilities/<name>.md` by `adapters/codex/bin/sync-native-skills.py` and
projected as `codex_setting/codex-skills`.

The same generated skills are also packaged into the adapter-owned Codex plugin
`adapters/codex/plugins/agent-harness-codex`, with repo-local marketplace
metadata projected through `adapters/codex/plugin-marketplace/`. This makes
the harness discoverable through Codex's native plugin installer without
exposing Claude Skill files.

Codex custom prompts are deprecated. Command-like harness entries are therefore
realized through native Skills and the installable plugin, not through
`prompts/` files or Claude slash-command projections.

Before adding or changing Codex-native skills or plugins:

1. Use `capabilities/<name>.md` and `roles/` as source, not
   `skills/<name>/SKILL.md` or `adapters/claude/skills/`.
2. Generate or maintain concrete adapter-owned output under an explicit Codex
   adapter path, for example `adapters/codex/skills/<name>/SKILL.md`.
3. Keep Codex frontmatter, invocation syntax, sandbox/approval assumptions, and
   plugin metadata in the Codex adapter.
4. Add a guard that proves every generated Codex skill maps to a portable
   capability and that no Claude-native Skill file is exposed as Codex-native.
5. Verify discoverability using the Codex runtime contract, not byte parity with
   Claude files.

Design capabilities are a tool-contract exception: Codex has native Skill
guidance for them, but must run the adapter visual harness before claiming full
support. `capability-info` reports `status=tool-contract` for those capability
entries. Design mode fragments now have Codex-owned guides under
`adapters/codex/modes/design/`; `mode-info` reports the guide path and the
`visual-harness` contract, and Codex must report unavailable if the harness
cannot run. All generated mode guides embed sanitized projected portable mode
contracts so Codex sees the actual procedure while non-Codex runtime surfaces
are rewritten to Codex preflight/tool-contract wording.

`roles/modes/material/browser-fetch.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh browser-fetch --check <url>` verifies rendered
browser access through `adapters/codex/tools/material/` and reports exit 69
when the local Playwright browser stack is unavailable.

`roles/modes/material/data-script.md` is the first material mode with a
Codex-owned executable tool-contract surface:
`adapters/codex/bin/preflight.sh data-script --check <script.py>` verifies
generated Python analysis scripts through `adapters/codex/tools/material/`.

`roles/modes/material/figure-gen.md` has a Codex-owned executable tool-contract
surface:
`adapters/codex/bin/preflight.sh figure-gen --check <script.py>` verifies
generated matplotlib/seaborn figure scripts through
`adapters/codex/tools/material/`.

`roles/modes/material/pdf-extract.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh pdf-extract --check <file.pdf>` verifies
local PDF text extraction through `adapters/codex/tools/material/` and reports
exit 69 when the local extractor is unavailable.

`roles/modes/material/web-image-search.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh web-image-search --check <query>` verifies a
configured image-search provider command through `adapters/codex/tools/material/`
and reports exit 69 when no provider is configured.

`roles/modes/qa/security-review.md` is portable read-only mode guidance for
Codex. It is consumed with Codex file and git diff tools and does not project
or invoke Claude's `/security-review` slash command.

`roles/modes/research/claim-verify.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh claim-verify --check <claim>` verifies a
configured external verification provider command through
`adapters/codex/tools/research/` and reports exit 69 when no provider is
configured.

`roles/modes/qa/test.md` has a Codex-owned executable tool-contract surface:
`adapters/codex/bin/preflight.sh verification-runner --check -- <command>`
checks explicit verification commands and the same wrapper can execute them
with a bounded timeout. `capability-info code-test` exposes the same
`verification-runner` contract plus the `test_logs/` artifact contract so the
capability and mode surfaces agree.

The boundary guard checks that generated Codex skills and the generated Codex
plugin remain in sync, and that neither surface is built from Claude Skill
files.

## Native Custom Agent Surface

Codex supports custom subagents through TOML files under `$CODEX_HOME/agents/`
or project `.codex/agents/`. This adapter materializes those role profiles as
`adapters/codex/agents/<role>.toml`, generated from `roles/README.md` by
`adapters/codex/bin/sync-native-agents.py` and projected as
`codex_setting/codex-agents`.

Each file defines Codex's required custom agent fields (`name`, `description`,
and `developer_instructions`) while leaving concrete model and reasoning
choices to `adapters/codex/bin/preflight.sh role <portable-role|role-profile|pipeline-stage>` and the
runtime's parent session/config inheritance. The generated instructions also
encode role-specific runtime boundaries such as QA read-only behavior,
depth-one delegation, write preflight requirements, and external-adversary
independence. Mixed or variable role profiles include `Codex role-map inputs`
so the concrete role can be selected by mode and QA policy instead of
flattening the profile to one model role. Do not project Claude Agent files or
OpenCode Agent files into Codex.

Validation is currently structural plus install-path validation. The boundary
guard verifies generated TOML fields, portable role references, role-map
resolution, role-specific runtime boundaries, and absence of non-Codex adapter
paths. Codex CLI 0.142.x exposes `codex debug prompt-input` for
bootstrap/Skill/plugin discovery, but it does not expose a `codex debug agent` listing surface; add runtime discovery coverage when Codex exposes one.

## Native Hook Surface

Codex supports lifecycle hooks through `hooks.json` and inline config. This
adapter materializes a Codex-native hook projection under `adapters/codex/hooks/`.
Hook commands enter through `run-hook.sh`, which validates `AGENT_HOME` or the
Codex harness pointer before executing bridge scripts.
The `SessionStart` bridge calls `adapters/codex/bin/preflight.sh start` and
`memory` for stale workflow cleanup and memory context, then emits the collected
context as `hookSpecificOutput.additionalContext`. The `SessionEnd` and
`Stop` bridges call `session-end` for `mem sync` plus the verified automatic distill worker
(default on; `CODEX_DISTILL_ENABLE=0` opt-out) while emitting only Codex-valid
minimal hook JSON (`{}`) so Stop hook output never violates Codex parsing. The
`UserPromptSubmit` bridge calls `prompt-signal`, `mode`, `recall`, `briefing`,
and `turn-nudge` for prompt-time workflow and memory signals, then emits the
collected prompt context as one `hookSpecificOutput.additionalContext`. The structured
`prompt-signal` output reports `routing_contract=core/WORKFLOW.md`,
`routing_action=read-workflow-and-select-codex-skill`, and
`capability_entrypoints=codex-native-skills-plugin` for tracked work, extracting prompt
text from top-level and nested message/content payloads. The `PermissionRequest`
bridge calls `status` and emits it as `hookSpecificOutput.additionalContext` to
surface read-only harness context while Codex owns approval and sandbox
decisions. The write bridge registers
`PreToolUse` for write/edit/multiedit/patch tools, including qualified
`functions.apply_patch` payloads, and calls
`adapters/codex/bin/preflight.sh write <file> <session-id>`, which runs
the portable artifact-order, git-state, and memory-write guards, plus the spec
read gate for spec-changing artifacts (see below). The read bridge
registers `PostToolUse` for `Read` and calls `adapters/codex/bin/preflight.sh
read <file> <session-id>` so actual `spec/prd.md` reads satisfy spec-backed
capability gates.

Spec read gate — fitted to Codex's interception point. Claude hard-denies an
ungrounded `autopilot-code`/`autopilot-spec` *Skill* via `PreToolUse[Skill]`.
Codex has no skill-invocation event (Skills are implicitly selected, and there is
no slash-command router), so the same portable invariant — no spec-changing work
without a current `prd.md` read marker — is enforced where Codex *can* intercept:
the write of a spec-changing artifact. `preflight.sh write` runs the shared
`spec-skill-gate.sh` against `<artifact-root>/plans/*` (autopilot-code) and the
`spec/` blueprints (autopilot-spec), using the same per-cwd marker the read
bridge writes. Creating the first `prd.md` is not gated (no marker target yet —
artifact-order still applies); editing an existing artifact while ungrounded is
hard-denied. This is marginally stricter than Claude's skill-entry gate (it also
covers direct artifact edits), in the safe direction: it never weakens the
invariant. The headless `dispatch` wrapper additionally applies the gate before
launch. The design bridge registers `PostToolUse` for the same
write/edit/multiedit/patch surface, including qualified `functions.apply_patch`
payloads, and calls `adapters/codex/bin/preflight.sh design
<file>` for saved design HTML files.

Current Codex hook coverage includes structured tools plus targeted shell
detection, not arbitrary shell I/O coverage. Shell/Bash/`functions.exec_command`
commands with obvious write redirects, common mutation commands (`tee`, `touch`,
`cp`, `mv`, `rm`, `install`, `rsync`), `dd of=...`, `sed -i`, direct
`spec/prd.md` reads, and design HTML save paths are routed through adapter
hooks; target-ambiguous shell
reads/writes still require the agent to run the matching `preflight.sh write`,
`preflight.sh read`, or `preflight.sh design` wrapper. `preflight.sh prompt-signal` and
`preflight.sh permissions` report this as
`shell-read-write-targeted-detection-explicit-preflight-fallback`; do not claim
Claude-style hard hook parity for ambiguous shell I/O until Codex provides a
fully target-aware shell hook surface.

Do not project Claude `hooks/` or `settings.json` into Codex. Use
`codex_setting/codex-hooks` as the install source, and keep explicit
`preflight.sh` calls as fallback where Codex hooks are disabled or untrusted.
`adapters/codex/bin/check-runtime-projection.sh` reports `check=hook-trust:ok`
or `check=hook-trust:review-needed`; run `/hooks` in Codex after hook definition
changes. `check=hook-trust:ok session_end=stop-alias` means Codex trusted the
`Stop` hook and the projection maps it to the same session-end bridge as
`SessionEnd`. Use `adapters/codex/bin/preflight.sh runtime-projection
--require-hook-trust` or `adapters/codex/bin/preflight.sh doctor --runtime-strict`
when hook trust must fail runtime checks.
The lifecycle hooks are informational/context bridges and do not replace
deterministic write guards. The design hook is a console-check alert path, not a
full render/screenshot visual harness.

Codex CLI 0.142.x exposes `codex debug prompt-input`, but not a hook listing or
hook firing debug surface. Current tests validate `hooks.json` structure and
execute the concrete bridge scripts with synthetic Codex hook payloads,
including top-level and nested tool input, `cwd`, and session variants; add a
runtime hook discovery test when Codex exposes a hook debug surface.

## Explicit Non-Support

Codex must not consume these Claude-native files as native configuration:

| Claude-native surface | Codex status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; Codex needs wrapper/preflight equivalents |
| `adapters/claude/commands/` | Not consumable; command-like harness entries use Codex-native Skills and the installable `agent-harness-codex` plugin |
| `skills/*/SKILL.md` | Compatibility reference only; Codex should start from `capabilities/README.md` |
| `adapters/claude/statusline.sh` | Not consumable; input schema is Claude statusline JSON |
| `adapters/claude/track-toggle.sh` | Do not consume; portable semantics live in `utilities/workflow-toggle.sh`, and Codex exposes them through `preflight.sh track` |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; Codex custom agents are generated from `roles/README.md` |
| `roles/modes/*/*` | Portable source fragments; Codex consumes generated `adapters/codex/modes/*/*.md` guides plus `mode-info` metadata |

## Status Surface Boundary

Codex has its own `/statusline` configuration for the TUI footer. Do not replace
it with `adapters/claude/statusline.sh`, and do not duplicate Codex-native footer
items such as model, context, token/usage/limits, git baseline, session, or
Codex fast-mode state.

Codex UI customization is therefore a partial native parity surface, not a
Claude statusline clone. `/statusline` and `/title` configure Codex-owned
built-in item IDs; the adapter reports this boundary through
`adapters/codex/bin/preflight.sh ui-info`. Harness-specific state remains in
`preflight.sh status` and hook `statusMessage` output until Codex exposes an
arbitrary dynamic footer provider.

Harness-specific status signals still need Codex-native realization:

| Harness signal | Codex direction |
|---|---|
| stale workflow bypass flag cleanup | Codex `SessionStart` hook bridge runs `preflight.sh start`; explicit preflight remains fallback when hooks are unavailable |
| tracked/untracked workflow state | Codex `UserPromptSubmit` hook bridge runs `preflight.sh prompt-signal` and `preflight.sh mode`; explicit preflight remains fallback when hooks are unavailable |
| workflow/artifact/notes/git-risk snapshot | explicit `preflight.sh status`; keep Codex `/statusline` for native model/context/token/session fields |
| UI boundary report | explicit `preflight.sh ui-info`; reports built-in footer/title support, unsupported arbitrary live statusline scripts, Skill/plugin autopilot entrypoints, and explicit/main-dispatched subagent behavior |
| subagent delegation | explicit `preflight.sh subagent-info --check`; verifies the Codex `multi_agent` runtime feature and projected custom agents before claiming native subagent delegation parity |
| tracked/untracked toggle | explicit `preflight.sh track`; do not expose Claude `/track` command files |
| artifact root detection | `preflight.sh write` and shared artifact-root helper |
| headless/autopilot/background jobs | `preflight.sh headless` / `dispatch` / `liveness` / `harvest` provide the tool-contract path; `preflight.sh status` surfaces in-flight jobs as `headless_open_jobs` / `headless_open_slugs` from the dispatch registry. A Codex-native graphical display remains optional polish |
| sibling `-wt/<slug>` dispatch detection | preserve the worktree naming invariant; choose a Codex-native display surface later |
| pipeline stage nudges | preflight/AGENTS instructions first; UI only when Codex exposes a suitable surface |
| oncall/note/study/drill loop nudges | `preflight.sh briefing` plus `preflight.sh loop-info <loop>` for loop-specific support/fallback status |
| merge/rebase/merged-branch risk | `preflight.sh write` git safety checks; `preflight.sh status` reports `git_operation` (merge/rebase/cherry-pick) and `git_branch_done` (non-default branch fully merged = DONE-BRANCH hazard). A native graphical warning remains optional polish |

## Required Codex Mappings

| Portable invariant | Codex adaptation requirement |
|---|---|
| artifact order | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| git state safety | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits |
| memory write guard | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | Run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | Auto-enforced through Codex hooks: `PostToolUse[Read]` records actual `prd.md` reads, and `PreToolUse` write guard hard-denies an ungrounded write to a spec-changing artifact (`plans/*` or a `spec/` blueprint) — Codex's interception equivalent of Claude's `PreToolUse[Skill]` gate (no skill event exists). Manual fallbacks: `preflight.sh read <prd.md>` after reads, `preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| workflow start cleanup | Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh start [cwd] [session-id]`; run it manually when no automatic hook is attached |
| workflow signal | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`; run them manually when no automatic hook is attached |
| workflow toggle | Run `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly requests tracked/untracked mode switching |
| memory inject | Run `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text session-start memory injection |
| memory recall | Run `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` before prompt handling when no automatic prompt hook is attached |
| oncall briefing | Run `adapters/codex/bin/preflight.sh briefing [cwd]` before prompt handling on the dedicated agent desk |
| loop guidance | Run `adapters/codex/bin/preflight.sh loop-info <oncall|note|study|drill>` before following loop guides; Codex reports manual contracts, missing implementations, and drill auto-run restrictions without executing loop scripts. The `note` loop is an external scheduler/worklog-board contract; use the related `autopilot-note` Skill/plugin projection only for on-demand note routing |
| memory distill | Transcript delta extraction exists via `adapters/codex/bin/preflight.sh distill-delta <session-id>`. The user-facing `distill-propose` stays an explicit opt-in preview (reports `status=tool-contract`, exits 69 until `CODEX_DISTILL_ENABLE=1`). Automatic session-end and turn-nudge distillation is enabled by default: the `codex exec --sandbox read-only` worker is verified tool-free (see Distillation Boundary) and applies through `apply-distill-actions.py`; opt out with `CODEX_DISTILL_ENABLE=0` |
| worklog state signal | Run `adapters/codex/bin/preflight.sh worklog [cwd]` to inspect configured `<agent-notes-root>` / `<worklog-board-app>` paths read-only before Codex updates notes or diagnoses board state |
| role profiles | Read `roles/README.md`, then run `adapters/codex/bin/preflight.sh role <portable-role|role-profile|pipeline-stage>` to resolve Codex model/reasoning-effort settings or pipeline profile aliases to native custom agents |
| permission mapping | Run `adapters/codex/bin/preflight.sh permissions` to inspect the Codex approval/sandbox contract and confirm Claude `allowedTools` is unsupported |
| MCP mapping | Run `adapters/codex/bin/preflight.sh mcp --check` to inspect Codex's native MCP CLI/config surface; do not copy Claude `settings.json` MCP registrations or project `tools/design-mcp` wholesale |
| headless dispatch | Run `adapters/codex/bin/preflight.sh headless --check <worktree>` before Codex `exec` dispatch; it checks the worktree, command availability, and installed Codex runtime projection (`agent-harness`, bootstrap, hooks, native Skills, native Agents, and native Modes) without launching. Add `--require-hook-trust` when dispatch must prove complete Codex hook trust. Use `adapters/codex/bin/preflight.sh dispatch --dry-run|--register|--start [--require-hook-trust] --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <quick|light|standard|thorough|adversarial>` to build the Codex headless command and append `.dispatch/jobs.log` before launch. The wrapper validates `capability-info`, `mode-info`, and the portable QA level before writing `.dispatch/jobs.log`; `--register` and `--start` materialize a Codex harness prompt before appending the registry row. The prompt loads `AGENTS.md`, runs `prompt-signal`/`mode`, checks capability/mode realization, resolves pipeline role profiles, applies spec-read/capability/write gates, and bans Claude-native runtime files; `--start` reruns the same projection check before launching, and strict hook trust failure occurs before registry writes. While waiting on dispatched work, run `adapters/codex/bin/preflight.sh liveness [jobs.log]` to match open jobs to Codex session JSONL files by `cwd` and transcript mtime. After main-session harvest, run `adapters/codex/bin/preflight.sh harvest --slug <slug> --mark-done` to mark selected registry rows done; merge and worktree cleanup stay outside the adapter wrapper |
| role modes | Read `roles/MODES.md`, then run `adapters/codex/bin/preflight.sh mode-info <family/mode>`; read the reported `native_mode_path`, obey `fallback=reference-only` only for unsupported modes, and satisfy any named `tool_contract` / `tool_contract_check` before claiming tool-contract modes |
| mode guides | Use `adapters/codex/modes/<family>/<mode>.md` as the Codex-native realization guide reported by `mode-info`; satisfy named tool contracts or report unavailable before claiming support |
| design modes | Use `adapters/codex/modes/design/<mode>.md` as the Codex-native realization guide; satisfy `visual-harness` or report unavailable before claiming rendered visual verification |
| hook invariants | `adapters/codex/hooks/sessionend-lifecycle.py` realizes SessionEnd/Stop memory sync/distill hooks; `permissionrequest-lifecycle.py` realizes approval-blocker context through Codex `PermissionRequest`; `pretooluse-write-guard.py` realizes write guards (artifact-order, git-state, memory-write, and the spec read gate for spec-changing artifacts) through Codex `PreToolUse`; `posttooluse-read-marker.py` records actual spec reads through `PostToolUse`; `posttooluse-design-check.py` realizes design HTML console checks through `PostToolUse`; run explicit preflight wrappers for events not yet covered by native hooks |
| capabilities | Read `capabilities/README.md`, then run `adapters/codex/bin/preflight.sh capability-info <capability>`; do not assume Claude Skill invocation |

## Model Mapping

Codex exposes concrete choices through environment or config and resolves them
with `adapters/codex/bin/preflight.sh role <portable-role|role-profile|pipeline-stage>`:

```text
AGENT_MODEL_FAST
AGENT_MODEL_DEEP
AGENT_MODEL_EXTERNAL
AGENT_MODEL_ORCHESTRATOR
AGENT_REASONING_FAST
AGENT_REASONING_DEEP
AGENT_REASONING_EXTERNAL
AGENT_REASONING_ORCHESTRATOR
AGENT_EXTERNAL_CMD
```

When no concrete model is configured, the adapter reports `codex-default` and
`runtime-default`. `external adversary` remains unavailable unless
`AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured.

## Current Projection Boundary

`codex_setting/` should remain minimal and explicit. It may expose `AGENTS.md`,
`README.md`, `core/`, `capabilities/`, `roles/`, `bin/`, `codex-skills`,
`codex-agents`, `codex-plugin-marketplace`, `codex-hooks`, selected tools, and selected utilities, but must not expose Claude-native
`settings.json`, `commands/`, root `skills/`, `hooks/`, or `statusline.sh` as if Codex
could consume them.

`codex_setting/codex-plugin-marketplace` points at the dedicated marketplace
projection `adapters/codex/plugin-marketplace/`, not at the entire Codex
adapter. That projection exposes only `.agents/plugins/marketplace.json` and
`plugins/agent-harness-codex`.

`codex_setting/tools` points at `adapters/codex/tools/`, not the entire shared
`tools/` directory. The current allowlist is:

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

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `web-bundle` until
Codex has a documented design/tooling realization that uses it directly. The
shared `design-mcp` package is not projected wholesale; Codex exposes only the
adapter-owned visual harness launcher.

`codex_setting/utilities` points at `adapters/codex/utilities/`, not the entire
shared `utilities/` directory. The current allowlist is:

- `agent-home.sh` (Codex-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `harness-status.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Do not project the shared `dispatch-liveness.sh`; it assumes Claude
`projects/<encoded-cwd>/*.jsonl`. Codex uses the adapter-owned
`adapters/codex/bin/dispatch-liveness.py`, exposed as
`adapters/codex/bin/preflight.sh liveness [jobs.log]`, and maps open dispatch
jobs to `~/.codex/sessions/**/*.jsonl` by transcript `cwd`. Codex harvest is
adapter-owned under `adapters/codex/bin/preflight.sh harvest` and only updates
the portable jobs registry from `open` to `done`; it never performs merge or
worktree cleanup. Do not project material/design helpers such as `extract_web_figures.py` until a Codex
capability uses them directly.

## Distillation Boundary

Claude's adapter can run a detached `claude -p` worker with tool use denied by
runtime flags. Current Codex CLI inspection shows sandbox and approval controls,
but no explicit equivalent to a no-tools worker flag. The Codex adapter therefore
separates the pipeline:

1. `distill-delta` reads Codex JSONL session logs and emits transcript delta text.
2. User-facing `preflight.sh distill-propose` reports `status=tool-contract`
   and exits 69 while disabled. With `CODEX_DISTILL_ENABLE=1`, it invokes
   `codex exec --sandbox read-only --ephemeral --ignore-rules
   --skip-git-repo-check` and writes a JSON-lines proposal. `codex exec` does
   not accept `--ask-for-approval` (that is a top-level `codex` flag only); the
   read-only sandbox alone enforces the no-write contract.
3. The proposal is parsed by the shared `tools/memory/apply-distill-actions.py`
   applier only when both `CODEX_DISTILL_APPLY=1` and
   `CODEX_DISTILL_CONTRACT_ACCEPTED=1` are explicitly set.
4. The user-facing `distill-propose` command never applies automatically — it is
   the manual preview surface. The adapter's own `preflight.sh session-end` and
   `turn-nudge` dispatch enable the worker by default
   (`CODEX_DISTILL_ENABLE`/`CODEX_DISTILL_APPLY`/`CODEX_DISTILL_CONTRACT_ACCEPTED`
   default to `1`, each overridable to `0`), so Codex matches Claude's automatic
   session-end distillation. Both dispatch sites and the worker carry a
   `MEM_DISTILL` recursion guard.

Verification (codex-cli 0.142.4):
- Tool-free: an adversarial write probe under the exact worker flags
  (`codex exec --sandbox read-only --ephemeral --ignore-rules`) proved tool-free
  execution. Every model-attempted write — sentinel creation inside and outside
  the working root, overwriting an existing file, and creating a new file —
  failed with an OS-level `Read-only file system` error, so no write mechanism
  (shell command or `apply_patch`) can mutate state.
- No recursion: an isolated `CODEX_HOME` canary confirmed `codex exec` fires
  `SessionStart` but not `SessionEnd` hooks, so the worker's exec cannot
  re-trigger the session-end distill path. The `MEM_DISTILL=1` guard on the exec
  call plus the `session-end`/worker `MEM_DISTILL` early-exit are defense in depth.
- End-to-end: the enabled `preflight.sh session-end` against a throwaway store
  applied exactly one distilled record from a real `codex exec` JSON-lines
  proposal and terminated cleanly (no fork-bomb).

Automatic session-end and turn-nudge distillation is therefore enabled by
default; opt out by exporting `CODEX_DISTILL_ENABLE=0`.

## Worklog Boundary

Codex must treat `<agent-notes-root>` as mutable continuity state, not as harness
source. Before changing notes/routing state, run normal `write` preflight for the
target file and inspect `preflight.sh worklog` output. Codex may read/write
notes-root files only when the task is explicitly about notes, triage, feedback,
or worklog routing. It must not copy worklog-board DBs, caches, `.env*`, build
output, dispatch logs, or worktrees into this repo.
