# Evidence autobind implementation plan

## Route and scope

- Route: `autopilot-code`, `dev/refactor`, intensity `standard`, QA `standard`, staged depth 2.
- Source pin: `5972a61df915815a71b818fec83794a913e2e23e`; the worktree HEAD matched it during planning.
- Source changes are limited to `utilities/dispatch-node.py` and the three adapter wrappers. `utilities/nested-dispatch-eligibility.py` remains the checked probe executable unless a testability-only refactor is necessary; its eligibility semantics must not change.
- Do not edit `spec/**`, `capability-route.py`, dispatch-default meanings, authorization classification, broker remnants, or `loops/drill/cases_growing/g10_claude_opencode_depth2_start/**`.
- Planning produced no source edits.

## Spec significance (verbatim from the task brief)

- spec-significance: **within-spec** — governing item: `spec/stage-dispatch/prd.md` §13.7.6
  "v15 구현 흡수: dispatch-node.py가 record dispatch_evidence의 checked tuple을 wrapper 인자로
  결정론 전달" + acceptance ③ "dispatch-node 경유 분사가 추가 인자 없이 eligibility 검증 통과".

The canonical PRD confirms §13.7.6 and acceptance item ③. The route record already has `tracked_gate_evidence.spec_read.satisfied=true` and `drift_verdict=within-spec`; no specification update is authorized or needed.

## Current behavior and invariants

- `utilities/dispatch-node.py` verifies a route and materializes node metadata, but forwards no `dispatch_evidence` fields. Trailing adapter arguments can carry manually supplied evidence.
- Each wrapper parses the tuple identity plus `--nested-eligibility` and `--eligibility-source`, then calls `validate_nested_eligibility` before route validation and before any registry claim or child launch.
- `validate_nested_eligibility` already supplies the required fail-closed outcomes: missing or unknown identity evidence at depth-2 start becomes `nested-eligibility-evidence-missing`; checked unsupported/unknown becomes `nested-child-spawn-<status>`.
- The probe emits JSON for supported and unsupported results and exits 69 unless supported. It checks target authentication/headless readiness and preserves the Codex nested-network contract.
- Existing depth-2 registry rows contain tuple fields. The implementation adds `eligibility_probe` provenance and exposes the resolved tuple in wrapper output.

## Change design

### 1. `utilities/dispatch-node.py`: deterministic record binding

Refactor the compressed `main` into small pure helpers while retaining the CLI and route verification order.

1. For depth-1 nodes and resource-runner nodes, preserve current behavior and append no evidence arguments. Calls made directly to wrappers without a route remain outside this materializer and unchanged.
2. For a depth-2 route node, inspect that node's `dispatch_fallback` entries in ascending `ordinal` order. Consider only `same-harness-headless` and `cross-harness-headless` candidates whose `child_harness` equals `--adapter`.
3. Require a candidate to be `status=supported` and to have one exact checked counterpart in top-level `route.dispatch_evidence.tuples`. Match `parent_harness`, `parent_transport`, `parent_sandbox`, `child_harness`, `launch_authority`, `status`, `probe_source`, and `failure_class`, normalizing an absent failure class to empty. Do not use `probe_time` to distinguish otherwise identical evidence. Select by node fallback ordinal; fail loudly if the first eligible ordinal is ambiguous, has no top-level counterpart, or yields conflicting counterparts.
4. Map the row to `--launch-authority`, `--parent-harness`, `--parent-transport`, `--parent-sandbox`, `--nested-eligibility`, and `--eligibility-source`. Also pass non-empty `failure_class` through `--eligibility-failure-class`.
5. Parse trailing adapter arguments in both `--flag value` and `--flag=value` forms. If a caller-supplied value equals the record, keep it and do not append a duplicate. If it differs, or duplicate explicit occurrences disagree, stop before wrapper invocation with a structured diagnostic containing reason, flag, explicit value, and record value. Never silently overwrite either side.
6. Preserve unrelated adapter arguments and their order after the optional leading `--` separator. Keep route verification and the depth-2 `--parent` requirement unchanged.

### 2. `utilities/nested-dispatch-eligibility.py`: preserve the probe contract

No behavior change is planned. Wrappers invoke this file with `sys.executable`, the resolved parent tuple, their fixed child harness, `launch_authority`, `worktree`, and `--json`. A pure JSON-row validation helper may be extracted only if direct probe tests remain unchanged; authentication, headless readiness, Codex network checks, return codes, and classification must not weaken.

### 3. `adapters/claude/bin/dispatch-headless.py`: internal Claude-target probe

- Add a helper after action/worktree/input parsing and before `validate_nested_eligibility`.
- Trigger only for `depth >= 2` plus `action == start` when neither nested-evidence option was explicitly supplied and parsed evidence is at its absent default (`unknown` plus empty source). Explicit supported, unsupported, unknown, or partial evidence never causes a probe or overwrite.
- Reuse parsed `AGENT_DISPATCH_CURRENT_*` / owner-derived parent harness, transport, sandbox, and `launch_authority`. If required parent identity is empty/unknown, skip probing and let existing validation fail closed.
- Run the JSON probe with `child_harness=claude`. Parse JSON even on exit 69 so checked unsupported is retained. Accept the row only if all returned identity fields equal the request; malformed output, execution error, or identity mismatch remains unknown and fails closed.
- Bind status, probe source, and failure class to the namespace and set `eligibility_probe=internal`. Never infer supported from process success alone.
- Include provenance and the complete tuple in successful wrapper output and the depth-2 jobs pipe. On validation failure, include them in structured failure output without claiming a row or launching a child.

