# Plan: Context Recovery and Spectrogram Report QA

spec-significance: SPEC-SIGNIFICANT — routing, report metadata, and completion
verification change across portable sources and three adapters.

## Trace Matrix

| Requirement | Canonical/runtime files | Verification |
|---|---|---|
| 1–3 context recovery | `core/WORKFLOW.md`, `core/MEMORY.md`, `capabilities/analyze-project.md` | projection test: targeted recall, `show <id>`, root order, precedence, no orientation trigger |
| 4–6 band/metadata gate | `core/CONVENTIONS.md`, `roles/modes/material/figure-gen.md`, `tools/figure-semantic-verify.py`, JSON schema | positive 48 kHz fixture; 1 kHz, missing/wrong metadata, unequal-scale negatives |
| 7 claim gate | verifier + schema | Markdown-wrap normalization, stable ID, unregistered/unsupported claim negatives |
| 8 visual review | verifier + figure mode | actual PNG/hash, missing/stale/negative review fixtures plus recorded manual inspection |
| 9 low-band regression | verifier unit/integration test | metric-only change leaves figure manifest at 0–24 kHz and still passes |
| 10 projections | Claude mode, Codex generated mode/Skill, OpenCode generated Skill/command and wrapper | generator check, adapter mode/tool checks, adaptation boundary |

## Execution

1. Update the narrow read-only-orientation exception in core: agent-chosen
   recall, full-body lookup, artifact/spec/source order, and drift precedence.
2. Define the versioned manifest schema, explicit figure/panel scale evidence,
   normalized closed-type claims, and hash-bound visual review.
3. Implement a fail-closed CLI with exit 0 on pass, 2 on semantic failure, 64
   on usage, and 66 on missing/unreadable input.
4. Synchronize the portable contract to Claude Code, Codex, and OpenCode while
   retaining each adapter's documented fallback and local realization.
5. Run positive and negative unit/integration fixtures, visually inspect one
   generated PNG, record the evidence, then run all projection and adapter
   invariant checks.
