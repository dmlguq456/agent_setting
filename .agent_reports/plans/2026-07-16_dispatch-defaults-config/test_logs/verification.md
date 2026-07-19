# dispatch-defaults-config independent verification

- Stage: `code-test`; QA: `standard code`; worktree: `/home/Uihyeop/agent_setting-wt/dispatch-defaults-config`
- Baseline/reviewed commits: `3ebd1c77` → `efeab72e`, `7697c3b6`
- Tool contract: `verification-runner`; contract check returned `status=ok`.
- QA policy output: `quality_reviewers=1x-deep-reviewer+2x-fast-reviewers`, `fact_checker=skip-code-track`, `external_adversary=skip`, `max_round=1`, `assurance_scope=plan-check:selected-independent-pass:final-verify`.
- Source remained read-only for this stage.

## Overall verdict: FAIL

The gate is not met: the required live nested-headless probe is unsupported; all three adapter-projected selector entrypoints are broken by the missing `dispatch-defaults.py` projection; and the selector test uses its temporary config only after an initial block that still consumes the shipped default.

## 1. Selector suite and temporary fixture — FAIL

Command:

```sh
/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- sh utilities/dispatch-route.test.sh
```

Raw output:

```text
adapter=codex
runtime_surface=adapter-owned-verification-runner
tool_contract=verification-runner
command=sh
timeout=300
dispatch-route: PASS
status=ok
exit_code=0
```

The suite is green and does create `tmp=$(mktemp -d)` plus `cfg="$tmp/dispatch-defaults.yaml"`. However, source inspection shows:

```text
route() { AGENT_HOME="$tmp" "$root/utilities/dispatch-route.sh" --jobs "$jobs" "$@"; }
out=$(route --stage plan)
out=$(route --stage report)
...
cfg="$tmp/dispatch-defaults.yaml"
...
export DISPATCH_DEFAULTS_CONFIG="$cfg"
```

The first block runs before the export, so it validates/consumes `profiles/dispatch-defaults.yaml`. The new SD-66 cases use the temporary fixture, but the whole test is not isolated from the shipped default as required. The dev-log fixture-conversion claim is only partially supported.

## 2. Decision cascade and omitted behavior — PASS

Command: verification-runner around an own `mktemp` config/jobs fixture exercising each level.

Raw relevant output:

```text
CASE explicit_adapter_over_config
adapter=claude
trace.1=explicit=claude;family=none;eligibility=usage-ok
trace.2=affinity=neutral;maker_family=unknown;required=none;bias=codex
CASE family_over_config
adapter=claude
trace.1=explicit=none;family=claude;eligibility=usage-ok
CASE config_over_bias
adapter=codex
trace.2=affinity=neutral;maker_family=unknown;required=none;bias=claude
CASE bias_for_omitted_cell_codex
adapter=codex
trace.2=affinity=neutral;maker_family=unknown;required=none;bias=codex
CASE bias_for_omitted_cell_claude
adapter=claude
trace.2=affinity=neutral;maker_family=unknown;required=none;bias=claude
CASE hard_eligibility_over_config
adapter=claude
rejected.1=codex:usage-limited(unknown-reset)
fallback.1=claude:known-limit-on-codex
status=ok
exit_code=0
```

Observed effective order is explicit adapter > family > config > prior heuristic/bias, with hard eligibility veto/fallback after selection. `git diff 3ebd1c77..HEAD -- utilities/dispatch-route.sh` confirms the old heuristic/neutral block remains unchanged. Omitted registered cell `autopilot-apply.verify` follows the previous neutral/bias behavior.

## 3. Shipped SD-66 config — PASS with contract gap

Commands: `dispatch-defaults.py validate`, affinity queries for `execute/test/report/plan`, `owners`, `opencode-policy`, parsed-config inspection, topology-node inspection, and concrete-model token scan.

Raw output:

