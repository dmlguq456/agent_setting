# Claude Code Adapter

This adapter maps the common agent harness onto Claude Code.

## Entry Points

| Surface | File |
|---|---|
| Session bootstrap | `CLAUDE.md` |
| Runtime settings | `settings.json` |
| Slash commands | `commands/` |
| Capabilities | `skills/*/SKILL.md` |
| Role profiles | `agents/*.md` |
| Hook scripts | `hooks/`, `utilities/` |
| Status line | `statusline.sh` |

## Runtime Mapping

| Core Concept | Claude Code Implementation |
|---|---|
| capability | Skill |
| role profile | Agent |
| adapter bootstrap | `CLAUDE.md` |
| agent home | `$HOME/.claude` by default; overridable with `AGENT_HOME` or `CLAUDE_HOME` |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `workflow-guard-hook.sh` + `statusline.sh` |
| artifact-order gate | `hooks/artifact-guard.sh` |
| spec read gate | `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` |
| git safety gate | `hooks/git-state-guard.sh` |
| memory write guard | `hooks/builtin-memory-guard.sh` |

## Compatibility

Claude Code projects created before the neutral artifact root use `.claude_reports/`. This adapter recognizes both names. New projects should use `.agent_reports/`; existing projects can migrate later or keep the legacy directory indefinitely.

For shell code, use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

For harness-home paths, use `utilities/agent-home.sh` or the equivalent rule: prefer `AGENT_HOME`, then `CLAUDE_HOME`, then `$HOME/.claude`.
