# Codex Adaptation

This adapter is not a Claude Code surface clone. It defines the required mapping
so Codex can reproduce the portable harness invariants through Codex-native
surfaces, tool contracts, and explicit fallbacks without copying Claude-specific
assumptions into the common core.

## Canonical artifact and cleanup boundary (2026-07-14)

- **Runtime support:** the official Codex manual documents app-managed
  worktrees and their cleanup lifecycle, while the local `codex exec` CLI
  exposes `--add-dir` for an additional writable directory. That app lifecycle
  does not own harness-created sibling worktrees.
- **Adapter realization:** dispatch resolves the primary checkout's artifact
  root, injects `AGENT_ARTIFACT_ROOT`, and adds exactly that path with
  `--add-dir`. Shared guards reject worker-local artifact writes.
- **Parity gap/fallback:** Stop/SessionEnd cannot prove merge or push and never
  deletes worktrees. Main uses `preflight.sh worktree-cleanup` after integrated
  verification and push.

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
| Hook bridge | `adapters/codex/hooks/hooks.json`, `adapters/codex/hooks/run-hook.sh`, `adapters/codex/hooks/sessionstart-lifecycle.py`, `adapters/codex/hooks/sessionend-lifecycle.py`, `adapters/codex/hooks/userprompt-lifecycle.py`, `adapters/codex/hooks/permissionrequest-lifecycle.py`, `adapters/codex/hooks/pretooluse-write-guard.py`, `adapters/codex/hooks/posttooluse-read-marker.py`, `adapters/codex/hooks/posttooluse-design-check.py` | `codex_setting/codex-hooks` |
| Permission/sandbox contract | `adapters/codex/bin/preflight.sh permissions` | `codex_setting/bin/preflight.sh permissions` |
| MCP contract | `adapters/codex/bin/preflight.sh mcp` | `codex_setting/bin/preflight.sh mcp` |
| Design scaffold assets | `adapters/codex/scaffolds/` Codex-owned projection of shared scaffold HTML assets | `codex_setting/scaffolds` |
| Shared helper tools | selected `tools/`, selected `utilities/` | `codex_setting/tools`, `codex_setting/utilities` |
| Selected tools | `adapters/codex/tools/` adapter launchers plus selected portable tool projections | `codex_setting/tools` |
| Selected utilities | `adapters/codex/utilities/` adapter wrappers plus selected portable utility projections | `codex_setting/utilities` |

Permission/sandbox posture is now version-controlled for Codex the way it is for
Claude. Claude's auto-approve posture is captured in
`adapters/claude/settings.json` (`permissions.allow[]` plus
`defaultMode: "auto"`), so a fresh Claude Code install reproduces it from the
repo. The Codex equivalent — `approvals_reviewer`, per-project `trust_level`,
and the baseline `approval_policy`/`sandbox_mode` stance — is captured in the
adapter-owned fragment `adapters/codex/config/approval-sandbox.toml` (projected as
`codex_setting/codex-config/approval-sandbox.toml`, reported by
`preflight.sh permissions` as `config_fragment=…`). It holds the reproducible
posture only — no secrets and no machine-specific absolute project paths (the
`trust_level` project block is a template). The adapter never auto-applies it;
merge the relevant lines into `$CODEX_HOME/config.toml` on the target machine.
(codex-adapter-parity audit P-15: gap closed.)

## Native Skill And Plugin Surface

Current Codex support includes generated native Skill projections:
`adapters/codex/skills/<name>/SKILL.md` is generated from
`capabilities/<name>.md` by `adapters/codex/bin/sync-native-skills.py` and
projected as `codex_setting/codex-skills`. Runtime discovery should use either
per-skill native symlinks or the adapter-owned Codex plugin by default, not both;
`install-runtime-projection.sh --skills-mode both` is reserved for compatibility
or debugging because it duplicates skill metadata in Codex's initial context.

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