```text
dispatch-defaults: /home/Uihyeop/agent_setting-wt/dispatch-defaults-config/profiles/dispatch-defaults.yaml is valid
execute=codex
test=diverse
report=claude
plan=neutral
owners=claude,codex
opencode=relief-only
{"capabilities": {"autopilot-code": {"execute": "codex", "report": "claude", "test": "diverse"}}, "depth1_owner": ["claude", "codex"], "opencode": {"relief_only": true}, "schema_version": 1}
configured_capabilities=autopilot-code
CANONICAL AUTOPILOT-CODE NODES
plan,execute,test,report
CONCRETE MODEL/EFFORT TOKEN SCAN
none
```

The config comment contains `Target load share is roughly 1-2% of dispatched work.` Other capabilities are absent from the parsed config (comment-only scaffold). Values are limited to harness vocabulary.

Judgment: PRD `exec` → registry `execute` is sound. Using canonical `test` for reviewer intent is the least-lossy mapping because HEAD has no separate review node. A contract gap remains: PRD says `test·review=diverse`, while the topology can represent only `test`; a distinct review coordinate needs later spec/topology convergence.

## 4. Validator negative fixtures — PASS

Command: verification-runner around six independently created temporary fixtures.

Raw output:

```text
CASE unknown-cap
exit=65
... unknown capability: 'autopilot-nonexistent'
CASE unknown-stage
exit=65
... unknown stage 'exec' for capability 'autopilot-code' (canonical node ids: ['execute', 'plan', 'report', 'test'])
CASE out-of-vocabulary
exit=65
... invalid affinity value for autopilot-code.execute: 'banana' ...
CASE model-like
exit=65
... invalid affinity value for autopilot-code.execute: 'gpt-5.4-mini' ... model/effort values are never allowed here
CASE malformed-owner
exit=65
... depth1_owner must be a non-empty list of concrete harnesses
CASE bad-opencode
exit=65
... opencode.relief_only must be exactly true (relief-only policy)
status=ok
exit_code=0
```

## 5. POSIX sh + Python 3, no yq dependency — PASS

```text
$ sh -n utilities/dispatch-route.sh
PASS
$ dash -n utilities/dispatch-route.sh
PASS
$ python3 <ast.parse/import inspection>
imports=json,os,sys
$ rg -n 'yq|PyYAML' profiles/dispatch-defaults.yaml utilities/dispatch-defaults.py utilities/dispatch-route.sh
utilities/dispatch-defaults.py:5:... no PyYAML/yq dependency ...
profiles/dispatch-defaults.yaml:10:# ... no PyYAML/yq dependency.
```

The only matches are comments/docstrings. The loader imports only standard-library modules and the POSIX selector invokes `python3`.

## 6. g9 static linkage repair — PASS

```text
$ bash -n loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/assert.sh
PASS
$ bash -n adapters/claude/loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/assert.sh
PASS
$ cmp <root>/assert.sh <mirror>/assert.sh
byte-identical
$ cmp <root>/prompt.md <mirror>/prompt.md
byte-identical
owner_sid = owner["meta"].get("parent_sid")
bool(owner_sid) and re.fullmatch(r"[A-Za-z0-9_.:-]+", owner_sid or "")
154:    parent_sid="drill-parent-session",
172:    parent_sid="drill-parent-session",
197:require(all(j.parent_sid == "drill-parent-session" for j in children), ...)
```

The prompt says the depth-1 owner is intentionally rebound to the real Codex thread and only its SID format is checked, while both depth-2 rows retain exact `drill-parent-session`. No g9/g10 drill was run.

## 7. `core/OPERATIONS.md` SD-16/SD-48 — PASS

Exact-string checker output:

```text
SD16_config_source=true
SD16_explicit_hard_win=true
SD16_soft_default=true
SD16_unspecified_discretionary=true
SD48_verbatim=true
SD48_current_gap=true
SD48_followup_not_current=true
```

The required sentence is present verbatim and scoped to manual wrapper starts:

```text
Supplementing a `--start` invocation with the checked evidence flags obtained from the documented nested-headless probe is the required procedure, not a gate bypass; workers proceed without re-confirmation even when a caller-provided argument list omitted those flags.
```

The following prose truthfully says `dispatch-node.py --action start` does not currently forward `route.dispatch_evidence`; automatic forwarding is a follow-up.

## 8. Required empirical record — FAIL

Exact command:

