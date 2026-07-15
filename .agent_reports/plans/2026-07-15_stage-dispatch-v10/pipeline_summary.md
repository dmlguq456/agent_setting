# Pipeline summary

- Verdict: PASS — SD-44, SD-45, SD-46, SD-47 and all six v10 acceptance criteria implemented.
- Spec significance: `within-spec`; PRD unchanged.
- Changed source areas: core workflow/operations contracts; topology registry/validator; route compiler and worker validator; spec transaction helper; portable artifact guard and generated Claude projection; Claude/Codex/OpenCode dispatch/preflight bridges; independent fixtures and manifest.
- Verification: portable guards 359/359; focused v10 fixtures 23/23; manifest and 10 projection groups current; generated projection regression PASS; routing contract PASS; strict context footprint PASS; adaptation boundary PASS; wording census zero; `git diff --check` PASS.
- Independent assurance: native Codex SD-45 risk review PASS after fixes; no unresolved high/medium findings.
- Artifacts: `plan.md`, `checklist.md`, `_internal/execution_log.md`, `_internal/sd45-risk-review.md`, `test_logs/final-verification.md`, `final_report.md`.
- Unsupported contract: registered Codex headless stage execution was blocked by sandbox network policy; evidence in `_internal/failed-code-plan-network.json` and `_internal/failed-code-plan-runtime.json`. Inline stage fallback is explicit.
- Delivery: commit pending. This worker could not create the linked-worktree `index.lock` because `/home/Uihyeop/agent_setting/.git/worktrees/stage-dispatch-v10` is read-only. Nothing is staged. Main orchestrator owns the prepared commit, harvest, integration verification, push, and guarded cleanup; no merge/push occurred here.
