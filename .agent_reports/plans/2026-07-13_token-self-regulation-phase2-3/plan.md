---
status: ready_for_code_test
verdict: READY_FOR_CODE_TEST
spec_significance: within-spec
production_dynamic_absent: required
production_enabled: false
---

# Token Self-Regulation Phase 2/3 — Implementation Plan

## 1. Outcome and locked boundary

Implement component v2 exactly without changing the component spec or Phase 1 production policy:

- Phase 2 records one content-free accounting outcome for every Codex token-budget `UserPromptSubmit` lifecycle, preserves existing directive bytes and all zero paths, and exposes diagnostics only through `kv|json`.
- Phase 3 adds pure `offline-forecast-v1` replay plus a separate isolated experiment CLI/schema/evaluator. Production code must not import or activate it.
- `production_enabled` and `production_dynamic_enabled` remain false. Fixtures are synthetic tests, not experiment evidence. Maximum verdict is `eligible_for_user_review`, with `pending_user_decision`.
- Runtime-owned `$CODEX_HOME/config.toml`, credentials, transcripts, session DB, model/effort, intensity, dispatch/depth, QA, guards, safety, accessibility, and input context remain unchanged.

This is `within-spec`: `.agent_reports/spec/token-self-regulation/{prd.md,experiment_contract.md,pipeline_state.yaml}` already defines the aggregate, frozen candidate, gates, and production-disabled boundary. No spec back-jump is required.

## 2. Grounding and currentness

### Spec gate

- Flat `.agent_reports/spec/prd.md` was read/marked only for the current Codex gate; it is the unrelated Unified Memory System PRD.
- Actual component SoT was read: component `prd.md` v2, `experiment_contract.md` v1, and `pipeline_state.yaml`.
- Flat preflight does **not** model component SoTs: `hooks/spec-read-marker.sh` accepts only flat `*/.agent_reports/spec/prd.md` (or legacy), and `hooks/spec-skill-gate.sh` discovers only that path. Actual component-read evidence exists, but the flat marker is not component approval.

### Source and contract grounding

Read Phase 0–1 implementations/tests, Codex lifecycle/preflight, portable guard/boundary assertions, prior plan/checklist/metrics/review/implementation/verification/final evidence, core contracts, code capabilities, roles, and portable/Codex `dev/refactor` mode.

Phase 1 prints a canonical directive plus transport newline; the lifecycle strips it and inserts the same one-line string. That inserted string is the byte baseline and must not change.

### Runtime currentness

- Official Codex manual checked 2026-07-14: hooks are stable; `UserPromptSubmit` accepts `hookSpecificOutput.additionalContext`; matching hooks may run concurrently; input contains exact `session_id`/`cwd`; `rollout_budget` is under development/off by default. Sources: `https://learn.chatgpt.com/docs/hooks`, `https://learn.chatgpt.com/docs/config-file/config-reference` (fresh official-manual helper cache `/tmp/openai-docs-cache/codex-manual.md`).
- Local: `codex-cli 0.144.3`; hooks/multi-agent stable true; `rollout_budget`, `runtime_metrics`, `token_budget` under-development false. Runtime projection, hooks-json, and hook trust are ok.
- `codex features` rejects the read-only `--strict-config` probe itself. No native config-path claim or activation follows; exact-session rollout observation remains fallback.

## 3. Exact architecture

### 3.1 One lifecycle = one accounting event

UserPromptSubmit parent is the single accounting authority because it alone observes delivered output, timeout, and process error. The child helper never updates the aggregate.

1. `utilities/token-budget.py --format hook` keeps exact output. With private `AGENT_TOKEN_BUDGET_RESULT_PATH`, it atomically writes a transient content-free receipt: policy outcome, fixed zero reason, directive id/UTF-8 bytes, exact-session cumulative sample.
2. `userprompt-lifecycle.py` runs once, captures success/timeout/error, derives actual contribution, and records once. Timeout/nonzero/invalid receipt is one `timeout_or_error` zero, never a retry.
3. Accounting failure is silent/fail-open and cannot change output, transition state, or lifecycle success.

| Contribution | Condition | Class |
|---|---|---|
| non-empty | canonical directive delivered before timeout | emission |
| empty | validated native owner | `native` |
| empty | observed normal | `normal` |
| empty | observed tight/critical equals stored band | `same_band` |
| empty | missing/unsupported exact-session signal | `unknown` |
| empty | stale/malformed/ambiguous/decreasing signal or transition-state degradation | `degraded` |
| empty | timeout, nonzero, invalid receipt, exception | `timeout_or_error` |

