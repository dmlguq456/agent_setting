# Checklist — stage-dispatch Phase 2 (code-execute)

slug: 2026-07-10_stage-dispatch-phase2 · branch: stage-dispatch-phase2 · qa=standard · intensity=strong

## Decision Points
- **SD-14b① Stop probe (Phase A)**: `Stop` hook does **NOT** fire under `claude -p` (probe 2026-07-10, exit 1, no sentinel). Cross-check: CC issue #38651 (Stop empties `-p` output), #40506/#20063. → **Stop gate HELD** (E2 unregistered, on-disk only). SD-14 ships via depth_note + dispatch-wait.

## Phase status

- [x] **Phase A** — probe done. Verdict: Stop unfired → E2 registration held. Record: `_internal/dev_reviews/phaseA_stop_probe.md`.
- [x] **Phase B** — core doc increments (core-first)
  - [x] B1 OPERATIONS §5.10 one-shot wait contract + SD-13 spec precondition
  - [x] B2 WORKFLOW §5 diffusion rows + new autopilot-lab row
  - [x] B3 CONVENTIONS §1 capability-neutral clarifier
  - [x] B4 DESIGN_PRINCIPLES §8 SD-14 determinism note
- [x] **Phase C** — wrapper + dispatch-wait.sh
  - [x] C1 resolve_agent_home registry-gap fix
  - [x] C2 AGENT_DISPATCH_SELF_SLUG child env
  - [x] C3 depth-1 depth_note one-shot wait clause
  - [x] C4 utilities/dispatch-wait.sh + test
- [x] **Phase D** — SD-12 stage-worker profiles (4 fragments + 4 yaml + README + --check ok ×4, instance build clean)
- [x] **Phase E** — hooks
  - [x] E1 stage-dispatch-reminder.sh (SD-11, soft) REGISTERED + 5 conformance PASS
  - [x] E2 conductor-stop-gate.sh (SD-14b) — UNREGISTERED (held), on-disk + 4 CLI unit PASS
  - [x] E3 HOOKS.md catalog rows (parity note → Phase G)
- [x] **Phase F** — SD-10 dev-pipeline dispatch-first (closed 2-cond fallback, dispatch-headless.py×5, dispatch-wait per stage) + SKILL Stage Graph annotation
- [x] **Phase G** — adapter bootstrap parity (claude CLAUDE.md §0(C) + codex/opencode AGENTS.md one-shot parity)
- [x] **Phase H** — diffusion: 5 pipes gained stage-worker table + contract (via 5 parallel in-session 개발팀)
- [x] **Phase I** — drill case handoff artifact drill_case_stage_dispatch/ (fixture builds spec-backed repo; assert HARD passes; loops/ untouched)
- [x] **Phase J** — instrumentation.md (pilot seed row, SD-OPEN-2 observation table); post-it handoff pending final step

## Fix cycle (code-test 회귀 2건 — projection/mirror 동기화)
- [x] **Fix-1** utilities/dispatch-wait.sh·.test.sh 를 `tools/check-adaptation-boundary.sh` 의 Codex/OpenCode `UTILITY_DEFERRED` 목록에 추가 (dispatch-liveness.sh 선례 따름) — 2곳(check_codex_utility_projection, check_opencode_utility_projection).
- [x] **Fix-2** `adapters/claude/hooks/{conductor-stop-gate.sh,stage-dispatch-reminder.sh}` 심볼릭 링크 생성 (canonical `hooks/` collapse 기본 원칙, 기존 hooks 심링크 패턴과 동일).
- [x] **Fix-3** `skills/**` 10파일 Phase 2 편집분을 `adapters/claude/skills/**` 미러로 복사 (byte-equivalent 회복; diff 는 순수 추가분이었음, 충돌 없음).
- [x] **Fix-4** `python3 tools/build-manifest.py` 재실행 — 미러 변경분 반영해 manifest.json 재생성.
- 검증: `bash tools/check-adaptation-boundary.sh` → `OK: adaptation boundary checks passed`. 기록: `dev_logs/step_fix.md`.
- Commit: (아래 참조)

## Safety commits
- `5ae8c8a` Phase A+B (probe verdict + core docs)
- `e97d916` Phase C (wrapper + dispatch-wait)
- `d27ab12` Phase D (profiles)
- `3dfb993` Phase E (hooks)
- `7a74889` Phase F (SD-10 dev-pipeline)
- `976ba3a` Phase G (adapter parity)
- `a63b708` Phase H+I+J (diffusion + drill + instrumentation)
- (final: plan status → implemented)

## Deferred (out of code-execute write class — for conductor/code-report)
- J3 post-it handoff memo (drill case awaiting loops/ install · SD-14b Stop-gate held · SD-11 deny-escalation deferred) — DB write, not code-execute class.
- `pipeline_summary.md` Decision Points sync — code-report class (§5.8 lock).
