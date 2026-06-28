# Agent Harness Core

> Model-agnostic contract. This file defines the portable workflow substrate. Tool-specific files such as `CLAUDE.md` are adapters that map this contract onto one runtime.

## 1. Layers

| Layer | Owns | Portable? |
|---|---|---|
| Core | workflow, artifact layout, memory lifecycle, QA tiers, safety invariants | yes |
| Adapter | tool bootstrap, hook schema, slash commands, status UI, permission model | no |
| Local runtime | credentials, session state, caches, daemon logs | no |

`CLAUDE.md` is the Claude Code adapter entry file. Runtime-specific adapter notes live under `adapters/`; future adapters should keep their own bootstrap instructions there and point back to this core contract.

## 2. Artifact Root

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

## 3. Workflow Invariants

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

## 4. Adapter Responsibilities

Each adapter should provide:

- a bootstrap file that loads this core contract;
- a way to expose capabilities (`skills/`) and role profiles (`agents/`);
- hooks or checks for artifact order, git safety, and memory writes;
- a status/reminder surface for tracked vs untracked mode;
- compatibility with both `.agent_reports/` and `.claude_reports/` until legacy projects are migrated.

## 5. Naming Policy

Use neutral names for new cross-tool concepts:

| Prefer | Avoid for new core concepts |
|---|---|
| agent harness | Claude setting |
| artifact root | `.claude_reports` as a generic term |
| capability | Claude-only Skill semantics |
| role profile | Claude-only Agent semantics |
| adapter | tool-specific bootstrap |
