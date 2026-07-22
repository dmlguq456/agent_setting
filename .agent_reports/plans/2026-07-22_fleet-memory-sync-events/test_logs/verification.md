# Verification report — fleet-memory-sync-events

## Target and trigger

- Route: `rt-d7392fcfbc9ce241`, node `test`, contract `code-test`, QA `standard`.
- Trigger: independent verification after the implementation-review PASS.
- Worktree: `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`.
- Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`.
- Plan/checklist: `plans/2026-07-22_fleet-memory-sync-events/{plan.md,checklist.md}`.
- Changed-file target resolved from the plan/checklist and live diff: `tools/memory/mem.py`, `tools/memory/mem_cluster_j.test.sh`.
- Governing evidence read: D-37 v22, Fleet F-19/F-35f v15, `dev_logs/execute-fix2.md`, `_internal/dev_reviews/phase_review_r2.md`, and `_internal/distill-baseline-disposition.md`.

## Runtime guards and assurance

- `preflight.sh mode-info qa/test`: `tool-contract`, `verification-runner`, adapter-owned runtime surface.
- `preflight.sh qa-policy standard code`: standard assurance, `selected-independent-pass:final-verify`; inline review was not claimed.
- `preflight.sh verification-runner --check -- true`: `status=ok`.
- Worker route recheck: `status=ok`, immutable route/node/scope matched.
- Every executable verification command below ran through `preflight.sh verification-runner`.
- No source, test, spec, adapter, commit, or push mutation was made by this stage. Only this canonical report was written.

## Graduated verification

### Level 1 — Syntax: PASS

Command:

```text
preflight.sh verification-runner --timeout 60 -- bash -lc 'bash -n tools/memory/mem_cluster_j.test.sh; python3 - <<... ast.parse(tools/memory/mem.py) ...'
```

Evidence: shell syntax passed; AST parse passed for `tools/memory/mem.py`.

### Level 2 — Import/entry load: PASS

Command:

```text
preflight.sh verification-runner --timeout 60 -- bash -lc 'PYTHONPATH=tools python3 -c ... import memory.mem ...; python3 tools/memory/mem.py --help'
```

Evidence: public import `memory.mem` succeeded, `write_record` is callable, and the CLI help entry loaded successfully.

### Level 3 — Smoke: PASS

Command: isolated temporary `MEM_STORE`, `MEM_PROJECTS`, `MEM_PROFILE`, and journal; hostile `MEM_CWD=/wrong/repo`, `MEM_DISTILL=1`, `MEM_ACTOR=curator`; one auto-memory source; `python3 tools/memory/mem.py migrate --apply`.

Evidence: `smoke absorption assertions: 3`; exactly one event, `action=add`, literal `actor=sync`, and decoded existing logical cwd. Temporary fixtures were removed.

### Level 4 — Functional: PASS for the approved surface; baseline warning recorded

Primary focused regression:

```text
preflight.sh verification-runner --timeout 180 -- bash tools/memory/mem_cluster_j.test.sh
```

Result: `exit_code=0`, `RESULT: PASS=44 FAIL=0`.

Observed required behavior and counts:

- Hostile environment: one auto-memory INSERT event with literal `action=add`, `actor=sync`, and source logical cwd; ambient `MEM_CWD`, `MEM_DISTILL`, `MEM_ACTOR`, and process cwd did not leak.
- Manual add: `MEM_CWD` and process-cwd fallback remained intact; source upsert and body-dedup continued to journal.
- Repeat migrate: DB id/source/strength snapshot and journal line count unchanged.
- Fenced sync: fresh empty non-Git store; `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`; before/after real memory/profile/journal/dump/worktree snapshot digests equal (`1d4ebff8...235eac`); isolated DB/FTS/dump consistent.
- Post-it: one INSERT event for duplicate-normalized sources, zero on dedup; real producer row grouped in Fleet under `by_repo["agent-note"]` with `action=add`, `actor=sync`.
- Existing source plus sentinel: row/source preserved and no historical backfill (`2` assertions).
- Global/decode-impossible/invalid legacy cwd: `cwd` omitted; valid legacy cwd preserved (`10` assertions).
- `mem log --json --actor sync`: exactly the absorption ID set, only `action=add`/`actor=sync`, manual event excluded (`4` assertions).

Focused Fleet test:

```text
preflight.sh verification-runner --timeout 60 -- bash -lc 'cd tools; PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory -v'
```

Result: `Ran 26 tests ... OK`, `exit_code=0`.

Relevant canonical memory suites, each run via the verification runner:

| Command | Result |
|---|---|
| `bash tools/memory/empty-store-guard.test.sh` | exit 0, PASS |
| `bash tools/memory/inject.test.sh` | exit 0, `PASS=21 FAIL=0` |
| `bash tools/memory/mem_cluster_e.test.sh` | exit 0, `PASS=31 FAIL=0` |
| `bash tools/memory/mem_cluster_e_gamma.test.sh` | exit 0, `PASS=40 FAIL=0` |
| `bash tools/memory/mem_repairs_v15.test.sh` | exit 0, `PASS=38 FAIL=0` |
| `bash tools/memory/mem_retrieval_v14.test.sh` | exit 0, `PASS=22 FAIL=0` |
| `bash tools/memory/pending_drain.test.sh` | exit 0, `PASS=23 FAIL=0` |
| `bash tools/memory/retrieval-eval.test.sh` | exit 0, `PASS=9 FAIL=0` |

Required plan suite warning:

```text
preflight.sh verification-runner --timeout 60 -- bash tools/memory/distill.test.sh
```

Result: `exit_code=1`, `RESULT: PASS=35 FAIL=2`. This is the first failing signal in the functional command set. The suite, its exercised hook files, and all other distill-adjacent files have zero diff; HEAD matches the sealed baseline. `_internal/distill-baseline-disposition.md` records the depth-1 owner’s explicit acceptance as a pre-existing, out-of-scope exception and requires this warning to remain visible. Per the parent assignment’s explicit request for independent later checks, the remaining suites and integration checks were still run. No edit or waiver was made by this worker.

### Level 5 — Integration: PASS

```text
preflight.sh verification-runner --timeout 180 -- bash -lc 'PYTHONPATH=. python3 -m unittest discover -s tools/fleet/tests -p "test_*.py" -v'
```

Result: `Ran 744 tests in 19.376s`, `OK`, exit 0.

Additional integration/projection checks passed:

- `python3 tools/build-manifest.py --check`: manifest up to date.
- Claude memory symlink target matched `../../../../tools/memory/mem.py`.
- Codex and OpenCode memory launcher `--help` loads succeeded.
- `./tools/check-adaptation-boundary.sh`: passed; warning of 126 documented concrete Claude/model references remains pre-existing.
- `git diff --quiet -- tools/fleet/collectors/memory.py`: collector unchanged.
- Exact approved-path status audit: only `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh` changed.
- `git diff --check`: passed.
- `python3 tools/generate.py --check`: explicitly skipped because projection ownership was not touched; adaptation boundary and launcher checks were run anyway.

### Level 5b — Behavioral runtime observation: PASS

The caller-facing CLI path was exercised, not inferred from import/tests: isolated `mem.py migrate --apply` was launched under hostile ambient attribution and its JSONL journal response was parsed. The full Cluster J runtime acceptance also exercised migrate, repeat migrate, fenced sync, post-it registration, Fleet `collect()`, and `mem log --json --actor sync` against real temporary fixtures.

## Summary

- Graduated levels observed correct: Levels 1, 2, 3, 4 (approved surface), 5, and 5b.
- In-scope test counts: Cluster J `44/44`; focused Fleet `26/26`; eight additional memory suites `21/21`, `31/31`, `40/40`, `38/38`, `22/22`, `23/23`, `9/9`, plus empty-store PASS; full Fleet `744/744`.
- First failing signal: `tools/memory/distill.test.sh`, `PASS=35 FAIL=2`; owner-accepted zero-diff baseline exception, unrelated to the assigned files.
- Residual risks: the accepted distill baseline remains unresolved outside this route; adaptation-boundary warning remains pre-existing. No in-scope failure observed.
- Verdict: `✅ All assigned in-scope verification levels passed; owner-accepted baseline warning carried forward.`