depth caveat: byte parity is not depth parity. Codex-native `SKILL.md`
projections stay at capability-summary depth, while the largest Claude Skills
reach roughly 59KB of step-level procedural detail — an order of magnitude
(roughly 8x) more than the generated Codex skill. This step-level depth gap is
a known parity limitation distinct from the byte-parity disclaimer above;
re-running `sync-native-skills.py` does not close it.

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
`adapters/codex/tools/material/`. Report spectrograms additionally run
`figure-gen --verify-report <manifest.json> <report.md>` and fail closed on
metadata, scale, claim-evidence, or hash-bound visual-review drift.

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
and `developer_instructions`) and the Codex-native runtime config fields
`model`, `model_reasoning_effort`, and `sandbox_mode`. Adapter defaults follow
the current Codex documentation shape: the fast/deep model tuple defined in
**Model Mapping** below, and read-only sandboxing for QA, external-adversary,
and memory-scout agents. The generated instructions also
encode role-specific runtime boundaries such as QA read-only behavior,
depth-one delegation, write preflight requirements, and external-adversary
independence. Mixed or variable role profiles include `Codex role-map inputs`
so the concrete role can be selected by mode and QA policy instead of
flattening the profile to one model role. Do not project Claude Agent files or
OpenCode Agent files into Codex.

parity caveat: Codex custom agents can carry model/reasoning/sandbox settings,
but they are not Claude Code Agent frontmatter. Runtime discovery, UI surfacing,
child approval behavior, config inheritance, and noninteractive/headless
behavior must be verified in Codex itself before claiming Claude Code parity.
Recent Codex issue reports show that model/reasoning settings can be runtime-
or surface-dependent, so this adapter treats TOML generation as the source
projection and keeps runtime validation separate.

permission-model caveat: Claude's per-agent `tools:` frontmatter allowlist
(for example `editorial-team` and `plan-team` both carry no `Bash` and no
network tools) has no Codex custom-agent-schema equivalent — Codex custom
agent TOML exposes no per-agent `tools` field, only `model`,
`model_reasoning_effort`, and `sandbox_mode`. The closest Codex approximation
is `sandbox_mode` plus `mcp_servers`, which cannot express a fine-grained tool
allowlist. Because `editorial-team.toml` and `plan-team.toml` both set
`sandbox_mode = "workspace-write"`, these two roles are strictly more
permissive under Codex than under Claude.

write-access caveat: Claude `qa-team` carries `Write` in its tool allowlist
and creates its durable review-log directly. Codex's `qa-team.toml` sets
`sandbox_mode = "read-only"` and cannot write at all, so under this adapter
the review-log for a Codex QA pass must be ghostwritten by the
orchestrator/dispatch harness on the QA agent's behalf, not written by the QA
agent itself. This is part of the Codex QA agent contract, not an oversight.

See Model Mapping below for the corresponding model-tier asymmetry across
these same custom agents.

Validation is currently structural plus install-path validation. The boundary
guard verifies generated TOML fields, `model_reasoning_effort` / `sandbox_mode`
runtime config fields, portable role references, role-map resolution,
role-specific runtime boundaries, and absence of non-Codex adapter paths. Codex
CLI 0.142.x exposes `codex debug prompt-input` for bootstrap/Skill/plugin
discovery, but it does not expose a `codex debug agent` listing surface; add
runtime discovery coverage when Codex exposes one.

## Native Hook Surface

