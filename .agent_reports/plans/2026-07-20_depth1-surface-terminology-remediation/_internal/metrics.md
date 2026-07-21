# Cycle metrics and exceptions

## Self-hosting bootstrap exception

- route: `rt-4ddceb3e346c0941`
- immutable record: `_internal/code-route.json`
- exception: this implementation route was compiled by the pre-v20 compiler
  immediately after the v20 spec transaction, so it retains legacy `depth`,
  `owner_depth`, and legacy fallback/transport fields.
- scope: this remediation cycle only; the record is bootstrap evidence and is
  not evidence that its own schema satisfies v20.
- acceptance: after implementation, fresh direct, quick, and standard+ routes
  must be compiled by the new compiler and preserved as acceptance evidence.
- prohibition: no new or resumed legacy route may be emitted.

## QA assurance

- policy: `standard` / `code`
- assurance: `plan-check:selected-independent-pass:final-verify`
- independent review: reserved for the separate depth-2 `code-test` worker;
  no independent-review claim is made for the owner or execute stage.