### 4. `adapters/codex/bin/dispatch-headless.py`: internal Codex-target probe

Implement the same helper and ordering with `child_harness=codex`. Preserve `_bind_runtime_parent`, `CODEX_THREAD_ID`/session ownership, runtime-home projection, hook-trust checks, `AGENT_NESTED_HEADLESS_NETWORK`, and all existing start gates. The probe executes from the requested worktree and may report supported only through existing Codex auth, headless readiness, and owner-network checks.

### 5. `adapters/opencode/bin/dispatch-headless.py`: internal OpenCode-target probe

Implement the same helper and ordering with `child_harness=opencode`. Preserve OpenCode config scoping, auth/headless checks, relief/runtime behavior, and hang-on-limit handling. JSON or probe failure remains fail-closed and can never become a launchable tuple.

### 6. Symmetry and non-weakening

- Keep helper behavior and output/registry keys homomorphic; only child harness and adapter-specific runtime detection differ.
- Probe before eligibility validation, route validation, registry claim, and child spawn. Do not probe for dry-run/register, depth 1, or explicit evidence.
- Preserve the launch-authority allowlist, retired-broker rejection, and exact `nested-child-spawn-unsupported`, `nested-child-spawn-unknown`, and `nested-eligibility-evidence-missing` outcomes.
- Do not add evidence flags to the g10 drill prompt/assert fixtures. The unchanged fixture is the acceptance proof for automatic binding.

## Test design

### New or expanded cases

1. Add `utilities/dispatch_node.test.py` with fixture route records and intercepted wrapper invocation:
   - supported record tuple plus matching fallback emits all six required flags and non-empty failure class;
   - fallback ordinal and adapter select the deterministic same/cross-harness tuple;
   - equal explicit arguments pass without duplicates;
   - mismatched explicit and conflicting duplicate arguments fail before wrapper invocation and show both values;
   - missing, unsupported, ambiguous, or node/top-level-inconsistent tuples fail loudly;
   - depth-1 materialization emits no evidence and preserves adapter args.
2. Expand each adapter's `dispatch-headless.sd45.test.py` with mocked internal-probe cases:
   - absent evidence on depth-2 start binds supported JSON, marks `eligibility_probe=internal`, and passes existing validation;
   - JSON unsupported/exit 69 binds the result and fails `nested-child-spawn-unsupported` with no row or launch;
   - explicit evidence does not invoke the probe;
   - unknown parent identity and malformed or identity-mismatched JSON fail closed;
   - successful binding appears in wrapper output and the registry pipe.
3. Keep `utilities/nested_dispatch_eligibility.test.py` as the direct probe contract suite. If a helper is extracted, add cases proving JSON and exit-code semantics remain identical.

### Exact commands from the task worktree

New dispatch-node suite:

```sh
python3 utilities/dispatch_node.test.py
```

The six existing regression-suite groups:

```sh
# 1. Shared dispatch contract
python3 utilities/dispatch_contract.test.py

# 2. Wrapper SD-15 suites
bash adapters/claude/bin/dispatch-headless.sd15.test.sh
bash adapters/codex/bin/dispatch-headless.sd15.test.sh
bash adapters/opencode/bin/dispatch-headless.sd15.test.sh

# 3. Wrapper SD-45 suites
python3 adapters/claude/bin/dispatch-headless.sd45.test.py
python3 adapters/codex/bin/dispatch-headless.sd45.test.py
python3 adapters/opencode/bin/dispatch-headless.sd45.test.py

# 4. Stage fallback
python3 utilities/stage_dispatch_fallback.test.py

# 5. Direct nested eligibility probe
python3 utilities/nested_dispatch_eligibility.test.py

# 6. Dispatch route selection
bash utilities/dispatch-route.test.sh
```

Syntax/import verification for every planned changed Python file:

```sh
python3 -m py_compile utilities/dispatch-node.py utilities/nested-dispatch-eligibility.py adapters/claude/bin/dispatch-headless.py adapters/codex/bin/dispatch-headless.py adapters/opencode/bin/dispatch-headless.py utilities/dispatch_node.test.py adapters/claude/bin/dispatch-headless.sd45.test.py adapters/codex/bin/dispatch-headless.sd45.test.py adapters/opencode/bin/dispatch-headless.sd45.test.py
```

Forbidden-scope and patch checks:

```sh
git diff --exit-code -- loops/drill/cases_growing/g10_claude_opencode_depth2_start spec
git diff --check
```

The g10 drill itself is excluded from this cycle stage and remains a depth-0 post-integration verification.

## QA and handoff assurance

`preflight.sh qa-policy standard code` reported `quality_reviewers=1x-deep-reviewer+2x-fast-reviewers`, one selected plan-check pass, final verification, and no code-track fact checker/external adversary. The stage kernel forbids dispatching another worker, so no independent reviewer is claimed. An inline plan-check verified scope, fail-closed ordering, conflict handling, new cases, all six regression groups, exact commands, and the untouched g10 requirement.

Runtime warning: the first `preflight.sh read` call targeted the primary harness marker path and was denied by this worker's filesystem sandbox. Re-running it with `AGENT_HOME` bound to the task worktree succeeded before the final artifact edits. The immutable route also retains `tracked_gate_evidence.spec_read.satisfied=true`; the canonical PRD section was read directly and no spec file is edited.