Codex supports lifecycle hooks through `hooks.json` and inline config. This
adapter materializes a Codex-native hook projection under `adapters/codex/hooks/`.
Hook commands enter through `run-hook.sh`, which validates `AGENT_HOME` or the
Codex harness pointer before executing bridge scripts.
The `SessionStart` bridge calls `adapters/codex/bin/preflight.sh start` as
a silent side effect for stale workflow cleanup. It keeps memory injection off by
default because Codex `SessionStart` can run on startup, resume, clear, and
compact; `CODEX_SESSION_MEMORY_INJECT=1` restores `memory` output as
`hookSpecificOutput.additionalContext`. The `SessionEnd` bridge calls `session-end` for `mem sync` plus the verified automatic distill worker
(default on; `CODEX_DISTILL_ENABLE=0` opt-out). The `Stop` bridge enters the same lifecycle bridge but detaches
`session-end` into the background and exits 0 with silent stdout so turn-scoped Stop hook output and timeouts never block on distillation. The
`UserPromptSubmit` bridge extracts prompt text from top-level and nested
message/content payloads, then calls `mode`, suppresses the default tracked anchor, preserves
non-default mode context such as untracked state, plus `recall` and `briefing`
when they have content, a transition-only `token-budget ... hook` response, and
the `turn-nudge` side effect. Token-budget output is byte-identical to Phase 1:
it is empty for normal, unknown, repeated-band, degraded/failure, and
validated-native states; only entry into `tight`/`critical` adds one compact
directive. The parent lifecycle records exactly one content-free receipt-derived
outcome after observing success, timeout, and process failure. Accounting uses a
sha256 session digest, bounded XDG aggregate, bounded stale-safe lock, atomic
replace, and 8 KiB/file / 256 files / 2 MiB oldest-first pruning; every failure
is silent and fail-open. Exact inserted bytes and monotonic exact-session runtime
counter deltas remain separate non-billing observations, with no tokenizer
estimate absent exact runtime/model/version provenance. The directive can shorten output and defer optional
extras, but core/CONVENTIONS.md §1.2 forbids changing intensity, dispatch/depth,
model role, required tools/tests, safety/validation/security/error handling/
accessibility, input context, or guards. It emits
`hookSpecificOutput.additionalContext` only when non-default prompt context exists
(`CODEX_MODE_ANCHOR_ALWAYS=1` restores the tracked anchor); no routing-contract or
git-risk aggregate is injected per turn. The structured
`prompt-signal` subcommand (worker-startup/manual, not a per-turn hook call) reports
`routing_contract=core/WORKFLOW.md`,
`routing_action=read-workflow-and-select-codex-skill`, and
`capability_entrypoints=codex-native-skills` for tracked work. The `PermissionRequest`
bridge is a registered no-op that emits nothing; harness monitoring is owned by
Codex native `/statusline` while Codex owns approval and sandbox
decisions. The write bridge registers
`PreToolUse` for write/edit/multiedit/patch tools, including qualified
`functions.apply_patch` payloads, and calls
`adapters/codex/bin/preflight.sh write <file> <session-id>`, which runs
the portable artifact-order, git-state, core-first adapter edit, and memory-write guards, plus the spec
read gate for spec-changing artifacts (see below). The read bridge
registers `PostToolUse` for `Read` and calls `adapters/codex/bin/preflight.sh
read <file> <session-id>` so actual `spec/prd.md` reads satisfy spec-backed
capability gates and actual `core/*.md` reads satisfy the core-first adapter edit gate.

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
`spec/prd.md` / `core/*.md` reads, and design HTML save paths are routed through adapter
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
| `adapters/claude/commands/` | Not consumable; command-like harness entries use Codex-native Skills |
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
`preflight.sh status` output until Codex exposes an arbitrary dynamic footer
provider; Codex hooks themselves run silently with no `statusMessage` labels,
matching Claude Code's quiet hooks.

Harness-specific status signals still need Codex-native realization:

