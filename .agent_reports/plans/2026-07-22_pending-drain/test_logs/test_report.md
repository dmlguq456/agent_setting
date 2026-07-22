verdict: PASS

# Test Report — pending drain (2026-07-22)

- worktree: `/home/Uihyeop/agent_setting-wt/pending-drain` (branch `task/pending-drain`)
- verified commit: `eae36aad` — feat(memory): pending drain 정책 — doctor 나이순 노출 + maintenance --drain-pending
- target: `tools/memory/mem.py` (`drain_pending()`, `doctor()` stale-pending 확장, CLI wiring) + 신규 `tools/memory/pending_drain.test.sh`
- unit: qa/test (read-only verification, no source edits made)

## Level 1 — Syntax

```
$ python3 -m py_compile tools/memory/mem.py
```
Result: OK, no diagnostics.

## Level 4 — Functional (plan §5 verification commands)

### (a) New regression suite — isolation confirmed before execution

Read `tools/memory/pending_drain.test.sh` first: every case exports
`MEM_STORE`/`MEM_PROJECTS`/`MEM_WRITE_EVENTS` to fresh `mktemp -d` paths under a
`trap rm -rf … EXIT`, and `cd`s into a separate non-git `mktemp -d` workdir before
any `mem.py` invocation. No case unsets these overrides mid-run. Confirmed no
contact with the real store during this suite.

```
$ bash tools/memory/pending_drain.test.sh
```
Result: **RESULT: PASS=23 FAIL=0**, exit 0. All 8 planned cases covered (doctor
age-ordering, doctor 0-record OK regression, drain dry-run non-destructive, drain
--apply consumed deletion + graveyard/write-event journaling, drain --apply pending
survival + human-gate string, `--pending-stale-days` boundary, squash-path
non-regression, consumed non-reappearance after connect-time normalization).

### (b) Existing tools/memory/ suite regression

```
$ bash tools/memory/mem_cluster_j.test.sh
```
Result: **RESULT: PASS=33 FAIL=0**, exit 0. Covers D-37 journal-on-every-mutation,
actor determinism, fail-open journaling, rotation, D-38 `mem log` filters, D-39
`doctor` clean/violation fixtures including the `stale-pending` WARN this change
touches — `[WARN] stale-pending:` prefix and OK/exit-code contract intact.

```
$ bash tools/memory/mem_cluster_e_gamma.test.sh
```
Result: **RESULT: PASS=40 FAIL=0**, exit 0. Covers reinforce/graduate, prune
graveyard exact-match (DEST-1), merge sum + canonical preserve (DEST-3), rejection
paths (DEST-2), atomic merge rejection (DEST-4), anti-bloat, reattribute — no
regression in delete/graveyard code paths shared with `drain_pending()`.

```
$ bash tools/memory/mem_retrieval_v14.test.sh
```
Result: **RESULT: PASS=22 FAIL=0**, exit 0. Covers pending destructive fail-closed +
recovery, including "pending prune/delete/merge reject atomically" and "lifecycle
preserves pending expired" — direct regression coverage for the D-35/D5 pending
protection invariant this feature must not weaken.

Combined: 4 suites, **118 ok / 0 fail**, all exit 0. No FAIL-count increase vs. plan
baseline (plan §5 acceptance: 23+33+40+22, matches exactly).

### (c) `mem doctor` / `mem maintenance --drain-pending` dry-run — isolated smoke + real-store read-only check

Isolated smoke (plan §5, fresh mktemp store, no real-runtime contact):
```
$ MEM_STORE="$(mktemp -d)" MEM_PROJECTS="$(mktemp -d)" \
  python3 tools/memory/mem.py maintenance --drain-pending
```
Result: ran to completion, `0 consumed · 0 stale-pending (report-only, never
auto-deleted)`, `dry-run; use --apply to drain consumed records`, exit 0.

Real-store read-only/dry-run pass (no `--apply` at any point; required by the
assignment to confirm behavior against the real store without mutating it):
```
$ python3 tools/memory/mem.py doctor
```
`[WARN] stale-pending: 1 records (oldest 2026-06-26, no auto-expiry):
hint_hint-25-17-트래커_e4bfd6(26d)` — new age-ordered format renders correctly
against real data; `integrity_check`/`fts-parity`/`schema-invariants` all OK; exit 1
(WARN, expected/unchanged contract — 9 checks reported).

```
$ python3 tools/memory/mem.py maintenance --drain-pending
```
4 `[consumed]` rows reported as `would delete`, 1 `[stale-pending]` row reported as
discard candidate with the human-gate message (`… or delete --force (human gate)`),
summary `consumed 4 · stale-pending 1 (report-only, never auto-deleted)`, `dry-run;
use --apply …` hint, exit 0. **No `--apply` was run against the real store.**

Non-mutation verification: `records` count before and after this run is unchanged
(`SELECT COUNT(*) FROM records` = 1380, matching the `fts-parity` line the same
`doctor` call reported), confirming the dry-run path issued no writes.

## D5 human-gate code-level check

Read `drain_pending()` (`tools/memory/mem.py:2979-3046`) in full, plus its diff in
commit `eae36aad`:

- The only statement that can mutate `pending` rows would be an UPDATE/DELETE
  against `delivery_state='pending'`. None exists — the pending branch issues a
  single `SELECT id, created, type FROM records WHERE delivery_state='pending' …`
  (`mem.py:3025-3028`) and only `print()`s each row; there is no code path from
  that result set to `_delete_rows`, `_graveyard_append`, or any `UPDATE`.
- Destructive action (`_graveyard_append` → `_delete_rows`) is scoped strictly to
  `consumed_rows`, itself drawn from `WHERE delivery_state='consumed'`
  (`mem.py:2996-2998`) — disjoint from the pending query.
- This holds identically whether `apply` is `True` or `False` — the pending block
  runs unconditionally after the `if apply:` consumed-deletion block and contains
  no `apply` branching of its own.
- `maintenance()` (unchanged, squash-only) is untouched by this diff and is only
  reached when `--drain-pending` is absent from argv (`mem.py:3811-3813`); the two
  code paths do not share a deletion routine.
- Docstring at `mem.py:2980-2985` states the invariant explicitly and the
  regression suite's case 5 (`drain --apply pending 인간 게이트`) exercises it
  behaviorally (3/3 pending rows survive `--apply`, `delivery_state` unchanged).

No D5/D-35 violation found in this diff: no pending record can be deleted,
consumed, or otherwise mutated by any code path added or changed in `eae36aad`.

## Summary

| Level | Target | Result |
|---|---|---|
| 1 Syntax | `mem.py` compile | ✅ PASS |
| 4 Functional | `pending_drain.test.sh` (new) | ✅ PASS 23/23 |
| 4 Functional | `mem_cluster_j.test.sh` | ✅ PASS 33/33 |
| 4 Functional | `mem_cluster_e_gamma.test.sh` | ✅ PASS 40/40 |
| 4 Functional | `mem_retrieval_v14.test.sh` | ✅ PASS 22/22 |
| 4 Functional | isolated-store `maintenance --drain-pending` dry-run smoke | ✅ PASS |
| 4 Functional | real-store `doctor` / `maintenance --drain-pending` dry-run (no `--apply`) | ✅ PASS, non-mutating |
| Code review | D5/D-35 human-gate (pending never deleted) | ✅ CONFIRMED — no violation |

**✅ All levels passed.** Levels passed: 8/8 (syntax + 6 functional checks + code
review). First failure: none. Recommended action: none — plan acceptance criteria
(§5) fully met; no source changes required from this stage.
