---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: design-refs
description: "Use when invoking the portable design-refs capability. Collect external and user-provided visual references and create a brief."
argument-hint: "<design task> [--design <path>] [--refs <image paths>] [--no-web]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "Collect external and user-provided visual references and create a brief."
---

## Language Rule
- User-facing output follows the user's communication language unless the target audience requires another language.

## Design Resolution

1. `--design <path>` 있으면 그것
2. 없으면 `<artifact-root>/designs/` 또는 `<artifact-root>/spec/*/design/` 안 최신 `design_state.yaml`
3. 부재 → "먼저 `/design-init` 실행 필요"

## Procedure

> **컨텍스트 없이 시작하지 않는다 (스펙 §1.3 — slop 의 근원).** 브랜드·디자인 시스템·레퍼런스·톤이 전혀 없으면 _먼저 한 라운드 집중 질문_ 으로 brief 를 채운다 (시작점/제품 컨텍스트, 어느 측면의 변형인지, 톤·분량·청중·제약). 작은 수정·후속이면 생략. 빈칸이 잘못 채운 brief 보다 낫다.

### Step 1: 사용자 제공 자료 정리

`--refs <paths>` 또는 사용자 첨부:
- 이미지 (jpg/png/webp) — `01_refs/_internal/user_provided/` 로 복사 (또는 symlink)
- URL — `_internal/references_url.md` 에 기록
- 텍스트 브리프 — `01_refs/brief_input.md` 로 저장

### Step 2: 외부 레퍼런스 수집 (옵션, `--no-web` 미지정 시)

scope 별 검색 쿼리 자동 생성:
- `ui`: "<feature> dashboard UI inspiration", "<feature> mobile app UI"
- `slide`: "<topic> presentation slide design"
- `icon`: "<concept> icon set minimalist"
- `diagram`: "<concept> architecture diagram"

자료팀 위임:

```
Agent(자료팀, mode=web-image-search):
  "사용자 디자인 brief: <brief>
   검색 쿼리: <queries>
   max_results: 5 per query
   Output: <design_path>/01_refs/_internal/web_references/
   각 결과: thumbnail + URL + caption + 출처"
```

저작권 fair use — 레퍼런스는 _스타일 참고용_ 으로만 쓴다.

### Step 3: 기존 디자인 자산 review

`00_init/asset_inventory.md` 에서 식별된 기존 토큰·컴포넌트:
- 어떤 스타일인지 짧게 요약
- 새 작업과 일관성 유지 필요한 부분 명시

### Step 4: 사용자 paper figure 자료 (옵션, 음성 AI 관련 디자인 시)

`python3 <agent-home>/tools/memory/mem.py profile 01_paper_figure_style` + `python3 <agent-home>/tools/memory/mem.py profile 03_presentation_strategy` 실행 — 사용자 시각 시그니처 확인.

### Step 5: 브리프 작성

`01_refs/brief.md`:

```markdown
# Design Brief — <name>

## 의도
사용자가 무엇을 만들고 싶은가 — 1-2 줄.

## 사용자 / 청중
누가 보고 쓰는가.

## scope
ui / slide / icon / diagram / mixed

## 톤·무드
- 키워드 (minimal, playful, technical, warm 등) 3-5개
- 사용자 메모에서 추출 + 레퍼런스 inspection

## 레퍼런스
### 사용자 제공
- <path>: 짧은 설명
### 외부 검색
- <url>: 짧은 설명
### 기존 자산
- <path>: 짧은 설명

## 제약
- 기존 토큰 호환 (필수 / 옵션 / 새로 시작)
- 반응형 범위 (모바일 우선 / 동등)
- 접근성 (WCAG AA 최소)
- 학회·venue 스타일 (paper figure 인 경우)

## 다음 phase 입력
- 핵심 무드: ...
- 색감 방향: ...
- 폰트 방향: ...
```

### Step 6: design_state.yaml 업데이트

`phases.refs: done` + `brief_path: 01_refs/brief.md`.

## Output

- `01_refs/brief.md` — 디자인 브리프 (다음 phase 들 입력)
- `_internal/user_provided/` — 사용자 제공 이미지
- `_internal/web_references/` — 외부 검색 결과 (자료팀 산출)
- `_internal/references_url.md` — 외부 URL 모음

## Return Format

```
<design_path>/01_refs/ -- ✅ brief ready (N user refs + M web refs)
```

## Update agent memory

- 사용자 톤 키워드 누적 (자주 등장하는 무드 어휘)
- 자주 참고하는 레퍼런스 출처 사이트
- scope 별 효과적인 검색 쿼리 패턴
