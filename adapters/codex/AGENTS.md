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
- Before treating a capability as supported, run `adapters/codex/bin/preflight.sh capability-info <capability>` and follow the reported Codex realization.
- Treat Codex-native skills under `adapters/codex/skills/` and the installable plugin under `adapters/codex/plugins/agent-harness-codex/` as generated adapter output from `capabilities/`; do not load Claude Skill files as native Codex skills.
- Treat Codex custom agents under `adapters/codex/agents/*.toml` as generated adapter output from `roles/`; do not load Claude Agent files as native Codex agents.
- Expose Codex custom agents through `codex_setting/codex-agents`.
- Expose the installable Codex plugin through `codex_setting/codex-plugin-marketplace`, not by copying Claude Skill or command files.
- Treat command-like capability entrypoints as Codex-native Skills/plugin output, not deprecated custom prompt files or Claude slash commands.
- Before using a `roles/modes/` fragment, run `adapters/codex/bin/preflight.sh mode-info <family/mode>` and obey portable/tool-contract/unsupported status plus any named `tool_contract`, `tool_contract_check`, `runtime_surface`, and `fallback`.
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
- After design HTML writes, run `adapters/codex/bin/preflight.sh design <file>`.
- Before claiming full design/autopilot-design support, run `adapters/codex/bin/preflight.sh visual-harness <file.html>` and inspect the reported screenshot. Exit 69 means the local Playwright-backed checker is unavailable.
- After actually reading `<artifact-root>/spec/prd.md`, run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`; before spec-changing capability work, run `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`.
- Codex `SessionStart` hook bridge runs `adapters/codex/bin/preflight.sh start [cwd] [session-id]` and `adapters/codex/bin/preflight.sh memory [cwd]`; run them manually when hooks are unavailable.
- Codex `UserPromptSubmit` hook bridge runs `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`, `adapters/codex/bin/preflight.sh recall "<prompt>" [cwd]`, and `adapters/codex/bin/preflight.sh briefing [cwd]`; run them manually when hooks are unavailable.
- Use `adapters/codex/bin/preflight.sh status [cwd] [session-id]` when you need a read-only harness snapshot for workflow, artifact, notes, worktree, and git-risk signals. Keep Codex `/statusline` responsible for model, context, token, limit, and session footer fields.
- Use `adapters/codex/bin/preflight.sh doctor` for a quick adapter readiness check covering manifest freshness, native projections, hook bridge syntax, and boundary rules.
- Use `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly wants to toggle the tracked/untracked workflow escape hatch.
- Use `adapters/codex/bin/preflight.sh worklog [cwd]` before worklog-board or agent-notes work to inspect configured notes/app paths without mutating data.
- Use `adapters/codex/bin/preflight.sh headless [--check] <worktree>` before any Codex headless dispatch. Use `adapters/codex/bin/preflight.sh dispatch --dry-run|--register|--start --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <level>` to build/register/start the headless command. Do not launch headless work unless the job is main-dispatched, depth 1, registered in `.dispatch/jobs.log`, and monitored with `adapters/codex/bin/preflight.sh liveness [jobs.log]` while waiting. After main-session harvest, use `adapters/codex/bin/preflight.sh harvest --slug <slug> --mark-done` only to update the registry; merges and cleanup remain main/orchestrator responsibilities.
- For `research/claim-verify`, run `adapters/codex/bin/preflight.sh claim-verify --check <claim>` before treating adversarial external verification as satisfying the mode tool contract. Exit 69 means no external verification provider is configured.
- Use `adapters/codex/bin/preflight.sh distill-delta <session-id>` to inspect Codex transcript deltas. Use `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` only for explicit proposal generation; do not auto-apply memory distillation until a Codex no-tools worker contract exists.
- Treat `codex_setting/tools` as a selective memory/material/QA/design tool projection. Do not assume every shared tool is Codex-supported.
- Treat `codex_setting/utilities` as a selective utility projection. Do not assume every shared utility is Codex-supported.
- Keep Codex-owned credentials, sessions, logs, caches, and local databases outside the harness repo.

## Response Policy

- Answer the user in Korean unless they explicitly request another language.
- Keep implementation work grounded in the repo's current files and existing conventions.
- When modifying this harness repo, commit and push after validation.
- Do not run drill automatically; it can invoke headless runtime sessions and spend tokens. Report when drill would be useful.

## Compatibility Boundary

Claude Code files are implementation references, not Codex bootstrap files:

- `adapters/claude/CLAUDE.md`
- `adapters/claude/settings.json`
- `adapters/claude/commands/`
- `adapters/claude/statusline.sh`

When porting behavior, copy the invariant from `core/` first, then map it to Codex tools, approval behavior, and session lifecycle.
