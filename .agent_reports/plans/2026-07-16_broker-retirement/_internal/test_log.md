# Test Log

- `bash hooks/portable-guards.test.sh`: pre-integration PASS=359 FAIL=0; latest-main integration PASS=368 FAIL=0
- `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`: 565 passed
- `python3 -m unittest adapters.claude.tools.fleet.tests.test_dispatch`: 69 passed
- `tools/check-adaptation-boundary.sh`: PASS (documented compatibility-reference warning only)
- Focused route, fallback, registry, wrapper, broker-retirement, eligibility, completion, spec transaction, and worker-route suites: PASS
- Concurrent real wrapper fixture: one registry row and one child for duplicate v3 starts
- Live nested Codex: inner token `NESTED_HEADLESS_OK_7F3A`; outer confirmation `OUTER_CONFIRMED_NESTED_HEADLESS_OK_7F3A`
- `git diff --check` and modified shell syntax checks: PASS
- Independent verifier on integrated head: 107 focused tests + 69 Fleet dispatch tests PASS; no merge blocker
