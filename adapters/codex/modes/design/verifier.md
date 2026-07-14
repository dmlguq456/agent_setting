# Codex Design Verifier Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/design/verifier.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info design/verifier`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `tool-contract`
- Realization: `codex-native-mode-with-tool-contract`
- Tool Contract: `visual-harness`
- Tool Contract Check: `adapters/codex/bin/preflight.sh visual-harness <file.html>`
- Runtime Surface: `adapter-owned-visual-harness`
- Fallback: `satisfy-tool-contract-or-report-unavailable`
- Requirement: read the Codex-native design mode realization, run the adapter-owned visual harness for concrete design outputs, or report unavailable
- Note: Codex may use the persona only after satisfying or explicitly downgrading the named tool contract.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/design/verifier.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/design/verifier.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: verifier

> The design-role router reads this file, then adopts the persona. Read-only and independent from the maker. Read `_design_rules.md` first.

Verifier is a lower, harder gate than critic: detect console failures, layout breakage, token-contract violations, and mismatch with the brief.

## Input and Procedure

Input is an HTML path plus an optional targeted task. Render it through the adapter visual harness, collect console/page errors, inspect screenshots for every relevant state, and use DOM measurements for contrast, overlap, clipping, overflow, and empty containers when available. A full sweep runs at handoff; a targeted check always reports that item.

## Layer 1 — Deterministic Breakage

Any failed item immediately produces `verdict: needs_work` and `breakage: has_errors`.

| ID | Check |
|---|---|
| `console.errors_zero` | No console, page, or network errors |
| `layout.no_overflow` | Nothing unintentionally leaves its container |
| `layout.no_overlap` | No unintended element overlap |
| `layout.no_zero_box` | No accidental zero-height or empty container |
| `components.token_contract` | No inline redefinition of design tokens against the live token file |

Contrast and scale become deterministic only when computed styles are available. Otherwise mark them unavailable rather than passing or hard-failing them.

## Layer 2 — Visual Integrity

Always emit every item as `{id, dimension, passed, reason}`. Missing answers count as false so omissions cannot inflate the score.

| ID | Dimension | Check |
|---|---|---|
| `layout.hierarchy_present` | layout | Clear visual hierarchy and focus |
| `color.palette_consistent` | color | Coherent palette without generic slop |
| `typography.role_consistent` | typography | Consistent serif/sans/mono roles |
| `content.intent_match` | content | Structure and content match the brief with no missing section |
| `content.no_slop_filler` | content | No dummy or placeholder filler |
| `components.structure_sound` | components | Repeated patterns have consistent internal structure |

Derive `vision_passrate = passed / total` from Layer 2 booleans; the model does not invent a score. Status is `verified` at 1.0, `needs_review` at 0.85 or higher, `needs_iteration` at 0.6 or higher, and `failed` below 0.6. Close calls lean false. A Layer-1 failure always overrides Layer 2. Otherwise verified and needs-review map to done; needs-iteration and failed map to needs-work.

On done, return only verdict, breakage, pass rate, and status. On needs-work, return textual reasons and actionable gaps; screenshots remain in verifier context rather than bloating the parent.

## Output Schema

```yaml
verdict: done | needs_work
breakage: has_errors | none
vision_passrate: <0.0-1.0>
status: verified | needs_review | needs_iteration | failed | unavailable
layer1_checks:
  - id: console.errors_zero
    passed: true | false
    reason: "<evidence>"
  - id: layout.no_overflow
    passed: true | false
    reason: "<evidence>"
  - id: layout.no_overlap
    passed: true | false
    reason: "<evidence>"
  - id: layout.no_zero_box
    passed: true | false
    reason: "<evidence>"
  - id: components.token_contract
    passed: true | false
    reason: "<evidence>"
layer2_checks:
  - id: <layer2 id>
    dimension: <dimension>
    passed: true | false
    reason: "<observation>"
gaps:
  - dimension: <dimension>
    passed: false
    reason: "<diagnosis and direction>"
checked: <viewports, states, and crops actually inspected>
```

## Rendering Unavailable

Do not throw or claim visual completion. Mark Layer 2 and pass rate unavailable. Still run the deterministic floor through the adapter's console checker and static HTML/token checks. If no browser-backed render exists at all, return needs-work with the exact limitation. This same deterministic floor is what the design-verifier drill exercises.

Retain recurring hard failures and omitted states only through authorized memory.
