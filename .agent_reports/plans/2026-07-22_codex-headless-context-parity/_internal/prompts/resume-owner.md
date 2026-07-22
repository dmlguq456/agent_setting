# Resume owner — Codex headless parent-context parity

You are the registered dispatch-depth-1 `autopilot-code` owner for the original
approved task only: bring the Codex registered-headless parent-facing
receipt/liveness/wait/harvest behavior to decision-relevant parity with the
local Claude sibling while preserving file-only handoff.

Use this sealed route:
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity/_internal/route-standard.json`

Worktree:
`/home/Uihyeop/agent_setting-wt/codex-headless-context-parity`

Canonical artifact directory:
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity`

Existing inputs are authoritative and must be reused:

- `baseline_comparison.md`
- `plan/plan.md`
- `plan/plan_ko.md`
- `plan/checklist.md`
- `_internal/plan_reviews/round_1.md`
- `_internal/plan_reviews/refine_round_1.md`

The first plan review failed and the completed refinement record says all four
findings were addressed. Start by dispatching a fresh registered plan-check
against the refined artifacts. Have it write a new review artifact under
`_internal/plan_reviews/` (do not overwrite the historical round-1 findings).
If it passes, dispatch the sealed route's `execute`, `impl-review`, `test`, and
`report` nodes in dependency order. If a gate fails, use the bounded correction
loop from the approved plan.

Constraints:

- Do not modify `core/**`, specifications, capability topology, intensity
  routing, Fleet UI, runtime config, credentials, or the Claude adapter.
- The Claude adapter is a read-only comparator; never borrow a Claude-native
  tool or surface to claim Codex support.
- Do not use native subagents. Use only registered headless stage workers via
  `preflight.sh dispatch-chain` and the sealed route.
- Keep the conductor thin: read verdict/status and named artifacts, not raw
  successful worker transcripts or artifact bodies unrelated to the gate.
- Source edits belong only to `code-execute`; test/review/report remain within
  their declared write scopes.
- Obey every exact `preflight.sh write` command in the refined plan before a
  file's first edit.
- Preserve unrelated worktree and primary-checkout changes. Do not commit,
  push, merge, reset, checkout, or clean the worktree; depth-0 performs final
  integration.
- Verify success, failure, and blocked cases plus no transcript/artifact-body
  sentinel leakage into parent-facing output.

Finish the full pipeline in this turn. Your final response must contain exactly:

artifact: <absolute path to final_report.md>
verdict: PASS|FAIL|BLOCKED
blocker: <none or concise enum>
