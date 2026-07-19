# Evidence autobind — independent test report

## Target and assurance

- Worktree: `/home/Uihyeop/agent_setting-wt/evidence-autobind`
- Diff: `5972a61d..1685cd3d` (`HEAD=1685cd3d4cffb9129abc4b8c89b4558da241b58b`)
- Changed surface: the three adapter wrappers and SD-45 tests, `utilities/dispatch-node.py`, and new `utilities/dispatch_node.test.py`; no uncommitted worktree changes were present.
- Mode/tool contract: Codex `qa/test`, `verification-runner`; contract check passed and all executable verification below ran through the adapter-owned runner.
- QA policy: `standard code` reported `quality_reviewers=1x-deep-reviewer+2x-fast-reviewers`, `fact_checker=skip-code-track`, `external_adversary=skip`, `max_round=1`, assurance `plan-check:selected-independent-pass:final-verify`. This depth-2 stage did not dispatch reviewers; this report is the independently dispatched test stage.

## Command log

All commands ran from the task worktree unless a `/tmp` base-copy path is stated.

| Command | Real verdict |
|---|---|
| `git status --short --branch` | PASS — clean branch, `evidence-autobind...origin/main [ahead 1, behind 7]` |
| `git rev-parse HEAD` | PASS — `1685cd3d4cffb9129abc4b8c89b4558da241b58b` |
| `git diff --name-status 5972a61d..HEAD` | PASS — exactly 8 expected changed files |
| `python3 -m py_compile utilities/dispatch-node.py adapters/claude/bin/dispatch-headless.py adapters/codex/bin/dispatch-headless.py adapters/opencode/bin/dispatch-headless.py utilities/dispatch_node.test.py adapters/claude/bin/dispatch-headless.sd45.test.py adapters/codex/bin/dispatch-headless.sd45.test.py adapters/opencode/bin/dispatch-headless.sd45.test.py` | PASS |
| `python3 utilities/dispatch_node.test.py` | PASS — 17 tests |
| `python3 utilities/dispatch_contract.test.py` | PASS — 10 tests |
| `bash adapters/claude/bin/dispatch-headless.sd15.test.sh` | PASS — 5 checks |
| `bash adapters/codex/bin/dispatch-headless.sd15.test.sh` | PASS — 8 checks |
| `bash adapters/opencode/bin/dispatch-headless.sd15.test.sh` | PASS — 7 checks |
| `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` with inherited `AGENT_DISPATCH_JOBS` | ENVIRONMENT FAIL — 1 of 9 failed, wrapper rc 73 |
| `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` with inherited `AGENT_DISPATCH_JOBS` | ENVIRONMENT FAIL — 1 of 9 failed, wrapper rc 73 |
| `python3 adapters/opencode/bin/dispatch-headless.sd45.test.py` with inherited `AGENT_DISPATCH_JOBS` | ENVIRONMENT FAIL — 1 of 9 failed, wrapper rc 73 |
| `env -u AGENT_DISPATCH_JOBS python3 adapters/claude/bin/dispatch-headless.sd45.test.py` | PASS — 9 tests |
| `env -u AGENT_DISPATCH_JOBS python3 adapters/codex/bin/dispatch-headless.sd45.test.py` | PASS — 9 tests |
| `env -u AGENT_DISPATCH_JOBS python3 adapters/opencode/bin/dispatch-headless.sd45.test.py` | PASS — 9 tests |
| `python3 utilities/stage_dispatch_fallback.test.py` | PASS — 7 tests |
| `python3 utilities/nested_dispatch_eligibility.test.py` | PASS — 4 tests |
| `bash utilities/dispatch-route.test.sh` | PASS |
| direct `validate_nested_eligibility` assertions for checked `unknown` and missing source | PASS — preserved `nested-child-spawn-unknown` and `nested-eligibility-evidence-missing` |
| `git diff --exit-code 5972a61d..HEAD -- loops/drill/cases_growing/g10_claude_opencode_depth2_start spec` | PASS — both forbidden trees untouched by the committed diff |
| `git diff --check 5972a61d..HEAD` | PASS |
| adversarial helper assertion: JSON `status=supported` with probe `returncode=69`, run once per Claude/Codex/OpenCode wrapper | FAIL in all 3 — each bound `nested_eligibility=supported` |
| adversarial dispatch-node assertion: record has empty `failure_class`, caller supplies `--eligibility-failure-class forged` | FAIL — no `DispatchNodeError`; conflicting explicit value was preserved |
| parser/helper assertion: explicit `--nested-eligibility unknown` versus omitted option | FAIL — parser states are identical and a successful internal probe overwrote explicit `unknown` with `supported` |

