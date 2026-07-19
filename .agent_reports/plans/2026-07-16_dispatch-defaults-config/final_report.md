# Final Report — dispatch-defaults-config (SD-66)

- capability/mode/intensity: `autopilot-code` / dev/feature / standard
- route: `rt-20f4481665281810`, contract v3, attempt `att-c74e50560edf49bb9d5c8dfc65f31db3`
- worktree: `/home/Uihyeop/agent_setting-wt/dispatch-defaults-config`
- baseline `3ebd1c77` → final HEAD **`81a5cd88`** (3 commits: `efeab72e`, `7697c3b6`, `81a5cd88`)
- spec-significance: within-spec (`spec/stage-dispatch/prd.md` v16 §13.8 SD-66)

## Overall verdict: **PASS — after round-2 fix-forward**

Round-1 verification (`code-test`) FAILed on three findings. A depth-0
fix-forward pass (commit `81a5cd88`) fixed the two material ones and noted
the third; round-2 re-verification PASSed. Round-1's FAIL history is kept
intact below rather than erased, per the pipeline-summary instruction.

## What SD-66 delivered

1. **`profiles/dispatch-defaults.yaml`** (new) — narrow, comment-scaffolded
   config: `schema_version`, `depth1_owner: [claude, codex]`,
   `opencode.relief_only: true`, and `capabilities.autopilot-code` populated
   with `execute: codex`, `test: diverse`, `report: claude` (`plan`
   intentionally omitted → neutral). Every other registered capability/stage
   coordinate exists only as a commented, parse-neutral scaffold. No
   PyYAML/yq dependency, no concrete model/effort tokens.
2. **`utilities/dispatch-defaults.py`** (new) — stdlib-only YAML-subset
   loader/validator/CLI (`validate`, `affinity`, `owners`,
   `opencode-policy`). Fails loud (exit 65 + stderr) on unknown
   capability/stage, out-of-vocabulary or model-like affinity values,
   malformed `depth1_owner`, and any `opencode.relief_only != true`.
   `DISPATCH_DEFAULTS_CONFIG` / `--config` overrides the production path for
   fixtures.
3. **`utilities/dispatch-route.sh`** wiring — new cascade step inserted
   between `--family` and the prior heuristic/bias fallback: explicit
   `--adapter` > `--family` > validated config affinity > prior
   heuristic/bias > hard-eligibility reject/fallback (unchanged). Config
   always validates first, so a malformed file fails even with an explicit
   `--adapter`. `opencode` from config is honored only when
   `--adapter`/`--family` are unset, and is never added to the automatic
   neutral/diverse candidate set.
4. **`utilities/dispatch-route.test.sh`** — converted to temporary
   `DISPATCH_DEFAULTS_CONFIG` fixtures covering configured/omitted/diverse/
   precedence/owner/relief/malformed/read-only cases, plus every original
   assertion preserved.
5. **`core/OPERATIONS.md`** §5.10 SD-16 + SD-48 — declares
   `profiles/dispatch-defaults.yaml` the user source for cascade step 3
   (soft default; explicit choice and hard eligibility always win); records
   the SD-48 no-reconfirmation sentence for manual `--start`, plus the
   HEAD-truth caveat that `dispatch-node.py --action start` does not yet
   forward `route.dispatch_evidence`.
6. **g9 drill repair** (`loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/`
   root + byte-identical `adapters/claude/` mirror) — relaxed only the
   depth-1 **owner** row's `parent_sid` check from exact
   `drill-parent-session` equality to a well-formed-SID format check
   (`[A-Za-z0-9_.:-]+`, non-empty); both depth-2 **child** rows still assert
   exact equality, unchanged. `prompt.md` documents the intentional owner
   rebinding. Drill itself was correctly never run.

## Round-1 code-test — FAIL (`test_logs/verification.md`, independent codex reviewer)

Confirmed good: decision cascade, shipped config contract, all six negative
validator fixtures, POSIX/stdlib-only compliance, g9 static repair, and the
OPERATIONS.md SD-16/SD-48 prose.

Material findings:
- **F1 (material, caused by this cycle):** `utilities/dispatch-defaults.py`
  had no adaptation-boundary projection classification, and because
  `dispatch-route.sh` is symlink-projected into all three adapters while
  resolving the new helper relative to the invocation path, **all three
  adapter-projected selectors were broken** (`exit=64`, file not found).
- **F2 (real):** `dispatch-route.test.sh`'s first `route()` block ran
  *before* `export DISPATCH_DEFAULTS_CONFIG`, so it still consumed the
  shipped default instead of the fixture — isolation was incomplete.