| Harness signal | Codex direction |
|---|---|
| stale workflow bypass flag cleanup | Codex `SessionStart` hook bridge runs `preflight.sh start`; explicit preflight remains fallback when hooks are unavailable |
| tracked/untracked workflow state | Codex `UserPromptSubmit` hook bridge runs `preflight.sh mode`, suppresses the default tracked anchor, and emits only non-default mode context such as untracked state (`CODEX_MODE_ANCHOR_ALWAYS=1` restores the tracked anchor); `preflight.sh prompt-signal` (worker-startup/manual subcommand, not a per-turn injection) additionally carries the full routing contract plus git dirty/worktree/dead-branch risk fields from `preflight.sh status`; explicit preflight remains fallback when hooks are unavailable |
| workflow/artifact/notes/git-risk snapshot | explicit `preflight.sh status`; includes tracked-dirty vs untracked counts and sibling worktree counts; keep Codex `/statusline` for native model/context/token/session fields |
| UI boundary report | explicit `preflight.sh ui-info`; reports built-in footer/title support, unsupported arbitrary live statusline scripts, Skill/plugin autopilot entrypoints, and explicit/main-dispatched subagent behavior |
| subagent delegation | explicit `preflight.sh subagent-info --check`; verifies the Codex `multi_agent` runtime feature and projected custom agents before claiming native subagent delegation parity |
| tracked/untracked toggle | explicit `preflight.sh track`; do not expose Claude `/track` command files |
| artifact root detection | `preflight.sh write` and shared artifact-root helper |
| headless/autopilot/background jobs | `preflight.sh headless` / `dispatch` / `liveness` / `harvest` provide the tool-contract path; `preflight.sh status` surfaces in-flight jobs as `headless_open_jobs` / `headless_open_slugs` from the dispatch registry. A Codex-native graphical display remains optional polish |
| sibling `-wt/<slug>` dispatch detection | preserve the worktree naming invariant; choose a Codex-native display surface later |
| pipeline stage nudges | preflight/AGENTS instructions first; UI only when Codex exposes a suitable surface |
| oncall/note/study/drill/runtime-watch loop nudges | `preflight.sh briefing` plus `preflight.sh loop-info <loop>` for loop-specific support/fallback status |
| merge/rebase/merged-branch risk | `preflight.sh write` git safety checks; `preflight.sh status` reports `git_operation` (merge/rebase/cherry-pick), `git_branch_done` (non-default branch fully merged = DONE-BRANCH hazard), dirty counts, and extra worktree counts. A native graphical warning remains optional polish |
| fleet (multi-agent) observability | No Codex-native equivalent. Claude's adapter feeds a fleet dashboard via `hooks/herdr-agent-state.sh`, wired to 6 Claude hook events (`PermissionRequest`→blocked, `PreToolUse`→working, `UserPromptSubmit`→working, `SessionStart`→idle, `Stop`→idle, `SessionEnd`→release), plus a per-session `.statusline/<sid>.json` tap; Codex's `PermissionRequest` bridge is a registered no-op that emits nothing (see Native Hook Surface) |

observability caveat: the gap above is scoped to fleet (multi-agent)
observability specifically, not an absence of monitoring — Codex retains full
per-session observability through native `/statusline`. Only the cross-agent
dashboard view that Claude's adapter derives from `herdr-agent-state.sh` has no
Codex-native counterpart today.

## Required Codex Mappings

