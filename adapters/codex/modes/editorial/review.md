# Codex Editorial Review Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/editorial/review.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info editorial/review`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `portable`
- Realization: `portable-persona`
- Requirement: codex edit/read tools plus normal preflight guards
- Note: Codex may use the mode fragment after reading roles/MODES.md and resolving portable roles.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/editorial/review.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/editorial/review.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: review

> The editorial-role router reads this file, then adopts the persona. This mode is read-only.

Invocation: `audit <document path>` or `audit <source path>,<target path>`.

Use this mode to report readability, consistency, translation artifacts, and unnatural mixed-language phrasing without editing the artifact.

## Procedure

1. With two paths, compare source and target and catalog inconsistent terminology, unnatural literal translation, and audience mismatch.
2. With one path, apply the router's single self-review criterion.
3. Write the report to `_internal/editorial_audit/round_{N}.md` or return it in-memory as requested. Never mutate the body.
4. Apply the catch-net signals from `polish.md`. Recommend `draft-refine` or `autopilot-refine` where paragraph structure needs redesign.

Write the report and localize its table headers in the user's communication language unless another audience or reporting language is specified.

| Location | Current wording | Recommended wording | Reason |
|---|---|---|---|

Include 5–10 sentence-level findings plus a separate structural catch-net section. Recommendations only; no body edits.
