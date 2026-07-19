You are the depth-2 `code-plan` worker (deep maker, strong intensity) for the
immutable route `rt-1d200b72bcfb544c`, node `plan`. Produce a durable, exact
implementation plan for the "conductor reliability · Codex mutation · registry
hygiene" cycle. Write ONLY plan artifacts; do not edit source.

## Required reading (absolute paths, read fully before planning)
- Conductor scope packet:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/conductor-prompt.md`
- Governing spec sections:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`
  §13.7.6 SD-64 and §13.10 SD-69~71
- Route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/route.json`
- Core contract first: `/home/Uihyeop/agent_setting-wt/conductor-reliability/core/CORE.md`
  and `AGENTS.md` (core-first ordering).
- Current implementation of every tool you will change, in the worktree
  `/home/Uihyeop/agent_setting-wt/conductor-reliability`:
  `utilities/dispatch-registry.py` (reconcile + classifier),
  `utilities/capability-route.py` (`complete`),
  `utilities/dispatch_contract.py` (`claim_attempt_row`/`close_attempt_row`),
  `adapters/*/bin/dispatch-headless.py` and the Codex/Claude sandbox wrappers,
  liveness/preflight/Fleet surfaces (`utilities/dispatch-liveness.sh`,
  `adapters/codex/bin/preflight.sh`, `tools/fleet/**`),
  and `tools/fleet/model/classify_attempt_evidence`.

## Scope — plan all four outcomes with exact files and functions
1. Claude one-shot conductor hardening (SD-71): probe exact fatal async
   wait/scheduling tool names in current Claude `-p`; only proven names via
   `--disallowedTools`; never disable Bash or synchronous `dispatch-wait.sh`.
   Re-run a disposable Claude 2.1.215 `-p` Stop-hook fixture; register a Stop
   gate ONLY if hook fires + can block + preserves stdout, else keep held
   fallback. Standardize the conductor prompt/depth-note contract at the
   portable core surface FIRST (no Monitor/wakeup; synchronous dispatch-wait in
   current turn), adapter projection follows. Add deterministic wrapper tests
   for the deny/fallback behavior.
2. Orphan conductor reconcile + visibility (SD-64/71): extend
   `dispatch-registry.py reconcile` using the existing single-attempt classifier
   so exact conductor death + unfinished completion node + open/live child or
   unstarted successor closes the conductor row with `note=dead-parent-orphaned`.
   Surface classification + route/resume boundary through liveness, Codex
   preflight status, and Fleet current-attempt view. No auto-resume/relaunch, no
   closing a live child. Zero false positives for live conductors + completed
   routes.
3. Codex linked-worktree mutation boundary (SD-69): do NOT make protected Git
   metadata writable; do NOT claim `--add-dir <git-common-dir>` enables commit.
   Project the exact primary `$AGENT_HOME/.spec-grounding` directory as a narrow
   writable root for route-bound Codex workers, created safely; never expose all
   of agent home or `.git`. Encode the linked-worktree Codex mutation stage as
   `no-commit` in owner/stage contract + dispatch metadata where needed; a
   trusted depth-0/Claude boundary commits after PASS. Add a disposable
   linked-worktree fixture proving source edits + primary spec-marker persistence
   while commit stays honestly unavailable.
4. Completion marker ↔ exact attempt row (SD-70): extend
   `capability-route.py complete` to accept canonical `--jobs` and exact current
   `--attempt-id`; write marker atomically then idempotently close ONLY that row
   done with `note=completed-marker` + marker evidence; preserve marker and
   return structured nonzero on row-close failure; reconcile repairs only the
   marker-backed exact stale row. Test prior BLOCKED + current PASS + later live
   retry, duplicate complete, mismatch/missing attempt, unwritable/missing jobs.
   Never breadth-close.

## Constraints
- Core-first: edit + commit portable `core/**` contract before adapter/runtime.
- Do NOT edit `spec/**`, `utilities/dispatch-route.sh`, or its tests
  (owned by the concurrent selector-paths cycle).
- Source edits only in the task worktree; never `git reset --hard`; preserve
  unrelated dirty/untracked state.
- Claude/Codex/OpenCode adapters are siblings; change only surfaces whose
  runtime semantics actually differ; keep parity disclosures honest.

## Verification floor to enumerate in checklist.md (exact focused suites)
- `git diff --check`, syntax/compile for touched Python/shell.
- focused tests for capability-route, dispatch-registry/reconcile, wrapper
  sandbox arguments, liveness/preflight/Fleet classification.
- existing dispatch contract/node/route/worker-guard suites affected.
- disposable linked-worktree Codex mutation fixture.
- current Claude `-p` Stop/tool-policy probe with captured evidence.
- `bash tools/check-adaptation-boundary.sh`.
- portable guard suite at the qa-policy assurance level.
- delete test-created `__pycache__` before commits.

## Outputs (write to these absolute paths; write scope plan/** + _internal/plan_reviews/**)
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/plan.md`
  — ordered, commit-grouped steps (core-first), each naming exact files and
  functions, the 4 outcomes, and honest runtime limitations already known
  (Claude 2.1.215 supports `--disallowedTools`; Codex 0.144.6 keeps `.git`
  and resolved gitdir protected even under writable roots → `--add-dir
  <git-common-dir>` is NOT an accepted commit fix).
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/checklist.md`
  — the focused verification suites above, mapped to steps.

Return a concise plan verdict. Your durable artifacts are the plan.md and
checklist.md; keep raw deliberation under `_internal/plan_reviews/`.
