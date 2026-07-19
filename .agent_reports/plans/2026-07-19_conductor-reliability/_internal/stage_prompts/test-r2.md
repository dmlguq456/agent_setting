You are the depth-2 `code-test` worker (deep reviewer, strong intensity) for
the immutable route `rt-1d200b72bcfb544c`, node `test`. You independently verify
the COMMITTED worktree at HEAD — do NOT trust the execute stage's logs. Run the
verification floor, record honest evidence, and emit a verdict.

## Inputs (read fully)
- Plan: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/plan.md`
- Checklist: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/checklist.md`
- Execute dev log (claims to verify, do NOT trust): `.../dev_logs/execute-r2.md`
- Scope packet: `.../_internal/conductor-prompt.md`
- Spec (READ-ONLY): `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` §13.7.6, §13.10
- Worktree under test: `/home/Uihyeop/agent_setting-wt/conductor-reliability`
  (5 commits `9d580b8e`→`e44c77a2` on `b9364824`).

## Verification floor — run against the committed worktree and capture evidence
1. `git diff --check` repo-wide clean; confirm `spec/**` and
   `utilities/dispatch-route.sh` (+ its tests) are UNTOUCHED
   (`git diff b9364824..HEAD --stat --` those paths must be empty).
2. Syntax/compile for every touched Python/shell file.
3. Focused suites (all must be green): capability-route, dispatch-registry /
   reconcile, dispatch_contract, dispatch_node, wrapper sandbox-argument tests,
   liveness / preflight / Fleet classification, worker-route-guard,
   stage-dispatch-fallback, nested-dispatch-eligibility, and fleet
   state/registry/route/dispatch tests.
4. **`bash hooks/portable-guards.test.sh`** — execute left this UNCONFIRMED
   (still running at its report time). You MUST run it to completion and record
   the real result; treat a failure here as a blocker.
5. `bash tools/check-adaptation-boundary.sh` — record result (a pre-existing
   unrelated WARN about concrete model refs is acceptable if it predates this
   branch; verify it is not newly introduced by these commits).
6. **SD-69 self-hosted proof**: you are a Codex worker launched via the newly
   committed worktree dispatch tooling. Independently exercise the disposable
   linked-worktree Codex mutation fixture and confirm: (a) source edits persist,
   (b) the primary `$AGENT_HOME/.spec-grounding` marker is writable/persists via
   the projected narrow writable root, and (c) commit remains honestly
   UNAVAILABLE (protected `.git`/gitdir) — the stage is correctly `no-commit`.
   If any part cannot be self-hosted in your sandbox, say so explicitly and do
   NOT claim Codex acceptance for it.
7. **SD-70**: verify `capability-route.py complete --jobs --attempt-id` writes
   the marker atomically then closes ONLY the exact row `note=completed-marker`;
   idempotent duplicate → already-closed; mismatch/missing attempt → structured
   nonzero with marker preserved; unwritable/missing jobs handled; never
   breadth-closes. Confirm the shipped focused test covers prior BLOCKED +
   current PASS + later live retry.
8. **SD-64/71**: verify reconcile closes an orphaned conductor row
   (`note=dead-parent-orphaned`) only under the exact three-condition classifier
   and produces ZERO false positives for live conductors + completed routes; and
   that liveness / Codex preflight status / Fleet current-attempt view surface
   the classification without auto-resume/relaunch or closing a live child.
9. **SD-71**: verify only probe-proven async tool names appear in
   `--disallowedTools`, `Bash`/`dispatch-wait.sh` are never denied, and the Stop
   gate is registered ONLY if the probe proved fire+block+stdout (else held
   fallback retained). Check the captured probe evidence under `_internal/`.

## Rules
- Delete any test-created `__pycache__` you generate; do NOT commit anything
  (you are read-only verification; execute owns commits).
- Do NOT edit `spec/**`, `utilities/dispatch-route.sh`, or its tests.
- Write scope: `test_logs/**`, `_internal/test_reviews/**` only.

## Output
- Write `test_logs/test-r2.md`: each floor item with command + real result
  (PASS/FAIL + evidence), the SD-69 self-hosting outcome (genuine Codex proof or
  explicit limitation), and any blocker.
- Return a concise verdict: PASS only if the verification floor is green and no
  blocker remains; otherwise FAIL/BLOCKED naming the exact failing item.
