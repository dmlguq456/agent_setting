## 📋 Code Review Results

**Verdict:** `FAIL` — 🔴 4 issues (4 major)

**Reviewed files:** `tools/memory/mem.py`, `tools/memory/mem_cluster_j.test.sh`; approved `plan.md`/`checklist.md`; `dev_logs/execute.md`; canonical D-37 v22 and Fleet F-19/F-35f v15; W1–W4 review verdict.

**Change summary:** The implementation adds additive journal options, a cwd sentinel, and create-only literal-`sync` events for the four `migrate()` source families. The focused producer/consumer behavior is correct, but the changed test/evidence does not close several explicitly approved completion gates.

### 🔴 Must-fix issues

1. **`tools/memory/mem_cluster_j.test.sh:430-453` — sync isolation is not proved.**

   **Why it matters:** Both `sync` calls reuse `AUTO_STORE` after the migrate fixture. The test checks only isolated row/journal counts and dump existence; it never proves the store was initially empty/non-Git or snapshots the real memory store, profile, effective journal/dump, or worktree status/diffs. This is like checking that a test package arrived while never checking that it was sent to the right address: the no-real-store-mutation claim in `dev_logs/execute.md:24,42-43,62` is unsupported. The approved plan requires this at `plan.md:170-173`, and `checklist.md:61,108-110` remains unchecked.

   **Suggested fix:** Add the approved fenced-sync helper. Before each invocation, allocate a fresh `mktemp -d` store, assert it is empty and outside Git, and hash/snapshot all required real paths plus staged/unstaged/status output. Run with explicit `MEM_STORE`, `MEM_PROJECTS`, `MEM_PROFILE`, `MEM_WRITE_EVENTS`, `MEM_DUMP_COMMIT=0`, and `MEM_DUMP_PUSH=0`; compare every before/after snapshot and verify FTS/index consistency and the isolated dump.

2. **`tools/memory/mem_cluster_j.test.sh:5,393-397,414-442,541-549` — migration/sync exit failures can be masked.**

   **Why it matters:** The suite uses `set -u` only and invokes the new migration/sync commands without capturing their exit status. A failed `migrate --apply` can therefore be followed by assertions against a pre-existing sentinel; the no-backfill case at `541-549` can report success even when migration never completed. The green `PASS=41 FAIL=0` result does not guarantee that each producer command ran successfully.

   **Suggested fix:** Wrap every new `migrate`/`sync` invocation in a status-checking helper and turn a nonzero exit into `bad`/test failure before inspecting outputs. For example:

   ```sh
   run_checked() { "$@"; rc=$?; [ "$rc" -eq 0 ] || bad "command failed ($rc): $*"; return "$rc"; }
   ```

   Use it in a conditional or make the test stop on a failed command, while preserving intentional nonzero probes elsewhere in the legacy suite.

3. **`tools/memory/mem_cluster_j.test.sh` lacks the required filtered-log assertion.**

   **Why it matters:** The plan explicitly requires `mem log --json --actor sync` to return exactly the absorption IDs and exclude a mixed manual event (`plan.md:185`; `checklist.md:68`). The new block parses raw JSONL and tests Fleet `by_repo`, but never exercises the public `mem log` filter. A regression in CLI filtering could ship unnoticed even though the journal and Fleet assertions pass.

   **Suggested fix:** After the mixed manual/sync fixture, run `python3 "$MEM" log --json --actor sync`, assert `count == len(events)`, every result is `action=add`/`actor=sync`, the ID set equals the expected absorption IDs, and the manual ID is absent.

4. **`dev_logs/execute.md:52-53` records required verification failures without a completed disposition.**

   **Why it matters:** `distill.test.sh` exited 1 and full Fleet discovery exited 1 (`ModuleNotFoundError: tools`). The execute log labels both pre-existing/environmental, but `checklist.md:81,91-94` and the plan's full verification gate are still open. Focused tests passing is useful evidence, not equivalent to the stated standard-QA completion gate.

   **Suggested fix:** Rerun the failed suites under their required import/dispatch environment and record passing evidence, or obtain and record an explicit owner-approved pre-existing-failure disposition that the final verifier accepts. Do not mark the full verification gate complete while these remain warnings only.

### 🟡 Suggested improvements

- `checklist.md:56-57,65,69,80,99,106-111` still contains unchecked evidence items. Update them only after the corresponding checks are actually run; do not infer completion from the focused 41/41 result.
- The no-backfill fixture should also assert the pre-seeded row/source remains present after `migrate --apply`; the unchanged sentinel alone can be a false positive if migration exits before scanning.

### 🟢 What is already solid

- `tools/memory/mem.py:1074-1104,1140-1143` correctly suppresses only source-upsert/body-dedup telemetry in insert-only mode while retaining the INSERT event.
- `tools/memory/mem.py:1289-1311` preserves the sentinel distinction: omitted cwd retains `MEM_CWD`/process fallback, explicit path wins, and explicit `None` omits the field. Existing direct callers remain additive-compatible.
- `tools/memory/mem.py:2149-2263` passes literal `journal_actor="sync"` and source-derived cwd/omission through all four migration families; no collector or schema change was introduced.
- The actual focused checks passed: syntax/import checks, `mem_cluster_j` 41/41, and Fleet F-19 26/26. The registered post-it producer row was consumed by the real collector and grouped under `by_repo["agent-note"]`.

### Review checks and runtime notes

- `preflight.sh qa-policy standard code`: `plan-check:selected-independent-pass:final-verify`.
- Route safety recheck: `status=ok`, `action=consume-route-only`, node `impl-review`.
- `bash -n tools/memory/mem_cluster_j.test.sh`: exit 0.
- AST/import checks for `mem.py` and Fleet collector: pass.
- `preflight.sh verification-runner --timeout 120 -- bash tools/memory/mem_cluster_j.test.sh`: exit 0, `PASS=41 FAIL=0`.
- `cd tools && PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory -v`: exit 0, 26/26.
- Canonical preflight read/write markers required the documented `AGENT_HOME="$PWD"` fallback because the installed `.spec-grounding` is read-only; no spec content changed.
