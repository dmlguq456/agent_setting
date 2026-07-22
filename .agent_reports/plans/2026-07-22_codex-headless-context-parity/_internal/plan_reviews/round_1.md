## 📋 Plan Review Results

- **Target:** `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity/plan/plan.md`
- **Plan summary:** The plan introduces one exact-attempt Codex terminal inspector, projects its sanitized result into launch/liveness/wait/harvest surfaces, and adds deterministic Claude/Codex conformance coverage while preserving registry and completion authority. Its dependency order is sound, but four interface and verification gaps must be closed before execution.
- **Evidence scope:** Reviewed only the assigned `plan.md`, `checklist.md`, `baseline_comparison.md`, and PRD SD-1/SD-2 passages. Per the assignment's file-input boundary, source citations were checked against the supplied baseline rather than independently reopening source files.
- **Gate:** **FAIL**
- **Verdict:** 🔴 4 issues (4 major); 🟡 1 suggestion.

### Thorough-QA evidence

`preflight.sh qa-policy thorough code` reported `assurance_scope=plan-check:selected-independent-pass:final-verify`, `max_round=2`, and reviewer upper bounds of two deep plus two fast reviewers. This registered depth-2 review is an independent plan-check pass; the counts are an upper bound, not a per-stage quota. Because the gate is FAIL, the owner should revise the plan and use the remaining review round before execution.

The required spec-read guard was invoked after reading SD-1/SD-2. Its marker hook reported that `.spec-grounding` is read-only while the command returned zero. This does not block this read-only review, and it reinforces the plan/checklist requirement that the execute owner re-establish the marker in its writable guard scope.

## 🔴 Must-fix before execution

### **plan step 1.1 / 2.1 / 2.5 — the free-form `blocker` field bypasses the bounded failure-output rule**

- **Current code state:** The supplied baseline defines arbitrary transcript text as isolated, while allowing only the typed terminal handoff into the control plane (`baseline_comparison.md`, “Comparable information classes”). The worker envelope's `blocker` is worker-authored one-line content. The plan caps and labels only `failure_diagnostic_excerpt` at 512 UTF-8 bytes (`plan.md`, Phase 1.1), yet the receipt and harvest steps separately emit “safely encoded artifact/blocker values” with no size bound (`plan.md`, Phase 2.1 and Phase 2.5).
- **Plan's assumption:** Control-character encoding is treated as sufficient containment for `blocker`. Encoding prevents record injection, but it does not prevent a huge or sensitive one-line worker message from entering the parent context. This is like putting an unbounded letter through a slot merely because the envelope has no newline.
- **Proposed correction:** Define one parent-output policy for worker-authored failure text. By default emit only a fixed blocker state/reason enum; if blocker detail is exposed, route it through the same explicit, failure-only, labeled, control-escaped, 512-byte UTF-8 cap as `failure_diagnostic_excerpt`. Enforce that `PASS` emits `blocker=none` and can never expose blocker or diagnostic text. Add oversized single-line, multibyte-boundary, control-character, and `PASS`-with-non-none-blocker negative fixtures.
- **Affected plan sections:** Phase 1.1 structured result and diagnostic option; Phase 2.1 receipt fields; Phase 2.5 harvest fields; Phase 3.1/3.4 diagnostic assertions; Safety invariants 3 and 9; Verification expected evidence.

### **plan step 1.1 / 2.3 / 2.5 — the shared inspector has neither a defined artifact-root source nor a defined wire grammar**

- **Current code state:** The assigned evidence preserves the six-field registry row/Fleet schema and says artifacts resolve through the canonical artifact root. It does not establish an `artifact_root` field stored on a registry row. The plan nevertheless says to validate against “the registry row's canonical `artifact_root`” and asks the shell liveness surface to consume a merely “machine-safe CLI view.”
- **Plan's assumption:** Implementers can infer both where the canonical root comes from and how shell/Python exchange encoded fields without changing the registry. Those are the two ends of an adapter cable; leaving the ground and pinout unspecified invites linked-worktree shadow reads, schema drift, or unsafe shell parsing.
- **Proposed correction:** Specify that the selected row's worktree is resolved through the existing canonical `utilities/artifact-root.sh` contract (or name another already-existing exact source) without adding a registry column. Then freeze a versioned inspector CLI schema: exact field order/names, encoding, one-record grammar, exit codes, invalid/absent behavior, and whether callers decode artifact paths at all. Add linked-worktree, missing-root, spaces/control bytes, malformed CLI output, and mixed-harness bypass fixtures.
- **Affected plan sections:** Phase 1.1 artifact validation and machine-safe CLI view; Phase 2.1/2.2 caller inputs; Phase 2.3 shell integration; Phase 2.5 harvest; Phase 3.1/3.3 conformance; Safety invariants 6 and 8.

### **plan step 3.1 / 3.2 — Codex launch isolation is tested at the renderer seam, not at the registered-headless wrapper boundary**

