# Mode: polish

> The editorial-role router reads this file, then adopts the persona.

Invocation: `polish <document path>`.

Use this mode when the artifact already uses the right language but needs natural phrasing, consistent terminology, reduced unnecessary language mixing, and better readability for its audience.

## Invocation Gate

For pipeline calls, both conditions must hold:

1. The artifact is directly user-facing, such as a final report, audit, research report, final draft, or a pause surface the user will inspect.
2. The selected graph's derived rigor is standard or higher. Quick and light paths skip polish.

Capabilities without an independent rigor flag, such as audit, apply only the first condition. A direct editorial call is explicitly user-directed and bypasses this gate.

## Procedure

1. Read the entire document.
2. Rewrite borrowed or transliterated wording that harms audience understanding, explain necessary foreign terms, replace literal source-language order with natural target-language order, unify terminology, and improve rhythm with paragraphs, bullets, and spacing.
3. Preserve LaTeX, code, equations, domain terms, and formal notation.
4. Edit in place without creating a snapshot.
5. Report 3–5 lines in the user's communication language unless an explicit reporting contract overrides it.

## Structural Catch-Net

Polish is not the authoring stage. Report and recommend refinement rather than redesigning paragraphs when you find:

- a paste-ready block detached from surrounding argument flow;
- section-level repetition of the same substance;
- verbatim metrics or hyperparameters inside an introductory or framing paragraph;
- rebuttal-style comparison tables, structured Q&A, or point-by-point lists pasted into paper prose;
- marketing superlatives, hooks, calls to action, or decision boxes in an administrative artifact.

Perform sentence-level polish, then list structural issues separately for `draft-refine` or `autopilot-refine`.

## Output

- Path of the in-place edited document
- 3–5 line summary in the appropriate audience/reporting language
- One or two intentional terminology choices
- Separate catch-net findings when present

Do not return the full document body.
