## 📋 Plan Review Results

- **Target:** `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity/plan/plan.md` (checked against `plan_ko.md` and `checklist.md`)
- **Plan summary:** The refinement keeps one exact-attempt terminal inspector as the dependency for receipt, liveness/wait, and harvest, then exercises the real foreground Codex wrapper with deterministic verdict fixtures. It substantially closes round 1, but the wire contract, fixture lifecycle, and post-exit orphan-reconcile proof still have three execution-blocking ambiguities.
- **Evidence scope:** Reviewed only the seven assigned files. In accordance with the assignment boundary, source claims were checked against `baseline_comparison.md` and the supplied round-1/refinement records rather than by reopening source files.
- **Gate:** **FAIL**
- **Verdict:** 🔴 3 issues (3 major); 🟡 1 suggestion.

### Thorough-QA evidence

`preflight.sh qa-policy thorough code` reported `assurance_scope=plan-check:selected-independent-pass:final-verify`, `max_round=2`, and reviewer upper bounds of two deep plus two fast reviewers. This registered depth-2 review is the selected independent round-2 plan check; the counts are upper bounds, not a per-stage quota.

The required spec-read guard was invoked after reading the assigned SD-1/SD-2 passages. Its marker hook again reported that `.spec-grounding` is read-only. That does not block this read-only review, and the plan/checklist correctly require the execute owner to re-establish the marker in writable guard scope.

## 🔴 Must-fix before execution

### **plan step 1.1 / 1.2 — `codex-terminal-v1` is called closed, but `artifact_state` and unsafe-root behavior remain open**

- **Current code state:** The supplied baseline says the current parser has no artifact-root validation and no normalized shell wire (`baseline_comparison.md`, “Measured current Codex behavior”). The new plan therefore owns the complete interface definition. Phase 1.1 enumerates `state`, `source`, `verdict`, and `blocker_reason`, but leaves the fifth field as only “typed artifact states.” Phase 1.2 names missing/mismatched roots, path containment, and symlink escape, but no explicit unsafe-root fixture or expected enum result.
- **Plan's assumption:** Calling every field a closed enum is treated as enough for independent Python and shell implementations to agree. It is like publishing a six-pin connector while leaving one pin labeled only “typed signal”: both ends can be locally reasonable and still be incompatible.
- **Proposed correction:** Enumerate the exact allowed `artifact_state` tokens and the legal state/source/verdict/artifact/blocker combinations for exit 0/2/3/4. Define which resolver/root conditions are unsafe and their fixed result (including any relative, over-broad, non-directory, escaped, or shadow-root cases that the existing resolver contract can produce), then add explicit producer and shell-consumer fixtures for each. Keep paths and free text out of the wire.
- **Affected plan sections:** Phase 1.1 wire/root bullets; Phase 1.2 wire/root boundary matrix; Phase 2.3 shell parsing; Phase 3.3 and 3.4; Safety invariants 8–9; Verification expected wire/root evidence; checklist Phase 1 wire/root items and required root evidence.

### **plan step 2.2 / 3.1 — the real foreground fixture lifecycle conflicts with failure-row closure and current-row filtering**

- **Current code state:** The plan's own current-state analysis says foreground Codex closes exact `FAIL`/`BLOCKED` rows before returning the receipt, and Phase 2.1 explicitly preserves that behavior. Phase 2.2 also preserves current-row filtering. Phase 3.1 nevertheless says that every wrapper-produced `PASS`/`FAIL`/`BLOCKED` row is subsequently fed through both liveness surfaces, wait, and harvest, while Phase 2 completion evidence expects one fixture to expose a consistent typed verdict across all surfaces.
- **Plan's assumption:** A foreground failure row remains selectable by normal current-row liveness/wait after the wrapper has already closed it. Unless an exact closed-attempt selector already exists and is intentionally used, the test loses its subject before those checks run—the registry equivalent of removing a train from the departure board before asking the board to classify it.
- **Proposed correction:** Specify a lifecycle-valid matrix. Use the real foreground wrapper for stdout/stderr isolation, exact JSONL retention, receipt fields, and exact `PASS`-open / `FAIL`-closed / `BLOCKED`-closed transitions. Then either (a) prove a supported exact-attempt read-only selector can inspect those closed rows without weakening current-row filtering, or (b) run typed liveness/wait failure checks against controlled current/open rows built from the same wrapper-shaped JSONL while keeping them explicitly supplemental. State which outputs and row state are asserted before and after harvest for every verdict.
- **Affected plan sections:** Phase 2.1 closure semantics; Phase 2.2 current-row filtering; Phase 2 completion evidence; Phase 3.1 wrapper-produced row/log flow and transition assertions; Phase 3.3; Verification expected evidence; checklist Phase 3 wrapper/feed/transition items.