Reducer enforces `hook_invocations = zero_injections + emissions` after each update.

### 3.2 Bounded content-free store

```text
${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/token-budget/accounting/
  <sha256(session-id)[:32]>.json
```

- Persist only schema v1, adapter, digest, timestamps, fixed counters, directive IDs/bytes, exact-session cumulative samples; never raw session id/prompt/response/transcript/directive body.
- Count final inserted-string bytes, excluding stdout newline, JSON escaping, wrapper metadata.
- Available non-negative totals increment sample count. First initializes first/last with delta zero. Non-decreasing adds `current-last_trusted`; decreasing retains last/delta and increments decrease; absent increments unavailable.
- No directive token estimate without exact payload tokenizer runtime/model/version provenance; field remains absent.
- Canonical JSON <=8 KiB. Under one bounded stale-safe directory lock, atomically replace and enforce <=256 JSON files and <=2 MiB, pruning oldest `last_observed_at` first (mtime only malformed fallback). Ignore temp/locks.
- Lock/scan/prune/validation/write failures degrade accounting only.
- `kv|json` read without incrementing; they are the only L2 surfaces. Hook injects no accounting explanation.

### 3.3 Isolated deterministic candidate/evaluator

Create `tools/fleet/token_experiment.py` plus separate `utilities/token-budget-experiment.py`. Production hook/CLI/preflight must not import it.

- Decisions use only `context_used_pct`, last up to 3 non-negative increments, current static band, target latches. Other telemetry is report/integrity only.
- `step=median(last up to 3)`; `forecast=min(99,current+step)`.
- Unknown/degraded/insufficient disables **early** emission but keeps static-equivalent transition.
- Select only canonical `tight-v1`/`critical-v1`; early emission suppresses later observed duplicate; reopen only when valid observed+forecast are below target.
- Frozen manifest owns thresholds/history/unknown behavior/IDs/code+fixture hashes/bootstrap/tolerance/minimum and `production_enabled:false`.
- Isolated control contributes zero bytes, static reproduces the exact v1 70/85 transition-only policy, and dynamic is the frozen candidate using only existing directives; all other workload/runtime/config fields must match.
- Validate workload/arm schemas; require exactly one control/static/dynamic per experiment+workload; fixed-priority exclusion, no imputation/reuse/partial pair.
- Fixed exclusions are exactly `missing_arm`, `pairing_fingerprint_mismatch`, `counter_unknown_or_degraded`, `counter_decreased`, `required_output_missing`, `runner_failure`, `rubric_missing_or_changed`, and `manifest_changed`.
- Gate order: n>=30 and multi-stratum n>=10 each; integrity; required+safety 100% and hard regression 0; both quality LCBs >=-0.02; both control/static observed-delta LCBs >0.
- Paired workload bootstrap: 10,000, `random.Random(20260713)`, paired mean, documented deterministic lower quantile.
- Report exact bytes/emissions separately; token label is `observed session-token delta difference (non-billing)`; no conversions.
- Canonical output is byte-identical for same sorted input. Verdict is only insufficient/reject/eligible; adoption pending and production false.
- Fixtures are synthetic/non-evidentiary and cannot update adoption state.

## 4. Executable file-by-file steps

### Step 1 — core-first + Phase 2 primitives

1. `core/CONVENTIONS.md`: add v2 separation/no-estimate/bounded content-free/isolation invariant; do not alter intensity/dispatch/QA.
2. `core/ADAPTATION_INVENTORY.md`: record Codex support, Claude mirror-only/no automatic accounting, explicit OpenCode defer.
3. `tools/fleet/token_budget.py`: add stable directive IDs and one canonical text map; preserve bytes/parser/bands.
4. `tools/fleet/token_accounting.py` (new): schema, reducer, digest/path, canonical read, bounded lock, atomic replace, prune, diagnostics.
5. `utilities/token-budget.py`: canonical map, private receipt, zero mapping, read-only accounting in `kv|json`; hook stdout unchanged.

Gate: focused Phase 0–2 tests cover bytes, all reasons, identity, samples, forbidden content, concurrency, bounds.

### Step 2 — Codex integration

