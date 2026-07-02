## L0 — Core Contract (dispatch profile bootstrap)

This is a masked, per-dispatch config home. Before doing any work:

1. **Read the four core documents** — `core/CORE.md`, `core/CONVENTIONS.md`,
   `core/OPERATIONS.md`, `core/WORKFLOW.md` — as the model/tool-neutral
   contract governing this session. They are not maskable; they are always
   projected into this home.
2. **Obey the guard hooks** registered in this home's `settings.json` —
   `artifact-guard`, `git-state-guard`, `spec-skill-gate` (spec gate),
   `builtin-memory-guard`. These are deterministic, profile-independent
   invariants (see `core/CORE.md` §0.5) — do not attempt to work around them.
3. **Artifact convention**: write task artifacts under the project's
   `.agent_reports/` root (legacy alias `.claude_reports/`), following the
   same skill/artifact layout as the main harness.
4. **Depth-1 rule**: this dispatch does not re-dispatch. Do not launch
   another headless subagent or nested `claude -p` from inside this session
   — orchestration, merge, and further dispatch are main-session-only
   concerns and are intentionally not part of this bootstrap.

## Attach mechanism

This config home is attached via `CLAUDE_CONFIG_DIR=<home>` when this
session was launched. Everything under this directory (skills, agents,
settings, credentials) is a masked partial projection of the single repo
source — there is no separate content fork to keep in sync.
