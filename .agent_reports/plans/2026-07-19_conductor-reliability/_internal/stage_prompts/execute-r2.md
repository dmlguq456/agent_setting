You are the depth-2 `code-execute` worker (fast implementer, strong intensity)
for the immutable route `rt-1d200b72bcfb544c`, node `execute`. Implement the
approved plan exactly, in the task worktree, committing core-first. You own
source mutation and commits.

## Authoritative inputs (read fully first)
- Plan: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/plan.md`
- Checklist: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/checklist.md`
- Scope packet: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/conductor-prompt.md`
- Spec (READ-ONLY, do NOT edit): `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` §13.7.6, §13.10
- Worktree: `/home/Uihyeop/agent_setting-wt/conductor-reliability`

## Mandatory execution rules
- **Core-first**: implement and COMMIT the portable `core/**` contract change
  (C1 in plan.md) BEFORE any adapter/runtime edit. Then implement the four
  outcomes as the plan's commit groups (C2..C5), each a self-contained commit
  with its focused tests green before moving on.
- Commit in the worktree branch `conductor-reliability`. Use clear commit
  messages. End each commit message with the Co-Authored-By trailer for Claude.
- **Do NOT edit** `spec/**`, `utilities/dispatch-route.sh`, or its tests
  (owned by the concurrent selector-paths cycle).
- Never `git reset --hard`; preserve unrelated dirty/untracked state.
- Delete any test-created `__pycache__` before each commit; keep `git diff
  --check` clean.
- Honor the plan's self-hosting boundary note: the live pipeline uses the
  INSTALLED `AGENT_HOME` tools, so your worktree edits do not hot-swap the
  running conductor — implement + commit in the worktree and record the
  boundary in dev_logs; do not try to hot-reload the conductor.

## Scope reminder (implement exactly what plan.md specifies)
1. SD-71 Claude one-shot conductor hardening: live `-p` probe for exact fatal
   async wait/scheduling tool names; deny ONLY probe-proven names via
   `--disallowedTools`; never deny `Bash`/`dispatch-wait.sh`. Disposable Stop-hook
   fixture; register Stop gate only if fire+block+stdout all hold, else keep
   documented held fallback. Deterministic wrapper deny/fallback tests.
2. SD-64/71 orphan conductor reconcile + visibility via the existing single
   attempt classifier; surface through liveness, Codex preflight status, Fleet
   current-attempt view; no auto-resume/relaunch, no closing live child; zero
   false positives.
3. SD-69 Codex linked-worktree mutation boundary: project the exact primary
   `$AGENT_HOME/.spec-grounding` as a narrow writable root for route-bound Codex
   workers, created safely; never expose all of agent home or `.git`; encode the
   Codex mutation stage as `no-commit`; disposable linked-worktree fixture
   proving source edits + primary spec-marker persistence while commit stays
   honestly unavailable. Do NOT make protected Git metadata writable; do NOT
   claim `--add-dir <git-common-dir>` enables commit.
4. SD-70 completion marker ↔ exact attempt row: extend
   `utilities/capability-route.py complete` to accept canonical `--jobs` +
   exact `--attempt-id`; write marker atomically then idempotently close ONLY
   that row done `note=completed-marker` + marker evidence; preserve marker +
   structured nonzero on close failure; reconcile repairs only the marker-backed
   exact stale row. Cover prior BLOCKED + current PASS + later live retry,
   duplicate complete, mismatch/missing attempt, unwritable/missing jobs. Never
   breadth-close.

## Verification during execute (per checklist.md, keep evidence in dev_logs/)
- Run the focused suites mapped to each commit BEFORE committing that group:
  capability-route, dispatch-registry/reconcile, dispatch_contract, dispatch_node,
  wrapper sandbox-argument tests, liveness/preflight/Fleet classification,
  worker-route-guard, stage-dispatch-fallback, nested-dispatch-eligibility, fleet
  state/registry/route tests.
- Capture the Claude `-p` tool-policy + Stop-hook probe evidence under
  `_internal/` (e.g. `probe_claude_tools.txt`, `probe_stop_hook.txt`).
- Keep raw command logs and the bootstrap-boundary note in
  `dev_logs/` (write scope: `source/**`, `checklist.md`, `dev_logs/**`,
  `_internal/dev_reviews/**`).

## Output / verdict
- Update `checklist.md` boxes as you complete them.
- Write `dev_logs/execute-r2.md` summarizing each commit (hash + subject), tests
  run with pass/fail, probe evidence paths, parity-honesty disclosures, and any
  honest runtime limitation (commit unavailability under Codex sandbox, etc.).
- Return a concise verdict: PASS only if all planned commits landed with their
  focused tests green in the worktree; otherwise FAIL/BLOCKED with the exact
  blocker. Do NOT merge or push main.
