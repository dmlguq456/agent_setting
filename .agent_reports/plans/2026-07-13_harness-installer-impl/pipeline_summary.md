# harness-installer 사이클 1 pipeline summary — 2026-07-13

## 사이클
plan → execute(Phase 0~7) → test → report (stage-dispatch, depth-2)

## 변경 파일
- `tools/install/paths.py` (신규)
- `tools/install/projector.py`
- `tools/install/manifest.py`
- `tools/install/drivers/{claude,codex,opencode}.py`
- `tools/install/verifier.py`
- `tools/install/installer.py`
- `tools/install/bootstrap.py` (신규)

## 내용
- symlink projection(INSTALL_LAYOUT 레시피 기계화) + hash-manifest(drift/reapply, `git merge-file` 3-way) + 3-런타임 driver(기존 adapter 스크립트 wrap, 재구현 없음) + verify check 목록 + `installer.py` cmd_* 실배선 + `mem import`/PATH launcher.
- Phase 7: Codex plugin 채널 wrap in-cycle 완료, **Claude plugin content generator + `install --plugin` claude 경로는 plan 자체 경계에 따라 다음 사이클로 명시 이월**.

## 검증
- code-test verdict: **PASS**
- functional E2E 51/51 green (`.agent_reports/plans/2026-07-13_harness-installer-impl/test_logs/e2e_lifecycle.md`)
- real-home 결정론 가드 통과(실행 전/후 real `~/.claude`·`~/.codex`·`~/.config/opencode` 무변경)
- 사이클 중 code-review 2라운드(Phase 1+2, Phase 3+4) — Phase 3+4 에서 HIGH(real 파일 데이터 유실 가능) 1건 발견 → 수정·재검증 완료(`_internal/dev_reviews/phase_03_04_fix.md`)

## 인시던트
- Phase 5 검증 중 검증 스크립트의 env-scoping 실수(Bash 호출 간 export 유실)로 실제 `~/.claude/settings.json` 손상(`Extra data: line 265`) — **installer 코드 결함 아님**. main orchestrator 가 이미 기계적 truncation 으로 복구·바이트 동일성 검증 완료(conductor 재확인: 현재 valid JSON, `.pre-incident-fix.bak` 백업 보존) — 잔여 action item 없음. 상세: `_internal/dev_reviews/INCIDENT_real_home_touched.md`(당시 기록, 문서 자체는 미갱신), `final_report.md` §5.
- 재발 방지: 이번 code-test 는 단일 self-contained 스크립트 + mktemp hard-code + 시작/종료 sha256 trap 으로 재구성, real-home 무결성 실행 전/후 동일함을 자체 검증.

## 산출물
- plan: `.agent_reports/plans/2026-07-13_harness-installer-impl/plan/plan.md` (status: done)
- checklist: `.agent_reports/plans/2026-07-13_harness-installer-impl/plan/checklist.md`
- dev_logs: `.agent_reports/plans/2026-07-13_harness-installer-impl/dev_logs/*.md` (8개)
- dev_reviews: `.agent_reports/plans/2026-07-13_harness-installer-impl/_internal/dev_reviews/*.md`
- test_logs: `.agent_reports/plans/2026-07-13_harness-installer-impl/test_logs/e2e_lifecycle.md`
- 최종 보고: `.agent_reports/plans/2026-07-13_harness-installer-impl/final_report.md`
- cross-project 요약: `.agent_reports/analysis_project/code/harness-installer-cycle1.md`

## spec 상태 갱신
- `.agent_reports/spec/harness-installer/pipeline_state.yaml` `phases.dev`: `in_progress` 유지(하향 아님, done 아님) — 사이클 1(installer CLI 경로, Phase 0~6 + Codex plugin wrap)은 완료했으나 PRD §0.5 원칙 1(2-채널 하이브리드)의 Claude plugin 축이 명시적으로 미완료라 전체 dev phase 를 `done` 처리하지 않음. 근거: `final_report.md` §2, §6.

## 커밋
- `24e2295` chore: Safety checkpoint before harness-installer-impl execution
- `a1490a1` feat: harness-installer Phase 0-2 — paths, projector, manifest
- `5aaf51a` feat: harness-installer Phase 3-4-6 — drivers, check lists, bootstrap
- `7e9b090` feat: harness-installer Phase 5 — installer.py cmd_* wiring
- `06fcece` feat: harness-installer Phase 7 (P1 in-cycle) — codex plugin channel wrap
- `a6fab8c` chore: harness-installer-impl plan status -> done (P1 partially deferred)
- 브랜치: `harness-installer-impl` (워크트리 `/home/Uihyeop/agent_setting-wt/harness-installer-impl`)
- merge·push·worktree 정리는 미수행 — 메인 오케스트레이터 몫.
