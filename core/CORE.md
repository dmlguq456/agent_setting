# Agent Harness Core

> Model-agnostic contract. This file defines the portable workflow substrate. Tool-specific files such as `adapters/claude/CLAUDE.md` are adapters that map this contract onto one runtime.

## 1. Layers

| Layer | Owns | Portable? |
|---|---|---|
| Core | workflow, artifact layout, memory lifecycle, QA tiers, model roles, safety invariants | yes |
| Adapter | tool bootstrap, hook schema, slash commands, status UI, permission model, concrete model mapping, runtime-home projection | no |
| Local runtime | credentials, session state, caches, daemon logs | no |

`adapters/claude/CLAUDE.md` is the Claude Code adapter entry file. Runtime-specific adapter notes live under `adapters/`; future adapters should keep their own bootstrap instructions there and point back to this core contract.

## 2. Agent Home

The canonical neutral name for the installed harness repository is:

```text
<agent-home>
```

Runtime code should resolve it in this order:

1. `AGENT_HOME`
2. adapter-specific compatibility variables such as `CLAUDE_HOME`
3. `$HOME/agent_setting` when present
4. the adapter's legacy default install path, currently `$HOME/.claude` for the Claude Code adapter

Use `utilities/agent-home.sh` in shell code when a concrete path is needed.

Preferred physical layout:

```text
$HOME/agent_setting/        # neutral git repo, common core + adapters
$HOME/.claude/              # Claude Code runtime home, mostly runtime-owned
$HOME/.codex/               # Codex runtime home, mostly runtime-owned
```

Runtime homes should be adapter projections, not the source repository. Keep credentials, sessions, logs, SQLite state, caches, and other runtime-owned files in the runtime home. Expose the harness into each runtime home with symlinks or adapter-owned bootstrap files.

Example projection:

```text
$HOME/.claude/CLAUDE.md      -> $HOME/agent_setting/adapters/claude/CLAUDE.md
$HOME/.claude/core           -> $HOME/agent_setting/core
$HOME/.claude/skills         -> $HOME/agent_setting/skills
$HOME/.claude/agents         -> $HOME/agent_setting/agents
$HOME/.claude/hooks          -> $HOME/agent_setting/hooks
```

`~/.claude` remains the current Claude Code adapter's legacy installation path during migration. New cross-tool documentation should prefer `<agent-home>` unless it is intentionally describing the Claude adapter runtime home.

## 3. Artifact Root

The canonical project artifact directory is:

```text
.agent_reports/
```

Existing projects may still use:

```text
.claude_reports/
```

`.claude_reports/` is a legacy alias. Runtime code must recognize both names during migration. New projects and new documentation should prefer `.agent_reports/`.

The artifact root contains durable, project-scoped work products:

| Folder | Meaning |
|---|---|
| `analysis_project/` | project source analysis |
| `research/` | topic research and external references |
| `spec/` | current product/code blueprint |
| `plans/` | implementation cycles |
| `documents/` | document drafts and refinement artifacts |
| `experiments/` | experiment setup, evaluation, and run logs |

## 4. Workflow Invariants

Artifacts move forward in one direction:

```text
research / analysis_project -> spec -> plans
research / analysis_project -> documents -> refinement
```

Tracked mode enforces creation order for new artifacts. Untracked mode is an explicit escape hatch for temporary, direct work.

Each artifact should be changed through the capability that owns it:

| Artifact | Owner |
|---|---|
| `spec/` | spec capability |
| `plans/` | code capability |
| `documents/` | draft/refine capability |
| `experiments/` | lab capability |
| user profile records | analyze-user / post-it capability |

## 5. Adapter Responsibilities

Each adapter should provide:

- a bootstrap file that loads this core contract;
- a way to expose capabilities (`skills/`) and role profiles (`agents/`);
- a concrete mapping from portable model roles (`fast reviewer`, `deep reviewer`, `external adversary`, etc.) to runtime-specific models, tools, or prompt profiles;
- a projection from the neutral `<agent-home>` repository into the runtime home using symlinks, generated files, or runtime-native registration;
- hooks or checks for artifact order, git safety, and memory writes;
- a status/reminder surface for tracked vs untracked mode;
- compatibility with both `.agent_reports/` and `.claude_reports/` until legacy projects are migrated.

## 6. Naming Policy

Use neutral names for new cross-tool concepts:

| Prefer | Avoid for new core concepts |
|---|---|
| agent harness | Claude setting |
| artifact root | `.claude_reports` as a generic term |
| capability | Claude-only Skill semantics |
| role profile | Claude-only Agent semantics |
| model role | `opus` / `sonnet` / vendor model names as portable semantics |
| adapter | tool-specific bootstrap |
