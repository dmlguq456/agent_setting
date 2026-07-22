## 📋 Code Review Results

**Verdict:** `PASS` — ✅ No blocking issues (0 major); 1 non-blocking suggestion

**Reviewed files:** `tools/memory/mem.py`, `tools/memory/mem_cluster_j.test.sh`; approved `plan.md`/`checklist.md`; prior `_internal/dev_reviews/phase_review.md` (4 must-fix, FAIL); retry evidence `dev_logs/execute-fix1.md`, `dev_logs/execute-fix2.md`; `_internal/distill-baseline-disposition.md`; canonical D-37 v22 and Fleet F-19/F-35f v15.

**Change summary:** Unchanged from the prior review's characterization — additive journal options (`journal_insert_only`, `journal_actor`, `journal_cwd`), a cwd-unset sentinel, and create-only literal-`sync` events for the four `migrate()` source families. This rerun independently re-verifies that all four prior must-fix findings are now closed by the diff/test evidence, not merely re-asserted in the retry logs.

### Independent verification of the four prior must-fix findings

1. **Sync isolation (prior finding 1) — CLOSED.** `runtime_snapshot()` (`mem_cluster_j.test.sh:55-75`) hashes the *real* `$HOME/agent_setting/memory`, `$HOME/agent_setting/user_profile`, the real XDG write-events journal, `memory/dump.jsonl`, and `git -C "$ROOT" status/diff --cached`, not the isolated fixture store. The fenced sync block (`:562-621`) allocates a fresh `mktemp -d` store, proves it empty and non-Git before use, runs the sole acceptance `sync` with `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0` plus isolated `MEM_STORE`/`MEM_PROJECTS`/`MEM_PROFILE`/`MEM_WRITE_EVENTS`, snapshots real state before/after with `cmp -s`, and separately asserts FTS/index/dump-id consistency inside the isolated store. I reran this suite fresh (`bash tools/memory/mem_cluster_j.test.sh`) and confirmed `PASS=44 FAIL=0`, and confirmed the primary worktree shows no unexpected mutation after repeated runs.
2. **Checked migrate/sync exit status (prior finding 2) — CLOSED.** `run_checked()` (`:15-23`) is defined once and used at all 8 call sites (`grep -n run_checked`): all 6 `migrate --apply`/`sync` invocations plus the manual-add and `mem log` invocations that participate in the acceptance assertions. A nonzero exit now flips `bad()` before any output is inspected.
3. **Public `mem log --json --actor sync` filter (prior finding 3) — CLOSED.** `mem_cluster_j.test.sh:503-521` runs `python3 "$MEM" log --json --actor sync` against a mixed manual/sync journal and asserts `count == len(expected)`, the returned ID set equals exactly the absorption ID, every event is `action=add`/`actor=sync`, and the manual event's ID is absent — exercising the real CLI filter path (`mem.py:2994-3018`, `3750`), not just raw JSONL parsing.
4. **`distill.test.sh` verification-gate disposition (prior finding 4) — CLOSED, with one non-blocking accuracy note (see 🟡 below).** `git diff --stat -- tools/memory/distill.test.sh hooks/mem-distill-dispatch.sh hooks/mem-turn-nudge.test.sh` is empty on this worktree, `git diff --quiet -- tools/fleet/collectors/memory.py` confirms the collector is byte-unchanged, and current `HEAD` (`e8938809d87e54474f5e7242a2552598c2636a0a`) matches the sealed baseline commit cited in `_internal/distill-baseline-disposition.md` — so the failure is tautologically identical to the pre-diff baseline regardless of its exact cause. `checklist.md:81,92` are honestly left unchecked (not self-certified), matching the plan's instruction. The depth-1 owner's signed disposition in `_internal/distill-baseline-disposition.md` explicitly accepts this as an out-of-scope baseline exception without waiving in-scope regressions, which is the correct scope for this route.

### Additional independent checks this pass

