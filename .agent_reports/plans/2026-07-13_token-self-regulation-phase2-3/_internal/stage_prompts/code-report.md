# Depth-2 code-report handoff — Ponytail token self-regulation Phase 2/3

You are the fast-writer `code-report` stage for the thorough standard+ cycle.
This is a depth-2 file-only handoff; depth 3 is forbidden. Work only in the
assigned worktree. Do not edit source, plan/checklist, dev logs, test logs,
specs, runtime configuration, or the main checkout. Do not commit, push, merge,
install projections, or clean the worktree.

Read and obey the materialized Codex bootstrap, then read all artifacts under:

`.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/`

including the plan/checklist, implementation and both correction logs/reviews,
all three test passes/reviews, and retry2 command evidence. Inspect current
`git status --short --untracked-files=all`, `git diff --stat`, and changed-file
names read-only. Use the code-report Skill's artifact ownership contract.

## Ownership

After explicit write preflight, create only:

- `pipeline_summary.md`
- `final_report.md`

Do not rewrite any other stage's evidence. The report must be evidence-led and
must not silently convert diagnostic or synthetic evidence into production
claims.

## Required content

1. Verdict and scope: `within-spec`, Phase 2/3 implemented, Phase 1 output and
   zero paths preserved, production dynamic absent, adoption pending.
2. Exact canonical-registry stage slugs in order:
   - `token-self-regulation-phase23-code-r2-plan`
   - `token-self-regulation-phase23-code-r2-execute`
   - `token-self-regulation-phase23-code-r2-test`
   - `token-self-regulation-phase23-code-r2-execute-fix1`
   - `token-self-regulation-phase23-code-r2-test-retry1`
   - `token-self-regulation-phase23-code-r2-execute-fix2`
   - `token-self-regulation-phase23-code-r2-test-retry2`
   - `token-self-regulation-phase23-code-r2-report`
3. Changed files grouped by portable core/invariants, Fleet Phase 2/3 and tests,
   utilities, Codex realization, Claude mirrors, OpenCode defer, guards/manifest,
   and report artifacts. Use actual `git status` evidence; do not omit untracked
   source or fixture files.
4. Final retry2 verification commands/results, including AST 8, Phase 2 16,
   Phase 3 8, Fleet 214, portable guards `PASS=344 FAIL=0`, adaptation guards,
   boundary, manifest, doctor/runtime, runtime-projection, diff check,
   `production_dynamic_absent=1`, replay/evaluate/manifest hashes, exact bytes
   and emissions. Clearly label installed-runtime checks as installed main
   wiring evidence, not execution of this uninstalled worktree diff.
5. Limitations and unsupported contracts:
   - flat component-spec gate models only unrelated flat PRD; actual component
     SoT read evidence was used and marked;
   - native `apply_patch` target inference required explicit-preflight shell
     `apply_patch` fallback;
   - initial test boundary cache issue and cross-worktree fixed `/tmp` capture
     issue were corrected and independently retested;
   - retry2 item 15 recorded two non-substantive verifier assertion-selection
     exits before a narrow contract check passed; do not hide them;
   - OpenCode Phase 2/3 realization is explicitly deferred;
   - fixtures and synthetic 30 triplets are not real n>=30 experiment evidence;
     adoption stays `pending_user_decision`, maximum verdict remains
     `eligible_for_user_review`;
   - no runtime-owned `config.toml` mutation and no commit/push/merge/cleanup.
6. Next main action: review diff/evidence, commit and push intentionally, merge,
   refresh/strictly validate runtime projection after integration if desired,
   then clean the worktree. Do not perform these actions.

End the final worker response with `PIPELINE_REPORT_READY`.
