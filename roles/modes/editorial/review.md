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
