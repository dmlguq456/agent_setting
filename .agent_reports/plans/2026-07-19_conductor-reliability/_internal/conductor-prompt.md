# Assignment — autopilot-code debug/strong conductor: conductor 신뢰성·Codex mutation·registry 위생

You are the depth-1 capability owner (thin conductor) for one approved
`autopilot-code` cycle. Load `capabilities/autopilot-code.md` and its
owner-execution reference completely, then run the immutable
`plan → execute → test → report` graph with separate registered depth-2
headless workers. Do not re-select capability, intensity, topology, or scope.

## Liveness and sequencing contract

This owner is a Codex headless process. Keep the whole pipeline in this turn:
after each launch, synchronously run

```sh
sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent conductor-reliability
```

until terminal (exit 2 means call it again immediately; exit 3 means diagnose
the exact attempt and take the checked fallback). Never leave a detached
completion promise. Run only one active stage at a time. After harvesting a
stage, close the exact current attempt row and write its completion marker
before starting the next node. Never breadth-close all rows for a route/node.

## Immutable route binding

- route:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/route.json`
- route_id: `rt-1d200b72bcfb544c`
- route_hash:
  `sha256:1d200b72bcfb544c5d875d8c6b1a09f0bcef5a6741aaebeeeba60970b9c45c63`
- dispatch contract: v3, conductor-direct
- worktree:
  `/home/Uihyeop/agent_setting-wt/conductor-reliability`
  (branch `conductor-reliability`, source commit `b9364824`)
- canonical artifacts:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/`
- governing spec:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`
  §13.7.6 SD-64 and §13.10 SD-69~71
- spec significance: within-spec; do not edit `spec/**`.

Read the governing sections and current implementation before planning.
Current official-runtime evidence has already been checked by depth-0:
Claude Code 2.1.215 supports `--disallowedTools`; Codex 0.144.6 keeps `.git`
and resolved gitdir protected even under writable roots, so adding the Git
common dir with `--add-dir` is not an accepted commit fix.

## Scope and required outcomes

Implement all of the following, including deterministic fixtures and honest
runtime evidence.

1. **Claude one-shot conductor hardening (SD-71)**
   - Probe the exact fatal asynchronous wait/scheduling tool names exposed by
     current Claude `-p`. Only names proven by the probe may be passed through
     `--disallowedTools`; do not disable Bash or synchronous
     `dispatch-wait.sh`.
   - Re-run a disposable Claude 2.1.215 `-p` Stop-hook fixture and record
     whether the hook fires, can block, and preserves stdout. Register a Stop
     gate only if all three conditions hold; otherwise retain the documented
     held fallback.
   - Standardize the conductor prompt/depth-note contract at the portable
     core surface first: no Monitor/wakeup scheduling; synchronous
     `dispatch-wait` in the current turn. Adapter projection follows core.
   - Add deterministic wrapper tests for the checked deny/fallback behavior.

2. **Orphan conductor reconcile and visibility (SD-64/71)**
   - Extend `utilities/dispatch-registry.py reconcile` using the existing
     single attempt classifier: exact conductor death + unfinished completion
     node + open/live child or unstarted successor closes the conductor row
     with `note=dead-parent-orphaned`.
   - Surface the classification and route/resume boundary through liveness,
     Codex preflight status, and Fleet's current-attempt view. Do not
     auto-resume, auto-relaunch, or close a live child.
   - Zero false positives for live conductors and completed routes.

3. **Codex linked-worktree mutation boundary (SD-69)**
   - Do not attempt to make protected Git metadata writable and do not claim
     `--add-dir <git-common-dir>` enables commit.
   - Project the exact primary `$AGENT_HOME/.spec-grounding` directory as a
     narrow writable root for route-bound Codex workers; create it safely.
     Do not expose all of agent home or `.git`.
   - Encode the linked-worktree Codex mutation stage as `no-commit` in the
     owner/stage contract and dispatch metadata where the current machinery
     needs it. A trusted depth-0/Claude boundary commits after PASS.
   - Add a disposable linked-worktree fixture proving source edits and primary
     spec marker persistence while commit remains honestly unavailable.

4. **Completion marker ↔ exact attempt row (SD-70)**
   - Extend `utilities/capability-route.py complete` to accept canonical jobs
     and exact current attempt identity. Write the marker atomically, then
     idempotently close only that row as done with
     `note=completed-marker` and marker evidence.
   - Preserve marker and return a structured nonzero on row-close failure.
     Reconcile must repair only the marker-backed exact stale row.
   - Test prior BLOCKED + current PASS + later live retry, duplicate complete,
     mismatch/missing attempt, and unwritable/missing jobs. Never breadth-close.

## Core-first, parity, and ownership

- Follow `AGENTS.md`: read `core/CORE.md` first and edit portable core contract
  before adapter realizations. Commit the core semantic change first, then
  adapter/runtime implementation commits.
- Claude, Codex, and OpenCode adapters are siblings. Change only surfaces whose
  runtime semantics actually differ and keep parity disclosures honest.
- Source edits only in the task worktree. Artifacts only in the canonical plan
  root. Do not merge or push main.
- The concurrently active `selector-paths` cycle owns only
  `utilities/dispatch-route.sh` and its tests. Do not edit those files.
- Preserve unrelated dirty/untracked state. Never use `git reset --hard`.

## Stage routing

Use `AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log` and:

```sh
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/route.json \
  --node <plan|execute|test|report> --adapter <adapter> --action start \
  --slug conductor-reliability-<stage> --parent conductor-reliability \
  --qa strong \
  --prompt-text "<absolute input/output paths, assigned sub-skill, strong intensity, exact scope>" \
  -- --model-role "<route node role>"
```

- `plan=codex` (`deep maker`).
- `execute=claude` (`fast implementer`): Codex is intentionally not used for
  the commit-owning stage until SD-69 is implemented and verified.
- `test=codex` (`deep reviewer`) for maker/checker harness diversity and direct
  validation of the fixed Codex writable-root contract.
- `report=claude` (`fast writer`).
- Run `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh` immediately
  before each dispatch and record any routing deviation.
- Stage prompts use absolute paths and assign only their named `code-*` skill.

For the plan-stage transition, the old `complete` interface is still in force:
harvest and exact-close the plan row first, then call the current marker
command. After implementation, exercise the new exact-attempt interface for
later nodes. If implementation changes make self-hosting unsafe, use the
worktree utility explicitly and record the bootstrap boundary.

## Verification floor

The plan worker must identify exact focused suites. At minimum include:

- `git diff --check`, syntax/compile checks for touched Python/shell.
- focused tests for capability-route, dispatch-registry/reconcile, wrapper
  sandbox arguments, liveness/preflight/Fleet classification.
- existing dispatch contract/node/route/worker-guard suites affected by the
  change.
- disposable linked-worktree Codex mutation fixture.
- current Claude `-p` Stop/tool-policy probe with captured evidence.
- `bash tools/check-adaptation-boundary.sh`.
- portable guard suite at the assurance level selected by `qa-policy`.

Delete test-created `__pycache__` before commits. The independent test worker
must verify the committed worktree, not merely trust execute logs.

## Completion

Write `pipeline_summary.md` under the canonical plan root while holding the
pipeline lock, and ensure `final_report.md` names commits, tests, known runtime
limitations, and any follow-up. Finish with exactly:

```text
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
