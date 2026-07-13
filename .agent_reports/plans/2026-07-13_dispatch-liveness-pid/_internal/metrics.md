# SD-17 separability 판정 기록 — inline 실행 근거

- 판정: **비분리 → inline** (스테이지 분사 안 함, depth-0 main 직접 · 브랜치 격리는 유지)
- 근거 1 (도메인): **분사-인프라 자기수정** — 수정 대상이 dispatch-headless/liveness/wait 자체라, 스테이지 분사는 고치려는 버그(ALIVE 오탐)에 스테이지 세션이 그대로 노출되는 메타리스크. durable lesson `lesson_lesson-분사-인프라-자기수정_92597e` 의 확립된 예외 경로.
- 근거 2 (규모): 4 파일 응집 변경(계약 1문단 + 함수 1 + 판정 분기 1 + 테스트) — 스테이지 분리의 컨텍스트 이득 미미.
- 의무 이행: (a) 본 기록 (b) 분리 가능한 부분 없음 — census 불요 단일 표면 (c) 계약-drift 은폐 없음 — core/OPERATIONS §5.10 을 먼저 갱신하고 adapter 가 따라감 (core-first-guard 통과 이력이 transcript 에 있음).
- 검증: 테스트 4 스위트 전부 PASS (plan.md §검증).
