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
- Run deterministic guard scripts directly when the Codex runtime cannot attach equivalent hooks.
- Before edits, run `adapters/codex/bin/preflight.sh write <file> [session-id]`.
- After design HTML writes, run `adapters/codex/bin/preflight.sh design <file>`.
- After actually reading `<artifact-root>/spec/prd.md`, run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`; before spec-changing capability work, run `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`.
- Use `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` to surface tracked/untracked workflow state when Codex has no automatic prompt hook.
- Use `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text memory injection when Codex has no automatic session-start hook.
- Use `adapters/codex/bin/preflight.sh recall "<prompt>" [cwd]` before answering prompts with recall signal words when Codex has no automatic prompt hook.
- Use `adapters/codex/bin/preflight.sh briefing [cwd]` on the dedicated agent desk when Codex has no automatic prompt hook.
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
