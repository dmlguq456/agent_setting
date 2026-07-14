# Stage: code-plan — Token Self-Regulation Phase 2/3

You are the depth-2 `code-plan` stage worker. Do not dispatch any child/headless job (depth 3 is forbidden). Work only in `/home/Uihyeop/agent_setting-wt/token-self-regulation-phase2-3`; do not modify the main checkout and do not commit/push/merge/clean worktrees.

Use the Codex bootstrap and `code-plan` Skill contract injected by the dispatch wrapper. Read the flat PRD only to satisfy the current gate, then read the actual component SoT `.agent_reports/spec/token-self-regulation/{prd.md,experiment_contract.md,pipeline_state.yaml}`, Phase 0–1 source/tests, current core/capability/mode contracts, and the prior Phase 0–1 plan evidence. Record that the flat preflight does not model the component SoT even though actual-read evidence exists.

Task scope is spec-significance `within-spec`, exact v2 implementation:

- Phase 2: content-free `sha256(session-id)[:32]` XDG accounting; every invocation classified exactly once as zero/emission with fixed zero reasons; exact inserted directive UTF-8 bytes; first/last exact-session cumulative total samples and monotonic delta with decrease/unavailable counts; no token estimate without exact tokenizer provenance; bounded atomic locking/store at <=8 KiB/file, <=256 files, <=2 MiB with oldest-first prune and fail-open behavior. Preserve Phase 1 production output byte-for-byte and all zero paths. L2 diagnostics only in `kv|json`; never persist content or call observations savings/billing/cost/ROI.
- Phase 3: pure deterministic `offline-forecast-v1` using only frozen decision features and existing directive IDs, manifest/replay fixtures, episode duplicate suppression, and unknown => no early emission. Implement isolated control/static/dynamic schema/evaluator with strict pairing exclusions, n>=30/per-stratum>=10, required+safety 100%, no hard regression, quality LCB >= -0.02 for dynamic-control and dynamic-static, one-sided paired bootstrap 10,000 seed 20260713 for control-dynamic and static-dynamic, exact bytes/emissions, maximum verdict `eligible_for_user_review`, adoption pending. Fixtures are not real evidence.
- No production import/activation/config mutation; `production_enabled` remains false. No pruning/RL/online fitting/model-effort/intensity/dispatch/QA/guard changes. Reuse canonical Fleet modules and adapter projection conventions. Add portable invariant core-first only where the v2 contract requires it; preserve required Claude mirrors and Codex selective projection; explicitly defer unsupported OpenCode. Never edit runtime-owned config.toml.

Own/write only:

- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/checklist.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/plan_reviews/**`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/metrics.md`

Do not modify source, `dev_logs`, `test_logs`, or `pipeline_summary.md`. Include an executable file-by-file plan, stage class ownership, exact verification commands through `preflight.sh verification-runner`, requirements coverage, over/under-scope check, spec-significant risk check, expected changed-file list, and explicit production-dynamic-absent assertion. Leave a concise completion verdict in the plan artifacts.
