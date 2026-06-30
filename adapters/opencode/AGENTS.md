# AGENTS.md — OpenCode Adapter Bootstrap

This file maps the shared agent harness onto OpenCode sessions. It is an
adapter bootstrap, not the portable source of truth. Load it through the
`instructions` array in `opencode.json` / `opencode.jsonc`.

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
- Before treating a capability as supported, run `adapters/opencode/bin/preflight.sh capability-info <capability>` and follow the reported OpenCode realization.
- Treat OpenCode-native skills under `adapters/opencode/skills/` as generated adapter output from `capabilities/`; do not load Claude Skill, command, or agent files as native OpenCode surfaces.
- Treat OpenCode-native commands, agents, skills, and plugins as adapter-owned output from `capabilities/`, `roles/`, and portable hook invariants.
- Expose OpenCode skills, agents, commands, and plugin guards through `opencode_setting/opencode-skills`, `opencode_setting/opencode-agents`, `opencode_setting/opencode-commands`, and `opencode_setting/opencode-plugins`; do not copy Claude-native surfaces.
- When validating OpenCode-native discoverability, run with `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` so OpenCode's `~/.claude/skills/` compatibility autoload cannot mask missing adapter-owned output.
- Before using a `roles/modes/` fragment, run `adapters/opencode/bin/preflight.sh mode-info <family/mode>` and obey portable/tool-contract/unsupported status plus any named `tool_contract`.
- Run deterministic guard scripts directly when the OpenCode runtime cannot attach equivalent hooks. The adapter provides a JS plugin guard for write/edit/patch tools; use explicit preflight wrappers when that plugin is not installed or trusted.
- Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
- After design HTML writes, run `adapters/opencode/bin/preflight.sh design <file>`.
- Before claiming full design/autopilot-design support, run `adapters/opencode/bin/preflight.sh visual-harness`; exit 69 means the required OpenCode-native render/screenshot/image-inspection harness is still a tool-contract.
- After actually reading `<artifact-root>/spec/prd.md`, run `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`; before spec-changing capability work, run `adapters/opencode/bin/preflight.sh capability <name> [cwd] [session-id]`.
- Use `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` when no automatic session-start hook is attached, so stale untracked flags are GC'd.
- Use `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]` to surface tracked/untracked workflow state when OpenCode has no automatic prompt hook.
- Use `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly wants to toggle the tracked/untracked workflow escape hatch.
- Use `adapters/opencode/bin/preflight.sh memory [cwd]` for plain-text memory injection when OpenCode has no automatic session-start hook.
- Use `adapters/opencode/bin/preflight.sh recall "<prompt>" [cwd]` before answering prompts with recall signal words when OpenCode has no automatic prompt hook.
- Use `adapters/opencode/bin/preflight.sh briefing [cwd]` on the dedicated agent desk when OpenCode has no automatic prompt hook.
- Use `adapters/opencode/bin/preflight.sh worklog [cwd]` before worklog-board or agent-notes work to inspect configured notes/app paths without mutating data.
- Use `adapters/opencode/bin/preflight.sh distill-delta <session-id>` to read transcript deltas through `opencode export`. Use `adapters/opencode/bin/preflight.sh distill-propose <session-id> [cwd]` only for explicit proposal attempts; it is disabled by default and reports the remaining OpenCode no-tools worker tool-contract instead of auto-applying memory distillation.
- Treat `opencode_setting/tools` as a selective memory-tool projection. Do not assume every shared tool is OpenCode-supported.
- Treat `opencode_setting/utilities` as a selective utility projection. Do not assume every shared utility is OpenCode-supported.
- Keep OpenCode-owned credentials, sessions, DB state, logs, caches, and local databases outside the harness repo.

## Response Policy

- Answer the user in Korean unless they explicitly request another language.
- Keep implementation work grounded in the repo's current files and existing conventions.
- When modifying this harness repo, commit and push after validation.
- Do not run drill automatically; it can invoke headless runtime sessions and spend tokens. Report when drill would be useful.

## Compatibility Boundary

Claude Code files are implementation references, not OpenCode bootstrap files:

- `adapters/claude/CLAUDE.md`
- `adapters/claude/settings.json`
- `adapters/claude/commands/`
- `adapters/claude/statusline.sh`
- `adapters/claude/hooks/*.sh` (Claude hook event schema)

OpenCode has native surfaces for commands (`.opencode/command/`), skills
(`.opencode/skill/`), agents (`.opencode/agent/`), and plugin hooks (JS/TS).
When porting behavior, copy the invariant from `core/` first, then map it to
OpenCode tools, permission behavior, agent mode, and session lifecycle. Do not
copy Claude frontmatter or hook payloads into OpenCode-native files.
