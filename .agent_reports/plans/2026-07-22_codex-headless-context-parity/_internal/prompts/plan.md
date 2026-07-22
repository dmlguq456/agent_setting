No asynchronous Monitor/wakeup/scheduling waits; this is an atomic depth-2 planning stage.

Objective: produce an implementation-ready plan for verified Codex-to-Claude parity in registered-headless session handoff and parent-context hygiene.

Inputs (read these files directly; do not expect conversational context):
- Worktree: /home/Uihyeop/agent_setting-wt/codex-headless-context-parity at starting commit 8db730a48ca82ec23a9cd1a39fb65dd507e1be5a
- Canonical spec: /home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md, especially SD-1 and SD-2; contract is within-spec and must not be edited.
- Governing contracts: core/OPERATIONS.md main/worker and file-only handoff rules; roles/worker-bootstrap.md exact handoff envelope.
- Claude sibling comparator: adapters/claude/bin/dispatch-headless.py plus its deterministic wait/harvest tests.
- Codex path: adapters/codex/bin/dispatch-headless.py plus wait/liveness/harvest utilities and deterministic tests.

Required analysis and plan content:
- Establish the actual local Claude baseline across success, failure, and blocked fixtures.
- Define comparable information classes for worker transcript isolation, launch receipt, wait/liveness output, harvest output, terminal handoff, and artifact reading.
- Identify only genuine Codex gaps; preserve registry, Fleet, completion-marker, fallback, liveness, and debugging contracts.
- Design deterministic parity/conformance tests proving raw worker content cannot leak into successful parent-facing output, while allowing a bounded explicitly labeled diagnostic excerpt on failure only when required.
- Keep runtime-native subagents, Claude agent-team surfaces, spec edits, unrelated refactors, commits, merge, push, and cleanup out of scope.
- Note that official runtime documentation is needed only for runtime-owned behavior claims; prefer local deterministic evidence for harness behavior.

Outputs under /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity/:
- plan/plan.md (primary implementation plan)
- plan/plan_ko.md (Korean mirror)
- plan/checklist.md (initial checklist)
- baseline_comparison.md (measured local comparator matrix and initial design choice)

Completion gate: the plan must name exact candidate files, exact tests/fixtures, safety invariants, verification commands, and evidence needed by the execute stage. Return only the bounded worker handoff; put stage reasoning in files.
