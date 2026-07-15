# Final verification

Verdict: **PASS** — v11 source is merged to main and all selected syntax,
functional, sibling-adapter, integration, and behavioral checks passed.

## Target

- Plan: `.agent_reports/plans/2026-07-15_stage-dispatch-v11/plan.md`
- Source commit: `298bc043`; merge commit: `7c293fd6`
- Scope: 38 source/projection/test files implementing SD-48~50 and O1/SD-15.

## Graduated levels

1. Syntax/import: `py_compile`, `sh -n`, and `git diff --check` — PASS.
2. Functional units:
   - route compiler 9/9;
   - dispatch contract 4/4;
   - three-adapter v11 fixture 1/1 (three harness subtests);
   - ordered fallback 3/3;
   - worker route guard 3/3;
   - spec transaction 2/2 — PASS.
3. Adapter and behavioral regression:
   - shared liveness including Codex PID/start-tick and PID-less JSONL cases — PASS;
   - Claude/Codex/OpenCode SD-15 suites — PASS;
   - Claude/Codex/OpenCode SD-45 suites — PASS.
4. Integration:
   - `tools/check-adaptation-boundary.sh` — PASS;
   - `python3 tools/build-manifest.py --check` — PASS;
   - `python3 tools/capability_topology.test.py` — 8/8 PASS;
   - `hooks/portable-guards.test.sh` — `PASS=359 FAIL=0`.
5. Main runtime observation:
   - root Codex headless projection — supported;
   - Codex headless/workspace-write → Codex conductor nested tuple — structured
     `unsupported`, exit 69, `network-operation-not-permitted`;
   - the corresponding ancestor-broker tuple — supported, exit 0.

No independent QA agent was invoked; this is adapter verification-runner
evidence under the `qa/test` contract.
