# Verification log

## QA policy

`preflight.sh qa-policy standard code` required
`1x-deep-reviewer+2x-fast-reviewers` and
`plan-check:selected-independent-pass:final-verify`. The native runtime probe
provided the risk-focused independent pass; the commands below are the final
concrete verification.

## Focused and related regression

PASS — `python3 -m unittest tools.fleet.tests.test_f29_subagents`

- 43 tests, 0 failures, 0 errors, 1.507s.
- Covers exact parent linkage, exact source-parent agreement, role type,
  path fallback, matching completion/abort, multi-turn ordering, stale starts,
  partial JSON, WAL-only edges, ambiguous/malformed/non-subagent/unknown input,
  absent schema, enrichment-only behavior, alternate runtime home ownership,
  and a completion marker preceding a >64 KiB non-lifecycle tail.

PASS — `python3 -m unittest tools.fleet.tests.test_f29_subagents tools.fleet.tests.test_f18_attribution tools.fleet.tests.test_codex_nested_home_rollout tools.fleet.tests.test_f16_f17_subtitle tools.fleet.tests.test_f30_process_view tools.fleet.tests.test_mirror_parity`

- 113 tests, 0 failures, 0 errors, 1.410s.
- Includes Claude/OpenCode subagents plus render/JSON/additive and mirror
  regression surfaces.

## Full Fleet suite

PASS — `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`

- 681 tests, 0 failures, 0 errors, 19.118s on the post-merge `main` rerun.
- This trusted-main rerun clears the nested owner-worker's environment-only
  F-27 ancestry failure.

## Repository and parity checks

PASS — `cmp tools/fleet/collectors/codex.py adapters/claude/tools/fleet/collectors/codex.py`

PASS — `cmp tools/fleet/tests/test_f29_subagents.py adapters/claude/tools/fleet/tests/test_f29_subagents.py`

PASS — `cmp tools/fleet/model.py adapters/claude/tools/fleet/model.py`

PASS — `git diff --check`

PASS — `python3 tools/build-manifest.py --check`

- `manifest up-to-date; delta baselines bound`

PASS — `tools/check-adaptation-boundary.sh`

- `OK: adaptation boundary checks passed`
- Existing warning: 106 concrete Claude/model references remain in portable
  areas where documented adapter/compat mapping is required.

## Live read-only smoke

Current native live probe:

- Under parent `019f7af6-…`, child `019f7b7d-…`
  (`agent_path=/root/fleet_live_probe`) reported `active=true` while its turn
  was running, then `active=false` after matching `task_complete`.
- Both snapshots used the real `fleet.py --json --harness codex --all` path.
- State DB/WAL/SHM, config, and child-rollout content hash, size, and mtime were
  identical around each collector call (`runtime_changed=[]`).

Historical host runtime review (`/home/Uihyeop/.codex`) established why the
projection is conservative: of 67 open edges, 47 ended in `task_complete`, 13
in `turn_aborted`, and 7 in `task_started`; only one start was actually fresh
during the review. Fleet therefore omits stale unmatched starts.

## Independent review

PASS — `/root/fleet_final_review`

- No findings at Critical, High, Medium, or Low severity.
- Independently passed 681 full Fleet tests, 43 focused tests, `py_compile`,
  `git diff --check`, mirror parity, and read-only live-state attribution.
