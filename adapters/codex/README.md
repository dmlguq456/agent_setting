# Codex Adapter

This adapter maps the common agent harness onto Codex-style sessions.

## Status

Experimental. The portable contract is usable, but Codex does not consume Claude Code's `settings.json`, slash command registry, or hook event schema directly. Until a dedicated Codex bootstrap/wrapper exists, use the common files explicitly and run guard scripts as deterministic checks where needed.

## Entry Points

| Surface | File |
|---|---|
| Core contract | `CORE.md` |
| Workflow routing | `WORKFLOW.md` |
| Shared conventions | `CONVENTIONS.md` |
| Git and dispatch operations | `OPERATIONS.md` |
| Memory contract | `MEMORY.md` |
| Capabilities | `skills/*/SKILL.md` |
| Role profiles | `agents/*.md` |
| Hook and guard scripts | `hooks/`, `utilities/` |

## Runtime Mapping

| Core Concept | Codex Implementation |
|---|---|
| capability | Read and follow the relevant `skills/*/SKILL.md`; no native slash registry is assumed |
| role profile | Use `agents/*.md` and `agent-modes/` as delegation prompts or review personas |
| adapter bootstrap | Load `CORE.md` plus task-relevant shared docs; do not treat `CLAUDE.md` as portable bootstrap |
| agent home | Set `AGENT_HOME` to the installed harness directory |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `track-toggle.sh` and `utilities/workflow-guard-hook.sh` semantics; no automatic prompt hook unless wrapped |
| artifact-order gate | `hooks/artifact-guard.sh` can be run as a pre-write check by wrappers or manually |
| spec read gate | `hooks/spec-skill-gate.sh` / `hooks/spec-read-marker.sh` semantics apply when the runtime can emit equivalent events |
| git safety gate | `hooks/git-state-guard.sh` is the portable check; Codex must also honor sandbox and approval state |
| memory store | `tools/memory/mem.py` is runtime-neutral; hook automation is adapter-specific |

## Compatibility

Codex should create new project artifacts under `.agent_reports/`. Use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

Codex should resolve harness-home paths through `AGENT_HOME` or `utilities/agent-home.sh`. `CLAUDE_HOME` is accepted only as a Claude adapter compatibility alias.

Claude Code-specific files remain valid as implementation references, not as Codex bootstrap files:

- `CLAUDE.md` contains Claude Code routing and response rules.
- `settings.json` registers Claude Code hooks and permissions.
- `commands/` defines Claude Code slash commands.
- `statusline.sh` targets Claude Code's statusline contract.

When porting a behavior, copy the underlying invariant from `CORE.md`, `WORKFLOW.md`, `CONVENTIONS.md`, or `OPERATIONS.md`; then map it to Codex's tool, approval, and session model.