| Portable invariant | Codex adaptation requirement |
|---|---|
| artifact order | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| git state safety | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits |
| core first gate | Auto-enforced through Codex hooks: `PostToolUse[Read]` records actual `core/*.md` reads, and `PreToolUse` write guard hard-denies ungrounded `adapters/**` edits. Manual fallback: `preflight.sh read <core-doc.md>` after core reads |
| memory write guard | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | Run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | Auto-enforced through Codex hooks: `PostToolUse[Read]` records actual `prd.md` reads, and `PreToolUse` write guard hard-denies an ungrounded write to a spec-changing artifact (`plans/*` or a `spec/` blueprint) — Codex's interception equivalent of Claude's `PreToolUse[Skill]` gate (no skill event exists). Manual fallbacks: `preflight.sh read <prd.md>` after reads, `preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| workflow start cleanup | Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh start [cwd] [session-id]`; run it manually when no automatic hook is attached |
| workflow signal | Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` per turn; `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` is the worker-startup/manual subcommand carrying the full routing contract; run them manually when no automatic hook is attached |
| token/context pressure | `preflight.sh token-budget [cwd] [session-id] [kv|json|hook]` reads an exact Codex rollout session and keeps active context, exact directive bytes, and cumulative raw counters separate. `kv`/`json` are read-only L2 accounting diagnostics. Unknown/degraded signals fail open. `hook` remains transition-only and byte-identical; its parent lifecycle is the single exactly-once accounting authority for success/timeout/error and writes only a bounded content-free sha256-session aggregate under XDG state. `utilities/token-budget-experiment.py` is an explicit isolated `offline-forecast-v1` replay/evaluator: production hooks/preflight do not import or activate it, its maximum verdict is `eligible_for_user_review`, adoption stays `pending_user_decision`, and it never writes config. Native rollout-budget ownership requires `AGENT_TOKEN_BUDGET_NATIVE_VALIDATED=1` only after feature + no-side-effect config probes pass; local Codex 0.144.3 reports the feature under development and disabled, so exact-session rollout observation remains the fallback. The adapter never writes `$CODEX_HOME/config.toml` |
| workflow toggle | Run `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly requests tracked/untracked mode switching |
| memory inject | Run `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text memory injection; Codex SessionStart hook emission is opt-in via `CODEX_SESSION_MEMORY_INJECT=1` |
| memory recall | The agent decides contextually when memory may help, then runs `adapters/codex/bin/preflight.sh recall <query> [cwd] [session-id]`. No automatic prompt classifier is attached |
| oncall briefing | Run `adapters/codex/bin/preflight.sh briefing [cwd]` before prompt handling on the dedicated agent desk |
| loop guidance | Run `adapters/codex/bin/preflight.sh loop-info <oncall|note|study|drill|runtime-watch>` before following loop guides; Codex reports manual contracts, missing implementations, and drill auto-run restrictions without executing loop scripts. The `note` loop is an external scheduler/worklog-board contract; use the related `autopilot-note` Skill/plugin projection only for on-demand note routing |
| memory distill | Transcript delta extraction exists via `adapters/codex/bin/preflight.sh distill-delta <session-id>`. The user-facing `distill-propose` stays an explicit opt-in preview (reports `status=tool-contract`, exits 69 until `CODEX_DISTILL_ENABLE=1`). Automatic session-end and turn-nudge distillation is enabled by default: the `codex exec --sandbox read-only` worker is verified tool-free (see Distillation Boundary) and applies through `apply-distill-actions.py`; the Stop hook schedules session-end distillation detached to avoid foreground hook timeouts; opt out with `CODEX_DISTILL_ENABLE=0` |
| worklog state signal | Run `adapters/codex/bin/preflight.sh worklog [cwd]` to inspect configured `<agent-notes-root>` / `<worklog-board-app>` paths read-only before Codex updates notes or diagnoses board state |
| role profiles | Read `roles/README.md`, then run `adapters/codex/bin/preflight.sh role <portable-role|role-profile|pipeline-stage>` to resolve Codex model/reasoning-effort settings or pipeline profile aliases to native custom agents |
| permission mapping | Run `adapters/codex/bin/preflight.sh permissions` to inspect the Codex approval/sandbox contract and confirm Claude `allowedTools` is unsupported |
| MCP mapping | Run `adapters/codex/bin/preflight.sh mcp --check` to inspect Codex's native MCP CLI/config surface; do not copy Claude `settings.json` MCP registrations or project `tools/design-mcp` wholesale |
| headless dispatch | Run `adapters/codex/bin/preflight.sh headless --check <worktree>` before Codex `exec` dispatch; it checks the worktree, command availability, and installed Codex runtime projection (`agent-harness`, bootstrap, hooks, native Skills, native Agents, and native Modes) without launching. Add `--require-hook-trust` when dispatch must prove complete Codex hook trust. Use `adapters/codex/bin/preflight.sh dispatch --dry-run|--register|--start [--require-hook-trust] --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <quick|light|standard|thorough|adversarial>` to build the Codex headless command and append `.dispatch/jobs.log` before launch. Dispatch keeps the active `CODEX_HOME` for auth and runtime projection, but it does not choose a default model and does not inherit the main session's selected model implicitly. The main/orchestrator must select per job with `--model-role <portable-role>`, `--model <model> --reasoning <effort>`, or explicit `--inherit-model-settings`; the wrapper then passes `--model`, `-c model_reasoning_effort=...`, and `-c approval_policy=...` to `codex exec` when applicable. The wrapper validates `capability-info`, `mode-info`, and the portable QA level before writing `.dispatch/jobs.log`; registry writes and harvest rewrites are serialized with a `.lock` file. `--register` and `--start` materialize a Codex harness prompt before appending the registry row. The prompt loads `AGENTS.md`, runs `status`, `prompt-signal`, and `mode`, checks capability/mode realization, resolves pipeline role profiles, applies spec-read/capability/write gates, and bans Claude-native runtime files; `--start` reruns the same projection check before launching, and strict hook trust failure occurs before registry writes. While waiting on dispatched work, run `adapters/codex/bin/preflight.sh liveness [jobs.log]` to match open jobs to Codex session JSONL files by `cwd` and transcript mtime. After main-session harvest, run `adapters/codex/bin/preflight.sh harvest --slug <slug> --mark-done` to mark selected registry rows done; merge and worktree cleanup stay outside the adapter wrapper |
| role modes | Read `roles/MODES.md`, then run `adapters/codex/bin/preflight.sh mode-info <family/mode>`; read the reported `native_mode_path`, obey `fallback=reference-only` only for unsupported modes, and satisfy any named `tool_contract` / `tool_contract_check` before claiming tool-contract modes |
| mode guides | Use `adapters/codex/modes/<family>/<mode>.md` as the Codex-native realization guide reported by `mode-info`; satisfy named tool contracts or report unavailable before claiming support |
| design modes | Use `adapters/codex/modes/design/<mode>.md` as the Codex-native realization guide; satisfy `visual-harness` or report unavailable before claiming rendered visual verification |
| hook invariants | `adapters/codex/hooks/sessionstart-lifecycle.py` realizes SessionStart bootstrap context injection; `userprompt-lifecycle.py` realizes UserPromptSubmit mode/recall/briefing plus transition-only token-budget context and turn-nudge; `sessionend-lifecycle.py` realizes SessionEnd memory sync/distill and Stop detached session-end scheduling; `permissionrequest-lifecycle.py` is a registered no-op for Codex `PermissionRequest` (harness monitoring is owned by Codex native `/statusline`); `pretooluse-write-guard.py` realizes write guards (artifact-order, git-state, core-first, memory-write, and the spec read gate for spec-changing artifacts) through Codex `PreToolUse`; `posttooluse-read-marker.py` records actual spec/core reads through `PostToolUse`; `posttooluse-design-check.py` realizes design HTML console checks through `PostToolUse`; run explicit preflight wrappers for events not yet covered by native hooks |
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

When no override is configured, the adapter reports defaults for non-external
roles: fast reviewer/fact-checker/writer/tool=`gpt-5.6-luna`/medium,
fast implementer=`gpt-5.6-terra`/medium, deep roles including `deep orchestrator`
=`gpt-5.6-sol`/high, and retained balanced `orchestrator`=`gpt-5.6-terra`/medium
through the named `AGENT_MODEL_BALANCED` override. `external adversary` remains unavailable
unless `AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured, because
the independent-adversary contract is stronger than the existence of a
generated `external-adversary.toml` projection. `AGENT_EXTERNAL_CMD` can route
an external adversary to a separate external process when stronger independence
is required.

