# Test Report

## Target

On-call memory-to-proposal promotion, exact-key recurrence, stale-context
reconciliation, Claude loop projection, and existing install/release boundaries.

## Graduated verification

| Level | Command | Result |
|---|---|---|
| Syntax | `python3 -m py_compile tools/improvement/proposals.py tools/improvement/test_proposals.py` | PASS |
| Shell syntax | `bash -n loops/oncall.sh adapters/claude/loops/oncall.sh` | PASS |
| Functional/CLI | `bash tools/improvement/proposals.test.sh` | PASS, 19 tests |
| Concurrent ingest | two simultaneous exact-key CLI collectors | PASS, one proposal and two occurrences |
| Runtime isolation | proposal durable test snapshots runtime config/plugin state | PASS, byte-stable |
| Generation | `python3 tools/generate.py --check` | PASS |
| Projection | `bash tools/generated-projections.test.sh` | PASS, 29 semantic verifier tests |
| Adaptation | `bash tools/check-adaptation-boundary.sh` | PASS, existing 51-reference warning only |
| Skill contract | `bash tools/skill-conformance/check.sh` | PASS |
| Runtime activation | `bash tools/install/runtime-activation.test.sh` | PASS |
| Extension lifecycle | `bash tools/install/extension-lifecycle.test.sh` | PASS |
| Managed release | `bash tools/install/release-lifecycle.test.sh` | PASS |
| Diff hygiene | `git diff --check` | PASS |

Commands ran through the Codex verification-runner contract. No drill or real
on-call run was executed.

## Failure and correction

The first prompt-contract assertion assumed one-line wording and failed after
Markdown wrapping; the assertion was corrected to preserve the semantic check.
Inline review then found that stale exact-key recurrence had no route to a fresh
review base. The implementation now keeps ingest non-mutating and permits a
base change only with explicit context-bound reproduction. All tests were
rerun after the correction.

## Verdict

PASS. No independent-agent QA is claimed; the standard policy's inline fallback
was used because this session did not authorize subagent delegation.
