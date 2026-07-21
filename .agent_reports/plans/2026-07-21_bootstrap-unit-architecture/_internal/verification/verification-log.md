# Adversarial Verification Log — architecture-spec v1 → v2

2-way cross-harness adversarial review of spec **v1**. Both legs delivered verdicts
(Codex captured via `codex exec -o`; Claude-side via subagent). Both = **FIX-NEEDED**.
Raw Codex verdict: `codex-cross-harness-verdict.md`.

## Convergence (the strongest signal)
**Both independent engines flagged the SAME deepest flaw**: v1 conflated "unit" as a
fine-grained **mode-persona** (Decisions 1-3, 9, §3 floor table) with a coarse **topology
node-worker** (Decisions 4, 7, §1 "unit projects onto a node"). Claude-side proved it:
`topologies.json` = 38 nodes → **11 `(role,kind)` pairs**; highest-floor personas
(ml-debug, plan-review, maker, critic, code-review) are **not nodes at all**. `(role,kind)`
cannot key a 25-mode floor table. → v2 §1 three-entity model (unit / team / node).

## Findings → v2 disposition (16 raised, ~10 distinct)

| Finding (leg) | Severity | v2 fix |
|---|---|---|
| Granularity: unit=mode-persona vs node-worker (both) | SEVERE | §1 rewritten: unit(fine)/team(native aggregate)/node(graph slot, mode-aware resolution); floor per-unit; risk #1 |
| Native cardinality: 1 agent per role-TEAM bundles many mode-units; per-unit model undefined (Codex) | SEVERE | Decision 2: native=team aggregation, ONE model; per-unit model = dispatch-only |
| "capability LAST" violated — persona relocation edits capability refs in Ph1-3; node.unit only Ph4 (both) | MAJOR | Decision 3 compat-symlinks; §5 dispatch runtime migration deferred; refs retire in Ph4 |
| Hot-path: shared compose()/generated overlay = stale→wrong-persona (both) | MODERATE | §5: dispatch reads authored `.md` directly, NO generated overlay on hot path; compose() = build-only logic |
| write_scope wrongly unit-owned = covert lifecycle merge (Codex) | MODERATE | Decision 7: write_scope node-owned; unit = read-only *nature* only |
| Cross-validator incomplete (Codex) | MODERATE | Decision 4 / §4: + requires.units membership + kind↔worker_type |
| Reversibility unproven — hand moves not regen-reversible (both) | MODERATE | §5: git-revert-based for hand moves, atomic phase commits |
| Phase 0 not byte-neutral — resolves sonnet/opus (both) | MINOR | §5 Ph0 reframed as drift-resolving (→sonnet, opus is failover-only) |
| QA not "most mechanical" pilot — bimodal (Codex) | MINOR | §5 Ph1 pilot = mechanical UNITS (qa/test+material/*), not qa family |
| Security bar already drifted 7 vs 8 (Claude-side) | MINOR | Decision 1: name the drift, resolve (default 8) |

## Genuinely clean (both legs, no change)
Decision 11 (dispatch syntax/lifecycle preserved), branch preservation, capability/unit
separation, security silence≠proven-safe nuance, family-floor direction, figure-semantic-
verify dual placement (verified `material/figure-gen.md:42` + `qa/test.md:18`), special-case
agents (build-manifest.py:577 alias real), "codex/opencode already the target" reframe,
guard generated-region machinery already exists (`GEN_OPEN/GEN_CLOSE`), cross-validator net-new.

## Residual gate
The v2 core model (§1) changed materially. Before Phase 0 code lands, re-run a lightweight
2-way check on the revised §1 three-entity model. This spec is a PLAN, not code — real
verification is at implementation time.
