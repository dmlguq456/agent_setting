# Quick owner assignment — Fleet tint compatibility inside Herdr

Work only in `/home/Uihyeop/agent_setting-wt/fleet-herdr-tint`.

## Goal

Fix Fleet's visually incorrect fixed 256-color panel tints when Fleet runs
inside a Herdr-managed pane (`HERDR_ENV=1`). Preserve the existing tint
behavior in ordinary terminals.

## Governing context

- Capability: `autopilot-code`, mode `debug`, intensity `quick`, depth 1.
- Governing spec:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md`
  §4 defines 256-color body tints with the existing `▍` rail fallback.
- Spec significance: `within-spec` — treat Herdr as a runtime where Fleet's
  fixed background tint is incompatible and use the already-specified rail
  fallback. Do not edit the spec.
- The canonical implementation is `tools/fleet/`. The
  `adapters/claude/tools/fleet/` tree is a byte-parity mirror, not the source.

## Required quick graph

Perform `orient-lite → micro-plan → plan-check-lite → produce → verify-lite →
report` in this one worker. Before editing, self-check:

1. Does the change affect only Herdr-managed panes?
2. Does a normal 256-color terminal retain `_TINT_OK=True` when initialization
   succeeds?
3. Does Herdr reliably fall back to the existing rail path without changing
   foreground semantic colors?
4. Are canonical and Claude mirror files byte-identical after the change?

## Implementation scope

- Make the smallest renderer change that prevents `_TINT_OK` from becoming
  true under `HERDR_ENV=1`; reuse the existing rail+gap fallback.
- Preserve the current Herdr mouse-suppression behavior.
- Add focused deterministic tests proving both Herdr fallback and normal
  terminal tint initialization.
- Update the Claude Fleet mirror byte-for-byte for every changed canonical
  Fleet file.
- Do not modify Herdr configuration, runtime-owned state, the Fleet PRD, or
  unrelated files.
- Preserve all pre-existing user files and changes.
- Use `apply_patch` for file edits and run required Codex preflight read/write
  guards before touching guarded files.

## Verification

At minimum run:

- the focused new/changed test module;
- Fleet mirror-parity tests;
- the complete `tools/fleet/tests` unittest suite;
- `git diff --check`;
- a source assertion that ordinary-terminal tint remains enabled and
  `HERDR_ENV=1` forces the fallback.

Write a concise evidence report to the canonical shared artifact root:

`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_fleet-herdr-tint/quick_report.md`

Commit the source/test/mirror changes on branch `fleet-herdr-tint`. Do not
merge, push, or clean the worktree; the main session owns integration.

End with exactly:

```text
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_fleet-herdr-tint/quick_report.md
verdict: PASS|FAIL|BLOCKED
blocker: none|<one line>
```