## `AGENT_DISPATCH_JOBS` deviation reproduction

The execute-log deviation is confirmed as pre-existing and environment-shaped.

- `printenv AGENT_DISPATCH_JOBS` returned `/home/Uihyeop/agent_setting/.dispatch/jobs.log` in this depth-2 worker.
- On current HEAD, each SD-45 suite's one subprocess/registry fixture failed with rc 73 while that inherited registry was present, and all three complete 9-test suites passed when the variable was unset.
- I created a read-only source copy from `git archive 5972a61d` under `/tmp` without changing the branch. On the base commit, each original one-test SD-45 suite failed identically with rc 73 under the inherited variable and passed when it was unset.
- Therefore this rc-73 result is not introduced by `1685cd3d`. It is recorded as an environment failure, not the implementation defect driving the overall verdict.

## Gate-weakening audit

Result: **FAIL**.

What remains intact:

- `validate_nested_eligibility` still emits `nested-eligibility-evidence-missing` for absent/unknown identity/source and `nested-child-spawn-unknown|unsupported` for checked non-supported status (`utilities/dispatch_contract.py:206-238`).
- Identity-mismatched JSON and non-JSON output leave status unknown in all wrappers; the new SD-45 cases pass.
- For ordinary missing/unknown/unsupported/malformed outcomes, wrapper control flow returns from eligibility validation before route validation, registry resolution/claim, or `Popen`. The claim/spawn sites remain later: Claude `dispatch-headless.py:779-791` before `:857/:861`; Codex `:970-988` before `:1083/:1086`; OpenCode `:841-859` before `:908/:911`.
- Dispatch-node record/explicit conflicts for the six required tuple flags fail before wrapper invocation, and the suite covers both `--flag value` and `--flag=value` forms.

Defects:

1. **Failed probe can become supported and reach launch gates.** Each wrapper parses JSON and accepts `status=supported` without checking `subprocess.run(...).returncode`. A probe returning rc 69 with identity-matching supported JSON is therefore bound as supported; `validate_nested_eligibility` passes and later claim/spawn paths become reachable. Reproduced for all three wrappers. Locations: `adapters/claude/bin/dispatch-headless.py:662-690`, `adapters/codex/bin/dispatch-headless.py:875-903`, `adapters/opencode/bin/dispatch-headless.py:754-782`. The binding must require return-code/status consistency (supported only on successful probe completion) while still retaining checked unsupported/unknown JSON from rc 69.
2. **Explicit unknown evidence is not distinguishable from absence and is overwritten.** Parser default `unknown` plus empty source is identical to explicit `--nested-eligibility unknown`; the helper treats both as absent and may replace the caller's explicit unknown with supported. This violates the approved rule that explicit supported/unsupported/unknown/partial evidence never invokes or is overwritten by the internal probe. Locations: Claude `:158-159` and `:652-655`; Codex `:162-163` and `:865-868`; OpenCode `:183-184` and `:744-747`. Parser provenance or argv-presence tracking is required.
3. **Empty record failure-class conflict does not fail loud.** `bind_dispatch_evidence` adds `--eligibility-failure-class` to the comparison map only when the record value is non-empty. With an empty record value, a caller's explicit non-empty failure class is neither compared nor rejected. Reproduced with `--eligibility-failure-class forged`. Location: `utilities/dispatch-node.py:136-142`. The flag must always participate in conflict detection, while still being omitted from appended output when both sides are empty.

## Residual risk #3 assessment

The unconditional dispatch-node binding for every depth-2 route node regardless of `--action` is **acceptable under current route-compile invariants, not a present defect**.

For standard+ headless routes, `compile_route` requires checked dispatch evidence, builds one checked fallback chain, and copies it to every depth-2 node (`utilities/capability-route.py:197-203`). `verify_route` revalidates the evidence and requires every depth-2 node's chain to equal that checked chain (`:237-245`). Consequently, a currently valid depth-2 route node cannot omit the matching evidence merely because the requested action is dry-run or register. Binding on those actions is redundant but safe; wrappers do not launch for them. A future compiler that intentionally omits evidence for non-start actions would need a coordinated materializer change, but that shape is invalid today and the current fail-loud result is safer than silent dispatch.

## Overall verdict

**FAIL** — the mandatory regression suites pass in their valid top-level registry environment and the reported rc-73 deviation is confirmed pre-existing, but the independent gate audit found three contract defects, including a direct path that treats a failed probe's supported JSON as launchable evidence.
