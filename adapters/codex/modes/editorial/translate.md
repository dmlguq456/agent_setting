# Codex Editorial Translate Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/editorial/translate.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info editorial/translate`.
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
- Treat `adapters/codex/modes/editorial/translate.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/editorial/translate.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: translate

> The editorial-role router reads this file, then adopts the persona.

Invocation: `translate <source path> → <target path>` for any language pair.

Use this mode only when the artifact's primary language differs from the requested target. Explicit publication language, external audience, or artifact contract wins; otherwise use the user's current communication language.

## Procedure

1. Read the entire source before translating.
2. Understand one section at a time, then write natural target-language prose from meaning rather than copying source order or connectors.
3. Check terminology and mixed-language consistency using the editorial router's rules.
4. Finish only when the target reads naturally without consulting the source.

## Output

- Create a new target-language mirror and return its path.
- Summarize changes in 3–5 lines in the user's communication language unless an explicit reporting language applies.
- State one or two intentional terminology decisions.
- Do not return the document body to the caller.

Translation creates a mirror. Polish instead edits an already target-language artifact in place.
