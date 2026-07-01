# AGENTS.md — Codex Adapter Bootstrap

This file maps the shared agent harness onto Codex-style sessions. It is an adapter bootstrap, not the portable source of truth.

## Source Order

1. Read `core/CORE.md` for the model-neutral harness contract.
2. For routing and tracked work, read `core/WORKFLOW.md`.
3. For QA levels, model roles, artifact layout, and cross-doc invariants, read `core/CONVENTIONS.md`.
4. For git/worktree/dispatch rules, read `core/OPERATIONS.md`.
5. For memory behavior, read `core/MEMORY.md`.
6. For task-specific behavior, read `capabilities/README.md`, `roles/README.md`, and `roles/MODES.md` first. Use Claude Skill, Agent, or mode files only as compatibility references.

## Runtime Mapping

- Treat `AGENT_HOME` as the installed harness root.
- Use `.agent_reports/` for new artifacts. Read legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.
- Use portable model roles from `core/CONVENTIONS.md`; do not treat Claude model names such as `sonnet` or `opus` as portable semantics.
- Use `adapters/codex/bin/preflight.sh role <portable-role|role-profile|pipeline-stage>` to resolve both model roles and pipeline role profiles such as `planning`, `implementation`, `verification`, and `report`.
- Before treating a capability as supported, run `adapters/codex/bin/preflight.sh capability-info <capability>` and follow the reported Codex realization.
- Treat Codex-native skills under `adapters/codex/skills/` and the installable plugin under `adapters/codex/plugins/agent-harness-codex/` as generated adapter output from `capabilities/`; do not load Claude Skill files as native Codex skills.
- Treat Codex custom agents under `adapters/codex/agents/*.toml` as generated adapter output from `roles/`; do not load Claude Agent files as native Codex agents.
- Expose Codex custom agents through `codex_setting/codex-agents`.
- Expose the installable Codex plugin through `codex_setting/codex-plugin-marketplace`, not by copying Claude Skill or command files.
- Expose Codex mode guides through `codex_setting/codex-modes`.
- Treat command-like capability entrypoints as Codex-native Skills/plugin output, not deprecated custom prompt files or Claude slash commands.
- Before using a `roles/modes/` fragment, run `adapters/codex/bin/preflight.sh mode-info <family/mode>` and obey portable/tool-contract/unsupported status plus any named `tool_contract`, `tool_contract_check`, `runtime_surface`, and `fallback`.
- Read the reported `native_mode_path` under `adapters/codex/modes/` before applying a mode persona.
- For `design/*` modes, satisfy `adapters/codex/bin/preflight.sh visual-harness <file.html>` before claiming rendered visual verification.
- Use `<agent-home>/scaffolds/` for reusable design scaffold assets; this resolves through `codex_setting/scaffolds` to the Codex-owned scaffold projection, not Claude Design MCP paths.
- Run deterministic guard scripts directly when Codex hooks are unavailable or untrusted.
- Expose Codex hook bridges through `codex_setting/codex-hooks`; do not project Claude `settings.json` or hook payloads.
- Use `adapters/codex/bin/preflight.sh permissions` to inspect the Codex approval/sandbox contract; do not port Claude `allowedTools`.
- Use `adapters/codex/bin/preflight.sh mcp [--check]` to inspect Codex's native MCP surface; do not copy Claude `settings.json` MCP registrations or project `tools/design-mcp` wholesale.
- Before edits, run `adapters/codex/bin/preflight.sh write <file> [session-id]`.
- For `material/browser-fetch` URLs, run `adapters/codex/bin/preflight.sh browser-fetch --check <url>` before treating rendered browser access as satisfying the mode tool contract. Exit 69 means the local Playwright browser stack is unavailable.
- For `material/data-script` outputs, run `adapters/codex/bin/preflight.sh data-script --check <script.py>` before treating the generated analysis script as satisfying the mode tool contract.
- For `material/figure-gen` outputs, run `adapters/codex/bin/preflight.sh figure-gen --check <script.py>` before treating a generated matplotlib figure script as satisfying the mode tool contract.
- For `material/pdf-extract` inputs, run `adapters/codex/bin/preflight.sh pdf-extract --check <file.pdf>` before treating local PDF text extraction as satisfying the mode tool contract. Exit 69 means the local extractor is unavailable.
- For `material/web-image-search` queries, run `adapters/codex/bin/preflight.sh web-image-search --check <query>` before treating image search as satisfying the mode tool contract. Exit 69 means no provider command is configured.
- For `qa/security-review`, use the portable read-only mode with Codex file and git diff tools; do not invoke or project Claude `/security-review`.
- For `qa/test` verification commands, run `adapters/codex/bin/preflight.sh verification-runner --timeout <seconds> -- <command> [args...]` and report the captured exit status.
- For QA level routing, run `adapters/codex/bin/preflight.sh qa-policy <level> [code|research|doc|general]` and obey the reported reviewer, external-adversary, and fallback policy before claiming independent QA delegation.
- After design HTML writes, run `adapters/codex/bin/preflight.sh design <file>`.
- Before claiming full design/autopilot-design support, run `adapters/codex/bin/preflight.sh visual-harness <file.html>` and inspect the reported screenshot. Exit 69 means the local Playwright-backed checker is unavailable.
- After actually reading `<artifact-root>/spec/prd.md`, run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`; before spec-changing capability work, run `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`.
- Shell/Bash/`functions.exec_command` reads and writes have targeted hook coverage for obvious write redirects, common mutation commands (`tee`, `touch`, `cp`, `mv`, `rm`, `install`, `rsync`), `dd of=...`, `sed -i`, direct `spec/prd.md` reads, and design HTML save paths. Before target-ambiguous shell I/O touches guarded paths, run the matching explicit `preflight.sh write`, `preflight.sh read`, or `preflight.sh design` wrapper.
- Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh start [cwd] [session-id]` and `adapters/codex/bin/preflight.sh memory [cwd]`, then emits `hookSpecificOutput.additionalContext`; run them manually when hooks are unavailable.
- Codex `SessionEnd` and `Stop` hook bridges run `adapters/codex/bin/preflight.sh session-end [cwd] [session-id]` for memory sync plus automatic distillation (enabled by default; opt out with `CODEX_DISTILL_ENABLE=0`) and emit no stdout so helper output never violates Stop hook parsing; run it manually when hooks are unavailable.
- Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`, `adapters/codex/bin/preflight.sh recall "<prompt>" [cwd]`, `adapters/codex/bin/preflight.sh briefing [cwd]`, and `adapters/codex/bin/preflight.sh turn-nudge [cwd] [session-id]`, then emits one aggregated `hookSpecificOutput.additionalContext` with workflow state plus git dirty/worktree/dead-branch risks; run them manually when hooks are unavailable.
- Codex `PermissionRequest` hook bridge runs `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, then emits `hookSpecificOutput.additionalContext` with read-only harness context while Codex owns approval and sandbox decisions.
- Use `adapters/codex/bin/preflight.sh status [cwd] [session-id]` when you need a read-only harness snapshot for workflow, artifact, notes, worktree, and git-risk signals. Keep Codex `/statusline` responsible for model, context, token, limit, and session footer fields.
- Use `adapters/codex/bin/preflight.sh ui-info` to inspect the Codex UI boundary. Codex supports native `/statusline` and `/title` built-in item configuration, but not a Claude-style arbitrary live statusline script; harness-specific signals stay in `preflight.sh status` and hook `statusMessage` output. `/statusline` persists user choices in `$CODEX_HOME/config.toml`; keep that file runtime-owned and use `codex_setting/codex-config/tui-statusline.toml` only as the harness-recommended fragment. Run `adapters/codex/bin/preflight.sh tui-config` only when you explicitly want to apply that fragment to the runtime-owned config file.
- Use `adapters/codex/bin/preflight.sh subagent-info --check` before claiming Codex subagent delegation parity; Codex subagents are native, explicit workflows backed by `multi_agent` and projected custom agents under `$CODEX_HOME/agents`.
- Use `adapters/codex/bin/preflight.sh doctor` for a quick adapter readiness check covering manifest freshness, native projections, hook bridge syntax, and boundary rules. Use `adapters/codex/bin/preflight.sh doctor --runtime` or `adapters/codex/bin/preflight.sh runtime-projection` when you also need to verify the installed `$CODEX_HOME` wiring; use `doctor --runtime-strict` or `runtime-projection --require-hook-trust` when complete hook trust must be proven.
- Use `adapters/codex/bin/preflight.sh loop-info <oncall|note|study|drill>` before following a loop guide; do not run Claude-coupled loop scripts as Codex-native executables.
- Use `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly wants to toggle the tracked/untracked workflow escape hatch.
- Use `adapters/codex/bin/preflight.sh worklog [cwd]` before worklog-board or agent-notes work to inspect configured notes/app paths without mutating data.
- Use `adapters/codex/bin/preflight.sh headless [--check] [--require-hook-trust] <worktree>` before any Codex headless dispatch. Use `adapters/codex/bin/preflight.sh dispatch --dry-run|--register|--start [--require-hook-trust] --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <quick|light|standard|thorough|adversarial>` to build/register/start the headless command. The dispatch wrapper validates `capability-info`, `mode-info`, and the portable QA level before writing `.dispatch/jobs.log`; `--register` and `--start` materialize the Codex harness prompt before appending the registry row, and the prompt includes the Codex bootstrap, `prompt-signal`/`mode`, capability/mode checks, pipeline role profile checks, spec-read/capability/write gates, and a Claude-native surface ban. Use `--require-hook-trust` when launch must fail unless all Codex hook trust records are present; missing trust fails before registry writes. Do not launch headless work unless the job is main-dispatched, depth 1, registered in `.dispatch/jobs.log`, and monitored with `adapters/codex/bin/preflight.sh liveness [jobs.log]` while waiting. After main-session harvest, use `adapters/codex/bin/preflight.sh harvest --slug <slug> --mark-done` only to update the registry; merges and cleanup remain main/orchestrator responsibilities.
- Treat autopilot entrypoints as Codex-native Skills/plugin guidance. Codex may implicitly select matching Skills, but there is no Claude slash-command router; for spec-backed work, satisfy the spec-read/capability gates and use the relevant `autopilot-*` Skill or explicit headless dispatch path.
- For `autopilot-code`, `capability-info` and `route` print the portable pipeline contract (`code-plan>code-execute>code-test>code-report`), optional `code-refine`, required plan artifacts, role mapping, and dispatch fallback; follow that contract before claiming the cycle is complete.
- Treat Codex subagents as native subagent workflows. Use them when the user explicitly asks for parallel/subagent work or when the main session dispatches depth-one headless work; run `adapters/codex/bin/preflight.sh subagent-info --check` before claiming runtime support, and do not promise Claude-style automatic background delegation from UI state alone.
- For `research/claim-verify`, run `adapters/codex/bin/preflight.sh claim-verify --check <claim>` before treating adversarial external verification as satisfying the mode tool contract. Exit 69 means no external verification provider is configured.
- Use `adapters/codex/bin/preflight.sh distill-delta <session-id>` to inspect Codex transcript deltas. The user-facing `adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` stays an explicit preview: it reports `status=tool-contract` and exits 69 until `CODEX_DISTILL_ENABLE=1`. The adapter-owned `session-end` and `turn-nudge` paths apply distillation automatically by default — the read-only `codex exec` worker is verified tool-free — so opt out with `CODEX_DISTILL_ENABLE=0`. OpenCode is separate and is not automatic.
- Use `adapters/codex/bin/install-runtime-projection.sh [--install-plugin]` to wire `$CODEX_HOME` (default `$HOME/.codex`) to the harness projection (`agent-*` pointers for bootstrap, common docs, capabilities, roles, bin/tools/utilities, scaffolds, hooks, native skills/agents/modes/plugin marketplace, `hooks.json`, native skill/agent symlinks, and the read-only `agent-config` fragment pointer); it is idempotent and never touches Codex credentials, sessions, logs, caches, `config.toml`, or DBs. Use `adapters/codex/bin/check-runtime-projection.sh`, `adapters/codex/bin/preflight.sh runtime-projection`, or `adapters/codex/bin/preflight.sh doctor --runtime` for read-only `status=ok|failed` validation of that wiring, including exact per-skill/per-agent symlink targets. If `check=hook-trust:review-needed` appears, run `/hooks` in Codex and trust the changed harness hooks; `check=hook-trust:ok session_end=stop-alias` means Codex trusted `Stop`, which runs the same session-end bridge as `SessionEnd`; use `adapters/codex/bin/preflight.sh runtime-projection --require-hook-trust` or `adapters/codex/bin/preflight.sh doctor --runtime-strict` when hook trust should fail the check.
- Treat `codex_setting/tools` as a selective memory/material/QA/design tool projection. Do not assume every shared tool is Codex-supported.
- Treat `codex_setting/utilities` as a selective utility projection. Do not assume every shared utility is Codex-supported.
- Keep Codex-owned credentials, sessions, logs, caches, and local databases outside the harness repo.

## Response Policy

- Answer the user in Korean unless they explicitly request another language.
- Keep implementation work grounded in the repo's current files and existing conventions.
- When modifying this harness repo, commit and push after validation.
- Do not run drill automatically; it can invoke headless runtime sessions and spend tokens. Run `adapters/codex/bin/preflight.sh loop-info drill` and report when drill would be useful.

## Compatibility Boundary

Claude Code files are implementation references, not Codex bootstrap files:

- `adapters/claude/CLAUDE.md`
- `adapters/claude/settings.json`
- `adapters/claude/commands/`
- `adapters/claude/statusline.sh`

When porting behavior, copy the invariant from `core/` first, then map it to Codex tools, approval behavior, and session lifecycle.
