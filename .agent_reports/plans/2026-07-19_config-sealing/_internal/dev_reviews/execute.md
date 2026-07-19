# internal dev review notes — code-execute (SD-68)

- Plan (`plan.md`) was fully implementation-complete; execute required no
  design judgment calls beyond following it verbatim.
- `_seal_dispatch_defaults` placement: called right after the
  `dispatch_fallback` injection loop and before `spec_touch`/`payload`
  construction, matching plan §3.2(c) exactly (nodes mutated in place before
  `route_hash(payload)` runs, so the stamp is auto-sealed with zero extra hash
  logic).
- `VALID_AFFINITY` is computed once at module import time from
  `DEFAULTS.AFFINITY_VALUES`, not recomputed per call — matches the loader's
  own module-level `AFFINITY_VALUES` constant pattern.
- Confirmed `DefaultsConfigError` does not subclass `ValueError` before writing
  the wrapping `try/except` (grep on `class DefaultsConfigError` showed
  `Exception` base) — the `raise ValueError(...)` wrap in `_seal_dispatch_defaults`
  is required for `main()`'s `except (ValueError, TOPO.TopologyError)` to catch
  it and exit 64, per plan's explicit rationale.
- The core-first gate (guard hook) blocked the wrapper edits mid-session
  because `core/OPERATIONS.md` had been edited without a fresh `Read` in this
  turn's tool-call history; re-reading the file before retrying the wrapper
  edits satisfied the gate with no code change needed.
- Pre-existing test failures (1 sd45 test on claude, 4 sd15 rows on claude,
  all env/governor-related, unrelated to `harness_affinity`) were verified via
  `git stash` / `git stash pop` to reproduce identically on the pre-change
  tree, so they are not regressions introduced by this work.
- Did not touch `dispatch-route.sh` or any selector-cascade file — out of
  scope per plan §6, confirmed via `dispatch-route.test.sh` PASS (behavior
  unchanged).
