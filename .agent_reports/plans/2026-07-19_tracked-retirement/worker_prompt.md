/autopilot-code — tracked/untracked 모드 전면 퇴역 (standard, 승인 완료)

플랜: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_tracked-retirement/plan.md
플랜의 체크리스트 A→E를 순서대로 전부 실행하라. 핵심 계약:

1. 삭제 대상은 "모드"다 — `.untracked` 플래그·/track 토글·프롬프트 리마인더·게이트 배지·생성순서 게이트. 존치 대상은 모드와 무관한 guard 기능(canonical-root 강제, spec_touch route 검사, worktree sibling 규약)과 spec-read·core-first·git-state 게이트다. 혼동 금지.
2. "untracked" 문자열을 기계적으로 치환하지 마라. 각 히트를 판정해서 git-untracked(git 의미), route-record `tracked_gate_evidence`, 과거 기록물(.agent_reports/research·documents·analysis_project)은 그대로 둔다.
3. .agent_reports/spec/** 는 읽기만 한다. 쓰지 마라(등재는 메인 세션 몫).
4. fleet 시각 변경은 제거만 한다 — 빈자리에 대체 표식을 발명하지 마라(healthy-silent).
5. 편집 전 core/CORE.md를 읽어라(코어 문서 편집 게이트). 문서 재표현은 "tracked project" → "spec-backed project" 결로 통일한다.
6. 검증: rsync 미러 동기화 → fleet 전체 스위트 + hooks/portable-guards.test.sh + tools/adaptation-guard.test.sh + tools/install/profile-activation.test.sh 전부 exit code로 게이트 → 전수 grep 잔존 0 확인 → COLUMNS=168 python3 tools/fleet/fleet.py --once 스모크.
7. 완료 시: worktree 브랜치에 커밋(메시지: `refactor(workflow): retire tracked/untracked mode`), 로그 마지막에 3줄 계약(RESULT: pass|fail / EVIDENCE: 테스트·grep·스모크 요약 / FILES: 변경 파일 수)을 남겨라.
