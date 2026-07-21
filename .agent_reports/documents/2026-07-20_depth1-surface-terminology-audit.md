# Depth-1 / surface terminology audit

Date: 2026-07-20  
Reviewed: `7094c92b`, `c95ed391`, `6b3a34bc` against local `origin/main` `6b323f33`  
Verdict: **FAIL — changes requested**

The registered-headless/native-subagent distinction is directionally correct, and the branch applies it consistently across many prose projections. It is not yet safe to merge: executable routing still permits the forbidden quick/native combination, Claude's team/session terminology is misstated, and §0.2a introduces a prose-only multi-route DAG that conflicts with the existing semantic-primary and ownership contracts.

## Findings

### 1. Major — quick routes can still compile as native subagents

`core/CONVENTIONS.md:37`, `core/OPERATIONS.md:86,121`, and `adapters/codex/AGENTS.md:99` now require quick depth-1 owners to be registered headless sessions, never runtime-native subagents. The machine contract does not encode that rule:

- `capabilities/topologies.json:6,19,31` globally allows `native-subagent`, while each quick recipe records only `owner_depth/max_depth/topology/write_scope` and no allowed transport.
- `utilities/capability-route.py:182-219` copies the caller's unvalidated `transport` into direct/quick nodes. The registry transport vocabulary is not checked.
- Reproduction completed successfully:

  ```text
  capability-route.py compile ... --intensity quick --transport native-subagent
  => effective_intensity=quick, owner_depth=1, node.transport=["native-subagent"]

  capability-route.py compile ... --intensity quick --transport arbitrary-runtime
  => node.transport=["arbitrary-runtime"]
  ```

Current Codex documentation uses `agents.max_depth` for **native subagent nesting** (root thread starts at 0; the default 1 permits direct children). Therefore bare `depth`/`max_depth` in the Codex projection is collision-prone even if the portable meaning is intended to be different. Qualify it as `dispatch_depth`/`max_dispatch_depth` in portable and adapter prose, and make quick transport `headless` fail-closed in the topology/compiler. The local `preflight.sh subagent-info --check` confirms `codex-native-subagents` is a separate runtime surface but does not expose or validate the effective `agents.max_depth` value.

