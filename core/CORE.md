# Agent Harness Core

> Model-agnostic contract. This file defines the portable workflow substrate. Tool-specific files such as `adapters/claude/CLAUDE.md` are adapters that map this contract onto one runtime.

## 1. Layers

| Layer | Owns | Portable? |
|---|---|---|
| Core | workflow, artifact layout, memory lifecycle, QA tiers, model roles, safety invariants | yes |
| Adapter | tool bootstrap, hook schema, slash commands, status UI, permission model, concrete model mapping, runtime-home projection | no |
| Local runtime | credentials, session state, caches, daemon logs | no |

`adapters/claude/CLAUDE.md`, `adapters/codex/AGENTS.md`, and `adapters/opencode/AGENTS.md` are runtime adapter entry files. Runtime-specific adapter notes live under `adapters/`; future adapters should keep their own bootstrap instructions there and point back to this core contract.

## 2. Agent Home

The canonical neutral name for the installed harness root is:

```text
<agent-home>
```

Runtime code should resolve it in this order:

1. `AGENT_HOME`
2. adapter-specific compatibility variables such as `CLAUDE_HOME`
3. `${XDG_DATA_HOME:-$HOME/.local/share}/agent-harness/current` when a managed release is installed
4. `$HOME/agent_setting` when a linked checkout is present
5. the adapter's legacy default install path, currently `$HOME/.claude` for the Claude Code adapter

Use `utilities/agent-home.sh` in shell code when a concrete path is needed.

Supported physical layouts:

```text
$HOME/.local/share/agent-harness/releases/<version>/  # immutable managed release
$HOME/.local/share/agent-harness/current              # atomic pointer to active release
$HOME/agent_setting/                                  # linked maintainer checkout
$HOME/.claude/              # Claude Code runtime home, mostly runtime-owned
$HOME/.codex/               # Codex runtime home, mostly runtime-owned
```

General-user installation uses a checksum-verified managed release. Maintainer
development uses a linked checkout. Release updates stage and validate a new
root before switching `current`; they must not fetch, pull, or rewrite a linked
checkout. Runtime activation remains local after the release has been
downloaded, and session reload or restart boundaries remain runtime-specific.

Runtime homes should be adapter projections, not the source repository. Keep credentials, sessions, logs, SQLite state, caches, and other runtime-owned files in the runtime home. Expose the harness into each runtime home with symlinks or adapter-owned bootstrap files.

Projection example:

```text
<runtime-home>/<adapter-bootstrap> -> <agent-home>/<adapter-projection>/<adapter-bootstrap>
<runtime-home>/core                -> <agent-home>/<adapter-projection>/core
<runtime-home>/<capability-surface> -> <agent-home>/<adapter-projection>/<capability-surface>
<runtime-home>/<role-surface>      -> <agent-home>/<adapter-projection>/<role-surface>
<runtime-home>/<hook-surface>      -> <agent-home>/<adapter-projection>/<hook-surface>
```

Legacy runtime homes remain adapter-owned compatibility paths during migration.
New cross-tool documentation should prefer `<agent-home>` and `<runtime-home>`
unless it is intentionally describing a specific adapter runtime home.

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

## 3.1. Agent Notes And Worklog Board

The canonical neutral name for the cross-project continuity board data root is:

```text
<agent-notes-root>
```

It is not the project artifact root and not the unified memory store. It is a
mutable operator-facing state layer used to carry agent work across projects and
sessions:

| Folder | Meaning | Commit policy |
|---|---|---|
| `cards/` | Layer 1 user-owned task/project cards | user data; never commit to the harness repo |
| `_layer2/` | Layer 2 agent-owned notes, catalogs, and source-to-card routing rows | mutable board data; never commit to the harness repo |
| `_triage/`, `_feedback/`, `_change_review/` | approval, feedback, and change-review queues | runtime/user state; never commit to the harness repo |
| `digests/`, `oncall/`, `study/`, `manual/` | daily summaries, operator reports, study proposals, and board manual content | state/docs for the notes root; never commit to the harness repo unless intentionally mirrored in a separate notes repo |

The neutral name for the UI/application that reads and updates this state is:

```text
<worklog-board-app>
```

The app may live in its own repository or local runtime workspace. Its source,
build output, local DBs, caches, `.env*`, dispatch logs, and worktrees are not
part of this harness repository unless a future migration explicitly promotes a
runtime-neutral board component into `tools/` or another portable source
directory.

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

- a bootstrap note that declares it is derived from core and that edits start in
  core before adapter changes;
- a bootstrap file that loads this core contract;
- a way to expose portable capabilities (`capabilities/`) and portable role profiles (`roles/`);
- a concrete mapping from portable model roles (`fast reviewer`, `deep reviewer`, `external adversary`, etc.) to runtime-specific models, tools, or prompt profiles;
- a projection from the neutral `<agent-home>` repository into the runtime home using symlinks, generated files, or runtime-native registration;
- hooks or checks for artifact order, git safety, and memory writes;
- hooks or checks that prevent adapter edits before the relevant core contract
  has actually been read in the current session;
- a status/reminder surface for tracked vs untracked mode;
- compatibility with both `.agent_reports/` and `.claude_reports/` until legacy projects are migrated;
- a documented realization of `<agent-notes-root>` and `<worklog-board-app>` if
  that runtime reads or updates cross-project worklog state.

## 6. Naming Policy

Use neutral names for new cross-tool concepts:

| Prefer | Avoid for new core concepts |
|---|---|
| agent harness | Claude setting |
| artifact root | `.claude_reports` as a generic term |
| capability | Claude-only Skill semantics |
| role profile | Claude-only Agent semantics |
| model role | vendor model names as portable semantics |
| adapter | tool-specific bootstrap |
