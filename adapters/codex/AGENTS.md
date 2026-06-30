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
- Run deterministic guard scripts directly when the Codex runtime cannot attach equivalent hooks.
- Expose Codex hook bridges through `codex_setting/codex-hooks`; do not project Claude `settings.json` or hook payloads.
- Before edits, run `adapters/codex/bin/preflight.sh write <file> [session-id]`.
- After design HTML writes, run `adapters/codex/bin/preflight.sh design <file>`.
- Before claiming full design/autopilot-design support, run `adapters/codex/bin/preflight.sh visual-harness`; exit 69 means the required Codex-native render/screenshot/image-inspection harness is still a tool-contract.
- After actually reading `<artifact-root>/spec/prd.md`, run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`; before spec-changing capability work, run `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`.
- Use `adapters/codex/bin/preflight.sh start [cwd] [session-id]` at session start when Codex has no automatic session-start hook, so stale workflow bypass flags are cleaned.
- Use `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` to surface tracked/untracked workflow state when Codex has no automatic prompt hook.
- Use `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly wants to toggle the tracked/untracked workflow escape hatch.
- Use `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text memory injection when Codex has no automatic session-start hook.
- Use `adapters/codex/bin/preflight.sh recall "<prompt>" [cwd]` before answering prompts with recall signal words when Codex has no automatic prompt hook.
- Use `adapters/codex/bin/preflight.sh briefing [cwd]` on the dedicated agent desk when Codex has no automatic prompt hook.
- Use `adapters/codex/bin/preflight.sh worklog [cwd]` before worklog-board or agent-notes work to inspect configured notes/app paths without mutating data.
- Use `adapters/codex/bin/preflight.sh distill-delta <session-id>` to inspect Codex transcript deltas. Use `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]` only for explicit proposal generation; do not auto-apply memory distillation until a Codex no-tools worker contract exists.
- Treat `codex_setting/tools` as a selective memory-tool projection. Do not assume every shared tool is Codex-supported.
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
