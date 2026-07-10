# dev_log — Phase F (SD-10 priority-0: dispatch-first dev-pipeline + SKILL Stage Graph)

## F1 — skills/autopilot-code/references/dev-pipeline.md
- **Closed the escape hatch**: replaced the unbounded `When still orchestrating in-session (e.g. …)` open list with a **closed two-condition fallback** ([a] direct/quick, [b] runtime has no headless dispatch); "dispatch is mandatory, not optional" for all other standard+.
- Added a top **one-shot wait (SD-14)** block: poll `dispatch-wait --parent <conductor-slug>` (exit 0/2/3), do not end the turn on a notification wait.
- **Rewrote Step 1/3/4/5 bodies dispatch-first**: each carries a `dispatch-headless.py --start … --worker-role code-<stage> --profile code-<stage> --model-role <role>` invocation + `dispatch-wait` harvest + a `[direct/quick] or [headless-unavailable] fallback: invoke Skill code-<stage>` line. Step 1 also states the SD-13 spec precondition check before dispatch.
- **Retry loop 6/7** re-execute/re-test → **re-dispatch** (same templates); conductor-side rollback (`git checkout <safety-commit>`) reads the Safety commit from checklist (file read, thin-conductor-safe).
- **plan-check Step 2** explicitly annotated as an **inline micro-stage** (not dispatched); independent plan review = bounded depth-2 review sub-worker, distinct from code-* stage-workers.
- **Verify**: `grep -c dispatch-headless.py` = 5 (≥4 ✓); `dispatch-wait` present in every durable stage; 4 fallback lines; the old open-ended escape-hatch sentence is gone (the `grep "e.g."` residual hits are regex-dot false positives in unrelated prose, not the escape hatch).

## F2 — skills/autopilot-code/SKILL.md Stage Graph
- Added a one-line `standard+` dispatch annotation under the Stage Graph table (each durable stage = depth-2 headless session; conductor passes paths + reads verdict/status; wait via dispatch-wait; direct/quick + plan-check inline). `grep -c "depth-2 headless"` = 1.
