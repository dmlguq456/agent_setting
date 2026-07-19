# code-test r2 — conductor reliability

- Route/node: `rt-1d200b72bcfb544c` / `test`
- Target: committed worktree `/home/Uihyeop/agent_setting-wt/conductor-reliability`
- Range: `b9364824..e44c77a2` (commits `9d580b8e`, `de7db348`, `225eefc6`, `ae1165cc`, `e44c77a2`)
- Runtime: registered Codex depth-2 stage worker; execute claims were treated as untrusted.
- Tool contract: Codex `verification-runner` checked and used for explicit commands.
- QA: `qa-policy thorough code` reported `2x-deep-reviewers+2x-fast-reviewers`, `assurance_scope=plan-check:selected-independent-pass:final-verify`. This is one independent Codex deep-review pass; no extra reviewer count is claimed.

## Verdict

**FAIL.** The mandatory `bash hooks/portable-guards.test.sh` gate completed with `PASS=366 FAIL=2`. The assignment makes any failure here a blocker even if it predates the branch.

1. `codex doctor --runtime should include runtime projection validation`
2. `codex doctor --runtime-strict should require and accept complete hook trust`

`git diff --quiet b9364824..HEAD -- adapters/codex/bin/preflight.sh adapters/codex/bin/check-runtime-projection.sh hooks/portable-guards.test.sh` returned 0, so those paths are unchanged by this branch. The required floor is nevertheless red.

## Verification floor

### 1. Repository integrity and ownership — PASS

Commands: `git diff --check`; `git status --short --branch`; `git log --oneline b9364824..HEAD`; and `git diff b9364824..HEAD --stat -- spec utilities/dispatch-route.sh utilities/dispatch_route.test.py utilities/dispatch-route.test.sh`.

- Diff check exited 0; worktree is clean at `e44c77a2`; the expected five commits are present.
- Protected spec, dispatch-route, and named route-test paths produced an empty stat.
- Final `find . -type d -name __pycache__ -print` was empty; generated caches were removed.

### 2. Syntax/compile — PASS

`python3 -m py_compile` succeeded for all 15 touched Python files. `bash -n tools/check-adaptation-boundary.sh utilities/dispatch-liveness.sh utilities/harness-status.sh` also exited 0.

### 3. Focused suites — PASS (283 tests)

All ran through the verification runner with `AGENT_DISPATCH_JOBS` unset.

| Suite | Result |
|---|---:|
| `utilities/capability_route.test.py` | 11 OK |
| `utilities/dispatch_completion_marker.test.py` | 8 OK |
| `utilities/dispatch_registry.test.py` | 13 OK |
| `utilities/dispatch_contract.test.py` | 10 OK |
| `utilities/dispatch_node.test.py` | 17 OK |
| `utilities/worker_route_guard.test.py` | 13 OK |
| `utilities/stage_dispatch_fallback.test.py` | 8 OK |
| `utilities/nested_dispatch_eligibility.test.py` | 4 OK |
| `adapters/codex/bin/dispatch-headless.sd45.test.py` | 12 OK |
| `adapters/claude/bin/dispatch-headless.sd45.test.py` | 15 OK |
| `utilities/dispatch_codex_nocommit_fixture.test.py` | 2 OK |
| `tools/fleet/tests/test_f25_state_model.py` | 33 OK |
| `tools/fleet/tests/test_f26_registry.py` | 41 OK |
| `tools/fleet/tests/test_f28_route.py` | 23 OK |
| `tools/fleet/tests/test_dispatch.py` | 73 OK |

Critical suites were rerun verbose. Named cases covered exact-attempt-only close, duplicate idempotency, missing-attempt preservation, unwritable-jobs marker preservation/classification, orphan positives and false-positive guards, live-child preservation, unstarted successor, Fleet annotation, Claude deny scoping, and Codex no-commit behavior.

### 4. Portable guards — FAIL / BLOCKER

`bash hooks/portable-guards.test.sh` ran to terminal completion:

```text
PASS=366 FAIL=2
status=failed
exit_code=1
```