model-tier caveat: static Codex projections use Luna for QA/material fast paths,
Terra for implementation, and Sol for plan/research/design/editorial/deep-review
paths. Runtime measurement
(2026-07-04) confirmed these static TOML `model`/`model_reasoning_effort` pins
are actually applied to the spawned child process, not merely declared in the
file — verified against child rollout JSONL, with 5 static-pin/role-map
mismatches confirmed. This is therefore a confirmed effective gap:
`adapters/codex/bin/preflight.sh role`/role-map resolution does not
automatically escalate these three roles to a stronger tier at spawn time; the
projection is a static default, not a validated model-tier equivalence.

## Current Projection Boundary

`codex_setting/` should remain minimal and explicit. It may expose `AGENTS.md`,
`README.md`, `core/`, `capabilities/`, `roles/`, `bin/`, `codex-skills`,
`codex-agents`, `codex-hooks`, selected tools, and selected utilities, but must not expose Claude-native
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
- `design/convert-harness.sh` (Codex-owned launcher for PDF/PPTX/bundle design export via the shared `convert.mjs`)

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `web-bundle` until
Codex has a documented design/tooling realization that uses it directly. The
shared `design-mcp` package is not projected wholesale; Codex exposes the
adapter-owned visual harness launcher plus the converter launcher
(`design/convert-harness.sh`, wrapping the shared `convert.mjs` for PDF/PPTX/
bundle export — the design-handoff surface the visual harness alone does not
cover).

### MCP registration (design)

