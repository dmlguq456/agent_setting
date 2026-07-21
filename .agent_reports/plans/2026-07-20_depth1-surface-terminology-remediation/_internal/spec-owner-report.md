# Autopilot-spec owner report — stage-dispatch v20

Date: 2026-07-20  
Route: `rt-24a883963a582a4a` (`sha256:24a883963a582a4a179760de8b5865f4cfcfcfaa04f7ce2f24bc4480dfb3ecab`)  
Node: `prd-transaction`  
Capability/intensity/QA: `autopilot-spec` / `strong` / `standard-general`  
Verdict: **PASS**

## Outcome

The approved pre-implementation blueprint update is complete. Stage-dispatch is now PRD v20 with three locked decisions:

- SD-73 supersedes SD-19 for new quick routes: one registered-headless-only capability-owner node, no native-subagent or inline fallback, typed compile/exhaustion failures, and at most one live attempt while retaining serial registered-headless retry history.
- SD-74 defines `dispatch_depth`, `max_dispatch_depth`, and `owner_dispatch_depth` as logical portable route topology, separate from attempt execution surface, registration status, process ancestry, runtime-native nesting, and Codex `agents.max_depth`.
- SD-75 separates wrapper transport, attempt execution surface, and fallback-hop vocabularies, and distinguishes Codex native subagents, Claude subagents, Claude agent-team teammate sessions, and registered headless worker sessions.

Direct main-inline and the existing standard+ fallback chain are preserved. Multi-capability composition, co-primary routes, cross-capability DAGs, source implementation, concrete model selection, and user runtime configuration are explicit non-goals.

## Stage handoffs

| Stage | Registered attempt | Artifact | Stage handoff | Owner use |
|---|---|---|---|---|
| research | `att-442ac6ce9b456e8c38f851c8932704e85306a8e834be5d3c` | `shards/spec-research/depth1-surface-terminology.md` (`d3071eed...`) | PASS | Proposed SD-73~75, acceptance, migration, and non-goals. |
| review | `att-396e4d60d717d905ae3cf7add2df7ffc28873e8d329489f9` | `reviews/spec/spec-verdict.json` (`20e3e5c9...`) | PASS (review completed); proposal verdict FAIL | V20-R1~R6 were all resolved before transaction: missing Codex term, logical-depth definition, retry cardinality, vocabulary namespaces, typed recovery, and legacy boundary. |

Both stages were launched by checked `preflight.sh dispatch-chain` dry-run/register/start calls with exact parent `depth1-terminology-spec-owner`. `utilities/dispatch-wait.sh` was called synchronously in the current turn until terminal evidence appeared; no asynchronous monitor, wakeup, scheduler, or detached completion promise was used. Each terminal handoff was harvested, bound to an exact route completion marker, and its registry row was closed before the successor ran.

## Atomic transaction

Command contract:

```text
python3 utilities/spec-transaction.py run \
  --artifact-root /home/Uihyeop/agent_setting/.agent_reports \
  --worktree /home/Uihyeop/agent_setting-wt/depth1-surface-terminology \
  --route .../_internal/spec-route.json \
  --node prd-transaction \
  --spec-root .../.agent_reports/spec/stage-dispatch \
  --require-snapshot -- bash /tmp/apply-stage-dispatch-v20-transaction.sh
```

Result: lock acquired without waiting; component `next_version=19`; transaction released with result 0. The previous v19 PRD was snapshotted to `_internal/versions/v19/prd.md` before the three current files were replaced in the same locked sequence.

Changed canonical artifacts:

- `spec/stage-dispatch/_internal/versions/v19/prd.md` — previous v19 snapshot, SHA-256 `b3cfb8713ccf1a9bcd9c14e8dd3cf016b45c907d36030059d625e1b5a458dba5`.
- `spec/stage-dispatch/prd.md` — v20, SHA-256 `ea312020d3230c099989aa01b730eb0e060a6ccaf1e6fee00263a9f4eed9d1c1`.
- `spec/stage-dispatch/pipeline_state.yaml` — version 20, SHA-256 `8904e05bcf97d49ff181d3f761fc27524691f1470d366f33d34c9b7482bb49a3`.
- `spec/stage-dispatch/pipeline_summary.md` — v20 narrative, SHA-256 `fc8df3e7a082eba7516fbb24b95b291e4a3b6856d953c165dca9e18b24368c04`.

Repository source, core, capability contracts, adapters, generated projections, Git index, commits, and worktree source files were not modified.

## Verification

All required final checks passed:

```text
snapshot existence + previous-PRD SHA/byte identity                 PASS
current PRD exact draft SHA                                          PASS
pipeline_state YAML parse + version/project assertions               PASS
SD-73/74/75 and typed-failure token coverage                         PASS
direct preservation / standard+ fallback / one-live-attempt checks   PASS
closed vocabulary / legacy read-only / no-composition checks         PASS
pipeline_summary v20 narrative check                                 PASS
python3 utilities/spec_transaction.test.py                           PASS (3/3)
preflight.sh worker-route ... --node prd-transaction                 PASS
git status                                                           source worktree unchanged
```

## QA assurance and warnings

`preflight.sh qa-policy standard general` required `1x deep reviewer + 2x fast reviewers`, `1x fast fact-checker`, maximum one round, with assurance scope `plan-check:selected-independent-pass:final-verify`; reviewer counts are upper bounds for the selected pass rather than per-stage loops. This route ran a separate registered-headless deep review and final deterministic verification. The audit input supplied the prior deep review, official-source fact verification, and deterministic reproductions. No additional fast-reviewer or fast-fact-checker processes were run, so this report claims only the independent headless review actually performed plus the audit's recorded fact boundary.

Two runtime details are recorded without weakening the gate:

1. The owner and both depth-2 workers attempted the Codex spec-read marker, but the worker-visible `.spec-grounding` path was read-only. The immutable route had already sealed `spec_read=stage-dispatch-prd-v19` and `artifact_guard=preflight-write-pass`; the actual four canonical target write preflights passed immediately before the locked transaction.
2. Both foreground wrappers returned typed `progress-watchdog-fail-closed` after their child had already emitted a valid three-line PASS handoff and `turn.completed`. The owner did not infer success from process exit: it inspected exact transcript terminal evidence, verified each artifact, wrote the route-bound exact-attempt completion marker, harvested, and closed the child row before continuing. This is an unsupported wrapper/watchdog reconciliation detail for the implementation follow-up, not a missing stage result.
