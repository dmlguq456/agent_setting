# Verification — round 2 (depth-0 fix-forward, 2026-07-16)

- Basis: round-1 codex verification (`verification.md`) FAIL findings F1/F2/F4;
  fix-forward commit `81a5cd88` on branch `dispatch-defaults-config`
  (round-1 work `efeab72e`, `7697c3b6` preserved — no baseline restore).
- Executor: depth-0 main (inline micro-stage; reason recorded in `_internal/metrics.md`).
- All commands ran inside the task worktree `/home/Uihyeop/agent_setting-wt/dispatch-defaults-config`
  (never the primary checkout, per guard policy).

## F1 — adapter projection regression: FIXED, verified

- `utilities/dispatch-defaults.py` symlinked into all three
  `adapters/{claude,codex,opencode}/utilities/` (`../../../utilities/dispatch-defaults.py`,
  same idiom as `dispatch-route.sh`).
- `tools/check-adaptation-boundary.sh` updated in three lists per adapter pattern:
  symlink allowlist pairs (codex+opencode), `find` allowlists, `UTILITY_PROJECTED`
  (codex §P-40 and opencode audits).
- `utilities/dispatch-defaults.py::_repo_root` switched `abspath` → `realpath` so the
  projected symlink resolves shipped config/topology at the real repo root
  (round-1 helper projection alone still broke one layer deeper on
  `adapters/<h>/profiles/dispatch-defaults.yaml`).
- Boundary guard re-run: the two remaining FAILs
  (`adapters/{codex,opencode}/tools/memory/mem.py` AGENT_HOME validation) reproduce on
  baseline `3ebd1c77` and are outside this cycle (round-1 verifier concurred).

```text
$ bash tools/check-adaptation-boundary.sh   # worktree
FAIL: adapters/codex/tools/memory/mem.py must validate AGENT_HOME ...   (baseline)
FAIL: adapters/opencode/tools/memory/mem.py must validate AGENT_HOME ... (baseline)
# no dispatch-defaults / projection / worker_type findings
```

- Adapter-projected selector surfaces: this cycle's regression is gone — all three
  selectors now execute past the SD-66 validate/config step and fail only at the
  **pre-existing** `usage-check.sh`/`model-map.sh` invocation-relative resolution,
  reproduced verbatim on a clean baseline checkout of `3ebd1c77`:

```text
baseline codex-projected: adapters/codex/utilities/dispatch-route.sh: 30:
  .../adapters/codex/utilities/usage-check.sh: not found   # identical class at HEAD
```

  Recorded as a known baseline issue (same class as mem.py), not fixed here.

## F2 — fixture isolation: FIXED, verified

- Fixture config creation + `export DISPATCH_DEFAULTS_CONFIG` moved above every
  `route()` call; heading comment documents the isolation contract. The first block
  passes no `--capability`, so assertions are unchanged by the fixture.

```text
$ sh utilities/dispatch-route.test.sh
dispatch-route: PASS
```

## F4 — unittest invocation: NOTED

- `python3 -m unittest utilities/nested_dispatch_eligibility.test.py` raises
  `ModuleNotFoundError` (dotted-path expectation); direct execution is the correct form:

```text
$ python3 -B utilities/nested_dispatch_eligibility.test.py
Ran 4 tests ... OK
```

## F3 — in-sandbox probe artifact: NO ACTION (per retry memo)

- Round-1 verifier's `unsupported/auth-unavailable` probe ran inside the nested codex
  sandbox, which cannot see host auth. Conductor-level probes on this worktree returned
  `supported` 3× during the cycle, and every cross-harness dispatch launched on that
  evidence. Depth-0 confirmation on this session (12:31–12:33Z):
  `claude/codex/opencode` all `status=supported`.

## Shipped-config validator

```text
$ python3 utilities/dispatch-defaults.py validate
dispatch-defaults: .../profiles/dispatch-defaults.yaml is valid
```

## Verdict

- code-test gate: **PASS** (round-1 material findings fixed and re-verified;
  residual FAILs are baseline-reproduced and out of scope).
