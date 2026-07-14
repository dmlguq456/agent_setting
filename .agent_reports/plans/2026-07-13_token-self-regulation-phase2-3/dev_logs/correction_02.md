# Correction 02 — hermetic portable guard captures

## Verdict

`READY_FOR_CODE_TEST_RETRY`

This correction is focused implementation evidence only. It does not replace the
fresh independent code-test matrix.

## Diagnosis

The runtime-projection/doctor block in `hooks/portable-guards.test.sh` already
creates an invocation-unique `$TMP` tree, but its command output and assertion
reads used fixed `/tmp/codex_rp_*`, `/tmp/codex_doctor_runtime*`, and adjacent
`/tmp/context_footprint*` files. Concurrent guard runs from another worktree could
overwrite those captures between command execution and assertion reads.

## Change

### `hooks/portable-guards.test.sh`

**Decision:** Move every output/error capture and corresponding read in the
affected runtime-projection/doctor block under the existing unique `$TMP` tree.
This is the narrow owning test-harness fix: command order, exit-code behavior,
negative miswire checks, hook-trust checks, doctor checks, and all assertion
patterns remain unchanged.

The corrected block includes unwired, install/check, plugin-only, miswired,
runtime-projection, hook-trust, doctor/runtime-strict, and adjacent
context-footprint captures. It does not add global serialization or change any
production/adapter implementation.

## Tool fallback

Explicit write preflights succeeded for the portable guard and both correction
artifacts. Native `apply_patch` was rejected because the Codex PreToolUse bridge
could not infer the target even after preflight, so the identical patch was
applied with the shell `apply_patch` fallback.

## Correction-focused verification

- Shell syntax:
  `$AGENT_HOME/adapters/codex/bin/preflight.sh verification-runner --timeout 60 -- bash -n hooks/portable-guards.test.sh`
  — exit 0.
- Static affected-block scan:
  verification-runner plus `awk`/`rg` found no fixed
  `/tmp/{codex_rp,codex_doctor_runtime,context_footprint}` capture and printed
  `fixed_runtime_projection_captures_absent=1` — exit 0.
- Isolated full portable guard, invoked once from its initial command and captured
  once at `/tmp/token-self-regulation-correction02-portable-guards.nwLAyJ.log`:
  `$AGENT_HOME/adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- bash hooks/portable-guards.test.sh`
  — exit 0, `PASS=344 FAIL=0`.
- `$AGENT_HOME/adapters/codex/bin/preflight.sh verification-runner --timeout 60 -- git diff --check`
  — exit 0.
- Production-dynamic-absence scan over the four production Codex paths from the
  plan — exit 0, `production_dynamic_absent=1`.

No test evidence, pipeline summary, spec, production code, adapter behavior,
runtime projection/config, commit, push, merge, or worktree cleanup was changed.
