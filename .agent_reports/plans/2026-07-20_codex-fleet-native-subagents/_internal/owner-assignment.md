# Owner assignment — Codex native subagents in Fleet

Act as the depth-1 `autopilot-code` capability owner for an approved
`dev/strong` cycle.

## Working surfaces

- Source worktree:
  `/home/Uihyeop/agent_setting-wt/codex-fleet-native-subagents`
- Canonical artifact cycle:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_codex-fleet-native-subagents`
- Governing specification:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md`,
  especially F-29 and the v11 collection/display amendments.
- Portable capability:
  `/home/Uihyeop/agent_setting/capabilities/autopilot-code.md`

Use the canonical artifact root only for plan/dev/test/report records. Treat the
linked worktree's `.agent_reports` snapshot as read-only.

## Objective

Implement read-only observation of Codex native subagent threads so Fleet shows
them under their parent Codex session with the same `Session.subagents` and
horizontal-strip contract already used by Claude and OpenCode.

The current contract deliberately reports an honest Codex gap pending a state
DB/rollout probe. Close that gap from observed runtime evidence; do not guess.

## Required runtime grounding

1. Current official Codex manual:
   `https://learn.chatgpt.com/docs/agent-configuration/subagents.md`
   establishes agent threads, active/done states, `/agent`, custom-agent type,
   and parent orchestration.
2. Current official Claude reference:
   `https://code.claude.com/docs/en/sub-agents`
   is parity context only. Claude implementation remains a sibling reference.
3. Inspect current local Codex runtime state read-only:
   `$CODEX_HOME/state_*.sqlite`, `$CODEX_HOME/sessions/**/rollout-*.jsonl`, and
   the runtime records created by recent native `spawn_agent` calls. Never edit,
   migrate, vacuum, checkpoint, or copy credentials/runtime databases into the
   repository.
4. Separate runtime support, local passive projection, and remaining
   schema/platform gaps.

## Pipeline

Run the strong standard+ graph through registered stages:

`code-plan -> code-execute -> code-test -> code-report`

Use current dispatch-contract-v3 checks and `dispatch-chain`; do not replace
separable stages with unrecorded inline work. If a checked nested headless hop
fails, follow the recorded fallback chain and preserve the failure evidence.
Strong requires one risk-focused independent review, preferably around
read-only runtime-schema attribution and parent/active/done correctness.

## Implementation constraints

- Core-first: portable meaning stays in core/spec; Claude, Codex, and OpenCode
  collectors are siblings.
- Zero injection: Fleet must not write Codex sessions, transcripts, state DB,
  configuration, or caches.
- Enrichment only: subagents never create or suppress a top-level `Session`.
- Attribution must be fail-closed: ambiguous/missing parent linkage omits the
  subagent rather than attaching it to the wrong session.
- Existing `--json` remains additive and stable.
- Preserve active-vs-done semantics and the current `a`-toggle/render contract.
- Reuse existing model/render surfaces where possible. Avoid a second
  subagent schema.
- Maintain canonical `tools/fleet/` and
  `adapters/claude/tools/fleet/` byte parity where the repository currently
  requires it. Do not copy Claude runtime files into Codex adapter surfaces.
- Do not edit `$CODEX_HOME/config.toml` or any runtime-owned file.
- Use `apply_patch` for source/artifact edits and all required preflight guards.
- A Codex linked-worktree mutation stage is no-commit; leave the source diff
  for the trusted main session to commit after PASS.

## Verification

At minimum:

- focused Codex subagent collector fixtures covering parent linkage,
  agent type, active/done, malformed/ambiguous input, and tolerant absence;
- Claude/OpenCode subagent regression;
- render/JSON additive regression;
- full canonical Fleet test suite;
- canonical↔Claude mirror parity;
- `python3 tools/build-manifest.py --check`;
- `tools/check-adaptation-boundary.sh`;
- read-only live smoke against an actual Codex native subagent record, with no
  runtime mutation by Fleet.

Record exact commands and results. If the live runtime does not persist enough
parent/type/status data, stop with the honest supported subset and a checked
fallback instead of inventing inference.

## Deliverables

- `plan.md`, `checklist.md`, `dev_logs/`, `test_logs/`,
  `_internal/` reviews, and `pipeline_summary.md` in the canonical cycle.
- Source/test changes in the isolated worktree.
- Final handoff exactly:

```text
artifact: <pipeline_summary.md>
verdict: PASS|FAIL|BLOCKED
blocker: none|<one line>
```
