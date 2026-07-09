## Mirror Generation (편집팀 — conditional, NOT default)

**Skip condition (default)**: strategy primary language == 사용자 작업 언어. strategy.md 자체가 사용자 영역 산출이라 mirror 단계가 불필요.

**Trigger**: strategy primary language ≠ 사용자 작업 언어 (예: academic paper strategy in English, 한국어 사용자 → strategy_ko.md mirror). 그때만 편집팀 모드 A 호출.

```
모드 A — {원본 언어}에서 {대상 언어}로 옮기기.
원본 strategy 경로: {strategy_path}
대상 출력 경로: {same directory}/strategy_{ko|en}.md
<agent-home>/adapters/claude/agents/editorial-team.md 의 모드 A 절차를 따른다.
<agent-home>/adapters/claude/agents/editorial-team.md 의 판교체 회피 절을 강제 적용 (한국어 산출 시). 사용자 표기 선호는 `mem profile 02_paper_writing_style` 보조 참조.
LaTeX 명령·논문 제목·학회 이름·약자·모델 이름·데이터셋·지표는 원본 언어 그대로, 그 외 일반 표현은 대상 언어로.
완료 시 파일 경로 + 한국어 요약 3-5 줄 + 의도적으로 한 표기 결정 한두 개만 돌려준다.
```

> Primary language 는 autopilot-draft SKILL.md 의 mode/subtype 표를 따름 (paper academic body → English / paper paste-ready cheatsheet → Korean / rebuttal·review → venue / presentation·report·proposal → audience). 사용자가 task description 에서 명시한 언어가 1순위 override.

Then report to the user: strategy path(s) + summary + QA verdict.
