# Orchestration metrics

- intensity: strong
- requested topology: registered headless depth-1 owner with depth-2 stages
- execution exception: inline implementation under `STAGE_DISPATCH_INLINE_OK=1`
- reason: this cycle changes the registered dispatch transport and its parent-wait contract; using that transport as the mutating owner would make the evidence recursive and could strand the work under the defect being replaced (`core/OPERATIONS.md` SD-17 self-modification exception).
- retained independent pass: post-implementation Claude registered-headless review when the checked cross-harness tuple remains available.
- forbidden shortcut: native subagents do not substitute for registered-headless parity.
- parent-idle acceptance: zero parent model/tool calls between the intermediate owner turn completion and the deterministic child-join terminal event.
- independent review round 1: registered Claude attempt `att-sd78-claude-review-01`
  produced a report but an invalid terminal artifact envelope; the exact row was
  harvested and closed. Findings retained: duplicate Codex final message,
  Claude hook asymmetry, and cross-turn diagnostic bleed.
- correction trigger: supervised park enforcement blocked the second sibling
  registration after the first row opened. The revised phase contract must
  preserve both parent idleness and strong two-way batch fan-out.
- independent review round 2: `att-sd78-claude-review-02` reached the 900-second
  bound without a report and was closed as `dead-timeout`.
- independent review round 3: `att-sd78-claude-review-03` wrote a PASS report
  with no high/medium findings. Its extra final prose failed the exact terminal
  envelope and was closed explicitly; a fourth formatting-only retry was also
  rejected and closed, so no terminal PASS is fabricated.
- live parity: Codex App Server same-thread two-turn smoke passed; Claude Code
  same-session resume passed; Claude command-scoped wildcard PreToolUse denied
  Bash without changing user-owned settings.
- focused verification: 90 tests passed across join, supervisors, phase guards,
  terminal, orphan, wrappers, adapter v11, and context conformance; 34 parent
  captures were checked.
- repository-wide verification: portable guards `PASS=356 FAIL=0`, adaptation
  boundary PASS, and `git diff --check` PASS.
- final registry state: `headless_open_jobs=0`,
  `orphaned_conductor_jobs=0`, supervisor-state files 0.
