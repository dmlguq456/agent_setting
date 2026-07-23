# SD-78 Dispatch Completion Join — Round 3 Audit

## Contract Review: Four Enforcement Points

### Point 1: Undelivered Batch — Only Exact Same-Parent Dispatch Allowed ✓

**Finding**: PASS

The classifier in `dispatch_completion_join.py` lines 191–267 correctly enforces:
- `classify_supervised_shell_command()` rejects shell composition (line 200)
- Dispatch requires exact path via `_local_contract_path()` (line 236)
- Dispatch requires all six mandatory options: `--route`, `--node`, `--adapter`, `--action`, `--slug`, `--parent` (line 256)
- `--action` must be `"start"` (line 262)
- `--parent` must match parent_slug (line 263)
- `--adapter` restricted to {"claude", "codex", "opencode"} (line 264)
- Harvest in undelivered state rejected at `read_supervisor_state()` level (lines 97–98 of registered-parent-park.py)

Test coverage in `dispatch_completion_join.test.py` lines 179–201 rejects: invalid attempts, composition, wrong paths, foreign parent, unrelated commands. ✓

---

### Point 2: Delivered Batch — Only Exact Harvest Allowed ✓

**Finding**: PASS

Recovery and delivery state logic:
- `read_supervisor_state()` (lines 100–128) validates parent_attempt_id scope and returns delivered set or None
- When state is None: harvest only (no dispatch allowed) — lines 97–98, 315–316
- When state exists and delivered_open ≠ ∅: harvest only from delivered_open (lines 99–104, 326–330)
- When state exists but delivered_open = ∅: dispatch only (lines 105–106, 334)

Path safety: `_safe_identity()` (lines 48–53) enforces UTF-8 ≤256 bytes, no commas, no control chars.

Test coverage in `registered_parent_park.test.py` lines 90–134:
- Undelivered empty list → dispatch allowed
- Delivered=[CHILD] → harvest of CHILD allowed, dispatch denied
- Missing state → harvest allowed (recovery-only), dispatch denied

✓

---

### Point 3: Codex & Claude Parity; Hook Injection; State Lifecycle ✓

**Finding**: PASS with minor note

**Codex enforcement** (`adapters/codex/hooks/pretooluse-write-guard.py`):
- PreToolUse hook validates shell commands via `park_control_allowed()` (line 494)
- Calls same `classify_supervised_shell_command()` logic (line 318)
- Applies identical delivery state checks (lines 324–334)

**Claude enforcement** (`hooks/registered-parent-park.py` + adapter wrapper):
- Adapter wrapper (`adapters/claude/hooks/registered-parent-park.py` lines 1–8) is a shell trampoline to root hook
- Root hook applies same classifier and delivery logic (lines 89–116)
- Injected only through command-scoped `--settings` (claude-session-supervisor.py lines 160–176)
- JSON settings payload properly namespaced under `hooks.PreToolUse[].hooks[]` with timeout=10s (line 169)

**State atomicity & cleanup**:
- Write: tempfile + fsync + atomic replace (dispatch_completion_join.py lines 79–90)
- Permissions: mode 0o600 (line 89)
- Bounds: MAX_STATE_BYTES = 16384 (line 26), enforced at write/read (lines 77–78, 109)
- Cleanup: `remove_supervisor_state()` (lines 131–141) in both supervisors' finally blocks (codex line 442, claude line 336)
- Orphan watch reconciliation also removes state (dispatch-orphan-watch.py lines 54–60)

Test evidence: codex_app_server_supervisor.test.py line 177, claude_session_supervisor.test.py line 153 both verify state file is deleted after completion. ✓

Minor note: Codex hook also checks `parent_sid` (pretooluse-write-guard.py line 189), but Claude hook only checks `parent_attempt_id`. For registered-headless dispatch (test rows use only `parent_attempt_id`, never `parent_sid`), this is not a contract violation—`parent_sid` is for other dispatch modes outside this review scope.

---

### Point 4: Supervisor Joins Outside Model; Once Per Batch; Terminal Handoff; Last-Turn Diagnostics ✓

**Finding**: PASS

**Join ownership**:
- Codex supervisor (`codex-app-server-supervisor.py`) owns join via subprocess (lines 116–148)
- Claude supervisor (`claude-session-supervisor.py`) owns join via subprocess (lines 92–124)
- Both spawn `dispatch_completion_join.py` as separate process, not inside model

**Once per exact batch**:
- Codex: loop structure (lines 380–410) writes state before each turn (line 381), detects new attempts (line 387), runs join once (line 398), marks as delivered (line 407), advances to completion prompt (line 408)
- Claude: same structure (lines 265–318) writes state (line 266), detects new attempts (line 279), runs join once (line 290), marks as delivered (line 299), advances to completion prompt (line 300)

**Terminal handoff**:
- Both verify `exact_handoff()` (lines 36–42 and 127–136 respectively) enforces 3 lines with exact prefixes: `artifact: `, `verdict: `, `blocker: `
- Return code 0 only if handoff is exact (codex line 427, claude line 323)

**Scoped diagnostics**:
- Codex: captures final agentMessage text only (lines 299–301)
- Claude: captures final result.result only (lines 225–226)
- Supervisor state file removed immediately after (both finally blocks)

**Child output never exposed**:
- `dispatch_completion_join.py` docstring (line 4–6): "The joiner never returns child output"
- Join receipt is typed JSON only (no raw stdout)
- Tests verify: dispatch_completion_join.test.py line 79 asserts `"RAW_CHILD_SENTINEL"` not in json output; similar for supervisors (codex_app_server_supervisor.test.py line 176, claude_session_supervisor.test.py line 151)

✓

---

## Test Coverage Summary

| Test File | Scope | Status |
|-----------|-------|--------|
| `dispatch_completion_join.test.py` | Batch join, liveness, classification, state ops | ✓ Complete |
| `registered_parent_park.test.py` | Claude hook undelivered/delivered/missing states | ✓ Complete |
| `codex_app_server_supervisor.test.py` | Codex loop, join resume, terminal handoff | ✓ Complete |
| `claude_session_supervisor.test.py` | Claude loop, session resume, terminal handoff | ✓ Complete |
| `dispatch_orphan_watch.test.py` | Owner exit, orphan cascade, state cleanup | ✓ Complete |

---

## Conclusion

All four contract points are satisfied. The implementation correctly enforces exact-batch dispatch semantics for registered headless children:
- Undelivered state blocks all tools except sibling dispatch
- Delivered state blocks all tools except harvest of delivered attempts
- Codex and Claude hooks are observationally equivalent for registered dispatch
- Hook injection is command-scoped and port-safe
- State is atomic, bounded, and properly removed on all exit paths
- Supervisors own the join logic outside the model, resume once per batch, and emit only terminal handoffs

```
verdict: PASS
```

---

## No Blockers

All requirements met. No high/medium severity issues detected.