1. `adapters/codex/hooks/userprompt-lifecycle.py`: structured runner with existing timeout/kill; receipt cleanup; exact stdout; record once; preserve mode/recall/briefing/turn-nudge order.
2. `adapters/codex/bin/preflight.sh`: keep public `kv|json|hook`; extend doctor only; no activation/config command.
3. `adapters/codex/{AGENTS.md,README.md,ADAPTATION.md}`: document Phase 2/L2/current runtime/isolated Phase 3/config boundary.
4. `hooks/portable-guards.test.sh`: installed-fixture normal/transition/same-band accounting, exact bytes, no diagnostic injection, timeout/error fail-open, production absence.

Gate: production output/inserted directive bytes exactly match Phase 1; accounting failure silent/nonfatal.

### Step 3 — isolated Phase 3

1. `tools/fleet/token_experiment.py` (new): manifest/schema, forecast state, arms, strict pairing, bootstrap, gates, canonical output.
2. `utilities/token-budget-experiment.py` (new): replay/evaluate only; reject production true, config writes, unknown candidate/hash mismatch.
3. `tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json}` (new): IDs/hashes, episode/unknown cases, synthetic label.
4. `tools/fleet/tests/test_token_experiment.py` (new): byte identity, latch/reopen, unknown equivalence, all exclusions, n/strata, safety, quality, both deltas, bytes/emissions, verdict/adoption/production.

Gate: repeat outputs byte-match and production imports contain no candidate.

### Step 4 — mirrors/projections/full boundary

1. Extend `tools/fleet/tests/test_token_budget.py` while retaining Phase 0–1 tests.
2. Resync complete `tools/fleet/` to `adapters/claude/tools/fleet/`; mirror parity byte-matches modules/tests/fixtures.
3. Add Claude and allowlisted Codex symlinks for `token-budget-experiment.py`; neither activates hooks.
4. Update `adapters/opencode/{AGENTS.md,README.md,ADAPTATION.md}`: explicitly defer Phase 2 automatic accounting/Phase 3 CLI; no silent parity.
5. Update `tools/check-adaptation-boundary.sh`: Codex allowlist, Codex projected/OpenCode deferred classification, production import/activation negative guard.
6. Regenerate `manifest.json` only via builder.

## 5. Expected changed files

```text
core/CONVENTIONS.md
core/ADAPTATION_INVENTORY.md
tools/fleet/token_budget.py
tools/fleet/token_accounting.py                         # new
tools/fleet/token_experiment.py                         # new
tools/fleet/tests/test_token_budget.py
tools/fleet/tests/test_token_experiment.py              # new
tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json} # new
utilities/token-budget.py
utilities/token-budget-experiment.py                    # new
adapters/codex/hooks/userprompt-lifecycle.py
adapters/codex/bin/preflight.sh
adapters/codex/{AGENTS.md,README.md,ADAPTATION.md}
adapters/codex/utilities/token-budget-experiment.py     # new symlink
adapters/opencode/{AGENTS.md,README.md,ADAPTATION.md}
hooks/portable-guards.test.sh
tools/check-adaptation-boundary.sh
manifest.json                                           # generated
adapters/claude/tools/fleet/token_budget.py
adapters/claude/tools/fleet/{token_accounting.py,token_experiment.py} # new mirrors
adapters/claude/tools/fleet/tests/{test_token_budget.py,test_token_experiment.py}
adapters/claude/tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json}
adapters/claude/utilities/token-budget-experiment.py     # new symlink
```

Any expansion requires recorded justification before edit. Forbidden/unexpected: `.agent_reports/spec/**`, component pipeline state, runtime config, Codex `hooks.json`, `adapters/claude/CLAUDE.md`, Claude settings/commands/statusline, OpenCode utility symlink, model/dispatch/QA contracts, fixture-based adoption evidence.

## 6. Coverage matrix

