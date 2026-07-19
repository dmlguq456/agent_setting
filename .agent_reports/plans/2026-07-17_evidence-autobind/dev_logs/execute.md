# Evidence autobind — execute log

Worktree: `/home/Uihyeop/agent_setting-wt/evidence-autobind` (branch `evidence-autobind`).
Source pin: `5972a61df915815a71b818fec83794a913e2e23e` — worktree HEAD matched at entry.
Commit: `1685cd3d feat(dispatch): SD-66 evidence autobind — record→wrapper forwarding + internal probe`.

## Changed files

- `utilities/dispatch-node.py` — refactored the compressed `main` into small
  pure helpers (`select_checked_tuple`, `bind_dispatch_evidence`,
  `collect_explicit_evidence`, `strip_leading_separator`) plus a local
  `DispatchNodeError`. For a depth-2 route node, walks `dispatch_fallback` in
  ascending ordinal order, takes the first ordinal offering exactly one
  `supported` candidate whose `child_harness == --adapter`, cross-checks it
  against exactly one top-level `route.dispatch_evidence.tuples` counterpart
  (matching all 7 identity/status/source fields, normalizing an absent
  `failure_class` to `""`, deliberately excluding `probe_time`), and maps the
  result to `--launch-authority --parent-harness --parent-transport
  --parent-sandbox --nested-eligibility --eligibility-source` plus
  `--eligibility-failure-class` when non-empty. Caller-supplied explicit
  values matching the record pass without duplication; a mismatch or
  disagreeing duplicate explicit occurrence raises `DispatchNodeError` with
  `reason/flag/explicit/record` before the wrapper is invoked (exit 65).
  Depth-1 and resource-runner nodes are untouched — no evidence flags, same
  CLI/verification/adapter-argument order as before.
- `adapters/claude/bin/dispatch-headless.py`,
  `adapters/codex/bin/dispatch-headless.py`,
  `adapters/opencode/bin/dispatch-headless.py` — added
  `bind_internal_eligibility_probe(args)` (mirrored per adapter, `child_harness`
  fixed to the adapter's own name, same duplication pattern already used for
  `DEATH_PATTERNS`). Triggers only when `depth >= 2`, `action == "start"`, and
  both evidence options are still at their parser default (`nested_eligibility
  == "unknown"` and empty `eligibility_source`) with fully known, non-`unknown`
  parent identity. Runs `utilities/nested-dispatch-eligibility.py --json`
  in-wrapper; accepts the row only when every identity field it echoes back
  (`parent_harness/parent_transport/parent_sandbox/child_harness/launch_authority`)
  matches the request — malformed JSON, execution error, or identity mismatch
  leaves `nested_eligibility` at its unknown default so the existing
  `validate_nested_eligibility` call still fails closed
  (`nested-eligibility-evidence-missing` / `nested-child-spawn-<status>`).
  `eligibility_probe` is set to `"internal"` as soon as the probe is attempted
  (regardless of outcome) and to `"-"` otherwise; both wrappers now print
  `eligibility_probe=` in their success stdout block and the depth-2 job pipe
  (alongside the existing `nested_eligibility`/`eligibility_source`/
  `eligibility_failure_class` fields), and the `DispatchContractError` failure
  path now also emits the full tuple plus `eligibility_probe` as structured
  fail fields — no row is claimed and no child is launched on that path.
  Added `import json` to the claude/codex wrappers (opencode already had it).
- `utilities/dispatch_node.test.py` (new) — 17 unit tests covering
  `select_checked_tuple` (deterministic ordinal/adapter selection, unsupported/
  ambiguous/missing/conflicting-counterpart fail-loud, `probe_time` exclusion),
  `bind_dispatch_evidence` (six/seven-flag emission, empty-failure-class
  omission, equal-explicit pass-through, explicit conflict and
  duplicate-explicit conflict fail-loud with both values shown, `--flag=value`
  form), and `main()` end-to-end via a mocked `subprocess.run` (depth-1 emits
  no evidence flags and preserves adapter args; depth-2 binds evidence into
  the captured wrapper argv; depth-2 with no dispatch_evidence exits 65).
- `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` —
  added one `*SD45InternalProbe` class per adapter (8 tests each, 24 total)
  that imports the wrapper module directly (`importlib` spec-from-file, same
  pattern as `utilities/nested_dispatch_eligibility.test.py`) and calls
  `bind_internal_eligibility_probe` on a constructed `argparse.Namespace` with
  a mocked `subprocess.run`: absent-evidence supported binding + `internal`
  marker + downstream `validate_nested_eligibility` passes; unsupported probe
  result binds + fails closed with `nested-child-spawn-unsupported`; explicit
  evidence never invokes the probe; unknown parent identity never invokes the
  probe; malformed JSON and identity-mismatched JSON both leave
  `nested_eligibility` at `unknown` (fail-closed) while still marking
  `eligibility_probe=internal` (probe was attempted); depth-1 and
  `--register` never probe.

