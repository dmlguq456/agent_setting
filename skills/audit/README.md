# audit

> 본 README 는 `SKILL.md` 의 GitHub 표시용 mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Read-only multi-aspect audit / lint for `<artifact-root>/{plans,research,documents}/*` artifacts. Single global entry — auto-detects artifact type from path prefix (plans=code; research=field-survey; documents=doc deliverable).

Type별 lint aspects:
- **doc** → facts / style / structure / cross-ref / coverage
- **research** → cards 정합성 / Tier consistency / coverage / cross-card
- **plans** → test results / lint / code review / TODO·미구현

doc / research artifact는 추가로 **dual-perspective** 점검:
- **P1 — vs last major baseline**: `pipeline_summary.md` `## 마이너 변경 로그` + `_internal/versions/v{N}/` 스냅샷 diff. 누적된 minor가 _집합적으로_ artifact를 어디로 drift시켰는지.
- **P2 — vs universal principles**: 현재 artifact 상태의 aspect-by-aspect 점검 (시점 무관).
- 두 결과 cross-correlate → P2 finding의 file:line이 P1 minor entry의 Files touched에 매칭되는지 확인 → "최근 도입 (fix 우선순위 高)" vs "기존 잔존" 분류.

기본 `--scope auto`. **Report-only** — 본 skill은 절대 artifact를 수정하지 않습니다. autopilot-refine과 보완 관계 (refine = edit flow, audit = inspect flow).

## Cadence (언제 audit 실행)

- **사용자 명시 `/audit <artifact>`** — 즉시
- **AUDIT_HINT_THRESHOLD (default 5 minors since last major)** 도달 시 — autopilot-refine 또는 직접 Edit 작업 종료 후 chat alert로 권장 (자동 실행 X)
- **자동 fix chain dispatch에서 spawned audit** — autopilot-refine 또는 autopilot-code의 fix routing에서

## 호출 형식
```
/audit <artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]
```

- `<artifact_path>` — `<artifact-root>/{documents,research,plans}/{name}` 또는 fuzzy match 가능한 단축명
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
*원본: `<agent-home>/skills/audit/SKILL.md`*
