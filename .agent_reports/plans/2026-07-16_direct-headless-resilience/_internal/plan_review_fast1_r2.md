# Fast independent plan re-check — direct-headless resilience

verdict: **FAIL (three prior blockers remain)**

review scope: amended `plan.md` and `_internal/plan_refinement.md` only.

## Resolved

- The plan now names `utilities/stage-dispatch-fallback.py --start --progress-window-seconds N` as the synchronous watchdog/continuation owner and specifies exact revalidation, idempotent persisted state, row close, and resumption at the next SD-50 hop.
- It now provides adapter-paired capacity-selection option shapes, makes the canonical row the cross-process exactly-one retry authority, and explicitly rejects partial/same/cooled/unproved selections before wrapper launch.
- It adds a substantially safer two-window exact/newest stale predicate with legacy/identity/clock/newer-attempt vetoes and lock-time reclassification.
- It removes the nonexistent Claude preflight projection, records `qa: thorough`, reserves live nested smoke and commit for the depth-1 owner, and names the required durable artifacts.

## Remaining blockers

### 1. Watchdog bound contradicts “two consecutive no-progress windows”

Stage 1.3 says the foreground owner remains active “for at most two bounded windows.” If deterministic progress occurs in either window, the quiet count resets but the total-window cap can make the monitor exit before a later pair of consecutive quiet windows. That does not guarantee SD-58 after an initially progressing worker stalls.

Amend this to remain active until an exact terminal/completion outcome, identity-safe failure, or two **consecutive quiet** windows. Bound each poll/window and expose an optional overall test timeout, but do not cap the production monitor at two total observations. Add a fixture for `quiet warning -> deterministic progress reset -> quiet warning -> quiet interrupt/fallback`.

### 2. Capacity allow-list authority is still unnamed

Stage 2.2 says “the adapter role/profile resolver and its configured allowed model set,” but neither `plan.md` nor `plan_refinement.md` identifies the file/command/data source that owns that allow-list or proves a named profile resolves to a concrete model. The “Likely files” list likewise omits a concrete resolver target. This leaves a core safety decision to implementation-time invention and does not close the first review’s request to name the actual authority.

Amend the plan to name the exact resolver/registry command and source file(s), define its structured output used by the orchestrator, and include its focused test target. If no configured allow-list exists, the plan must explicitly define the checked authority being introduced and its ownership rather than presupposing one.

### 3. Heartbeat and liveness target ambiguity remains

Stage 1.2 still says repeated phase refreshes are rejected, while Stage 1.3 says a phase may repeat when its deterministic digest changes. Make the former say that only unchanged/replayed phase evidence and sequence rollback are rejected; valid tool/write/test cycles with changed evidence are accepted.

Stage 3.2 still says “Codex and portable liveness readers” without naming the existing readers/tests that must stop duplicating exact PID/start or heartbeat decisions. Replace the vague target with the concrete Codex/OpenCode/portable liveness files and their regression tests, and explicitly name the three wrapper prompt functions plus `utilities/worker_dispatch_prompt.test.py` for heartbeat projection. Otherwise the single-classifier acceptance cannot be audited from the plan.

## Gate to PASS

PASS after the plan monitors two consecutive quiet windows rather than two total windows, names the capacity allow-list/profile-resolution authority and tests, and removes the repeated-phase contradiction while naming the concrete liveness/prompt consumers.
