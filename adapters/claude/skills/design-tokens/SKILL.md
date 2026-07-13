---
name: design-tokens
description: "디자인 토큰(색·타이포·간격) 정의·생성 sub-skill"
argument-hint: "<design path or app path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "디자인 토큰(색·타이포·간격) 정의·생성 sub-skill"
---

## Language Rule
- Korean output, English token names (color hex, font family names, spacing units).

## Design Resolution

`design_state.yaml` 발견:
- `<artifact-root>/designs/<name>/` 또는 `<artifact-root>/spec/design/`

## Pre-Check

- `phases.refs: done` 검증 → brief 없이는 token 결정 불가
- `00_init/asset_inventory.md` Read — 기존 `tokens.css` 또는 `tailwind.config.ts` 발견 여부

> **토큰 = 단일 계약 (DESIGN_PRINCIPLES §9).** canonical 파일 = **앱이 실제 import 하는 파일** (`<project_root>/app/globals.css` 의 `@theme` / `styles/tokens.css` / `tailwind.config.ts`) _하나뿐_. design 이 그 파일을 소유·편집, code 는 참조만. **`designs/02_tokens/` 에는 `tokens.md`(결정 근거) + `specimen`(시각 증명) 만 둔다** — 토큰 값 자체는 위 canonical 파일이 단일 보유. `design_state.tokens_path` 는 _앱 실제 파일_ 을 가리킨다.

**codebase seed (빌트앱·기존 토큰 — design-system awareness)**: 앱 코드를 먼저 스캔해 _실사용 토큰_ 추출·seed — `globals.css`/`tailwind.config` 의 색·폰트·spacing·radius + 컴포넌트의 반복 hex·px(인라인 흩어진 값 포함). _현 코드를 계약으로 승격_ 후 정련한다 (앱 실사용 토큰 추출·seed — 빈 캔버스에서 발명 X 가 아니라 현 코드부터).

기존 토큰(=앱 실제 파일) 발견 시:
- 기본 mode: **확장** (앱 파일 보존 + 새 토큰 추가, 그 파일에 직접)
- 명시 요청 시: **재설계** (앱 파일 `_internal/versions/v{N}/` snapshot 후 신규)

## Procedure

### Step 1: brief Read

`01_refs/brief.md` 의 _색감 방향 / 폰트 방향 / 톤·무드_ 추출.

### Step 2: 디자인 결정 (`02_tokens/tokens.md`)

작성 대상 절: Color Palette(Brand/Neutral/Semantic) · Typography(Font Family/Scale) · Spacing · Radius · Shadow · Motion — 각 절은 값 + **결정 사유** 1줄. 전체 worked exemplar = [references/tokens-exemplar.md](references/tokens-exemplar.md).

### Step 3: specimen 시각 자가검증 (필수 — 토큰을 component 가 소비하기 _전_)

토큰은 그 자체로 시각 시스템 (palette / type / spacing) 이라, 값만 정하고 넘기지 않는다. **렌더해서 본 것** 으로만 완료.

`02_tokens/specimen.html` — 자체 완결 단일 파일 (inline `<style>`, 외부 빌드 의존 0):
- **color swatch** — 각 색 칩에 hex 표기 + 주요 foreground/background 쌍의 **WCAG contrast ratio** 명시 (본문 ≥4.5:1, large ≥3:1 통과 여부 라벨)
- **type scale 전체** — xs~2xl 까지 실제 글자로 렌더 (line-height 포함)
- **spacing / radius / shadow ruler** — 각 단계를 시각 막대·박스로

루프: specimen.html 을 렌더해 **이미지로 직접 보고** 대비·조화 자가 비평 (대비 미달 쌍 / 색 충돌 / scale 점프 불균일) → 토큰 조정 → 재렌더, 깨끗할 때까지. 대비는 `mcp__design__eval_js` 로 `getComputedStyle` 수치 확인. 공통 렌더 흐름(`preview`→`screenshot`→`view_image`)은 [_design_rules.md §시각 자가검증 루프](../../roles/modes/design/_design_rules.md) 단일 SoT. **이 검증을 통과해야 component 가 토큰을 소비** (specimen-consume gate — design-tokens 고유).

### Step 4: 실제 토큰 파일 작성

CSS variables(`tokens.css`) 또는 `tailwind.config.ts` — 스택에 따라 둘 중 하나 또는 둘 다. 템플릿 = [references/templates.md](references/templates.md).

### Step 5: 기존 토큰 호환 + 버전 스냅샷

토큰 변경은 spec 의 `_internal/versions/v{N}/` 와 같은 방식으로 추적한다. 기존 `tokens.css`/`tailwind.config.ts` 또는 `02_tokens/tokens.md` 발견 시 **덮어쓰기·확장 _전_**:

1. 직전 `02_tokens/tokens.md` + 실제 토큰 파일(`tokens.css`/`tailwind.config.ts`)을 `_internal/versions/v{N}/` 로 자동 snapshot (N = `_internal/versions/` 의 기존 최대 +1).
2. 새 토큰 추가 (확장 mode — 기존 키 보존) 또는 신규 작성 (재설계 mode — 명시 요청 시).
3. 변경 narrative 를 `design_summary.md` 에 통합 기록 — _바뀐 토큰 / old→new 값 / 사유 / 날짜_. design cycle 의 **단일 변경 이력 source** (spec 의 `pipeline_summary.md` 미러). 별도 CHANGELOG 두지 않음.
4. 충돌 시 사용자 confirm.

> **minor/major 판정** (DESIGN_PRINCIPLES §4 동일 원리): minor (1~2 토큰 미세조정) → snapshot 생략 + `design_summary.md` minor-log 만. major (palette/scale 재설계·신규 axis) → `v{N}` snapshot. 누적 minor 5+ 시 `/audit` alert.

### Step 6: design_state.yaml 업데이트

`phases.tokens: done` + `tokens_path: <실제 파일 경로>` + `tokens_version: v{N}` (현재 토큰 버전) + `tokens_updated: <date>` + `specimen: 02_tokens/specimen.html` + `tokens_verified_visually: true`.

> `tokens_version` / `tokens_updated` 는 autopilot-code 의 _역방향 drift 체크_ 가 읽는 필드 — 토큰이 직전 코드 작업 이후 갱신됐는지 판정하는 anchor.

## Output

- `02_tokens/tokens.md` — 결정 사유 + 토큰 값
- `02_tokens/specimen.html` — swatch·type·spacing 시각 검증 산출 (렌더 → Read 자가검증 완료)
- 프로젝트 루트의 `tokens.css` 또는 `tailwind.config.ts` (사용자 confirm 후 작성·확장)
- `_internal/versions/v{N}/` — 직전 토큰 snapshot (major 변경 시; `tokens.md` + 토큰 파일)
- `design_summary.md` — 토큰 변경 이력 narrative (단일 변경 이력 source; spec `pipeline_summary.md` 미러)

## Return Format

```
<design_path>/02_tokens/ -- ✅ tokens decided (N colors, K type scale, M spacing)
```

기존 확장:
```
<design_path>/02_tokens/ -- ✅ tokens extended (+K new tokens, existing preserved)
```

## Update agent memory

- 사용자 자주 선택하는 색감 방향
- 폰트 선호 (Inter / system / serif 자주 선택)
- shadcn default 에서 자주 바꾸는 토큰
- 다크 모드 적응 패턴
