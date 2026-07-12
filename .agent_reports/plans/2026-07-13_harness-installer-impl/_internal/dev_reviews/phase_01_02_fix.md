# Phase 1+2 review fix — atomic dest/pristine/backup writes

Applied the [medium] finding from `phase_01_02.md` #1: `reapply()`'s writes to
`dest_abs` / `pristine_path` (both call sites) / `backup_path` used direct
`Path.write_bytes` (truncate-then-write). Added `_atomic_write_bytes()`
(temp-file + `os.replace`, same pattern as `_write_manifest`) and routed all
four call sites through it (`record()`'s pristine write included).

Re-verified end-to-end in a fresh `mktemp -d` HOME: record → drift → reapply
with two non-adjacent additions (user edit + new canonical key) merges
cleanly, `check_drift` returns `[]` afterward, and `compile()` syntax-checks
clean. The other three findings (#2 docstring wording, #3 substring-verifier
heuristic note, #4 crash-window ordering, #5 step-log miscount) are
low/nit-severity per the reviewer and left as-is (documented limitations, not
correctness bugs) — no code change needed for those.
