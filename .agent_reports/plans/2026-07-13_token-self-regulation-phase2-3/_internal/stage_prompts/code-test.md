# Depth-2 code-test handoff — Ponytail token self-regulation Phase 2/3

You are the separate deep reviewer/verifier for the thorough `code-test` stage.
This is a depth-2, file-only handoff. Do not dispatch any child (depth 3 is
forbidden). Work only in the assigned worktree. Do not commit, push, merge,
install runtime projections, mutate `$CODEX_HOME/config.toml`, or touch the main
checkout.

Read and obey the Codex bootstrap in the materialized dispatch prompt, then read:

- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/checklist.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/dev_logs/implementation.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/dev_reviews/implementation_review.md`
- component v2 PRD, experiment contract, and pipeline state

The flat spec gate limitation is already recorded: the gate models only the flat
unrelated PRD, while actual component-SoT read evidence exists. Do not treat this
as a reason to skip verification.

## Ownership and behavior

- Source and existing dev evidence are read-only. Do not fix source or alter
  plan/checklist/dev logs/pipeline summary.
- You may write only
  `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/test_logs/**`
  and `_internal/test_reviews/**`, after explicit write preflight.
- Use the adapter verification runner for every executable verification command.
- Run graduated syntax/import/smoke/functional/integration checks. For this CLI
  and library change, public CLI replay/evaluate is the behavioral runtime
  observation. Record stdout hashes or exact deterministic comparisons without
  persisting prompt/session content.
- Stop on the first substantive failure, record exact evidence, and return
  `RETURN_TO_CODE_EXECUTE`; do not edit source.
- This is a genuinely separate headless verification pass, so it may report
  independent verification relative to code-execute. It must not claim external
  adversary review or depth-3 QA.

## Required assertions

Verify the exact v2 contract, not just test presence:

1. Phase 2: sha256 session digest only, exact invocation/zero/emission/reason and
   inserted UTF-8 bytes, monotonic exact-session delta with decrease/unavailable
   counters, no token estimate without exact tokenizer provenance, atomic bounded
   stale-safe locking/store (`<=8KiB/file`, `<=256 files`, `<=2MiB`, oldest first),
   privacy and always fail-open behavior.
2. Phase 1 compatibility: production output and zero paths remain byte-for-byte
   stable; L2 accounting appears only in `kv|json` and never hook output.
3. Phase 3: frozen pure `offline-forecast-v1`, existing directive IDs, deterministic
   replay, episode duplicate suppression/reopen, unknown means no early emission,
   strict control/static/dynamic pairing exclusions, n>=30 and per-stratum>=10,
   safety+required 100%, no hard regression, both quality LCBs >= -0.02, both paired
   comparisons using 10,000 bootstrap resamples seed 20260713, exact bytes/emissions,
   maximum `eligible_for_user_review`, adoption pending, fixtures synthetic only.
4. Isolation: no production import/activation/config mutation; dynamic remains
   false; no model/effort/intensity/dispatch/QA/guard or pruning/RL/online fitting
   change. OpenCode remains explicitly deferred; Claude Fleet mirrors and Codex
   selective projection remain synchronized.

## Required verification matrix

Run these commands in order through
`$AGENT_HOME/adapters/codex/bin/preflight.sh verification-runner` and save exact
command, exit status, duration where available, and relevant summary in test logs:

1. AST parse of all changed Python implementation/test files from plan section 8.
2. `python3 -m unittest -v tools.fleet.tests.test_token_budget`
3. `python3 -m unittest -v tools.fleet.tests.test_token_experiment`
4. `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`
5. public CLI replay twice with byte-identical output and evaluator smoke on a
   synthetic 30-triplet input; confirm fixtures are non-evidentiary and adoption
   remains pending.
6. `bash hooks/portable-guards.test.sh`
7. `bash tools/adaptation-guard.test.sh`
8. `bash tools/check-adaptation-boundary.sh`
9. `python3 tools/build-manifest.py --check`
10. `$AGENT_HOME/adapters/codex/bin/preflight.sh doctor`
11. `$AGENT_HOME/adapters/codex/bin/preflight.sh doctor --runtime`
12. `$AGENT_HOME/adapters/codex/bin/preflight.sh runtime-projection`
13. `git diff --check`
14. Explicit production-dynamic-absent scan over `utilities/token-budget.py`,
    `adapters/codex/hooks/userprompt-lifecycle.py`,
    `adapters/codex/bin/preflight.sh`, and `adapters/codex/hooks/hooks.json` for
    `offline-forecast-v1`, `token_experiment`, and `production_dynamic_enabled`.
15. Explicit manifest candidate hash, canonical/Claude mirror byte parity, Codex
    projection symlink, and OpenCode absence/defer checks.

The runtime projection checks are read-only installed-wiring evidence; do not
install this worktree. If they validate the currently installed main checkout,
say so explicitly and do not claim they exercised the uninstalled diff.

Write at least:

- `test_logs/verification.md`
- `test_logs/commands.log`
- `_internal/test_reviews/thorough_review.md`

End with exactly one verdict token in your final message:
`READY_FOR_CODE_REPORT` or `RETURN_TO_CODE_EXECUTE`.
