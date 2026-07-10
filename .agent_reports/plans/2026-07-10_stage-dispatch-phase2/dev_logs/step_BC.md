# dev_log — Phase B (core docs) + Phase C (wrapper + dispatch-wait)

## Phase B — core doc increments (core-first)
- **B1** `core/OPERATIONS.md §5.10`: added `one-shot 대기 계약 (§8.5.7 SD-14)` bullet after the stealth-death guard (line 99), and `spec 전제 선보장 (§8.5.4 SD-13)` clause inside the ③ conductor narrative (line 94). Noted in the SD-14 clause that layer (b) Stop gate is HELD for Claude (probe + #38651). No duplication of the existing stealth-death guard (`grep -c stealth-death` = 1).
- **B2** `core/WORKFLOW.md §5`: appended the diffusion clause ("`standard+` 각 durable 스테이지 = 독립 headless 세션 …") to rows autopilot-research/spec/design/draft/refine, and inserted a **new autopilot-lab row** (setup/eval stages dispatch; long/async training run stays inline). `독립 headless 세션` now in 7 rows (6 added + pre-existing code row).
- **B3** `core/CONVENTIONS.md §1` Depth contract: generalized the stage-worker parenthetical to `code-* for autopilot-code; the homologous stage set for autopilot-draft/research/spec/design/lab`. Stage-graph Dispatch-policy column (line 34) is intensity-keyed and capability-neutral — **no edit required** (confirmed).
- **B4** `core/DESIGN_PRINCIPLES.md §8` (line 226): appended one SD-14 determinism sentence (wait/harvest is part of the deterministic flow; Claude holds the Stop gate). §0.7 left as-is (PRD §14 remains SoT — no forced insertion).

## Phase C — SD-14 wrapper increments + dispatch-wait helper
- **C1** `resolve_agent_home()`: was `AGENT_HOME`→`ROOT`; now mirrors `agent-home.sh` order (`AGENT_HOME`→`CLAUDE_HOME`→`$HOME/agent_setting`→`$HOME/.claude`, each validated by `core/CORE.md`)→`ROOT`. Fixes SD-14b② registry split (writer vs liveness/wait/Stop readers). **Verified**: `AGENT_HOME= CLAUDE_HOME= dispatch-headless.py --dry-run … | grep job_registry` → `/home/Uihyeop/agent_setting/.dispatch/jobs.log` == `$(agent-home.sh)/.dispatch/jobs.log`.
- **C2** start-env block: added `AGENT_DISPATCH_SELF_SLUG = args.slug` (line 412) so the Stop gate / dispatch-wait can match `parent=<my slug>` open children. **Verified**: source assertion.
- **C3** depth-1 `depth_note`: appended the one-shot wait clause (poll with dispatch-wait, do not end turn on notification wait; re-dispatch on SUSPECT/DEAD). Depth-2 stage-worker note untouched. **Verified**: register→prompt file has `one-shot process` ×1 at depth-1, ×0 at depth-2.
- **C4** new `utilities/dispatch-wait.sh` (+ `.test.sh`), dual-placed via symlink under `adapters/claude/utilities/` (matching liveness). POSIX sh, `set -u` (dash has no pipefail), reuses `dispatch-liveness.sh` (no reimplementation). Exit codes: **0** target children done, **2** alive/max reached (re-call), **3** SUSPECT/DEAD (diagnose). `--max` clamped ≤600, default interval 20s, default max 120s. No background/nohup. **Verified**: `dispatch-wait.test.sh` PASS (6 cases: missing jobs, done-only, foreign parent, alive→2, dead→3, clamp).

## Regression
- `dispatch-liveness.test.sh` PASS (unchanged).
- `python3 ast.parse dispatch-headless.py` OK.
