# Fast independent plan check — direct-headless resilience

verdict: **FAIL (plan amendment required before code-execute)**

scope: read-only review of `plan.md` against stage-dispatch PRD v14 §13.6.2–13.6.4, v15 §13.7.4, the retained F-25 plan boundary, the broker-withdrawal record, and the current direct-chain/registry entry points.

## Coverage summary

The plan correctly preserves strict SD-58 → SD-59 → SD-60 order, v15 broker retirement, SD-49 exact attempt identity, F-25 newest-attempt behavior, wrapper/orchestrator model-selection separation, SD-29 reconciliation gates, canonical/Claude Fleet parity, and the required focused/full/portable/adaptation/smoke verification groups. It also correctly withdraws the old broker stop/ensure recovery work.

The plan is not yet executable enough to guarantee three central acceptance outcomes: automatic watchdog continuation, exactly-one orchestrator-selected capacity retry, and safety-proved stale reconciliation.

## Actionable findings

### 1. BLOCKING — no concrete owner/invocation for the automatic watchdog loop

Stage 1.3 says to add a watchdog operation to the direct-chain path, but it does not define which command remains active after `stage-dispatch-fallback.py --start` returns, who polls it, or how the second quiet window re-enters the checked chain at the next eligible hop. The current direct-chain utility launches through `subprocess.run(...)`, accepts a successful wrapper launch, prints the selected attempt, and exits; a separate one-shot `dispatch-progress.py` command would not satisfy “warning → interrupt → fallback automatic progress.”

Amend the plan to choose one executable contract, for example:

- `utilities/stage-dispatch-fallback.py --start --watch-progress` owns launch + current-turn polling + exact interrupt + continuation; or
- `utilities/dispatch-progress.py watch-and-continue` is invoked synchronously by the `dispatch-chain --start` preflight surface and is passed the verified route/node plus the exact next-hop cursor.

Specify terminal conditions, exit codes, persisted quiet-window state, exact revalidation immediately before signal, and how the interrupted tuple/attempt is excluded while preserving route node/prompt/artifact ownership. The focused fixture must execute that public command end-to-end and assert warning first, exact signal/row close second, and invocation of the next checked hop. A unit test of fingerprint bookkeeping alone is insufficient.

Concrete targets: `utilities/stage-dispatch-fallback.py`, new `utilities/dispatch-progress.py`, `utilities/stage_dispatch_fallback.test.py`, new `utilities/dispatch_progress.test.py`, `adapters/codex/bin/preflight.sh`, and `adapters/opencode/bin/preflight.sh`.

### 2. BLOCKING — capacity alternative interface and allow-list authority are unspecified

Stage 2 says the orchestrator supplies an allowed different model/profile, but it does not define the CLI/route input carrying that choice, the authoritative validation source, or adapter-specific companion settings (`reasoning`, `effort`, or `variant`). Today `stage-dispatch-fallback.py` always passes one `--model-role` and can iterate direct-hop candidates; that is not an implementable guarantee of exactly one alternative model and can accidentally turn a different route candidate into an implicit retry.

Amend the plan with an explicit mutually exclusive interface such as adapter-qualified `--capacity-model` plus its required setting, or `--capacity-profile`/`--capacity-inherit-profile`. Name the authority used to prove the choice is allowed and to resolve inheritance to a concrete model before launch. Define the first-attempt and retry identity payloads and state that the normal candidate loop cannot create a second capacity alternative at the same hop. Persist and reload `capacity_retry=1`, prior attempt, cooled concrete model/profile, resolved alternative, and selection source from the locked canonical registry so conductor reruns cannot retry again.

The end-to-end fixture must inspect wrapper argv/counts, not only registry rows: exactly two launches on retry-success, exactly two before SD-50 descent on retry-failure, and zero launches for same-model/disallowed/unproved inheritance.

Concrete targets: `utilities/stage-dispatch-fallback.py`, `utilities/stage_dispatch_fallback.test.py`, the three `adapters/*/bin/dispatch-headless.py` wrappers and their SD-15/death-pattern tests, plus the actual role/profile resolver used for validation (name it in the amended plan rather than leaving “allowed” abstract).

### 3. BLOCKING — stale-row safety proof is circular/undefined

Stage 3.1 says “completion/age conditions prove” a stale terminal-not-updated row is inactive, but gives no threshold, source of terminal evidence, or rule for exact rows versus weak legacy rows. Age by itself cannot safely prove death, and an absent completion marker is explicitly “no claim” under SD-56. This leaves the most dangerous reconciliation class to implementation-time invention.

Amend the plan with a deterministic truth table. At minimum name: required exact/newest attempt identity; process evidence required or prohibited; terminal evidence source; injectable age threshold and production default; completion-marker semantics; legacy/unknown behavior; and the note chosen for each safe class. State that age alone and missing completion markers never authorize closure. Reconcile must re-read and reclassify under the jobs lock and compare the observed row identity/version before atomic replacement.

Concrete targets: `utilities/dispatch-registry.py`, `utilities/dispatch_contract.py`, new `utilities/dispatch_registry.test.py`, `utilities/worktree-cleanup.py` only for extracted SD-29 pure gates, and `tools/fleet/model.py` as the single classifier source.

### 4. MAJOR — heartbeat phase rules risk rejecting valid deterministic progress

The proposed total order `launch → analysis → tool → file-write → test → artifact/terminal` is stronger than the PRD and does not model normal repeated tool/write/test cycles. The plan elsewhere correctly says a repeated phase with unchanged evidence must not reset a window, but Stage 1.2 also says repeated phase refreshes are rejected.

Clarify that the monotonic value is an attempt-local sequence/observation generation, while a coarse phase may repeat when its deterministic evidence fingerprint changes. Reject only identical/replayed evidence, sequence rollback, route/attempt mismatch, and invalid transitions. This preserves real `tool → write → test → fix → write → test` progress without allowing speech or an unchanged heartbeat to refresh liveness.

### 5. MAJOR — replace vague projection/prompt targets with existing files

There is no `adapters/claude/bin/preflight.sh`. The amended plan should not imply one. Name the existing runtime surfaces:

- preflight/dispatch-chain: `adapters/codex/bin/preflight.sh`, `adapters/opencode/bin/preflight.sh`;
- liveness consumers that must delegate to the shared source: `adapters/codex/bin/dispatch-liveness.py`, `adapters/opencode/bin/dispatch-liveness.py`, and `utilities/dispatch-liveness.sh` (with `utilities/dispatch-wait.sh`/`hooks/conductor-stop-gate.sh` regression coverage as consumers);
- worker prompt projection: `dispatch_prompt()`/`task_prompt()` in all three `adapters/*/bin/dispatch-headless.py` files, verified by `utilities/worker_dispatch_prompt.test.py`.

Also name new focused test files rather than “plus its deterministic test.” This is necessary to keep Fleet/watchdog/liveness/reconcile on one classifier and to make source ownership reviewable.

### 6. MINOR — immutable QA metadata should be explicit

The header records mode and standard intensity but omits inherited `qa: thorough`. Add it and ensure direct-headless smoke/registered fixtures use the thorough QA value where route metadata is asserted. This does not change the immutable route; it prevents the implementation artifacts from reporting a weaker QA contract.

## Gate to PASS

PASS after the plan names the synchronous watchdog/continuation command, the capacity-selection input and validation authority, and the stale-reconciliation truth table; resolves the repeated-phase ambiguity; replaces vague/nonexistent targets with the concrete files above; and records `qa: thorough`. No source edit is recommended before those plan decisions are durable.