```sh
bash /home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh nested-headless --parent-harness claude --parent-transport headless --parent-sandbox default --child-harness codex --launch-authority conductor --worktree /home/Uihyeop/agent_setting-wt/dispatch-defaults-config --json
```

Raw output:

```json
{"child_harness": "codex", "failure_class": "auth-unavailable", "launch_authority": "conductor", "parent_harness": "claude", "parent_sandbox": "default", "parent_transport": "headless", "probe_source": "direct-auth-check", "probe_time": "2026-07-16T13:51:51.388580Z", "status": "unsupported"}
```

This is not the required `status=supported` codex-auth-stderr acceptance evidence.

The regression test exists with `stdout=""`, `stderr="Logged in using ChatGPT\n"`, return code 0, and expects `auth_check("codex", worktree) == (True, "")`.

Direct-file test output:

```text
$ verification-runner -- python3 -B utilities/nested_dispatch_eligibility.test.py
....
----------------------------------------------------------------------
Ran 4 tests in 0.005s
OK
status=ok
exit_code=0
```

Plan-command gap: the literal `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest utilities/nested_dispatch_eligibility.test.py` fails with `ModuleNotFoundError: No module named 'utilities.nested_dispatch_eligibility'`; direct file execution passes.

## 9. Repo guards and scope — FAIL

Adaptation command:

```sh
/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- bash tools/check-adaptation-boundary.sh
```

Raw failures:

```text
FAIL: adapters/codex/tools/memory/mem.py must not reference Claude-native surfaces: CLAUDE_HOME
FAIL: adapters/opencode/tools/memory/mem.py must not reference Claude-native surfaces: CLAUDE_HOME
FAIL: no projection decision for utilities/dispatch-defaults.py (must be classified projected or deferred)
FAIL: no projection decision for utilities/dispatch-defaults.py (must be classified projected or deferred)
FAIL: adapters/claude/utilities/dispatch-defaults.py is missing
```

The memory failures are outside the reviewed commits. The new utility projection failures are caused by this change and are material.

Independent adapter-surface command: invoke `adapters/{claude,codex,opencode}/utilities/dispatch-route.sh` with a temporary jobs file.

```text
CASE adapter-projected-claude-selector
exit=64
python3: can't open file '.../adapters/claude/utilities/dispatch-defaults.py': [Errno 2] No such file or directory
CASE adapter-projected-codex-selector
exit=64
python3: can't open file '.../adapters/codex/utilities/dispatch-defaults.py': [Errno 2] No such file or directory
CASE adapter-projected-opencode-selector
exit=64
python3: can't open file '.../adapters/opencode/utilities/dispatch-defaults.py': [Errno 2] No such file or directory
status=failed
exit_code=1
```

Each adapter selector is a symlink to the root script. The script resolves the new helper relative to the invocation path, so absent adjacent projections break all adapter surfaces. The root-only selector test misses this caller-facing regression.

Portable guard command `verification-runner -- bash hooks/portable-guards.test.sh` also returned nonzero at an unrelated, unchanged assertion:

```text
BAD codex dispatch wrapper should not trust invalid AGENT_HOME for default registry
```

Scope evidence:

```text
$ git diff --check 3ebd1c77..HEAD
PASS
$ git status --short
clean
$ git status --short -- .agent_reports .claude_reports
clean-or-absent
```

`git diff --name-status 3ebd1c77..HEAD` contains only the nine planned files: core operations, both g9 root/mirror pairs, the profile, loader, selector, and selector test. No source scope violation was observed. This stage did not merge, push, clean worktrees, execute drills, or edit the worktree report snapshot.

## Unsupported or incomplete implementation claims

- Root selector wiring passes, but the dev log did not account for the broken adapter-projected selector surfaces.
- The “temporary fixture config” conversion is incomplete for the initial test block.
- The adaptation-boundary projection contract for the new utility is unmet.
- The dev log correctly warned that its exploratory probe was unsupported; the independent required probe remains unsupported.

## Handoff

FAIL — live nested-headless support is absent; adapter-projected selectors are broken/missing the helper projection; and full temporary-config isolation is incomplete.
