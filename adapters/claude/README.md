# Claude Code Adapter

This adapter maps the common agent harness onto Claude Code.

## Entry Points

| Surface | File |
|---|---|
| Session bootstrap | `adapters/claude/CLAUDE.md` |
| Runtime settings | `adapters/claude/settings.json` |
| Slash commands | `adapters/claude/commands/` |
| Runtime worker wrappers | `adapters/claude/bin/` |
| Dispatch registry metadata | `adapters/claude/bin/dispatch-headless.py` records route/depth ownership plus SD-49 `attempt_id`, exact `parent_attempt_id`, PID/start/PGID identity, launch authority, fallback ordinal, and checked nested tuple evidence in the inherited canonical global registry so Fleet can render and safely reconcile cross-harness ownership such as Codex → Claude. |
| Capabilities | `adapters/claude/skills/*/SKILL.md` |
| Role profiles | `adapters/claude/agents/*.md` |
| Hook scripts | `hooks/`, `utilities/` |
| Status line | `adapters/claude/statusline.sh` |

## Worker bootstrap boundary

Headless dispatch injects the portable kernel and one worker-type fragment.
Masked profiles expose only selected Skills/agents, a small runtime attach
layer, and the selected specialization; they no longer instruct a worker to
read all four main core documents. Worker detail is artifact-only and the
return is the fixed `artifact` / `verdict` / `blocker` envelope. Claude custom
subagents can still inherit the runtime's project/user `CLAUDE.md` hierarchy,
so that residual runtime input is reported separately from profile masking.

## Runtime Mapping

| Core Concept | Claude Code Implementation |
|---|---|
| capability | Skill |
| role profile | Agent |
| adapter bootstrap | `adapters/claude/CLAUDE.md` |
| agent home | `$HOME/.claude` by default; overridable with `AGENT_HOME` or `CLAUDE_HOME` |
| artifact root | primary-checkout canonical `.agent_reports` via `utilities/artifact-root.sh`; linked-worktree snapshots are read-only; legacy fallback only at the canonical root |
| worktree cleanup | `adapters/claude/bin/worktree-cleanup.sh`; dry-run first, apply only after merge + integrated verification + push |
| artifact-order gate | `hooks/artifact-guard.sh` |
| spec read gate | `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` |
| git safety gate | `hooks/git-state-guard.sh` |
| material route gate | `hooks/material-route-guard.py`; same-session route compile marker plus source Edit/Write and `git commit` chokepoints |
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
| `deep orchestrator` | `opus` xhigh | Stage gates, failover, and evidence judgment for standard+ dispatch-depth-1 ownership |
| `fast implementer` | `sonnet` | Routine implementation and refactoring; escalate complex API/library design |
| `orchestrator` | `sonnet` high | Balanced mechanical coordination of decided calls, paths, and states |
| `external adversary` | Codex CLI via `codex-review-team` | Independent hostile review for the `adversarial` intensity pass. The same Codex engine also runs the neutral cross-harness reviewer used for the `strong`+ replica, but that is a reviewer role (different family), not this hostile role. |
| `external adversary orchestrator` | `sonnet` wrapper | Invoke and summarize the external engine rather than perform the review |

This mapping reproduces the intensity-derived rigor tiers from `CONVENTIONS §1.1`; there is no separate `--qa` axis. Wrappers never choose automatically: main or the orchestrator selects `--model-role` or concrete `--model --effort` for every job. Registered headless inheritance and config-declared interactive-main-only models are rejected before launch; interactive usage/status telemetry remains visible.

Two `CONVENTIONS §1.1` properties are intensity-independent and this adapter honors them: every review the `품질관리팀` runs carries the refute-by-default adversarial stance (anchored in `CONVENTIONS §1.1` / `roles/MODES.md`; `agent-modes/qa/_review_rules.md` is the single source for the code-review, plan-review, and test modes that load it), and an independent pass replicates across a different harness family: at `strong`+ the riskiest-point reviewer runs cross-harness on the Codex `codex-review-team` family as a 2-way replica/merge (a reviewer role on a different family, not the hostile `external adversary`), while the hostile `external adversary` pass stays reserved for `adversarial`. When Codex is unavailable, fail loudly if the cross-harness pass was explicitly requested; otherwise fall back to a same-family independent reviewer and report the reduced independence.

## Compatibility

Claude Code projects created before the neutral artifact root use `.claude_reports/`. This adapter recognizes both names at the project-wide canonical root. New projects should use `.agent_reports/`; existing projects can migrate later or keep the legacy directory indefinitely.

For shell code, use `utilities/artifact-root.sh`. In a linked task worktree it resolves the primary checkout, so a tracked local artifact snapshot is never a write target. Headless dispatch passes that exact path with Claude `--add-dir`.

For harness-home paths, use `utilities/agent-home.sh` or the equivalent rule: prefer `AGENT_HOME`, then `CLAUDE_HOME`, then `$HOME/agent_setting` when present, then `$HOME/.claude` as legacy fallback.