The two failing assertions are listed under Verdict. This is the first failing required level.

### 5. Adaptation boundary — PASS

After cache cleanup, `bash tools/check-adaptation-boundary.sh` exited 0:

```text
WARN: 103 concrete Claude/model references remain in portable areas.
OK: adaptation boundary checks passed
```

The same warning count was reproduced against base `b9364824` (`103`), so it was not introduced here.

### 6. SD-69 self-hosted Codex proof — PASS, bounded claim

`python3 utilities/dispatch_codex_nocommit_fixture.test.py -v` passed both disposable linked-worktree tests.

The verifier is itself the registered Codex worker. Current-worker observations showed:

- a real primary marker persisted at `/home/Uihyeop/agent_setting/.spec-grounding/codex-headless___home_Uihyeop_agent_setting__stage-dispatch`;
- gitdir resolved to `/home/Uihyeop/agent_setting/.git/worktrees/conductor-reliability`, common dir to `/home/Uihyeop/agent_setting/.git`;
- `test -w` returned status 1 for both, proving neither is writable in this Codex sandbox; no commit was attempted or claimed;
- fixture assertions prove only primary `.spec-grounding` plus canonical artifacts are projected, `.git`/common-dir are excluded, disposable source/marker writes persist, `no_commit=1` is stamped, and `source_commit`/`route_hash` remain honest.

Bounded claim: the fixture simulates worker writes directly instead of launching another nested `codex exec`; no nested-runtime acceptance is claimed. The actual current worker separately proved the real marker and protected gitdir boundaries.

### 7. SD-70 exact completion — PASS with coverage note

Verbose marker, registry, and contract suites proved prior blocked/current/later retry closes only current; duplicate is idempotent; missing attempt preserves marker with `attempt-row-absent`; missing/unwritable jobs preserves marker/linkage with `row-close-failed`; unrelated rows are not breadth-closed.

Coverage note: `test_complete_unwritable_jobs_marker_preserved_then_reconcile_repairs` checks marker-backed `classify()` but does not itself invoke `reconcile --apply`; exact under-lock application is covered separately by the registry suite. The test name overstates its end-to-end scope, though the combined suites cover both pieces.

### 8. SD-64/71 orphan reconcile and visibility — PASS

Verbose registry tests proved dead owner + incomplete route + live child or ready unstarted successor becomes `dead-parent-orphaned`; live conductor, completed route, and unreadable route do not; owner-only closure preserves a live child.

Fleet verbose tests proved `note=dead-parent-orphaned`, `resume_boundary=execute`, and no completed-route stamp. Static inspection confirmed liveness uses `orphan-status`, harness status uses `orphan-scan`, Fleet reuses the same classifier, and none auto-resumes/relaunches. Live `preflight.sh status` emitted `orphaned_conductor_jobs=0`. Portable liveness transition tests were green; a live-registry liveness probe exited 3 only because unrelated old jobs are suspect/exited.

### 9. SD-71 async deny and Stop gate — PASS with warning

Probe evidence under `_internal/` was read. `PROVEN_ASYNC_DENY` is exactly `Monitor,ScheduleWakeup,CronCreate,CronDelete,CronList,PushNotification,RemoteTrigger`. Comparison returned `subset_probe=True`, `bash_denied=False`, `dispatch_wait_denied=False`; verbose tests proved only standard+ owners receive it.

The Stop probe recorded 9 events, exit 0, and one stdout byte (empty content/newline). Blocking caused repeated turns rather than hard block. Fire + block + stdout preservation did not all hold, so the gate remains unregistered and the held fallback is correct.

Documentation warning: the probe shows Stop fired 9/9, while a pre-existing `core/OPERATIONS.md` sentence says it "does not fire reliably" under `claude -p`. The operational decision remains correct because block/stdout fail, but that reason is stale; `execute-r2.md`'s contrary claim is unsupported.

## Handoff

FAIL — focused checks are green, but the mandatory portable guard floor is red (`366/2`). Do not report overall PASS until both Codex doctor runtime-projection assertions pass and the full suite reruns green.
