# Independent test report — selector-paths

- Stage: \`code-test\`
- Worktree: \`/home/Uihyeop/agent_setting-wt/selector-paths\`
- Branch / HEAD: \`selector-paths\` / \`35d60fc1cd55e57ec15ea434b34a30730fe809e5\`
- Target: committed real-path resolution in \`utilities/dispatch-route.sh\`
- Source edits during this stage: none

## Runtime and assurance

\`mode-info qa/test\` reported the Codex-native \`verification-runner\` tool
contract. Availability checks succeeded for \`sh\` and \`dash\`; executable
verification commands below ran through \`preflight.sh verification-runner\`.

\`preflight.sh qa-policy standard code\` reported:

\`\`\`text
qa_level=standard
qa_track=code
quality_reviewers=1x-deep-reviewer+2x-fast-reviewers
fact_checker=skip-code-track
external_adversary=skip
max_round=1
assurance_scope=plan-check:selected-independent-pass:final-verify
independent_delegation_policy=claim-only-if-separate-codex-agent-headless-or-external-pass-ran
fallback=report-inline-review-if-independent-agent-unavailable
\`\`\`

This is the independent depth-2 \`code-test\` stage pass. Artifact write
preflight emitted the anticipated stale spec-read-marker warning. Per the
assignment, \`test_logs/\` is plain evidence and that warning is non-blocking.

## Results

### 1. POSIX syntax — PASS

\`\`\`text
sh -n utilities/dispatch-route.sh                         exit 0
dash -n utilities/dispatch-route.sh                       exit 0
sh -n utilities/dispatch-route.test.sh                    exit 0
dash -n utilities/dispatch-route.test.sh                  exit 0
\`\`\`

Each verifier result included \`status=ok\` and \`exit_code=0\`.

### 2. Focused suite — PASS

\`\`\`text
$ sh utilities/dispatch-route.test.sh
dispatch-route: PASS
status=ok
exit_code=0
\`\`\`

### 3. Manual adapter projections — PASS

The test-stage command was run through each of
\`adapters/{claude,codex,opencode}/utilities/dispatch-route.sh\` with
\`--stage test --capability autopilot-code --maker-family gpt\`. Each exited 0
and emitted:

\`\`\`text
status=eligible
adapter=claude
family=claude
role=deep reviewer
exact_model_id=opus
\`\`\`

The projected plan-stage command emitted:

\`\`\`text
status=eligible
adapter=codex
family=gpt
role=deep maker
exact_model_id=gpt-5.6-sol
exit_code=0
\`\`\`

No projection produced a helper \`not found\` error; every result included an
\`adapter=\` line.

### 4. Adaptation boundary — PASS

The requested cleanup first removed generated adapter \`__pycache__\`
directories.

\`\`\`text
$ bash tools/check-adaptation-boundary.sh
WARN: 103 concrete Claude/model references remain in portable areas.
      This is allowed only where documented as adapter mapping, compat-reference, or compat-passthrough.
OK: adaptation boundary checks passed
status=ok
exit_code=0
\`\`\`

### 5. Regression suites

PASS:

\`\`\`text
python3 utilities/dispatch_contract.test.py
Ran 10 tests in 0.421s
OK

python3 utilities/dispatch_node.test.py
Ran 17 tests in 0.008s
OK

bash adapters/claude/bin/dispatch-headless.sd15.test.sh
— dispatch-headless SD-15 conformance: PASS

bash adapters/codex/bin/dispatch-headless.sd15.test.sh
— codex dispatch-headless SD-15 conformance: PASS

bash adapters/opencode/bin/dispatch-headless.sd15.test.sh
— opencode dispatch-headless SD-15 conformance: PASS
\`\`\`

The three sd45 commands each reproduced exactly one known failure:

\`\`\`text
claude:   test_route_consumer_and_missing_evidence_refusal
          AssertionError: 73 != 0; Ran 9 tests; failures=1
codex:    test_route_consumer_and_scope_refusal
          AssertionError: 73 != 0; Ran 9 tests; failures=1
opencode: test_route_consumer_and_capability_reselection_refusal
          AssertionError: 73 != 0; Ran 9 tests; failures=1
\`\`\`

Classification: **pre-existing, not a selector-paths regression**.

### 6. Baseline reproduction — PASS (claim confirmed)

The worktree was clean at committed HEAD \`35d60fc1\`. The requested
\`git stash push\` was attempted, but Git created no stash because there were
no source changes to save. A detached checkout was blocked by managed
read-only worktree metadata (\`index.lock: Read-only file system\`). The parent
commit was therefore exported with \`git archive HEAD^\` to an isolated
temporary tree, preserving the source-read-only constraint.

Baseline commit:
\`321792e52cbc26ab4c3d5f59de9e26a4f4577098\`.

\`\`\`text
$ python3 adapters/claude/bin/dispatch-headless.sd45.test.py
FAIL: test_route_consumer_and_missing_evidence_refusal
AssertionError: 73 != 0
Ran 9 tests in 0.330s
FAILED (failures=1)
exit_code=1
\`\`\`

The baseline failure name, assertion, return code 73, and one-failure count
exactly match the selector-paths HEAD run. \`git stash pop\` was attempted and
reported \`No stash entries found\`; HEAD remained \`35d60fc1\` and
\`git status --short\` remained empty. The temporary export and regenerated
adapter \`__pycache__\` directories were removed.

## Final verdict

**PASS.** Syntax, focused behavior, all projected-path observations, boundary
guard, dispatch contract/node suites, and all sd15 suites passed. Independent
parent-commit reproduction proves the three sd45 failures pre-existed this
fix. The assigned worktree remains clean.

artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_selector-paths/test_logs/test_report.md
verdict: PASS
blocker: none
