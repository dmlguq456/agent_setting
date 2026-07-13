# code-execute — 2026-07-13

- SD-21/22: core now fixes the conductor high/deep boundary and portable priority.
- SD-23: `utilities/dispatch-route.sh` is a read-only selector; it calls usage-check once,
  traces limit fallback, and reports OpenCode as unknown rather than fabricating a model.
- Adapter maps own exact IDs and opt-in probe syntax; no live quota-consuming probe ran.
- SD-24: all dispatch wrappers export `AGENT_DISPATCH_CHILD=1`; procscan hides only that
  env-marked process. Fleet stage artifacts are consulted only for explicit code jobs.
- Acceptance repair: standard+ conductor is now `deep orchestrator`; retained
  `orchestrator` is balanced/mechanical. Codex maps Sol/Terra/Luna distinctly and
  has `CODEX_MODEL_BALANCED` / `AGENT_MODEL_BALANCED` knobs, so fast implementation
  cannot collapse to Luna. Selector applies checker maker-family diversity after
  hard usage eligibility; procscan also recognizes `AGENT_DISPATCH_DEPTH`.
- Focused evidence (2026-07-13): `bash utilities/dispatch-route.test.sh`,
  both Fleet unittest suites (162/162; Claude mirror 162/162 with 6 skips),
  `sync-native-agents.py --check`, and `git diff --check` pass. The adaptation
  guard now has no routing/model pin finding; its remaining failures are the
  pre-existing missing Claude mirror paths recorded by code-test.
- Focused regressions passed after syncing `tools/fleet` to the Claude Fleet mirror.
- `tools/check-adaptation-boundary.sh` reaches the new projection checks but remains red on
  pre-existing missing Claude drill/install/memory projection paths; this stage did not
  reconstruct those unrelated generated artifacts.
- Commit attempt `git commit -m 'feat: add deterministic dispatch routing policy'` was blocked:
  shared Git metadata cannot create `/home/Uihyeop/agent_setting/.git/worktrees/dispatch-routing-policy/index.lock`
  under the worker's read-only permission profile. No commit was created.
