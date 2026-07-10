# Remediation round 2 — D1 + D2 (code-test round1 findings)

Source: `test_logs/test_round1.md` (D1 medium display-layer, D2 low test gap).

## D1 — raw `code-*` capability key leaking as stage-row prefix

**Root cause**: `tools/fleet/render.py` builds the depth-2 stage-breadcrumb prefix as
`key + ": "` using the raw dispatch `key` (= capability, e.g. `code-execute`,
`code-test` per `collectors/dispatch.py` `pname = meta["capability"]`). This existed
in **two** render paths, not one:

- `_dispatch_row` (wide 1-line layout) — line ~857-858
- `_dispatch_row_2line` (narrow 2-line card layout) — line ~972-973 (same bug,
  found while live-verifying the wide-layout fix against `--demo`/live output,
  which renders narrow cards on this terminal width)

**Fix chosen**: reuse the existing SD-F1 `_stage_role_label(worker_role)` helper
(already used for the conductor breadcrumb aggregation) against the raw `key`
instead of inventing new vocabulary. `_stage_role_label` looks up `_STAGE_ROLE`
(`code-plan→plan`, `code-execute→exec`, `code-test→test`, `code-report→report`)
and falls back to the raw key only when it isn't a known stage sub-skill (so
unrelated dispatch prefixes, e.g. a hypothetical non-code capability, are
unaffected).

```python
role_label, role_suffix = _stage_role_label(key)
prefix_text = (role_label + role_suffix) if role_label else key
segs.append((prefix_text + ": ", "name_dim"))
```

Applied identically at both call sites:
- `render.py:857-863` (`_dispatch_row`)
- `render.py:972-976` (`_dispatch_row_2line`)

The conductor row breadcrumb (`_PIPE_STAGES["code"]` → `code: plan › exec › test`)
is untouched — its `key` is `"code"`, which is not in `_STAGE_ROLE`, so
`_stage_role_label` returns `(None, "")` and the raw-key fallback (`"code"`)
renders exactly as before.

## D2 — unit fixture used `key="code"` instead of the realistic `key="code-<stage>"`

`tools/fleet/tests/test_dispatch.py::StageWorkerRenderTest::test_stage_worker_rows_render_stage_labels`
built its depth-2 job fixture with `key="code"` (the depth-1 conductor's track
key) while only varying `worker_role`. Since `"code"` already reads as a
legitimate label (`"code: "` looked fine), the test never exercised the actual
live shape (`key == capability == worker_role`, e.g. `"code-execute"`), so it
could not have caught D1.

**Fix**: `key=worker_role` (matches how `collectors/dispatch.py` really
populates `j.key` for jobs.log-sourced depth-2 stage workers), plus a
strengthened assertion:

```python
job = DispatchJob(key=worker_role, slug="stage-job", depth=2, worker_role=worker_role,
                  liveness="working")
...
self.assertNotIn(worker_role + ":", text)   # new — the exact D1 leak shape
self.assertNotIn(worker_role, text)         # pre-existing
```

Verified the test is a genuine guard: reverted `render.py` only (`git stash`)
and re-ran this single test — it **FAILS** (`'code-plan:' unexpectedly found`),
confirming it fails before the D1 fix and passes after (see verification log
below).

## Verification

### 1. Unit — `python3 -m unittest fleet.tests.test_dispatch -v`
```
Ran 48 tests in 0.137s
OK
```
48/48 green, same count as round 1 (no assertion count change, only fixture
realism + one added `assertNotIn`).

### 2. Regression proof (D2 genuinely guards D1)
`git stash push -- fleet/render.py` (revert D1 fix only) →
`python3 -m unittest fleet.tests.test_dispatch.StageWorkerRenderTest.test_stage_worker_rows_render_stage_labels -v`:
```
FAIL: test_stage_worker_rows_render_stage_labels
AssertionError: 'code-plan:' unexpectedly found in '...  code-plan: —...'
```
`git stash pop` restored the fix; full suite green again (see #1).

### 3. Live re-check — `python3 tools/fleet/fleet.py --once`

Before (round-1 test capture, `test_round1.md`):
```
▍     ⠏ claude code fleet-ui-v2-execu… (dev·std/exec/qa:~std)  fleet-ui-v2
▍   —               sonnet (medium)        code-execute: queued
```

After (this session, live, same job — fleet-ui-v2-execute, key=code-execute):
```
▍     ⠏ claude code fleet-ui-v2-execu… (dev·std/exec/qa:~std)  fleet-ui-v2
▍   —               sonnet (medium)        exec: queued
```
No raw `code-execute:` prefix. Humanized `exec:` label via `_STAGE_ROLE`.

Conductor row (same live output, unchanged / PASS, no regression):
```
▍ ↳ ⠏ claude code   fleet-ui-v2 (dev·std/owner/qa:~std)  fleet-ui-v2
▍   —               opus (medium)          code: plan › exec › test
```

Also confirmed the narrow 2-line card layout (`--demo --once`, which renders
2-line cards at this terminal width) no longer leaks either — this is where
the second leak site (`_dispatch_row_2line`) was actually caught:
```
▍     ⠴ claude code fleet-ui-v2-execu… (dev·std/exec/qa:~std)  fleet-ui-v2
▍   —               sonnet (medium)        exec: queued
```
(before the second-site fix this line read `code-execute: queued`)

### 4. Exit codes
- `python3 tools/fleet/fleet.py --json --once` → exit 0, valid JSON emitted.
- `python3 tools/fleet/fleet.py --demo --once` → exit 0.

## Verdict

D1 and D2 both fixed and self-verified. 48/48 unit tests green, strengthened
D2 test confirmed to fail-before/pass-after the D1 fix, live re-check shows
the humanized `exec:` prefix with no raw `code-*` leak in both the wide and
narrow-card render paths, conductor breadcrumb aggregation unaffected.
