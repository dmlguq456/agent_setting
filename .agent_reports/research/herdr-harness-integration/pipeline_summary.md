# Research Pipeline Summary — Herdr × Current Harness

- 날짜: 2026-07-20
- 모드: technology / standard
- 상태: 완료
- 사용자 의도: 현재 세팅을 제거·대체하지 않고 Herdr 장점을 빠르게 이식·확장

## 수행 내역

| 단계 | 결과 |
|---|---|
| 공식 자료 조사 | Herdr stable 문서·v0.7.4 릴리스·소스, 공식 Codex subagent 문서 확인 |
| 로컬 실측 | Herdr 0.6.6/protocol 12 실행, Claude/Codex integration v4, Codex `multi_agent` stable/enabled 확인 |
| 하네스 분석 | native subagent, registered headless dispatch, Fleet, hook projection, 기존 PRD 대조 |
| 동시 교차 검토 | Herdr 담당과 하네스 담당을 병렬 실행하고 서로 주장 반박·수정 |
| 검증 | dispatch 동시성 테스트 3건 PASS, capability route 18 tests PASS, 관련 근거 line 확인 |

## 최종 판정

Herdr는 다중 에이전트의 **지속 터미널 런타임·관찰·입력 전송**에 강하다. 그러나 자체 토론 프로토콜이나 작업 의미론을 제공한다고 보기는 어렵다. 현재 하네스는 역할·QA·attempt·worktree·artifact·fallback 의미론에 강하다. 따라서 Herdr를 선택적 PTY/session transport와 관찰 소스로 추가하고, 현재 하네스를 권위 있는 실행·보증 계층으로 유지한다.

산출물은 [00_briefing.md](00_briefing.md), [analysis_summary.md](analysis_summary.md), [06_implementation.md](06_implementation.md)에 요약돼 있다.