## Commands run and results

All from the task worktree. `AGENT_DISPATCH_JOBS` was unset for the
`--jobs`-fixture-based subprocess tests — see "Deviation" below.

| Command | Result |
|---|---|
| `python3 -m py_compile utilities/dispatch-node.py utilities/nested-dispatch-eligibility.py adapters/claude/bin/dispatch-headless.py adapters/codex/bin/dispatch-headless.py adapters/opencode/bin/dispatch-headless.py utilities/dispatch_node.test.py adapters/claude/bin/dispatch-headless.sd45.test.py adapters/codex/bin/dispatch-headless.sd45.test.py adapters/opencode/bin/dispatch-headless.sd45.test.py` | OK |
| `python3 utilities/dispatch_node.test.py` | OK — 17 tests |
| `python3 utilities/dispatch_contract.test.py` | OK — 10 tests |
| `bash adapters/claude/bin/dispatch-headless.sd15.test.sh` | PASS — 5 checks |
| `bash adapters/codex/bin/dispatch-headless.sd15.test.sh` | PASS — 8 checks |
| `bash adapters/opencode/bin/dispatch-headless.sd15.test.sh` | PASS — 7 checks |
| `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` | OK — 9 tests (1 pre-existing + 8 new) |
| `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` | OK — 9 tests (1 pre-existing + 8 new) |
| `python3 adapters/opencode/bin/dispatch-headless.sd45.test.py` | OK — 9 tests (1 pre-existing + 8 new) |
| `python3 utilities/stage_dispatch_fallback.test.py` | OK — 7 tests |
| `python3 utilities/nested_dispatch_eligibility.test.py` | OK — 4 tests |
| `bash utilities/dispatch-route.test.sh` | PASS |
| `git diff --exit-code -- loops/drill/cases_growing/g10_claude_opencode_depth2_start spec` | clean (exit 0) — g10 fixtures and `spec/**` untouched |
| `git diff --check` | clean (exit 0) |

## Deviation from plan: `AGENT_DISPATCH_JOBS` unset for fixture-jobs tests

This execute stage itself runs as a nested depth-2 worker, so the session
inherits a real `AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log`
(SD-49 canonical global registry). The three existing (pre-change)
`*.sd45.test.py` subprocess cases pass their own `--jobs <tmp-fixture-path>` —
under SD-49 that is a non-authoritative "cycle-local override" against an
already-inherited `AGENT_DISPATCH_JOBS`, so `resolve_global_registry` fails
closed with `reason=global-registry-unwritable` (exit 73), independent of any
change in this cycle. Verified against the unmodified worktree via
`git stash` before starting: the same one test fails the same way with the
same exit code on HEAD. Confirmed the fix is purely environmental — every
suite above passes cleanly when run with `AGENT_DISPATCH_JOBS` unset (see the
results table), so no source or test change was made to route around it. This
does not touch the new SD-66 probe/binding logic, which never depends on
`AGENT_DISPATCH_JOBS`.

## Residual risks

- The pre-existing `AGENT_DISPATCH_JOBS` fixture-collision failure (see
  above) is environment-shaped, not code-shaped, but a depth-0 integration
  run of the g10 drill or a plain top-level `claude` session (no inherited
  `AGENT_DISPATCH_JOBS`) will not hit it; flagging so the test stage does not
  mistake it for a regression if it re-observes the same rc=73 under a
  similarly nested run.
- `utilities/nested-dispatch-eligibility.py` was read but not modified — no
  pure-JSON-validation-helper extraction was needed to keep the direct probe
  tests (`nested_dispatch_eligibility.test.py`) unchanged, so plan step 2's
  conditional refactor did not apply.
- `dispatch-node.py`'s evidence binding is unconditional for any depth-2 route
  node (regardless of `--action`), matching the existing route.json fixture
  shape where every depth-2 node always carries a matching
  `dispatch_fallback`/`dispatch_evidence.tuples` pair; a future route shape
  that omits `dispatch_evidence` for a depth-2 node while still requesting
  `--action dry-run`/`--register` would now fail loud (`dispatch-evidence-*`)
  where it previously succeeded silently with no evidence forwarded. This
  matches the PRD acceptance intent (record-bound depth-2 nodes always carry
  checked evidence) but is called out as a behavior change for the test/report
  stages to confirm against current route-compile invariants.
