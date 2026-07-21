# v20 route acceptance summary

Date: 2026-07-20  
Worktree: `/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated`  
Source HEAD: `36a8e849e8fde9c41f115b49f3a7b0fb8d67f117`  
Working diff: post-review remediation, uncommitted by design  
Result: PASS

## Fresh routes

| Case | Route | Hash | Required shape |
|---|---|---|---|
| direct | `rt-52debf28783a0fde` | `sha256:52debf28783a0fde3e1e2159c83d8cfeae16379f2207e2200589f40f433c2f94` | owner/max/node dispatch depth `0/0/0`, `execution_surface=inline`, `registered_worker=false`, no jobs row |
| quick | `rt-bf22640d1d6f60af` | `sha256:bf22640d1d6f60af1537be75b1115ff77f60734f3edb47e154dd58d9ee8c7016` | owner/max/node dispatch depth `1/1/1`, one registered-headless owner, serial-attempt policy, no child/fallback chain |
| standard+ | `rt-8dd94746d6c4aff4` | `sha256:8dd94746d6c4aff4ced3d3ee63e50b2af20046577ffa8b587179163b37f1ec94` | owner/max dispatch depth `1/2`, stage depth `2`, fallback order `same-harness-headless → cross-harness-headless → native-subagent → inline` |

All three records were compiled again from the changed worktree with
`utilities/capability-route.py compile` and verified with
`utilities/capability-route.py verify --cwd <worktree>`. Existing immutable files
matched the newly compiled bytes.

## Negative and preservation matrix

`python3 utilities/dispatch_v20.test.py` passed 8/8:

- quick without a checked route: `quick-headless-unavailable`, no registry/log/child;
- direct wrapper entry: `direct-main-inline-only`, no registry/log/child;
- unknown execution surface or fallback hop: exact typed failure before registry;
- checked quick route: exactly one registered row on Claude, Codex, and OpenCode;
- second live quick attempt: duplicate claim, no second row;
- exhausted quick candidate: `quick-registered-headless-exhausted`, no extra row;
- requested quick dispatch-depth-2 child: `invalid-dispatch-depth-two-intensity`, `child_spawned=0`;
- empty, interactive, native-subagent, inline-fallback, arbitrary, and unavailable
  quick compile inputs: no route output and no registry emission;
- current terminology and closed-vocabulary conformance: PASS.

Standard+ completion evidence passed 11/11 in
`utilities/dispatch_completion_marker.test.py`: registered-headless evidence is
derived from the exact attempt row; Codex native, Claude native, and inline
completion require explicit validated unregistered axes; missing axes fail before a
marker is written.

Standard+ fallback evidence passed 11/11 in
`utilities/stage_dispatch_fallback.test.py`, including the exact native mapping
`codex-native-subagent` / `claude-subagent`.

## Verification logs

- `regression-core.log`: all topology, route, attempt, node, registry, and completion suites PASS.
- `regression-dispatch.log`: all progress, guard, fallback, capacity, bootstrap, prompt, and v20 suites PASS.
- `regression-projections.log`: records the literal-plan `sh` runner mismatch for Bash-only SD-15 scripts.
- `regression-projections-retry.log`: the allowed Bash runner correction, 728 Fleet tests, routing contract, generation, and projection checks all PASS.
- `hooks/portable-guards.test.sh`: `PASS=355 FAIL=0`.
- `tools/check-adaptation-boundary.sh`: PASS; its documented concrete-Claude-reference warning remains non-fatal.