### **plan step 2.2 / 2.3 / 3.3–3.5 — post-exit orphan reconciliation is named but not concretely preserved**

- **Current code state:** The supplied baseline lists PID/heartbeat evidence and exact registry behavior as existing contracts. The change moves terminal inspection ahead of PID/transcript fallback, exactly where post-exit orphan classification and reconciliation can be masked. The refined plan says “preserve orphan precedence” and the checklist says “retain orphan regressions,” but neither defines the post-exit reconcile fixture, expected row/note transition, or the test command that owns it.
- **Plan's assumption:** A generic orphan regression is treated as proof that the new terminal-first branch cannot bypass or rewrite post-exit reconciliation. That is like testing the alarm while the door is open but never checking whether it still works after the door closes—the ordering is the contract at risk.
- **Proposed correction:** Add one named deterministic post-exit orphan-reconcile scenario at the affected liveness/registry seam. Assert the exact precedence, row/note transition, idempotence, and no breadth-close behavior before and after terminal inspection; also assert that raw terminal content remains isolated. Map the scenario to one concrete existing test command (or a narrowly scoped new case in an already-owned test file) and mirror the expected evidence in the checklist.
- **Affected plan sections:** Phase 2.2 Python liveness; Phase 2.3 shared liveness; Phase 3.3 liveness/wait coverage; Phase 3.5 registry coverage; Safety invariant 7; Verification expected evidence; checklist Phase 2 preservation and Phase 3 orphan-regression items.

## 🟡 Useful improvements

### **plan step 4.1 / Verification — replace the remaining capture-directory placeholder**

- **Missing content:** The final scoped check still contains `rg ... <captured-parent-output-directory>`, which is not directly executable even though the conformance test itself is concrete.
- **Reinforcement suggestion:** Give the conformance fixture a deterministic capture directory or make the test perform and report the negative search internally, then replace the placeholder with its exact command/path. This keeps the final verification block reproducible without weakening the already concrete wrapper-boundary test.
- **Affected plan sections:** Phase 4.1; Verification “Final scoped checks”; checklist required negative-sentinel evidence.

## 🟢 Well-constructed portions

### **plan step 1.1 / 2.1 / 2.5 — round-1 failure-text containment is materially resolved**

The primary and Korean plans plus the checklist consistently default to fixed blocker reasons, make both optional detail fields explicit and failure-only, escape controls before independently capping each field at 512 UTF-8 bytes, preserve complete code points/escape tokens, forbid agent-message diagnostics, and invalidate non-`none` blockers or any detail on `PASS`.

### **plan step 3.1 / 3.2 — the real Codex boundary and positive-retention proof are now explicit**

The refinement correctly promotes the actual foreground `dispatch-headless.py --start` subprocess with deterministic fake `codex exec --json` to the authoritative isolation test. It captures both wrapper streams, exact JSONL, artifacts, and registry transitions; renderer tests are clearly supplemental. Distinct log, message, diagnostic, and artifact-body sentinels prove both that private data remains durable and that parent-facing surfaces stay clean.

### **plan step 1 → 4 — scope, language mirrors, file-only handoff, and mutation guards are coherent**

English, Korean, and checklist artifacts enumerate the same 13 guarded source/test paths and the same executable test suite. Every planned mutation has an exact pre-edit guard, phase-local focused gate, and non-destructive `apply_patch` rollback boundary. The plan keeps SD-1's thin conductor and SD-2's file-only handoff, separates receipt/transcript/liveness/wait/harvest/artifact reading, and explicitly excludes spec/core/Claude-wrapper/Fleet-schema/runtime-config changes.

## Completion gate

**FAIL.** The four historical round-1 themes are substantially addressed without scope reduction, but the artifact-state/unsafe-root portion of the wire finding is not fully closed. Before execution, the plan must also make the foreground failure fixture lifecycle compatible with exact row closure/current-row filtering and add a concrete post-exit orphan-reconcile regression. The remaining placeholder is a useful reproducibility cleanup, not an independent gate blocker.
