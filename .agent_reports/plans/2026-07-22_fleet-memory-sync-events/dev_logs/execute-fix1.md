# Execute retry evidence — fleet-memory-sync-events

- Route: `rt-d7392fcfbc9ce241`, node `execute`, retry attempt `att-493cd2f9875248cd355c263b06e19f05a6ba0fc16ba7eff8` (second in-place retry; supersedes the prior retry attempt `att-848c4b2b2b7f717f7c6b9610ca39129654762d9137c48b4e` recorded in this same file)
- Capability/contract: `autopilot-code` / `code-execute`
- Unit: `dev/backend`, stage worker, dispatch depth 2, standard QA/intensity
- Worktree: `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`
- Artifact: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events`
- QA assurance: `preflight.sh qa-policy standard code` → `plan-check:selected-independent-pass:final-verify`

## Scope and changes this attempt

No source or test edit was made in this attempt. The worktree entering this retry already carried the prior retry's fix for all four `_internal/dev_reviews/phase_review.md` must-fix findings (sync isolation snapshots, checked `migrate`/`sync` exit status via `run_checked`, the public `mem log --json --actor sync` filter assertion, and the strengthened no-backfill row/source assertion), plus the suggested no-backfill improvement. `tools/fleet/collectors/memory.py` remains byte-unchanged. Each of the four findings was independently re-verified against the current diff (not merely re-asserted):

1. **Sync isolation (must-fix 1):** `tools/memory/mem_cluster_j.test.sh:560-616` allocates a fresh `mktemp -d` `SYNC_STORE`, asserts it is empty at allocation and non-Git via `git -C "$SYNC_STORE" rev-parse --is-inside-work-tree`, runs the sole acceptance `sync` with explicit `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0` plus isolated `MEM_STORE`/`MEM_PROJECTS`/`MEM_PROFILE`/`MEM_WRITE_EVENTS`, and `cmp`s a `runtime_snapshot` of the real memory store, profile, journal, dump, and worktree status/diff before and after. Verified live: matching digest `1d4ebff8b3273983a766b834230e48fe326b0b2a54640f0975ff570836235eac` before/after in this run's focused suite output.
2. **Checked exit status (must-fix 2):** `run_checked()` (`mem_cluster_j.test.sh:15-22`) wraps every new `migrate --apply`/`sync` call site (verified all 8 call sites via `grep -n run_checked`); legacy intentional nonzero probes elsewhere in the suite are untouched.
3. **Public actor-filter assertion (must-fix 3):** `mem_cluster_j.test.sh:500-521` runs `mem log --json --actor sync` against a mixed manual/sync journal and asserts `count == len(expected)`, the returned ID set equals exactly the absorption ID, every row is `action=add`/`actor=sync`, and the manual row's ID is absent.
4. **No-backfill preservation (must-fix 4 / suggested improvement):** `mem_cluster_j.test.sh:696-737` asserts the pre-seeded row's `(source, body)` survive a checked `migrate --apply` unchanged, in addition to the unchanged sentinel journal line.

Also independently re-verified (not previously checked off in `checklist.md`):

- `existing_src` skip logic is intact and untouched by the diff at all four migration source loops (`tools/memory/mem.py:2140,2193,2216,2240`).
- `_append_write_event()` preserves `MEM_SID`, snippet truncation/sanitation, timestamp, JSON shape, the 256KB/500-line rotation block, and the `except OSError: pass` fail-open wrapper (`tools/memory/mem.py:1289-1319`) — only the `cwd` key gained a conditional sentinel branch.

## Verification (this attempt, fresh run)

Focused suite:

```text
adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- bash tools/memory/mem_cluster_j.test.sh
exit=0; RESULT: PASS=44 FAIL=0
```

All ten canonical memory suites, run from the repository root:

| Command | Result |
|---|---|
| `bash tools/memory/distill.test.sh` | exit 1; `PASS=35 FAIL=2` — see disposition below |
| `bash tools/memory/empty-store-guard.test.sh` | exit 0 |
| `bash tools/memory/inject.test.sh` | exit 0; 21/21 |
| `bash tools/memory/mem_cluster_e.test.sh` | exit 0; 31/31 |
| `bash tools/memory/mem_cluster_e_gamma.test.sh` | exit 0; 40/40 |
| `bash tools/memory/mem_cluster_j.test.sh` | exit 0; 44/44 |
| `bash tools/memory/mem_repairs_v15.test.sh` | exit 0; 38/38 |
| `bash tools/memory/mem_retrieval_v14.test.sh` | exit 0; 22/22 |
| `bash tools/memory/pending_drain.test.sh` | exit 0; 23/23 |
| `bash tools/memory/retrieval-eval.test.sh` | exit 0; 9/9 |

Full Fleet discovery with the correct repository import root:

```text
PYTHONPATH=. python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v
exit=0; Ran 744 tests; OK
```

Other passing checks:

- `python3 tools/memory/mem.py --help`: exit 0.
- `test "$(readlink adapters/claude/tools/memory/mem.py)" = "../../../../tools/memory/mem.py"`: exit 0.
- `AGENT_HOME="$PWD" adapters/codex/tools/memory/mem.py --help` / `AGENT_HOME="$PWD" adapters/opencode/tools/memory/mem.py --help`: exit 0.
- `./tools/check-adaptation-boundary.sh`: exit 0; documented warning about 126 concrete Claude/model references in portable areas.
- `python3 tools/build-manifest.py --check`: exit 0, manifest up-to-date.
- Executable approved-path `git status --porcelain=v1 -z` parser: exit 0; only `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh` changed.
- `git diff --check`: exit 0.
- `git diff --quiet -- tools/fleet/collectors/memory.py`: exit 0; collector unchanged.

## `distill.test.sh` disposition (finding 4, second confirmation)

`bash tools/memory/distill.test.sh` exits 1 with `PASS=35 FAIL=2`. Both failures were re-confirmed this attempt as pre-existing and unrelated to the diff, with stronger evidence than the prior retry:

- `git diff --stat -- tools/memory/distill.test.sh hooks/mem-distill-dispatch.sh hooks/mem-turn-nudge.test.sh` returns **empty** — none of the three files this failure touches have any diff on this branch. Any failure inside them is therefore identical to the sealed baseline `e8938809d87e54474f5e7242a2552598c2636a0a`; the approved edit scope (`tools/memory/mem.py`, `tools/memory/mem_cluster_j.test.sh`) cannot repair it without exceeding the route's approved path set.
- Failure 1 — `distill.test.sh:97` hardcodes `grep -q "RESULT: PASS=11 FAIL=0"` against the nested `hooks/mem-turn-nudge.test.sh` run. The nested suite itself passes cleanly and deterministically — reproduced 3/3 runs at `RESULT: PASS=18 FAIL=0` under the plan's required isolated environment:

  ```text
  env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_DEPTH \
    -u CLAUDE_CODE_CHILD_SESSION -u OPENCODE_DISPATCH_SLUG -u FLEET_TITLE_REFRESH \
    -u MEM_DISTILL AGENT_HOME="$PWD" MEM_PY="$PWD/tools/memory/mem.py" \
    XDG_STATE_HOME="$(mktemp -d)" bash hooks/mem-turn-nudge.test.sh
  RESULT: PASS=18 FAIL=0   (3/3 identical runs)
  ```

  The suite's own expected count (11) is stale against the nested suite's current, larger, fully-passing case count (18); this is a pre-existing stale assertion in an unmodified file, not a regression.
- Failure 2 — `distill.test.sh:175` (`B: sentinel PRESENT — opt-in 게이트 실패`) is a deterministic cross-test race in the unmodified case block: case A-pos (`distill.test.sh:126-147`) spawns a detached `setsid claude &` child against a shared `$TMPSTUB/bin/claude` stub; case B (`distill.test.sh:168-175`) reuses the same stub directory, `rm -f`s the sentinel, and immediately re-checks it. Reproduced 3/3 identical runs under the same isolated env with zero diff on the file.
- Full isolated outer run, reproduced 3/3 identical: `RESULT: PASS=35 FAIL=2` (both failures listed above; no other failures).

Per the plan's required disposition (`plan.md` Phase 4.1 / `phase_review.md` finding 4), this is recorded as an explicit pre-existing-failure disposition rather than a self-certified pass: the ten-suite gate ran in full (no suite excluded — nine pass, one fails for reasons proven independent of this diff), but `checklist.md`'s `bash tools/memory/distill.test.sh` and gate-completion lines are left unchecked rather than marked complete, consistent with "do not mark the full verification gate complete while these remain warnings only." Repairing either failure requires editing `tools/memory/distill.test.sh` and/or `hooks/mem-turn-nudge.test.sh`/`hooks/mem-distill-dispatch.sh`, all outside this route's approved implementation surface — an owner-approved scope change or a separately scoped maintenance fix is required to close it, not further retry of this node.

## Verdict

`FAIL` — the create-only literal-`sync` producer implementation and all four review must-fix findings are confirmed fixed and independently re-verified; every suite in the approved scope (Cluster J 44/44, the other eight canonical suites, and full Fleet discovery 744/744) passes cleanly. The retry execute completion marker is intentionally left uncompleted because the ten-suite canonical gate still has one open, pre-existing, out-of-approved-scope failure (`tools/memory/distill.test.sh`) without an owner-approved disposition, per the plan's explicit instruction not to self-certify that gate complete.
