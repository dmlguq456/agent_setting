# Entry-route confirmation metrics

## Routing and topology

- capability: `autopilot-code`
- intensity: `standard`
- spec significance: `SPEC-SIGNIFICANT`
- source anchor: skill-design-refactor PRD v4, SD-17–SD-25
- execution: inline under the active runtime's no-subagent policy; no
  independent worker result is claimed
- separability note: portable policy, manifest schema, generators, generated
  projections, and conformance assertions share one invocation-class semantic
  anchor and were changed as one source-to-projection transaction
- validation isolation: the full adapter-boundary check ran in a clean detached
  test worktree so pre-existing ignored runtime bytecode caches in the primary
  checkout could not affect the result

## Static context measurements

- active Codex builder metadata: 3,205 normalized characters, 14 linked Skills,
  duplicate names 0, absolute budget 7,000
- full 27-Skill normalized metadata: 6,019 characters for Claude, Codex local,
  and OpenCode; Codex plugin 6,559 characters
- Codex generated `autopilot-code`: 134 → 46 lines; 9,146 → 2,687 characters
- Codex generated `autopilot-spec`: 128 → 46 lines; 8,458 → 2,767 characters
- Codex generated `autopilot-lab`: 123 → 46 lines; 7,766 → 2,725 characters
- invocation classes: 13 `entry-router`, 13 `parent-invoked`, 1 `model-support`

The metadata baseline was intentionally refreshed because concrete positive
triggers and exclusion boundaries add first-rung routing information. These are
static footprint measurements, not token, billing, or total-work savings.
