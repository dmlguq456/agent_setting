# dispatch-defaults-config implementation plan

## Binding

- capability/stage: autopilot-code / code-plan
- mode / QA / intensity: dev/refactor / standard / standard
- worktree: /home/Uihyeop/agent_setting-wt/dispatch-defaults-config
- canonical artifact root: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_dispatch-defaults-config/
- source baseline: 3ebd1c77928a1008dc581bd40a04fdf257c8826d
- spec-significance: within-spec (governing spec: spec/stage-dispatch/prd.md v16 §13.8 SD-66, present at worktree HEAD 3ebd1c77)

This plan is grounded in PRD v16 §13.8, core/OPERATIONS.md §5.10 SD-16/SD-48, the selector and tests, topology registry, profile conventions, both g9 copies, Codex _bind_runtime_parent(), dispatch-node.py, and nested-eligibility code/tests. No source file is changed in this stage.

## Fixed guards and assurance

- Run every edit, guard, test, suite, and probe from the task worktree, never the primary checkout /home/Uihyeop/agent_setting. Write source only in the worktree and artifacts only under the canonical plan root; never write worktree report snapshots.
- Before each source edit run preflight.sh write <file> <stage-session-id>. Retain spec/core read gates. Do not edit spec/**, route-hash/topology compilation, broker remnants, Fleet UI, or existing stage-profile harness semantics. Do not rerun g9/g10 drills.
- Workers do not merge, push, or clean up. Depth-0 integrates. Use two task-branch commits: a core-first safety/contract commit, then an implementation commit.
- Standard code QA requested 1x-deep-reviewer+2x-fast-reviewers, a selected independent plan-check, final verification, one round, and no code-track fact-checker/external adversary. This stage cannot dispatch another worker, so _internal/plan_reviews/inline-review.md records the inline fallback without claiming independent-agent assurance.
- Runtime warning: initial preflight read hooks could not persist into the read-only primary checkout’s .spec-grounding/.core-grounding. The required sections were actually read, then markers were rerun with the writable canonical artifact home. Preserve this runtime limitation downstream.

## Design decisions

1. Create dedicated utilities/dispatch-defaults.py. A strict standard-library utility keeps dispatch-route.sh POSIX, avoids yq/PyYAML, centralizes validation, and gives fixture tests a stable interface. Production paths resolve from the repo; DISPATCH_DEFAULTS_CONFIG supplies a fixture/operational override.
2. Use a narrow YAML subset with top-level schema_version, depth1_owner, opencode, and capabilities; nested capability maps contain only affinity cells. Accept comments, simple scalars, the inline owner list, and two-level mappings. Reject duplicate, unknown, or malformed structure. Strict keys plus the affinity vocabulary prevent model/effort values without pretending to catalogue every model name.
3. Persist only canonical topology node IDs. PRD prose says exec and review, while HEAD exposes autopilot-code nodes plan, execute, test, report and no separate review. Store execute: codex, test: diverse, report: claude; omit plan; comment that execute realizes prose exec and test is the reviewer stage. Literal exec/review keys fail validation. A separate review coordinate requires a future spec/topology change outside this cycle.
4. Scaffold all coordinates as comments, not empty keys. Union repeated recipes: autopilot-apply (apply, verify, handback); autopilot-code (plan, execute, test, report); autopilot-design (refs, build, visual-review, handoff); autopilot-draft (material-strategy, draft-production, review-refine, finalize); autopilot-lab (scaffold, smoke, full-run, eval-run, metrics, media, report, independent-verify, sync); autopilot-note (scan, route-apply); autopilot-refine (review, transaction); autopilot-research (retrieval, synthesis, report, claim-verify); autopilot-ship (release-setup, security-review, release-review); autopilot-spec (research, review, prd-transaction).
5. Keep default-role selection separate from affinity. Remove only affinity assignments from the current stage case. Preference order stays --adapter > --family > validated config affinity > capacity bias; hard eligibility then rejects/falls back as today. Missing capability, omitted cells, and noncanonical legacy lookups are neutral.
6. Validate depth1_owner as a non-empty, unique set of concrete harnesses (no diverse), shipping [claude, codex]. Require opencode: relief-only. OpenCode stays out of neutral/diverse automatic candidates; explicit or user-configured relief selection remains subject to runtime eligibility.

## Ordered file-level work

### 1. Core contract first

File: core/OPERATIONS.md

- In §5.10 SD-16, add 1–3 concise sentences declaring profiles/dispatch-defaults.yaml the user source for SD-22 step 3. Explicit choice and hard eligibility, including usage limits, win; the default is soft and may be changed with a recorded reason; omitted cells are discretionary.
- In SD-48, add the required no-reconfirmation sentence for manual wrapper starts. Also state current HEAD truth: dispatch-node.py --action start materializes a record but does not forward route.dispatch_evidence, so it currently still needs manual evidence flags. Include: “Supplementing a --start invocation with the checked evidence flags obtained from the documented nested-headless probe is the required procedure, not a gate bypass; workers proceed without re-confirmation even when a caller-provided argument list omitted those flags.”
- Keep automatic dispatch-node.py evidence forwarding as a follow-up only.

Verification: targeted diff review and git diff --check -- core/OPERATIONS.md; ensure the prose does not claim the route-record path is already covered.

### 2. Repair g9 parent linkage and mirror

Files:

- loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/{assert.sh,prompt.md}
- adapters/claude/loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/{assert.sh,prompt.md}

- Remove only the owner’s literal parent_sid=drill-parent-session metadata/Fleet filters. Require a non-empty SID matching [A-Za-z0-9_.:-]+; if the raw transcript exposes one unambiguous runtime thread ID, compare it, otherwise keep the mandatory format check with a best-effort diagnostic.
- Preserve exact drill-parent-session checks for both depth-2 children.
- Keep the owner registration argument in the prompt and add one line explaining intentional depth-1 rebinding to the real Codex thread.
- Make both mirror files byte-identical to the root case.

Verification: bash -n, targeted owner/child checks, and cmp. Do not run the drill.

### 3. Add config and loader/validator

Files: profiles/dispatch-defaults.yaml, utilities/dispatch-defaults.py

- Add the narrow schema, full commented coordinate inventory, [claude, codex], canonical populated autopilot-code cells, and no empty/plan cells. Comment that only harness names are allowed. Add a 1–2 line OpenCode comment stating the 1–2% relief target and automatic-approval premise.
- Implement validate, affinity lookup, and policy-query operations. Load and union capabilities/topologies.json nodes. Fail loudly on unknown capability/stage, duplicate keys, invalid vocabulary/model-like values, malformed/non-set owner sets, or invalid relief policy. Omitted cells return neutral; diagnostics go to stderr with nonzero status.

Verification: compile without bytecode, validate the shipped file, query populated/omitted cells, and run temporary malformed fixtures for every failure class.

### 4. Wire selector without changing its cascade

File: utilities/dispatch-route.sh

- Resolve default config/topology paths from the repo and honor DISPATCH_DEFAULTS_CONFIG for fixtures. Validate early enough that malformed config fails even with an explicit adapter.
- Preserve role-only cases, argument/conflict handling, explicit OpenCode behavior, usage logic, exact model mapping, traces, and read-only behavior.
- Look up canonical capability/stage affinity; use neutral for an omitted/non-addressable cell. Apply adapter, family, config, then bias; afterward preserve hard eligibility rejection/fallback. Never add OpenCode to neutral/diverse automatic candidates.

Verification: sh -n and targeted fixture calls for precedence, neutral, diverse, and limited-harness fallback.

### 5. Convert selector tests to temporary config fixtures

File: utilities/dispatch-route.test.sh

- Build a temporary valid config and set DISPATCH_DEFAULTS_CONFIG only in the helper.
- Cover configured values, omitted/neutral behavior, diverse selection against Claude/GPT makers, explicit/family precedence, hard eligibility, [claude,codex] policy query, OpenCode exclusion from automatic candidates, and preserved explicit OpenCode behavior.
- Add malformed fixtures for invalid/model-like affinity, unknown capability/stage, malformed owner set, and invalid relief policy. Assert nonzero failure plus useful stderr. Retain jobs-log non-mutation checks.

Verification: sh utilities/dispatch-route.test.sh in the worktree with exact results saved in test evidence.

### 6. Verification-only Codex auth coverage

Conditional file: utilities/nested_dispatch_eligibility.test.py

- The regression already exists: test_nested_auth_probe_runs_inside_checked_worktree uses empty stdout, “Logged in…” on stderr, and expects successful auth. Do not reimplement or duplicate it; restore an equivalent case only if it disappears before execution.
- Test stage runs that suite and independently records a fresh preflight.sh nested-headless ... --child-harness codex --json probe with conductor authority, task worktree, and actual parent transport/sandbox. A Codex workspace-write parent uses the documented owner network marker. Require status=supported and record fresh probe_source/probe_time; the conductor’s 12:38:01Z result is context only.

Verification: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest utilities/nested_dispatch_eligibility.test.py and the live probe. Non-supported live evidence fails the gate.

### 7. Integrated verification and commits

- From the worktree only, run syntax checks, default config validation, selector fixtures, nested unit suite, applicable adaptation-boundary verification, git diff --check, status/scope inspection, and bounded preflight verification-runner wrappers where applicable.
- Commit 1, core-first safety/contract: core/OPERATIONS.md and g9 root/mirror repairs. Commit 2, implementation: default config, Python loader, selector wiring, selector tests. The existing nested regression yields no diff.
- Do not merge, push, clean worktrees, run g9/g10, or touch route-hash sealing.

## Risks and follow-ups

- Canonical-stage mismatch: literal PRD exec/review cannot pass the current topology-key invariant. The chosen canonicalization preserves current topology/reviewer semantics; a separate review cell needs a later registered spec/topology change.
- dispatch-node.py currently does not forward route evidence. Manual supplementation is required; automatic forwarding plus wrapper tests is a follow-up, not this cycle.
- The strict YAML subset must fail loudly on unsupported editing forms. Comment scaffolding must remain parse-neutral.
- Affinity is soft, never a pin; explicit/config preference still yields to hard eligibility.
- Root and Claude g9 files are byte-identical at baseline and must remain synchronized.
- Do not turn read-marker persistence limitations into a false support claim.
