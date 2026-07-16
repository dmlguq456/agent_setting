# Pipeline summary

- code-plan: root cause isolated to synthetic depth-1 parent identity; plan
  checked against ambiguous-cwd safety and depth-2 broker ownership.
- code-execute: added runtime parent binding plus wrapper and Fleet regressions.
- code-test: focused tests, mirror parity, syntax, diff, and no-write dry-run pass;
  wider suite has the same six pre-existing failures as `main`.
- code-report: source commit `5ecff386`, main merge `faad4c87`, integrated
  verification, runtime projection check, and delivery record completed.

Verdict: PASS. The Fleet orphan regression is fixed at the Codex depth-1
registration boundary without changing native fallback or depth-2 broker logic.
