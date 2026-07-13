# depth-2 stage worker — code-report (harness-installer 사이클 3)

당신은 depth-2 stage worker 입니다. worktree `/home/Uihyeop/agent_setting-wt/harness-installer-hooks` (브랜치 `harness-installer-hooks`) 에서 **code-report** 스테이지만 수행하고 종료합니다. depth-3 분사 금지.

## 입력 (반드시 Read)

- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/plan.md` + `plan/checklist.md` (최종 상태 — Phase 1~4 + G1~G3 체크, G4 는 이 스테이지가 판단)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/dev_logs/step_01_hook_reconfirm.md`, `step_02_generator_extension.md`
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/test_logs/test_report.md`, `test_logs/t0_t6_spec_pipeline_rebase.md`
- `.agent_reports/plans/2026-07-13_harness-installer-impl2/_internal/hooks_inventory.md` (갱신됨 — defer→adopt)
- `.agent_reports/plans/2026-07-13_harness-installer-impl2/final_report.md` (사이클 2 — 이번 보고서의 형식·구조 선례)
- `git status` / `git diff --stat` (실제 변경분 전수)

## 작업

1. **커밋**: 사이클 2 선례(phase 별 커밋 컨벤션)를 따라 이번 사이클 변경분을 논리적 단위로 커밋하세요 — 예: (a) `feat: harness-installer Phase 2 — spec 파이프 3종 hook PLUGIN_DATA 재기준 (sync-native-plugin.py 확장 + 생성물)`, (b) `docs: harness-installer Phase 3 — hooks_inventory.md defer→adopt`, (c) `test+report: harness-installer cycle 3 — code-test (29/29 PASS) + final_report`. 커밋은 **이 브랜치(`harness-installer-hooks`)에만** — main 머지 절대 금지, push 도 하지 마세요.
2. **`final_report.md` 작성**: `.agent_reports/plans/2026-07-13_harness-installer-hooks/final_report.md`. 사이클 2 `final_report.md` 와 동형 구조(한 줄 요약 / 목표 대비 결과 / Phase별 완료 현황 / 확정 목록 / QA·자율판단 기록 / 테스트 결과 요약 / PRD OPEN 절 갱신 필요 여부 / 커밋 목록+브랜치 상태 / Deferred·Open 항목)로 작성하세요. 반드시 포함:
   - **verdict**: 사이클 3 목표(spec 파이프 hook 3종 PLUGIN_DATA 재기준) 달성 여부.
   - **이식 완료 hook 목록**: `spec-skill-gate.sh`(PreToolUse/Skill)·`spec-read-marker.sh`(PostToolUse/Read)·`spec-sync-nudge.sh`(PostToolUse/Edit|Write|MultiEdit), 재기준 방식(env-prefix `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"`, canonical 무수정).
   - **이중-발화 안전성 결론**: T2 결과(마커 디렉토리 분리, 멱등, deny-wins fail-safe) 요약.
   - **테스트 결과**: 29/29 PASS, real-home 결정론 가드 결과(중간 해프닝 포함 — 최종 PASS).
   - **PRD/INST-D-6 갱신 필요 사항**: 이 스테이지는 `spec/prd.md`·`pipeline_state.yaml` 을 편집하지 않습니다 — main orchestrator 가 `autopilot-spec update` 로 반영할 내용만 기록:
     - INST-OPEN-1: "확정(채택 2 / defer 3 / 제외 나머지)" → "확정(채택 5 — git-state-guard·artifact-guard·spec-skill-gate·spec-read-marker·spec-sync-nudge / 제외 나머지)"
     - INST-D-6: defer 3종 → 채택 완료(cycle 3) 반영
     - `pipeline_state.yaml` decisions_locked / dev: 이월 항목 텍스트 갱신 필요
   - **커밋 hash 목록** + 브랜치 상태(`harness-installer-hooks`, main 미머지).
3. **checklist G4 처리**: G4("code-report 가 PRD/state 갱신 포인터 기록")는 위 final_report.md 작성으로 충족되므로 `[x]` 로 갱신하세요(prd.md 자체 편집은 여전히 하지 않음).

## 비스코프

- `spec/prd.md`·`pipeline_state.yaml` 직접 편집 금지 — 기록만.
- main 머지·push·worktree 정리 — main orchestrator 몫.
- 새 테스트 작성/실행 — code-test 가 이미 완료.

완료 후 커밋 해시 목록 + final_report.md 경로를 짧게 보고하고 종료하세요.
