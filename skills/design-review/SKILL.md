---
name: design-review
description: "디자인 결과물 6축 비평·토큰 계약 점검 sub-skill"
argument-hint: "<design path or app path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "디자인 결과물 6축 비평·토큰 계약 점검 sub-skill"
---

## Language Rule
- Korean output.

## Design Resolution

`design_state.yaml` 발견.

## Pre-Check

- `phases.components: done` 검증
- 검토 대상 식별:
  - 코드: `03_components/*.tsx`
  - 스크린샷 (있으면)
  - 또는 사용자 제공 mockup

## Procedure

review 는 **두 게이트**다 — verifier 가 _깨졌는가_ (콘솔·레이아웃·의도) 를 먼저 걸러내고, critic 이 _얼마나 좋은가_ (6축 품질) 를 본다.

### Step 1: verifier 게이트 (독립 검수 — `Agent(디자인팀, mode=verifier)`)

별도 컨텍스트에서 산출물을 기계적으로 점검 (만든 사람 관대함 제거).

**기대 출력 스키마 (verifier TWO-LAYER 루브릭):**
- `verdict: done | needs_work` — 런타임 분기 키 (하위 호환 유지)
- `breakage: has_errors | none` — Layer-1 hard gate 결과
- `vision_passrate: <float>` — Layer-2 `[vis]` passCount/total
- `status: verified | needs_review | needs_iteration | failed | unavailable`
- `layer1_checks[]` — `[det]` 항목별 `{id, passed, reason}` (항상 전체)
- `layer2_checks[]` — `[vis]` 항목별 `{id, dimension, passed, reason}` (항상 전체)
- `gaps[]` — `needs_work` 시 실패 항목의 `{dimension, reason}` 목록
- **PASS → 침묵** (`verdict + breakage + vision_passrate` 한 줄); **FAIL → 텍스트 진단만** (gaps reason 목록 + breakage); **스크린샷 미반환** (verifier 자기 컨텍스트 안에서만 view_image).

**라운드 상한 (이 skill 이 루프 오너):**
- console/error 재검수 재호출 ≤ 3회 (OCD `MAX_DONE_ERROR_ROUNDS = 3`)
- verify-and-iterate (verifier → maker 수정 → 재검수) ≤ 2라운드 (OCD `BENCHMARKS.md:24`)
- 상한 도달 시 현재 verifier 상태 그대로 반환 + `round_cap_hit: true` 마커 추가; 강제로 `done` 으로 coerce 금지.

```
Agent(디자인팀, mode=verifier):
  "검수 대상: 03_components/preview.html (또는 slides.html)
   풀 스윕 — TWO-LAYER 루브릭.
   Layer-1 (0-tolerance): console.errors_zero / layout.no_overflow / no_overlap / no_zero_box / components.token_contract.
   Layer-2 (vision): layout.hierarchy_present / color.palette_consistent / typography.role_consistent / content.intent_match / content.no_slop_filler / components.structure_sound.
   PASS → 침묵 (verdict + breakage + vision_passrate 한 줄). FAIL → gaps reason 텍스트만. 스크린샷 메인 반환 X."
```

`needs_work` 면 — `design_state.yaml` `phases.review: failed`, 사용자 보고 후 **critic 까지 가지 않고** components phase 재호출 권장.

### Step 2: 검토 대상을 **렌더해서 본다** (critic 입력 — 렌더한 이미지로 본다)

critic 은 렌더한 _이미지_ 를 직접 본다 (좌표·코드가 아니라 눈으로). 공통 렌더 흐름과 scope 별 렌더 표(ui/webapp·slide·icon·diagram)는 [_design_rules.md §시각 자가검증 루프](../../roles/modes/design/_design_rules.md) 단일 SoT — 로드해 그대로 돈다.

> 렌더 불가 환경이면 그 사실을 critique 에 명시하고 _본 범위만_ 비평 (못 본 것을 본 척 X).

### Step 3: 디자인팀 critic 호출

```
Agent(디자인팀, mode=critic):
  "Visual review for <design_name>.
   대상: 03_components/ 또는 위 식별된 자료
   Brief: 01_refs/brief.md
   Tokens: 02_tokens/tokens.md

   6축 점검:
   1. 시각 위계 (hierarchy) — 시선 흐름 자연스러운가, 강조점이 맞는가
   2. 정렬·여백 (alignment, spacing) — 일관성, breathing room
   3. 접근성 (a11y) — WCAG AA contrast, keyboard nav, focus indicator, alt text
   4. 반응형 — breakpoint 깨짐 (모바일/태블릿/데스크탑)
   5. UX 흐름 — 로딩/에러/빈 상태, undo/취소
   6. 톤 일관성 — 토큰 일치, 다른 컴포넌트와 어울림

   산출: 04_review/critique.md
   우선순위 (🔴/🟡/🟢) 별 정리, 5-7개 핵심 발견만, 칭찬할 부분 별도"
```

### Step 4: critique 검증

🔴 발견 시 사용자에 보고:
- 어떤 axis 에서 문제
- 어떤 컴포넌트·파일
- 수정 방향 (코드 수정은 components phase 재호출 또는 maker mode 위임)

🟡 만 있으면 _다음 phase 진행 가능_, 단 사용자에 안내.

🟢 만 — 통과.

### Step 5: design_state.yaml 업데이트

- verifier `needs_work` OR critic `🔴 ≥ 1`: `phases.review: failed`
- verifier `done` AND critic `🔴 0`: `phases.review: done` (+ `verifier: passed`)

`04_review/verifier.md` 에 `breakage` + `vision_passrate` + `status` + 실패 항목 `reason` 기록.

> **`needs_review` 처리 (`vision_passrate` 0.85–0.99 → `verdict: done`)**: 페이즈는 통과하되, 실패한 `[vis]` 항목 reason 을 사용자에 노출한다 — critic 🟡 핸들링과 동형. 회귀 은닉 금지 (HONEST_SCORES). `round_cap_hit: true` 마커 있으면 "상한 도달, 미수렴" 안내 포함.

## Output

- `04_review/verifier.md` — verifier 판정 (verdict + breakage/vision_passrate/status + 실패 항목 reason; layer1/layer2 전체 체크 목록)
- `04_review/critique.md` — critic 6축 별 발견 사항
- `04_review/summary.md` — 종합 판정 (verifier + critic) + 다음 액션

## Return Format

```
<design_path>/04_review/ -- ✅ review passed (M minor, K praise) [vision_passrate=X.XX, status=verified]
```

```
<design_path>/04_review/ -- 🔴 N major issues found — see critique.md [breakage=has_errors|none, vision_passrate=X.XX]
```

`round_cap_hit: true` 시: `(상한 도달 — 마지막 status: <status>, 미수렴)` 추가.

## Update agent memory

- 자주 발견하는 UX 함정 (예: "이 프로젝트는 빈 상태 누락이 흔함")
- 사용자가 자주 받아들이는/거부하는 비평 패턴
- 6축 중 자주 fail 하는 축