| Requirement | Owner | Test |
|---|---|---|
| digest/content-free | accounting | digest + serialized forbidden content |
| exactly once | lifecycle/reducer | all reasons, timeout, concurrency, identity |
| exact bytes | canonical map/receipt | Phase 1 equality/cap |
| samples/delta/decrease/unavailable | reducer | ordered samples |
| no token estimate | schema | absent field |
| 8 KiB/256/2 MiB/oldest/atomic/fail-open | store | oversize/257/size/lock/unwritable/concurrency |
| L0/L1 unchanged, L2 only kv/json | CLI/hook | lifecycle/diagnostic tests |
| pure feature set | experiment | replay/feature isolation |
| IDs/latches | candidate | early/observed/reopen |
| strict exclusions | evaluator | each enum/no imputation |
| n/strata | G1 | 29/30, multi-stratum |
| safety/hard regression | G3 | single failure rejects |
| both quality LCBs | G4 | boundary/failure |
| both observed-delta LCBs | G5/G6 | positive/zero/failure |
| 10k seed | manifest/evaluator | repeat bytes |
| max verdict/pending | output | synthetic pass |
| production absent | isolation | explicit scan |
| mirrors/defer | boundary | parity/doctor |

## 7. Stage ownership

| Stage | May write | Must not write |
|---|---|---|
| current code-plan | plan/checklist/reviews/metrics | source/spec/dev-test logs/summary |
| code-execute | expected source/docs/tests, checklist, dev logs, plan status | spec/test evidence/final report/runtime config |
| code-test | test logs/reviews | source; failures return to execute |
| code-report | final report, summary, allowed analysis refresh | source/spec/dev-test evidence |
| main orchestrator | harvest/merge/push/runtime projection/cleanup | none delegated here |

This stage is separable/file-owned. Depth-2 worker dispatches no depth-3 child.

## 8. Exact verification commands

Set `PF="$AGENT_HOME/adapters/codex/bin/preflight.sh"`; every command goes through the verification runner:

```bash
"$PF" verification-runner --timeout 60 -- python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in sys.argv[1:]]' tools/fleet/token_budget.py tools/fleet/token_accounting.py tools/fleet/token_experiment.py utilities/token-budget.py utilities/token-budget-experiment.py adapters/codex/hooks/userprompt-lifecycle.py tools/fleet/tests/test_token_budget.py tools/fleet/tests/test_token_experiment.py
"$PF" verification-runner --timeout 120 -- python3 -m unittest -v tools.fleet.tests.test_token_budget
"$PF" verification-runner --timeout 180 -- python3 -m unittest -v tools.fleet.tests.test_token_experiment
"$PF" verification-runner --timeout 300 -- python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'
"$PF" verification-runner --timeout 300 -- bash hooks/portable-guards.test.sh
"$PF" verification-runner --timeout 180 -- bash tools/adaptation-guard.test.sh
"$PF" verification-runner --timeout 300 -- bash tools/check-adaptation-boundary.sh
"$PF" verification-runner --timeout 120 -- python3 tools/build-manifest.py --check
"$PF" verification-runner --timeout 180 -- "$PF" doctor
"$PF" verification-runner --timeout 60 -- git diff --check
"$PF" verification-runner --timeout 60 -- python3 -c 'from pathlib import Path; ps=[Path("utilities/token-budget.py"),Path("adapters/codex/hooks/userprompt-lifecycle.py"),Path("adapters/codex/bin/preflight.sh"),Path("adapters/codex/hooks/hooks.json")]; ns=("offline-forecast-v1","token_experiment","production_dynamic_enabled"); bad=[(str(p),n) for p in ps for n in ns if n in p.read_text(encoding="utf-8")]; assert not bad,bad'
```

After main integration/runtime refresh only, main runs `preflight.sh runtime-projection --require-hook-trust`. This worktree never installs/mutates runtime state.

## 9. Over/under-scope and risk

- Excluded: real workload/evidence/adoption, rollout/config, OpenCode implementation, input/transcript/artifact pruning or compression, RL/fitting, model/effort/intensity/dispatch/QA/guards, savings/billing/cost/ROI. Required bounded accounting-file pruning remains in scope.
- Included explicitly: timeout/error, all zero enums, exact bytes, samples, all bounds/prune, latches, pairing, both quality/delta comparisons, bytes/emissions, verdict cap, mirrors/defer, production absence.
- Any threshold/enum/manifest/bootstrap/verdict/production/spec-path change is spec-significant and stops execute for `autopilot-spec`.
- Highest risks: timeout double/missed count, prune race, newline bytes, production import leak, duplicate episode, permissive pairing, nondeterministic JSON/float/bootstrap, fixture evidence overclaim.

## 10. Verdict

**PASS WITH INLINE QA FALLBACK — ready for code-execute.** Independent thorough reviewers were not launched because depth 3 is forbidden. `_internal/plan_reviews/round_1.md` is inline fallback, not independent QA.
