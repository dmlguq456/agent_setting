# Root post-execute findings

Status: OPEN — integration is blocked pending correction and final review.

## 1. F-39 focused test is not hermetic outside dispatched-worker env

From the linked task worktree, with no inherited `AGENT_ARTIFACT_ROOT`:

```text
adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tools.fleet.tests.test_f36_work_projection \
  tools.fleet.tests.test_f37_context_detail \
  tools.fleet.tests.test_f38_context_orthogonality \
  tools.fleet.tests.test_f39_title_quota

Ran 27 tests ... FAILED (failures=1)
test_direct_worker_uses_same_start_budget_and_provider_is_not_reached_after_limit:
expected one mocked `subprocess.run` call, observed two.
```

The extra call is `model-worker-governor.default_root()` invoking
`utilities/artifact-root.sh`; the test counts every shared `subprocess.run` call
as a title-provider call. Dispatched workers inherit `AGENT_ARTIFACT_ROOT`, which
masked this environment dependency. Isolate `AGENT_MODEL_GOVERNOR_ROOT` under the
test temporary directory (and restore it in teardown), or assert provider argv
calls specifically.

## 2. Effective provider concurrency is still capped at one

`tools/fleet/refresh_title.py` raises its local slot contract to default 3 / hard
4, but every actual provider call also acquires the shared repository governor
with class `title`. `utilities/model-worker-governor.py` still defines:

```text
CLASS_LIMITS = {"dispatch": 3, "distill": 1, "title": 1, "loop": 2}
```

Consequently up to three title worker processes may be scheduled, but only one
can cross the provider boundary; the other workers fail closed at governor
admission. This does not satisfy the user-visible F-39 allowance increase or the
effective default concurrency 3 / hard max 4 contract. Any correction must keep
all repo-launched model workers behind the central governor per
`core/OPERATIONS.md`, align its title-class ceiling with the Fleet hard ceiling,
and add a combined admission regression rather than bypassing the governor.

## 3. Live main-session stage label names the generic contract, not the active node

With the independent `impl-review` attempt live, the provider-disabled 168-column
group command produced:

```text
codex ... multi-owner route stage projection ... main  stage autopilot-code 3/6
    ctx 78% tight · ...
  ↳ codex ... : execute✓ › impl-review › test › report
    ↳ claude ... impl-review ... : running
```

The common projection and context-first row are visibly attached, but the main
Session's stage label is `autopilot-code` even though the sealed route's active
node is `impl-review`. Owner projection currently inherits the selected child's
`assigned_contract`; for review workers that contract is the generic capability,
so it masks the active node ID. An owner/main Session must derive its display
stage from all active route nodes (`impl-review` here, or all siblings for a
parallel level), while a leaf may retain its assigned contract micro-label.

## 4. OpenCode `mode=ro` still mutates the live `-shm` file

A live WAL fixture with an open writer was snapshotted byte-for-byte and by
`st_mtime_ns` before and after `read_opencode_delta()`. The observed result was:

```text
paths: opencode.db, opencode.db-wal, opencode.db-shm
delta: ('hello', 1, 'message')
unchanged: db=True, wal=True, shm=False
```

This is normal SQLite WAL-index behavior: URI `mode=ro` prevents database writes
but a reader may still update the shared-memory WAL index. `immutable=1` kept all
three files unchanged in the same reproduction, but ignored uncheckpointed WAL
content and therefore could not see the message table. The checked Gate B/G
claims for DB/WAL/SHM bytes and write metadata are currently false.

Use a fail-closed, consistency-checked read snapshot (database plus existing WAL)
or an equivalent zero-source-write mechanism, then open only that private
snapshot with SQLite. The regression must keep an open WAL writer, prove the
uncheckpointed exact-session row is visible, and compare source DB/WAL/SHM bytes
and write metadata before/after. Do not restore or rewrite the live runtime files.