`preflight.sh mcp` reports `design_mcp_projection=policy-not-adopted-approval-gated`
rather than `unsupported`: the design MCP server *can* be registered with Codex and
its tools are discoverable and consume screenshots (runtime-verified — a
`[mcp_servers.design]` stdio server exposes the six tools, and a `codex exec` run
read `DESIGN PROBE` text out of a screenshot). The adapter does **not** adopt it as
the default design surface for two reasons: (1) policy — the owned visual harness +
converter launcher already cover render/screenshot/console and export without a
persistent server dependency; (2) a noninteractive `codex exec` under
`approval_policy = "never"` auto-denies MCP tool calls, so the render→view loop only
works interactively (TUI approval) or under an approval/trust policy that permits the
tool.

To register the design MCP server on a machine that wants the MCP path (guidance
only — the adapter never mutates `$CODEX_HOME/config.toml`):

```toml
[mcp_servers.design]
command = "node"
args = ["<agent-home>/tools/design-mcp/server.js"]
```

Then run design work in an interactive Codex session (so tool approvals can be
granted) or set an approval/trust policy for the project that allows the tool
(see `adapters/codex/config/approval-sandbox.toml`). Actually performing the
registration is out of scope for the adapter; this section documents the path.
For headless/export use without a server, prefer `preflight.sh convert
<pdf|bundle|pptx> <file.html>`.

`codex_setting/utilities` points at `adapters/codex/utilities/`, not the entire
shared `utilities/` directory. The current allowlist is:

