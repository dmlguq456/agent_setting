# Claude Code Adapter

This adapter maps the common agent harness onto Claude Code.

## Entry Points

| Surface | File |
|---|---|
| Session bootstrap | `adapters/claude/CLAUDE.md` |
| Runtime settings | `adapters/claude/settings.json` |
| Slash commands | `adapters/claude/commands/` |
| Runtime worker wrappers | `adapters/claude/bin/` |
| Dispatch registry metadata | `adapters/claude/bin/dispatch-headless.py` records `intensity`, `depth`, `parent_sid`, `worker_role`, `owner`, and `owner_harness` so fleet can render cross-harness ownership such as Codex → Claude. |
| Capabilities | `adapters/claude/skills/*/SKILL.md` |
| Role profiles | `adapters/claude/agents/*.md` |
| Hook scripts | `hooks/`, `utilities/` |
| Status line | `adapters/claude/statusline.sh` |

## Runtime Mapping

| Core Concept | Claude Code Implementation |
|---|---|
| capability | Skill |
| role profile | Agent |
| adapter bootstrap | `adapters/claude/CLAUDE.md` |
| agent home | `$HOME/.claude` by default; overridable with `AGENT_HOME` or `CLAUDE_HOME` |
| artifact root | primary-checkout canonical `.agent_reports` via `utilities/artifact-root.sh`; linked-worktree snapshots are read-only; legacy fallback only at the canonical root |
| worktree cleanup | `adapters/claude/bin/worktree-cleanup.sh`; dry-run first, apply only after merge + integrated verification + push |
| tracked/untracked signal | `workflow-guard-hook.sh` + `adapters/claude/statusline.sh` |
| artifact-order gate | `hooks/artifact-guard.sh` |
| spec read gate | `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` |
| git safety gate | `hooks/git-state-guard.sh` |
| memory write guard | `hooks/builtin-memory-guard.sh` |

## Runtime Home Projection

Target layout:

```text
$HOME/agent_setting/        # neutral repo
$HOME/agent_setting/claude_setting/ # versioned Claude projection
$HOME/.claude/              # Claude Code runtime home
```

Claude Code should see the same files it expects today, but they should be symlinked from the versioned Claude projection where practical:

```text
$HOME/.claude/CLAUDE.md      -> $HOME/agent_setting/claude_setting/CLAUDE.md
$HOME/.claude/README.md      -> $HOME/agent_setting/claude_setting/README.md
$HOME/.claude/core           -> $HOME/agent_setting/claude_setting/core
$HOME/.claude/skills         -> $HOME/agent_setting/claude_setting/skills
$HOME/.claude/agents         -> $HOME/agent_setting/claude_setting/agents
$HOME/.claude/agent-modes    -> $HOME/agent_setting/claude_setting/agent-modes
$HOME/.claude/hooks          -> $HOME/agent_setting/claude_setting/hooks
$HOME/.claude/utilities      -> $HOME/agent_setting/claude_setting/utilities
$HOME/.claude/tools          -> $HOME/agent_setting/claude_setting/tools
$HOME/.claude/commands       -> $HOME/agent_setting/claude_setting/commands
$HOME/.claude/bin            -> $HOME/agent_setting/claude_setting/bin
$HOME/.claude/statusline.sh  -> $HOME/agent_setting/claude_setting/statusline.sh
$HOME/.claude/track-toggle.sh -> $HOME/agent_setting/claude_setting/track-toggle.sh
```

Keep Claude-owned mutable state in `$HOME/.claude`: credentials, sessions, projects, history, shell snapshots, cache, daemon logs, and local DBs. Do not move those into the neutral repo.

## Model Role Mapping

The Claude Code adapter maps portable roles from `core/CONVENTIONS.md §2` to concrete models while preserving established operating quality. Shared docs use role names; only Claude-specific frontmatter and Agent calls use concrete model names.

| Portable role | Claude Code mapping | Reproduced behavior |
|---|---|---|
| `fast reviewer` | `sonnet` | Broad cost-efficient coverage, typo, style, cross-reference, structure, and verbatim checks |
| `fast fact-checker` | `sonnet` | Narrow citation, venue, year, metric, and lineage checks against source artifacts |
| `fast writer` | `sonnet` | Assemble verified artifacts into a final report |
| `deep reviewer` | `opus` | methodology, domain expertise, completeness, safety/security, architecture risk |
| `deep maker` | `opus` | Planning, research synthesis, and visual/editorial work requiring high judgment |
| `deep orchestrator` | `opus` high | Stage gates, failover, and evidence judgment for standard+ depth-1 ownership |
| `fast implementer` | `sonnet` | Routine implementation and refactoring; escalate complex API/library design |
| `orchestrator` | `sonnet` medium | Balanced mechanical coordination of decided calls, paths, and states |
| `external adversary` | Codex CLI via `codex-review-team` | Independent hostile review for adversarial intensity |
| `external adversary orchestrator` | `sonnet` wrapper | Invoke and summarize the external engine rather than perform the review |

This mapping reproduces the intensity-derived rigor tiers from `CONVENTIONS §1.1`; there is no separate `--qa` axis. Wrappers never choose automatically: main or the orchestrator selects `--model-role`, concrete `--model --effort`, or explicit `--inherit-model-settings` for every job.

## Compatibility

Claude Code projects created before the neutral artifact root use `.claude_reports/`. This adapter recognizes both names at the project-wide canonical root. New projects should use `.agent_reports/`; existing projects can migrate later or keep the legacy directory indefinitely.

For shell code, use `utilities/artifact-root.sh`. In a linked task worktree it resolves the primary checkout, so a tracked local artifact snapshot is never a write target. Headless dispatch passes that exact path with Claude `--add-dir`.

For harness-home paths, use `utilities/agent-home.sh` or the equivalent rule: prefer `AGENT_HOME`, then `CLAUDE_HOME`, then `$HOME/agent_setting` when present, then `$HOME/.claude` as legacy fallback.