- `bash -n tools/memory/mem_cluster_j.test.sh` and AST parse of `mem.py`: pass.
- Fresh `bash tools/memory/mem_cluster_j.test.sh`: exit 0, `PASS=44 FAIL=0`.
- Fresh `(cd tools && PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory)`: 26/26.
- Fresh `PYTHONPATH=. python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`: 744/744, OK.
- No-backfill row/source preservation assertion (`:722-734`) independently confirmed present and correct — closes the prior 🟡 suggested improvement as well.
- Full `mem.py` diff re-read line-by-line: `_event_cwd()` (`:410-428`) correctly special-cases encoded (`-`-prefixed) vs. absolute vs. relative/invalid input and requires the resolved path to exist; `write_record()`'s `journal_insert_only` (`:1071-1076`, `:1098-1103`) correctly suppresses only the upsert/dedup-reinforce journal calls while leaving the plain-INSERT call (`:1139-1142`) unconditional; all four migration families pass literal `journal_actor="sync"` and the correct per-family `journal_cwd` (decoded auto-memory dir, resolved post-it/legacy root, or explicit `None` for global/undecodable/invalid/no-frontmatter sources) — cross-checked against the omission/valid-legacy acceptance block (`mem_cluster_j.test.sh:737-786`), which exercises exactly these five source shapes and asserts `cwd` is fully absent (not `null`) where expected.
- `existing_src` skip logic at all four migration loops (`mem.py:2124,2140,2193,2216,2240`) is untouched by the diff.

### 🟡 Suggested improvement (non-blocking)

- The specific failure narrative recorded for `distill.test.sh` in `execute-fix1.md`/`execute-fix2.md`/`_internal/distill-baseline-disposition.md` ("stale nested-suite count, 11 vs. a fully-passing 18" and "a sentinel-PRESENT race between case A-pos and case B") does not reproduce verbatim when `distill.test.sh` is run in the same ambient dispatched-worker environment this review executes under (`AGENT_DISPATCH_CHILD=1`, `CLAUDE_CODE_CHILD_SESSION=1`, `MEM_DISTILL_ENABLE=1`, etc. — the same shape of environment `code-execute` itself runs in). In that ambient environment I reproduced (3/3 deterministic) `PASS=13 FAIL=5` for the nested `hooks/mem-turn-nudge.test.sh` run and a different named failure, `A-pos: lock dir 미생성`, instead of the documented pair. Re-running with the exact env-unset prefix the retry logs used for the *isolated* nested-suite check (`env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_DEPTH -u CLAUDE_CODE_CHILD_SESSION -u OPENCODE_DISPATCH_SLUG -u FLEET_TITLE_REFRESH -u MEM_DISTILL -u MEM_DISTILL_ENABLE`) applied to the *whole* `distill.test.sh` invocation reproduces exactly their documented signature (nested suite `18/0`, stale-count-only outer failure). This does not change the disposition's bottom line — the failing files are still byte-identical to the sealed baseline, so the failure (whatever its exact shape under a given ambient environment) cannot be caused by this diff, and it remains correctly out of the approved edit scope. But the docs' specific "reproduced 3/3 identical" claim should be understood as "identical under a from-a-clean-shell invocation," not universally across dispatched-worker ambient environments; a future owner-approved fix to `distill.test.sh`'s ambient-env leakage (it invokes `hooks/mem-turn-nudge.test.sh` at `distill.test.sh:95` without the same env-unset hygiene its own isolated verification commands use) would make the suite's outer result stable regardless of caller context.

### 🟢 What is already solid

- All four prior must-fix findings are closed by genuine test/implementation changes, independently re-verified against the current diff rather than by re-reading the retry logs' claims at face value.
- `checklist.md` bookkeeping is honest: items that don't apply (no collector change) or remain genuinely open (`distill.test.sh` gate) are left unchecked rather than inferred complete from the focused-suite green result.
- Zero unrelated files touched; `git status --porcelain` in this worktree shows exactly the two approved files.

### Review checks and runtime notes

- Route safety recheck: consumed the already-validated immutable route record; no reselection performed.
- `bash -n tools/memory/mem_cluster_j.test.sh`: exit 0.
- AST parse `mem.py`: pass.
- `bash tools/memory/mem_cluster_j.test.sh` (fresh, this pass): exit 0, `PASS=44 FAIL=0`.
- `bash tools/memory/distill.test.sh` (fresh, this pass, raw invocation): exit non-zero, `PASS=35 FAIL=2` — matches the documented aggregate count; see 🟡 above for the sub-case-identity caveat.
- `git diff --stat -- tools/memory/distill.test.sh hooks/mem-distill-dispatch.sh hooks/mem-turn-nudge.test.sh`: empty.
- `git diff --quiet -- tools/fleet/collectors/memory.py`: exit 0 (unchanged).
- `git rev-parse HEAD`: `e8938809d87e54474f5e7242a2552598c2636a0a`, matches the sealed baseline cited in the owner disposition.
- `(cd tools && PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory)`: 26/26.
- `PYTHONPATH=. python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`: 744/744, OK.
- `git status --porcelain=v1` in this worktree: only `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh` modified.
