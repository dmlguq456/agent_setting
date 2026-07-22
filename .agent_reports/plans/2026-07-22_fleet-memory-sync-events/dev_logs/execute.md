# Execute stage evidence — fleet-memory-sync-events

- Route: `rt-d7392fcfbc9ce241`, node `execute`, attempt `att-fefffdaca3599b9c404ced667c56cb696dd7c5a02949fd4b`
- Capability/contract: `autopilot-code` / `code-execute`
- Unit: `dev/backend`, worker type `stage`, dispatch depth 2, standard QA/intensity
- Worktree: `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`
- Sealed HEAD verified before edits: `e8938809d87e54474f5e7242a2552598c2636a0a`
- QA assurance retained: `preflight.sh qa-policy standard code` → `plan-check:selected-independent-pass:final-verify`; independent plan-check PASS is `_internal/plan_reviews/round_2.md`.

## Scope and implementation

Changed only the approved worktree files:

- `tools/memory/mem.py`
  - Added `_WRITE_EVENT_CWD_UNSET` and pure `_event_cwd()` resolution for encoded/existing absolute source paths.
  - Added additive `journal_insert_only`, `journal_actor`, and `journal_cwd` parameters to `write_record()`.
  - Suppressed absorption upsert/body-dedup journal branches only when insert-only is enabled; INSERT remains journaled.
  - Added sentinel-backed per-event cwd override to `_append_write_event()`; legacy callers retain `MEM_CWD` then process-cwd fallback, while explicit `None` omits `cwd`.
  - Wired auto-memory, post-it, global profile, and legacy Markdown migration sources to `action=add`, literal `actor=sync`, insert-only mode, and source-derived cwd/omission.
- `tools/memory/mem_cluster_j.test.sh`
  - Added isolated manual ambient/upsert/dedup regression coverage.
  - Added hostile auto-memory exact-one, repeat-migrate zero, fenced repeat-sync idempotency, post-it normalized-dedup zero, no-backfill sentinel, cwd omission/valid legacy, and real Fleet `agent-note` grouping assertions.
- `tools/fleet/collectors/memory.py`: unchanged; the producer-to-consumer acceptance passed.
- No schema, spec, runtime store, journal, adapter, commit, push, merge, or cleanup mutation was performed.

## Entry and guard evidence

- `preflight.sh capability-info code-execute` → `status=instruction-only`, native Codex Skill projection available.
- `preflight.sh mode-info dev/backend` → `status=portable`, `realization=portable-persona`.
- `preflight.sh qa-policy standard code` → standard code assurance above.
- `preflight.sh worker-route ...` → `status=ok`, `action=consume-route-only`, node `execute`.
- Exact canonical spec gate passed for `/home/Uihyeop/agent_setting/.agent_reports/spec/prd.md` D-37 v22 and `.../spec/agent-fleet-dashboard/prd.md` F-19/F-35f v15.
- The initial canonical `preflight.sh read`/artifact write attempt reported the installed primary `.spec-grounding` as read-only/stale. Retried with `AGENT_HOME="$PWD"` using the writable worktree-local markers; both governing spec reads and canonical artifact writes then passed. No spec content was changed.
- Every source/test/checklist/artifact edit was preceded by `preflight.sh write ... codex-headless`; no-commit boundary was preserved.

## Verification evidence

| Command | Result |
|---|---|
| `bash -n tools/memory/mem_cluster_j.test.sh` | exit 0 |
| `python3 -m py_compile tools/memory/mem.py` | exit 0 |
| `preflight.sh verification-runner --timeout 120 -- bash tools/memory/mem_cluster_j.test.sh` | exit 0; `PASS=41 FAIL=0` |
| Focused absorption checks | exact one hostile auto event; repeat migrate 0; repeat fenced sync preserves rows/journal and exports isolated dump; post-it dedup one INSERT event; no-backfill sentinel unchanged; global/decode-impossible/invalid legacy omit cwd; valid legacy cwd preserved; Fleet `by_repo[agent-note]` pass |
| `bash tools/memory/empty-store-guard.test.sh` | exit 0 |
| `bash tools/memory/inject.test.sh` | exit 0; 21/21 |
| `bash tools/memory/mem_cluster_e.test.sh` | exit 0; 31/31 |
| `bash tools/memory/mem_cluster_e_gamma.test.sh` | exit 0; 40/40 |
| `bash tools/memory/mem_repairs_v15.test.sh` | exit 0; 38/38 |
| `bash tools/memory/mem_retrieval_v14.test.sh` | exit 0; 22/22 |
| `bash tools/memory/pending_drain.test.sh` | exit 0; 23/23 |
| `bash tools/memory/retrieval-eval.test.sh` | exit 0; 9/9 |
| `bash tools/memory/distill.test.sh` | exit 1; unrelated dispatch-lock/turn-nudge environment checks reported `PASS=13 FAIL=5` and `PASS=35 FAIL=2`; no changed-file overlap |
| `(cd tools && python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v)` | exit 1; 737 tests, one pre-existing `test_v20_dispatch_contract` import error (`ModuleNotFoundError: tools`) |
| `(cd tools && PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory -v)` | exit 0; 26/26 |
| `python3 tools/memory/mem.py --help` and Codex/OpenCode adapter help | exit 0 |
| Claude memory symlink check | exit 0 |
| `./tools/check-adaptation-boundary.sh` | exit 0; documented warning about 126 concrete Claude/model references in portable areas |
| approved-path parser and `git diff --check` | exit 0; only the two approved worktree files changed |

## Warnings and handoff

- The two broader-suite failures are environmental/pre-existing and are retained as warnings rather than excluded. Focused product and Fleet tests pass.
- The canonical stage artifact and checklist were updated under `/home/Uihyeop/agent_setting/.agent_reports`; they are not worktree source changes.
- Worktree diff remains uncommitted for the depth-1 owner. No historical journal rewrite/backfill or user runtime-store mutation was run.