- **Current code state:** The baseline measured Claude through a fake `claude -p` wrapper invocation, but measured Codex terminal behavior from handcrafted JSONL/jobs fixtures across parser, liveness, wait, and harvest. The plan continues that asymmetry by exercising the “foreground receipt renderer” and adding receipt-rendering cases rather than explicitly driving the full Codex wrapper with a deterministic fake `codex exec --json` process.
- **Plan's assumption:** A renderer test proves the launched child's stdout/stderr redirection and wrapper-level exception/receipt paths. It does not; leakage can occur before rendering or on stderr even when the renderer itself is clean.
- **Proposed correction:** Add a fake-Codex registered-headless fixture parallel to the Claude fixture and invoke the actual `dispatch-headless.py` entry path for `PASS`, `FAIL`, and `BLOCKED`. Capture wrapper stdout, stderr, exact attempt JSONL, and registry before/after. Assert raw command/prior-agent/final-message sentinels remain in the log but not parent streams; assert `PASS` remains open and `FAIL`/`BLOCKED` close only the exact attempt. Keep renderer unit cases as supplemental coverage.
- **Affected plan sections:** Phase 3.1 first three bullets; Phase 3.2; Phase 3 completion evidence; Verification command for `dispatch_parent_context_conformance.test.py`.

### **plan step 4.1 / Verification — the write guard is a non-executable placeholder and is sequenced too late**

- **Current code state:** `plan.md` Verification contains the literal command `preflight.sh write <each-candidate-file> codex-headless` and Phase 4.1 says to run the “exact targeted commands listed.” The checklist correctly requires the guard before every source/test edit, but the change steps do not enumerate those invocations. The plan also names risks without giving phase-level rollback boundaries.
- **Plan's assumption:** A blanket placeholder in final verification can stand in for per-file pre-edit authorization. A write guard checked after editing is like validating a ticket after the train has departed: it cannot establish that the mutation was authorized when made.
- **Proposed correction:** Put an explicit `preflight.sh write <exact-path> codex-headless` immediately before each file's first edit in Phases 1–3, enumerating every candidate source and test path. Remove the placeholder from the executable Verification block. Add a non-destructive rollback boundary and focused test gate after each phase so a failed integration can be reversed only within that phase's owned files without reset/checkout or unrelated worktree changes.
- **Affected plan sections:** Phase 1.1/1.2, Phase 2.1–2.5, Phase 3.1–3.5, Phase 4.1, Risks, Verification “Guard and policy checks,” and checklist Preconditions.

## 🟡 Useful improvements

### **plan step 3.1 / 4.1 — reinforce both sides of transcript and artifact isolation**

- **Missing content:** The plan strongly asserts that parent-facing captures contain no sentinels, but it does not explicitly require a positive Codex assertion that the same raw sentinels remain durable in the exact attempt log. It also does not name a distinct artifact-body sentinel to prove that artifact readability metadata never becomes artifact reading.
- **Reinforcement suggestion:** In the conformance fixture, assert that command/prior-agent sentinels remain in the exact Codex log and that an artifact-body-only sentinel remains in the validated artifact. Assert that none appears in receipt, either liveness surface, wait, or harvest; then let a simulated next stage open the validated artifact path directly. Record these positive and negative assertions in Phase 4 evidence. This turns “the safe stayed locked” into “the valuables are still inside and the hallway stayed empty.”
- **Affected plan sections:** Phase 3.1 sentinel matrix; Phase 3 completion evidence; Phase 4.1 captured evidence; Safety invariants 1 and 8; checklist “Required evidence for code-test/code-report.”

## 🟢 Well-constructed portions

### **plan step 1 → 2 → 3 — dependency order and surface separation are explicit**

The plan correctly makes the normalized exact-attempt inspector the single dependency before integrating launch receipt, Python liveness, shared shell liveness/wait, and harvest. The baseline's information-class table cleanly separates worker transcript, receipt, wait/liveness, harvest, terminal handoff, and artifact reading, matching SD-1/SD-2's thin-conductor and file-only boundaries.

### **plan step 2.1–2.5 / Safety invariants — completion and operational authority remain intact**

The plan explicitly keeps textual `PASS` observational, requires exit 3 and harvest while the row is open, and leaves exact hash-bound completion-marker authority unchanged. It also names exact-attempt binding, mixed-harness/legacy fallbacks, PID/heartbeat/orphan/limit behavior, Fleet-readable registry data, `job_pipe`, raw debugging logs, and no spec/core/Claude-wrapper changes as preservation constraints, with focused regression commands for the affected seams.

## Completion gate

**FAIL.** Revise the exact sections named in the four must-fix findings before source execution. The plan can pass the next round once parent-visible failure text is bounded, the inspector's root and wire contracts are explicit, the real Codex wrapper is covered by deterministic verdict fixtures, and every mutation has a concrete pre-edit guard plus rollback boundary.