Official evidence: [Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md) and the current [Codex manual](https://developers.openai.com/codex/codex-manual.md).

### 2. Major — Claude “team agent” is incorrectly relabeled as a subagent

`core/OPERATIONS.md:120` changes “Light team delegation” to “open a team agent — a runtime-native subagent”. Claude Code's current surface model explicitly distinguishes them: subagents run within one session and report to the caller, while agent-team teammates are separate, full Claude Code sessions with peer communication. A teammate is not a subagent.

This matters because the patch is intended to define which restrictions and depth rules apply to which surface. Use three explicit nouns: Claude subagent, Claude agent-team teammate/session, and registered headless worker session. Do not group the first two under “runtime-native subagent”.

Official evidence: [Claude subagents](https://code.claude.com/docs/en/sub-agents), [Claude agent teams](https://code.claude.com/docs/en/agent-teams), and [parallel-agent surface comparison](https://code.claude.com/docs/en/agents).

### 3. Major — §0.2a makes semantic-primary routing internally contradictory

`core/WORKFLOW.md:128-157` calls spec+lab and design+code “co-primary”. Existing canonical clauses still require a singular semantic primary:

- §0.2 rule 3 (`:106-108`) says `autopilot-spec` is a secondary sync step and never replaces the execution primary.
- `capabilities/autopilot-spec.md:106-108` repeats that spec changes are sync-only relative to lab/code execution.
- §0.3 (`core/WORKFLOW.md:165`) asks for one semantic primary; §0.4's fixed route field (`:195`) and reconfirmation rule (`:220`) name one primary capability.
- The work-nature map (`:273`) still says multi-row requests resolve the primary only through §0.2.

The new text simultaneously presents spec as part of a co-primary example and as an asymmetric prerequisite/sync target (`:143-146`). That leaves two valid readings for the same request. Preserve one semantic execution primary and describe spec as an ordered secondary prerequisite/sync route; reserve composition for multiple genuinely independent execution owners, if that concept is retained.

### 4. Major — the claimed composition DAG has no durable contract

`core/WORKFLOW.md:136-154` requires nodes, dependency edges, bounded concurrency, one confirmation, and disjoint ownership, but deliberately leaves the single-capability compiler unchanged. `utilities/capability-route.py:182-248,390-410` accepts exactly one capability and emits one route ID. `capabilities/topologies.json` and `tools/capability_topology.py` validate dependencies and scope overlap only inside one recipe.

There is consequently no stable composition ID, no confirmation binding to all child route hashes, no cross-route edge or write-scope validation, and no deterministic resume/harvest state for the overall plan. A main-session interruption can recover individual routes but not prove which set formed the approved DAG or which successor became eligible. Either add a small immutable composition envelope (child route hashes, edges, shared approval/scope, cross-route overlap check, completion/join state) or keep the established single-primary route plus ordered secondaries model.

### 5. Major — design/code “disjoint ownership” is asserted, not true by contract

The new-screen example at `core/WORKFLOW.md:129-131,151` launches design and code owners. Yet `core/WORKFLOW.md:270` says substantial built-app design evolution goes through `autopilot-design`, including token-contract and code updates; `capabilities/autopilot-design.md:20` includes components; and `capabilities/topologies.json:47` lets design build write `components/**`. `autopilot-code` independently owns source implementation (`capabilities/autopilot-code.md:20-27`; topology `:34`).

The pipeline lock mentioned in §0.2a serializes writes but does not resolve semantic ownership or prevent a later owner from overwriting the first. Define a hard handoff boundary (for example, design owns tokens/render/handoff only; code owns application source) and validate it across child routes before using this as a co-primary example.

### 6. Major — propagation and tests give false confidence

No test changed in the three commits. Existing checks all pass while findings 1–5 remain:

- `tools/capability_topology.test.py`: 8/8 pass, but checks only intra-recipe depth/scope.
- `utilities/capability_route.test.py`: 18/18 pass; quick checks only intensity selection (`:90-91`), not transport rejection.
- `tools/routing-contract.test.sh`: pass, but contains no §0.2a/composition assertion.
- `tools/generate.py --check`, `tools/sync-entry-skill-layer.py --check`, and `tools/check-adaptation-boundary.sh`: pass; these prove generation/parity, not the new semantics.

Propagation is also incomplete: `skills/code-plan/SKILL.md:53` and both Claude/plugin mirrors still say only “one-shot worker”, while the adjacent READMEs were updated to “registered dispatch session”. `core/WORKFLOW.md:370` likewise still says only “one depth-1 session”. Byte-identical mirrors explain why parity checks pass; they do not prove the source phrase is correct.

Add deterministic negative tests for quick + `native-subagent` and unknown transports; a terminology test that distinguishes portable dispatch depth from Codex `agents.max_depth`; routing fixtures for spec+lab and design+code precedence; and, if §0.2a remains, schema tests for composition identity, edge ordering, cross-route scope overlap, confirmation binding, and resume.

## Baseline and assurance

The branch is three commits ahead of its merge base and two commits behind local `origin/main`. The `origin/main` capability-route change validates canonical **nested evidence** transport but does not validate the direct/quick `selection.transport`, so finding 1 survives integration. No source or Git state was modified.

QA policy was `standard/general`: `1x deep reviewer + 2x fast reviewers`, `1x fast fact-checker`, assurance scope `plan-check:selected-independent-pass:final-verify`. This audit performed the assigned deep review plus official-source fact verification and deterministic local checks. No separate reviewer process ran, so the report makes no independent-pass claim; the policy's documented inline fallback was used.

Commands/results:

```text
preflight.sh qa-policy standard general                         PASS
preflight.sh subagent-info --check                              PASS (native surface confirmed)
preflight.sh headless --check --require-hook-trust <worktree>   FAIL (hook trust review needed; diagnostic only)
python3 tools/capability_topology.test.py                        PASS (8 tests)
python3 utilities/capability_route.test.py                      PASS (18 tests)
sh tools/routing-contract.test.sh                               PASS
python3 tools/generate.py --check                               PASS
python3 tools/sync-entry-skill-layer.py --check                 PASS
sh tools/check-adaptation-boundary.sh                            PASS with existing warning
```