- **F4 (minor, docs-only):** the plan's `python3 -m unittest
  utilities/nested_dispatch_eligibility.test.py` invocation form raises
  `ModuleNotFoundError`; direct file execution is correct and already
  passes.
- Also observed, not a regression: the required live nested-headless probe
  reported `unsupported (auth-unavailable)` because it ran inside a nested
  codex sandbox that cannot see host auth — an environment artifact, not a
  code defect (conductor-level probes on the same worktree returned
  `supported` repeatedly).

Retry was triaged (`_internal/retry_memo_round1.md`) but **blocked at
launch**: `utilities/worker-route-guard.py` pins `execute` (the sole
mutating node) to `source_commit=3ebd1c77`, and HEAD had already moved to
`7697c3b6`; the sanctioned escape (reset to baseline and let the retry
re-apply) was denied by the permission classifier as irreversible local
destruction. `pipeline_summary.md` was left at verdict FAIL with the `test`
registry row deliberately open (no completion marker), so `report` could
not proceed on a false gate.

## Round-2 depth-0 fix-forward — commit `81a5cd88`, re-verified PASS

Executed inline by depth-0 (not a new retry node — `execute` has no
`refine` node in this route) because dispatch overhead exceeded the size of
the remaining fixes:

- **F1 fixed:** `dispatch-defaults.py` symlinked into all three
  `adapters/{claude,codex,opencode}/utilities/`
  (`../../../utilities/dispatch-defaults.py`, same idiom as
  `dispatch-route.sh`); added to `UTILITY_PROJECTED` and each adapter's
  `find` allowlist in `tools/check-adaptation-boundary.sh`.
  `dispatch-defaults.py::_repo_root` switched `abspath` → `realpath` so the
  projected symlink still resolves the real repo root (round-1's
  projection alone would have broken one layer deeper, on
  `adapters/<h>/profiles/dispatch-defaults.yaml`). Boundary guard re-run
  leaves only the two pre-existing, out-of-cycle `mem.py` `CLAUDE_HOME`
  FAILs (reproduce on baseline `3ebd1c77`). Adapter-projected selectors now
  clear the SD-66 validate/config step; they fail only at a **pre-existing**
  `usage-check.sh` resolution issue that reproduces verbatim on a clean
  baseline checkout — recorded as a known baseline issue, not fixed here.
- **F2 fixed:** fixture creation + `export DISPATCH_DEFAULTS_CONFIG` moved
  above every `route()` call; re-run confirms `dispatch-route: PASS`.
- **F4 noted:** direct-execution form documented as correct; no source
  change needed.
- **Probe artifact:** no action, per retry memo — sandbox-internal probes
  cannot see host auth; conductor-level probes on this worktree returned
  `supported` 3× this cycle, and every cross-harness dispatch launched on
  that evidence.

`test_logs/verification_round2.md` re-verifies F1/F2 fixed, F4 noted, and
records the shipped config as still valid. **code-test gate: PASS**
(residual FAILs are baseline-reproduced, out of scope for this cycle).

## Escalated contract findings (not blocking this cycle, carried forward)

1. **Dispatch-node evidence forwarding gap:** `dispatch-node.py --action
   start` does not forward `route.dispatch_evidence`; every `--start` this
   cycle needed manual evidence flags. The committed SD-48 prose states this
   HEAD truth correctly and marks automatic forwarding a follow-up, not a
   claim that it's already covered.
2. **execute-retry vs. source-commit pin:** a staged pipeline whose
   mutating node has already committed cannot retry that node in place
   without a destructive baseline restore (`worker-route-guard.py:114`
   pins `source_commit`). This blocked the sanctioned round-1 retry and
   forced the depth-0 fix-forward path instead. Candidate follow-up: either
   treat the safety commit as an acceptable retry baseline, or let a retry
   re-pin `source_commit` to a first-parent descendant. Worth a stage-dispatch
   PRD decision.
3. **Canonical-stage mismatch (carried from plan, not a defect):** PRD prose
   says `exec`/`review`; current topology only exposes `plan, execute, test,
   report`. `execute`/`test` are the least-lossy mapping; a distinct `review`
   coordinate needs a later spec/topology convergence.
4. Nested-headless probes run from inside a sandboxed child mis-report
   `unsupported (auth-unavailable)` regardless of actual host auth state —
   verifiers should probe at the conductor level, not from within a codex
   sandbox child.

## Scope discipline (both rounds)

No merge, push, worktree cleanup, or g9/g10 drill run at any point. No
writes to the primary checkout or to this worktree's own tracked
`.agent_reports` snapshot. `git diff --name-status 3ebd1c77..81a5cd88`
covers exactly the planned files plus the round-2 additive fixes (adapter
symlinks, boundary-guard allowlist entries, `_repo_root` realpath line,
test-fixture reorder). `git diff --check` clean at both rounds;
`git status --short` clean after each commit.
