# Correction 01 — adapter projection bytecode boundary

## Verdict

`READY_FOR_CODE_TEST_RETRY`

This correction is focused implementation evidence only. It does not replace the
fresh independent code-test matrix.

## Diagnosis

Standalone `tools/check-adaptation-boundary.sh` failed only because the focused
Phase 2 test loaded `adapters/codex/hooks/userprompt-lifecycle.py` through
`spec.loader.exec_module(module)`. Python then wrote
`adapters/codex/hooks/__pycache__/userprompt-lifecycle.cpython-38.pyc`, which the
existing non-Claude projection cache guard correctly rejects. The doctor runtime
checks themselves were already `ok`; their overall failure was downstream of
this repository-boundary pollution.

## Changes

### `tools/fleet/tests/test_token_budget.py`

**Decision:** Preserve execution of the real lifecycle source while bypassing the
loader's on-disk bytecode cache. Direct `compile(...)/exec(...)` keeps the module
namespace and filename behavior needed by the test without weakening the boundary
guard or changing production code.

**old:**

```python
spec.loader.exec_module(module)
```

**new:**

```python
source = lifecycle_path.read_text(encoding="utf-8")
exec(compile(source, str(lifecycle_path), "exec"), module.__dict__)
```

### `adapters/claude/tools/fleet/tests/test_token_budget.py`

**Decision:** Apply the identical portable Fleet test change to the required
Claude mirror. This is parity output only, not Codex-native input; `cmp` remains
byte-identical.

The ignored cache file/directory produced by the prior test run was removed after
explicit write preflight. No guard assertion, doctor behavior, runtime projection,
production hook, runtime config, Phase 2/3 contract, spec, or test evidence log was
changed.

## Tool fallback

Explicit write preflights succeeded for both tests, the ephemeral cache, and both
correction artifacts. Native `apply_patch` was then rejected because the Codex
PreToolUse bridge could not infer either target from the patch. Per the adapter
contract, the same patch was applied with the shell `apply_patch` fallback; no
redirect, `sed -i`, or Python file-write fallback was used for repository files.

## Correction-focused verification

- Pre-fix standalone boundary: exit 1; only concrete failure was the Codex hook
  `__pycache__` directory and `.pyc` file.
- Focused lifecycle test: exit 0; test passed and did not recreate an adapter cache.
- Standalone adaptation boundary: exit 0, `OK: adaptation boundary checks passed`.
- Manifest check: exit 0, `manifest up-to-date; delta baselines bound`.
- Full portable guards: exit 0, `PASS=344 FAIL=0`; both doctor runtime assertions
  passed exactly.
- Portable/Claude Fleet test mirror: `cmp` exit 0.
- Non-Claude projection bytecode scan: empty.
- `git diff --check`: exit 0.
- Production dynamic-absence scan: exit 0,
  `production_dynamic_absent=1`.

An initial targeted unittest command used the wrong class selector and exited 1;
the corrected `AccountingTest` selector passed. This was a command-selection
error, not a source failure.

Official Codex hook/currentness material was refreshed through the documented
manual helper. The correction changes no runtime hook/config surface, so no runtime
projection installation or config mutation was required or performed.
