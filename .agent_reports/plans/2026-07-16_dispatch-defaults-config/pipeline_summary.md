# pipeline_summary — 2026-07-16_dispatch-defaults-config

- capability/mode/intensity: `autopilot-code` / dev/feature / standard (staged, depth-1 owner)
- route: `rt-20f4481665281810`, hash `sha256:20f4481665281810...f87dde`, contract v3
- worktree: `/home/Uihyeop/agent_setting-wt/dispatch-defaults-config`, branch `dispatch-defaults-config`
- baseline: `3ebd1c77` → current HEAD **`81a5cd88`** (3 commits, core-first order + round-2 fix-forward)
- spec-significance: within-spec (`spec/stage-dispatch/prd.md` v16 §13.8 SD-66)

## Verdict: PASS — after round-2 depth-0 fix-forward (round-1 FAIL history preserved below)

The SD-66 work is implemented, committed, and independently re-verified after a
round-2 depth-0 fix-forward (commit `81a5cd88`) resolved the round-1 material
findings. See `final_report.md` for the full cycle account; round-1's FAIL is
kept intact in this file rather than erased.

## Stage results

| stage | harness | verdict | terminal artifact |
|---|---|---|---|
| plan | codex | PASS | `plan.md`, `checklist.md` |
| execute | claude | PASS | `dev_logs/implementation.md` (commits `efeab72e`, `7697c3b6`) |
| test (round 1) | codex (diverse checker) | **FAIL** | `test_logs/verification.md` |
| execute retry | claude | **BLOCKED at launch** | `_internal/retry_memo_round1.md` |
| fix-forward (depth-0, round 2) | claude | PASS | commit `81a5cd88` |
| test (round 2) | claude (re-verify) | PASS | `test_logs/verification_round2.md` |
| report | claude | PASS | `final_report.md` |

Registry/marker state: `plan`, `execute`, `test` (round 2), and `report` all have
completion markers and closed rows. The round-1 `test` row's deliberate `open` state
(no marker, to prevent `report` from satisfying `completion_marker_gate` on a false
gate) was resolved by the round-2 re-verification PASS; this report stage closes the
cycle.

## What is verified good (independent codex review, commands + raw output in `test_logs/verification.md`)

- Decision cascade unchanged and correct: explicit `--adapter` > `--family` > config affinity
  > bias, with hard eligibility vetoing afterwards; omitted cells still behave as `neutral`
  (PASS, each level exercised).
- `profiles/dispatch-defaults.yaml` matches the SD-66 contract: harness-only vocabulary,
  `depth1_owner: [claude, codex]` as a set, `autopilot-code` populated with
  `execute: codex / test: diverse / report: claude` and `plan` omitted, other capabilities
  comment-only scaffold (not empty keys), `opencode: relief-only` with the 1–2% comment,
  zero concrete model/effort tokens (PASS).
- `utilities/dispatch-defaults.py` fails loud on all six negative fixtures — unknown capability,
  unknown stage, out-of-vocabulary value, model-like value, malformed `depth1_owner`,
  bad opencode policy (PASS).
- No `yq`/PyYAML dependency; selector stays POSIX (`sh -n` + `dash -n` clean); loader imports
  stdlib only (PASS).
- g9 repair (item B): owner row relaxed to a well-formed-SID check, **both depth-2 children still
  assert exact `drill-parent-session`**, prompt.md carries the clarifying line, claude mirror
  byte-identical (PASS, static only — drills correctly not run).
- `core/OPERATIONS.md` §5.10 (item C): SD-16 consumption rule present with soft-default semantics;
  SD-48 sentence present verbatim and correctly scoped to manual wrapper starts (PASS).
- Item D: the stderr-acceptance regression test exists and passes (4 tests OK); `auth_check` was
  correctly **not** reimplemented.

## Open defects — must be fixed before merge

Full triage with the chosen fix in `_internal/retry_memo_round1.md`.

