# Verification log

## Passing checks

- `dispatch-headless.sd15.test.sh`: PASS, including depth-1 actual-thread bind
  and depth-2 broker-parent preservation.
- `tools/fleet/tests/test_dispatch.py`: 60 tests PASS.
- `tools/fleet/tests/test_mirror_parity.py`: PASS.
- `python3 -m py_compile adapters/codex/bin/dispatch-headless.py`: PASS.
- `git diff --check`: PASS.
- Real wrapper dry-run with `CODEX_THREAD_ID=019f68e6-34db-7512-bbc0-63af103f0bac`
  and explicit `synthetic-thread`: output used the actual thread, cleared
  `parent`, and reported `registered=0` / `started=0`.

## Wider baseline comparison

`hooks/portable-guards.test.sh` reports six existing expectation drifts on both
unmodified `main` and this branch. The failing set is identical, so this change
adds no portable-guard failures. The drift concerns typed worker-bootstrap and
registry-row expectations and remains outside this orphan-only scope.

## Integrated main verification

- Source merged to `main` as `faad4c87`.
- Wrapper regression, all 60 Fleet dispatch tests, and mirror parity passed again.
- `preflight.sh runtime-projection --require-hook-trust`: `status=ok`.
- Merged wrapper dry-run again replaced `synthetic-thread` with the current
  thread and performed no registration or launch.
