# Fleet post-unit migration — verification evidence

Target: `main...a4f7f040`, 29 source/test/doc files across the three dispatch wrappers, canonical Fleet, Claude Fleet mirror, and memory documentation.

## Graduated verification

1. **Syntax — PASS**: six changed wrapper/test Python files compiled with `compile(...)` without bytecode output.
2. **Import/smoke — PASS**: the Fleet test package imported through unittest discovery; real `fleet.py --json` cold-start returned the expected top-level schema.
3. **Behavioral CLI — PASS**: an isolated current-contract jobs.log fixture produced `unit=code-execute` through the public `fleet.py --json` surface.
4. **Focused functional — PASS**: dispatch, route, F-15 rows, memory, subagents, v20 contract, and mirror parity — 225 tests.
5. **Integration — PASS**: adapter-owned verification runner executed the canonical Fleet suite after the final rebase — 744/744 tests.
6. **Wrapper conformance — PASS**: Codex 16/16, Claude 14/14, OpenCode 9/9 through the adapter-owned verification runner.
7. **Projection/boundary — PASS**: canonical↔Claude `diff -qr`, `git diff --check`, and adaptation-boundary checks passed. The boundary checker retained its documented warning for 127 compatibility references.

One existing ResourceWarning in `test_f27_control.py:521` remains non-fatal and unrelated to this change.

## Checked residuals

- `hooks/portable-guards.test.sh` has one current-main red outside the Fleet diff: its Claude `fast implementer` fixture still expects `effort=medium`, while the newly landed model policy resolves it to `high`. The Fleet commit changes only unit emission in that wrapper path.
- Runtime projection links and hook trust pass, but profile activation remains failed/stale for the user-owned `builder` profile. No runtime projection or config mutation was authorized.
- Registered Codex headless strict preflight therefore remained unavailable; assurance used the checked native-owner fallback plus independent audits and the evidence above.

Verdict: **PASS for the Fleet post-unit migration scope; two external current-runtime/base-policy residuals are explicitly not claimed as fixed.**