- `agent-home.sh` (Codex-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `harness-status.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Do not project the shared `dispatch-liveness.sh`; it is the cross-harness
registry/wait fallback, while Codex uses the adapter-owned
`adapters/codex/bin/dispatch-liveness.py`, exposed as
`adapters/codex/bin/preflight.sh liveness [jobs.log]`, and maps open dispatch
jobs to `~/.codex/sessions/**/*.jsonl` by transcript `cwd`. Codex harvest is
adapter-owned under `adapters/codex/bin/preflight.sh harvest` and only updates
the portable jobs registry from `open` to `done`; it never performs merge or
worktree cleanup. Do not project material/design helpers such as `extract_web_figures.py` until a Codex
capability uses them directly.

### SD-15 limit-death detection (OPERATIONS §5.10 ⑨) — parity: realized

`adapters/codex/bin/dispatch-headless.py` ports the Claude wrapper's SD-15
early-limit-death detection homomorphically: `--early-exit-watch <secs>` watches a
just-launched `codex exec` child; if it exits within the window and its log tail matches a
limit/auth `DEATH_PATTERN`, the wrapper closes its own `jobs.log` row to
`done,note=dead-<reason>[,reset=<x>]`, writes `.dispatch/usage-reset.codex` (SD-16
usage-check cache), and surfaces `early_death=`/`row_closed=` on stdout. No retry — detection,
closure, and surfacing only; re-dispatch/harness failover is the orchestrator's semantic
zone (⑧). `adapters/codex/bin/dispatch-liveness.py` adds a `LIMIT_RE` log-tail scan (axis 6,
SD-15b) that judges an open row DEAD when its dispatch log shows a limit/auth pattern,
independent of transcript mtime. **Parity note vs OpenCode**: codex `exec` exits non-zero on
retry exhaustion (openai/codex#9148·#12677), so the launch early-exit-watch axis is realized;
runtime-currentness patterns (`exceeded retry limit`, `usage_limit_reached`, `429`) are
best-effort per 2026-07 issue evidence, conservative and kept in sync with the shared list.
Conformance: `adapters/codex/bin/dispatch-headless.sd15.test.sh`.

### SD-48~50 nested dispatch recovery — realized

Depth-2 starts require checked tuple evidence and an inherited canonical
`AGENT_DISPATCH_JOBS`; noncanonical nested `--jobs` and unwritable global
registries fail before spawn. Rows carry attempt identity, launch authority,
fallback ordinal, and tuple evidence. `nested-headless` keeps the observed
Codex-in-Codex workspace-write tuple unsupported, while `dispatch-chain`
enforces same-harness → cross-harness/broker → native → inline ordering.
Codex launches also attach `pid` and `/proc` start ticks; the shared liveness
fallback recognizes `.codex.jsonl`, closing the v10 O1 false-DEAD gap.

## Distillation Boundary

Claude's adapter runs a detached `claude -p` worker with tool use denied by
runtime flags. Codex has no equivalent no-tools worker flag, but a
`codex exec --sandbox read-only` worker is physically tool-free (every write
mechanism, shell or `apply_patch`, hits the OS read-only wall), so the adapter
realizes the **same portable 2-tier distillation contract**
(`core/MEMORY.md` §7, D-30/D-32) rather than only an add-only subset.

The adapter reimplements the portable `hooks/mem-distill-dispatch.sh` pipeline
**synchronously** in `adapters/codex/bin/distill-worker.sh` (the D-32
"reimplement + preserve" path) so a headless `codex exec` session captures memory
before it exits — the portable dispatcher detaches into the background, which is
right for interactive Claude but leaves a codex-exec teardown race. Crucially the
**safety layers are the shared code, not a divergent copy**: `mem.py
curate-snapshot` / `curate-artifacts` (snapshot + `IDS:` membership) and
`tools/memory/apply-distill-actions.py --mode/--snapshot-ids` (the whitelist
gate). Only the synchronous orchestration shell and the prompts are Codex-owned.

Two tiers + one manual surface:

1. `distill-delta` reads Codex JSONL session logs and emits transcript delta text.
2. **turn-nudge = increment (fast tier, `gpt-5.4-mini`)** — add-only. The prompt
   is add-only, and the shared applier now **enforces** add-only in `increment`
   mode (id-mutations `prune/merge/graduate/reattribute/reinforce` are rejected
   outside `curate`), so a prompt-injected transcript cannot bypass the snapshot
   whitelist (P-25).
3. **session-end = curate (deep tier, `gpt-5.5`)** — snapshot-grounded
   `prune/merge/graduate/consolidate`. The worker captures the current-project
   snapshot + artifact state, and id-mutations are gated by the `--snapshot-ids`
   membership whitelist (`member()` in the shared applier). Per-mode model tiers
   (P-36) override with `CODEX_DISTILL_MODEL` (global) /
   `CODEX_DISTILL_MODEL_INCREMENT` / `CODEX_DISTILL_MODEL_CURATE` /
   `AGENT_MODEL_FAST` / `AGENT_MODEL_DEEP`.
4. `preflight.sh session-end` invokes the worker in `curate` mode and
   `turn-nudge` in `increment` mode, both enabled by default
   (`CODEX_DISTILL_ENABLE`/`CODEX_DISTILL_APPLY`/`CODEX_DISTILL_CONTRACT_ACCEPTED`
   default to `1`, each overridable to `0`). Because session-end now realizes the
   curate tier (not just add), **Codex matches Claude's automatic session-end
   distillation on the curate axis** (both run increment+curate). The worker
   advances the distill marker only after a successful apply (a preview or a
   timed-out exec keeps the delta), holds a per-sid `mkdir` lock against
   concurrent turn/session runs, and carries the `MEM_DISTILL` recursion guard at
   both dispatch sites and inside the worker.
5. User-facing `preflight.sh distill-propose` stays the **add-only manual
   preview** surface: it reports `status=tool-contract` and exits 69 while
   disabled, and with `CODEX_DISTILL_ENABLE=1` writes a JSON-lines proposal that
   the shared applier consumes only when both `CODEX_DISTILL_APPLY=1` and
   `CODEX_DISTILL_CONTRACT_ACCEPTED=1` are explicitly set. It never advances the
   marker without applying.

Verification (codex-cli 0.142.5):
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
  applies distilled records from a real `codex exec` JSON-lines proposal through
  the shared applier and terminates cleanly (no fork-bomb). Increment
  add-only enforcement and curate `--snapshot-ids` membership are exercised by
  `tools/memory/apply-distill-actions.py` unit coverage and
  `hooks/portable-guards.test.sh`.

Automatic session-end (curate) and turn-nudge (increment) distillation is
therefore enabled by default; opt out by exporting `CODEX_DISTILL_ENABLE=0`.

## Worklog Boundary

Codex must treat `<agent-notes-root>` as mutable continuity state, not as harness
source. Before changing notes/routing state, run normal `write` preflight for the
target file and inspect `preflight.sh worklog` output. Codex may read/write
notes-root files only when the task is explicitly about notes, triage, feedback,
or worklog routing. It must not copy worklog-board DBs, caches, `.env*`, build
output, dispatch logs, or worktrees into this repo.
