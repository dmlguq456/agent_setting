# card 01 — Axis 1(core↔adapter drift) · Axis 6(계층 방향)

> inspector(축 1+6) + 오케스트레이터 spot-verify. 무게중심 = Claude bootstrap stale.

## 관찰
Codex(`AGENTS.md`)·OpenCode(`AGENTS.md`)는 intensity-first 모델·OPERATIONS 분리를 이미 반영했는데 **Claude bootstrap(`CLAUDE.md`)만 stale**. 또한 포터블 행동 규칙 일부가 Claude 에만 살아 있어 런타임 전환 시 소실.

## Axis 1 — 내용 drift
- **[1-1] P1** — `CLAUDE.md:46` `autopilot-code --qa quick` ↔ core "파이프 선택은 intensity, `--qa` 는 assurance override"(`WORKFLOW.md:165`·`CONVENTIONS.md:48`·§3#1). Codex/OpenCode 는 `intensity-not-qa` 로 정정 완료.
- **[1-2] P2** — `CLAUDE.md:120` 함정이 quick/standard 를 파이프 다이얼로 서술 ↔ `CONVENTIONS.md:13`.
- **[1-3] P2** — ScheduleWakeup `CLAUDE.md:67` 10–30분 vs `CONVENTIONS.md:604` "동일" 선언하며 15–20분.

## Axis 6 — 계층 방향(core-first 위반 잔재)
- **[6-1] P1** — "무조건 브랜치, 애매해도 브랜치"(`CLAUDE.md:54`, 근거 `drill g3`)가 core 에 대응물 없음(`OPERATIONS.md:84-88` 은 "본작업" 만). Codex/OpenCode 부재 → 포터블 행동 규칙이 Claude 에만. 제안: OPERATIONS §5.10 규모분기표로 승격.
- **[6-2] P1(판단필요)** — 응답 규율 §1~§3(`CLAUDE.md:56-77`) 상세 vs Codex/OpenCode Response Policy 4줄(`codex/AGENTS.md:82-86`·`opencode/AGENTS.md:68-72`). core `DESIGN_PRINCIPLES.md:133,196` 이 "응답 메타원칙 = adapter single source" 로 위임 → **어디까지 core 승격할지가 설계 결정**(GSD 종합).

## drift 아님(검증)
- `CLAUDE.md:70` opus/sonnet concrete 모델명 = `claude/ADAPTATION.md:75-76` 매핑에 명시된 정당한 어댑터 모델매핑.
