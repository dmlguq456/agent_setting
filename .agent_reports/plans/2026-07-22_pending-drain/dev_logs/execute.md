# Execute log — pending drain (2026-07-22)

worker: code-execute (dispatch_depth=2, stage)
worktree: /home/Uihyeop/agent_setting-wt/pending-drain (branch task/pending-drain)

## Changes

- `tools/memory/mem.py`
  - doctor `stale-pending` check: query now selects `id, created` `ORDER BY
    created ASC, id ASC` (oldest first). Message extended to
    `N records (oldest <date>, no auto-expiry): id(Nd),... [+K more]` while
    preserving the `[WARN] stale-pending:` prefix and the `0 records` OK
    branch (existing `mem_cluster_j.test.sh:267` grep contract intact).
  - New `drain_pending(stale_days=WORKING_TTL_DAYS, apply=False)` inserted
    directly before the `# ---------- D-39 ...` doctor section. Deletes
    `consumed` rows only (graveyard-append fail-closed → `_delete_rows` →
    commit → `_append_write_event("drain-consumed", ...)`, mirroring
    `lifecycle()`'s commit-then-journal order). Reports stale `pending` rows
    oldest-first as discard candidates; never issues UPDATE/DELETE against a
    pending row, apply or not (D5/D-35 human gate preserved).
  - CLI: `maintenance` subparser gains `--drain-pending` and
    `--pending-stale-days` (default `WORKING_TTL_DAYS`); dispatch routes to
    `drain_pending(...)` when `--drain-pending` is set, otherwise unchanged
    squash path (`maintenance(squash_days=..., apply=...)` signature
    untouched).
- `tools/memory/pending_drain.test.sh` (new, +x): 23 cases across doctor
  ordering, dry-run non-destructiveness, `--apply` consumed deletion +
  journal/graveyard entries, pending survival/human-gate messaging,
  `--pending-stale-days` boundary, squash-path no-regression, and
  consumed-non-reappearance after connect-time normalization.

## Commands run

```
python3 -m py_compile tools/memory/mem.py                 # OK
bash tools/memory/pending_drain.test.sh                    # PASS=23 FAIL=0
bash tools/memory/mem_cluster_j.test.sh                    # PASS=33 FAIL=0
bash tools/memory/mem_cluster_e_gamma.test.sh               # PASS=40 FAIL=0
bash tools/memory/mem_retrieval_v14.test.sh                 # PASS=22 FAIL=0
MEM_STORE=<mktemp> MEM_PROJECTS=<mktemp> \
  python3 tools/memory/mem.py maintenance --drain-pending   # dry-run, exit 0
```

All isolated (`MEM_STORE`/`MEM_PROJECTS`/`MEM_WRITE_EVENTS` via `mktemp -d`);
one read-only `doctor` smoke run against the real runtime store (no
`--apply`, no env override) confirmed the extended WARN message format in
practice before the isolated suites were written.

## Notes for downstream (test/report stage)

- Plan §5 acceptance criteria met: new suite 8/8 case groups ok (23 asserts),
  existing 3 suites show 0 new failures, record counts unchanged on every
  non-`--apply` path, pending rows unchanged on every `--apply` path too.
- No auto-transition added for pending records (no auto-consume, no
  auto-expire) — scope boundary from plan §4 held.
