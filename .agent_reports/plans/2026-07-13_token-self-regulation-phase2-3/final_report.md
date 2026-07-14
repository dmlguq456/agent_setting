# Final Report — Token Self-Regulation Phase 2/3

Verdict: `within-spec / READY_FOR_INTEGRATION`. Phase 2 accounting and the
production-disabled Phase 3 candidate/evaluator are implemented. Phase 1
canonical output is preserved, production dynamic behavior is absent, and
adoption remains `pending_user_decision`.

## Final evidence

- AST parse: 8 Python files passed.
- Phase 2 focused: 21/21; Phase 3 focused: 10/10.
- Fleet discovery: 221/221.
- Portable guards: `PASS=344 FAIL=0` in a collision-free isolated run.
- Adaptation negative guard and boundary check: passed; baseline restored.
- Manifest, repository doctor, diff check, production-dynamic absence: passed.
- Canonical/Claude mirrors: 9/9 byte-identical; Codex symlink and OpenCode
  defer boundary passed.
- Frozen candidate code SHA-256:
  `11288b737241598dcf585eb762cfc033f3cbcca70eee6ff583cb6065f6de3606`.
- Read-only independent review initially found five gaps; duplicate workload
  reuse, spawn-error accounting, raw CLI session id, impossible directive
  accounting/provenance, and schema drift were fixed. Re-review: `PASS`,
  no blocking/high/medium findings.

## Ponytail integration decision

Kept: exact-session pressure awareness, transition-only concise directives,
exact inserted-byte and monotonic counter accounting, and deterministic
offline forecast evaluation.

Excluded: repeated prompt tax, raw/contentful telemetry, heuristic token or
billing/savings claims, input pruning, model/effort/intensity/dispatch/QA or
safety downshift, online/RL adaptation, and automatic production adoption.

## Remaining boundary

The 30 fixture triplets are synthetic and non-evidentiary. No real paired
`n>=30` experiment was run, so Phase 3 adoption is still blocked on real
evidence, an explicit user decision, and a later spec/code cycle. OpenCode
automatic Phase 2 accounting and the Phase 3 CLI remain deferred. Runtime
`config.toml` was not modified.

PIPELINE_REPORT_READY
