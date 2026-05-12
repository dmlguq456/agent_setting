# audit

> 본 README는 Notion 페이지 [🔍 audit](https://www.notion.so/35e87c2bb75381cfb5c0f5f22500eccc)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Read-only multi-aspect audit / lint for `.claude_reports/{plans,research,documents}/*` artifacts. Single global entry — auto-detects artifact type from path prefix (plans=code; research=field-survey; documents=doc deliverable).

Type별 lint aspects:
- **doc** → facts / style / structure / cross-ref / coverage
- **research** → cards 정합성 / Tier consistency / coverage / cross-card
- **plans** → test results / lint / code review / TODO·미구현

기본 `--scope all`. **Report-only** — 본 skill은 절대 artifact를 수정하지 않습니다. autopilot-refine과 보완 관계 (refine = edit flow, audit = inspect flow).

## 호출 형식
```
/audit <artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]
```

- `<artifact_path>` — `.claude_reports/{documents,research,plans}/{name}` 또는 fuzzy match 가능한 단축명
- `--scope`: 강조할 측면 (override 1순위). 미명시 시 `auto` — artifact 특성(mode / refine 횟수 / status)을 보고 적절한 aspect 자동 선택
- `--read-only` (code plan 한정): 테스트 실행 없이 정적 lint만
- `--report-only`: 점검만, auto-fix dispatch 없이
- `--no-fact-check`: Stage B.5 fact-check 비활성화

## Auto-fix dispatch (default)
점검 결과 issue 발견 시 type별로 자동 dispatch:
- doc / research 산출물 → `autopilot-refine` (갈래 E)
- plans 산출물 → `autopilot-code --mode dev`

`--report-only` 명시 시 dispatch 없이 보고서만 작성.

## 산출물
보고서는 artifact root의 `_internal/audit/{YYYY-MM-DD}_{aspect}.md`에 누적.

---
*원본: `~/.claude/skills/audit/SKILL.md`*