1. **F1 — adapter projection regression (material, caused by this cycle).**
   `tools/check-adaptation-boundary.sh:1278` requires every top-level `utilities/*` file to be
   classified projected or deferred; new `utilities/dispatch-defaults.py` is neither, so the guard
   fails loud. Because the projected `utilities/dispatch-route.sh` resolves the helper relative to
   the invocation path, **all three adapter-projected selectors are broken** (`exit=64`,
   `can't open file .../adapters/<h>/utilities/dispatch-defaults.py`).
   Fix: symlink `dispatch-defaults.py` into `adapters/{claude,codex,opencode}/utilities/` as
   `../../../utilities/dispatch-defaults.py`, add it to `UTILITY_PROJECTED`, and add it to the
   per-adapter `find … ! \( -name … \)` allowlists.
2. **F2 — fixture isolation incomplete.** `utilities/dispatch-route.test.sh` runs its first
   `route()` block *before* `export DISPATCH_DEFAULTS_CONFIG`, so that block still consumes the
   shipped default. Move fixture creation + export above every `route()` call.
3. **F4 — minor, docs only.** `python3 -m unittest utilities/nested_dispatch_eligibility.test.py`
   raises `ModuleNotFoundError`; direct execution (`python3 -B utilities/…test.py`) passes.

Explicitly **not** defects of this cycle (fail on baseline too, verifier concurred):
`adapters/{codex,opencode}/tools/memory/mem.py` `CLAUDE_HOME` references; the
`hooks/portable-guards.test.sh` "invalid AGENT_HOME" assertion.

## Blocker — why the retry did not run

Two independent reasons, both requiring authority this worker does not have:

1. **The route guard forbids retrying `execute` in place, by design.**
   `utilities/worker-route-guard.py:114` demands `HEAD == route.source_commit` unless the node is
   `_post_mutation_node`. `execute` depends only on `plan` (non-mutating), so it is the mutating
   node itself and is pinned to baseline `3ebd1c77`; our own commits moved HEAD to `7697c3b6`, so
   the retry died at launch with
   `route-source-commit-mismatch expected=3ebd1c77… observed=7697c3b6…`.
   (`test` ran fine at the same HEAD precisely because it *is* post-mutation — not an adapter gap.)
   The sanctioned escape is dev-pipeline Step 4's "safety-commit restore": reset the branch to
   `3ebd1c77` and let the retry re-apply the work plus the fixes.
2. **That restore was denied by the permission classifier** as irreversible local destruction
   (`git reset --hard 3ebd1c77` discards committed cycle work). The denial is reasonable and was
   **not** worked around. Re-compiling the route with `source_commit=7697c3b6` was rejected as an
   alternative: the kernel binds this worker to an immutable route, and re-compiling would be
   re-selecting it.

Nothing is lost: all round-1 work is committed on `dispatch-defaults-config` at `7697c3b6`.

## Recommendation for depth-0

The remaining fixes are small and fully specified (F1/F2/F4 above). Cheapest correct path is to
**fix forward** — F1/F2 are additive and need no baseline restore — then re-run the codex
verification and close the open `test` row. A full `execute` retry would need a user-authorized
`git reset --hard 3ebd1c77` (round-1 commits are reproducible: they cherry-pick cleanly onto the
baseline), and buys nothing the fix-forward does not.

## Contract findings worth escalating (details + raw evidence in `metrics.md`)

1. `dispatch-node.py` does **not** forward `route.dispatch_evidence`; every `--start` in this
   cycle required manual evidence flags. The assignment's premise that the v15 record path covers
   this is false at HEAD — which is exactly the SD-48 trap item (C) documents. The committed SD-48
   prose already states this HEAD truth correctly.
2. A staged pipeline whose mutating node commits cannot retry that node without a destructive
   restore. Worth a spec decision: either treat the safety commit as the retry baseline, or let a
   retry re-pin `source_commit` to a first-parent descendant.
3. The `nested-headless` probe returns `unsupported (auth-unavailable)` when run from inside a
   codex sandbox, while conductor-level probes return `supported`. Verifiers running probes from a
   sandboxed child will keep mis-reporting this.
