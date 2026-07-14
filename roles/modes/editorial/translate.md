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
