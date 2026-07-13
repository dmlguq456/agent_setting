# Pipeline Execution — Phase 0-5 상세

> SKILL.md 본문의 phase 요약 표(Pipeline Overview·stage-worker mapping)에서 pointer 된 실행 상세. [CONFIRM Gate] 문구·응답 4갈래 동작은 SKILL.md 본문이 checkable completion criterion 으로 잔류 — 여기엔 옮기지 않는다.

You (메인 에이전트) orchestrate by invoking each skill directly via the Skill tool.

### Phase 0: design-init

If `design_state.yaml` 부재 OR `--from init` 명시:

Invoke Skill: `design-init` with the design task as args.

design-init 이 **Design MCP (①) 를 자가 프로비저닝** — 설치(`npm install`)·등록(`claude mcp add design --scope user`)·스모크(`npm run smoke`). 부재 도구는 깔고 진행 (스펙 §0.5), OS 전역 설치만 한 줄 알림.

결과: `00_init/environment_check.md` + `design_state.yaml` 생성

### Phase 1: design-refs

Invoke Skill: `design-refs` with task description + (옵션) image paths as args.

레퍼런스 수집:
- 사용자 제공 이미지 (drag-drop 또는 path)
- 외부 검색 (autopilot-design 이 자체로 `Agent(자료팀, mode=web-image-search)` 호출 가능)
- 기존 디자인 system / paper figure / 이전 cycle 자산

결과: `01_refs/brief.md` + `_internal/references/` 폴더 (이미지·URL·메모)

### Phase 2: design-tokens

scope 가 `icon` 이면 skip 가능. 그 외엔:

Invoke Skill: `design-tokens` with the design path as args.

결과:
- `02_tokens/tokens.md` — 디자인 결정 사유
- `02_tokens/specimen.html` — palette/type/spacing specimen. **렌더 → Read 자가검증 필수** (대비·조화 확인 후에야 토큰을 component 가 소비). 토큰도 시각 시스템이라 값만 정하고 넘기지 않음
- `02_tokens/tokens.css` 또는 `tailwind.config.ts` — 실제 토큰 파일

기존 토큰 파일 발견 시 _확장_ (덮어쓰기 X).

### Phase 3: design-components

Invoke Skill: `design-components` with the design path as args.

내부: `Agent(디자인팀, mode=maker)` 호출 — maker 는 **시각 자가검증 루프** 를 거쳐 산출 (렌더→Read→수정).

결과:
- `03_components/` — 컴포넌트 spec / mockup / 실제 코드
- scope 따라:
  - `ui`: shadcn/ui 컴포넌트 + custom
  - `webapp`: 페이지 합성 + 전체 화면 `preview.html` (인터랙션 상태 포함)
  - `slide`: 슬라이드 비주얼 가이드 (마크다운) + **전 슬라이드 렌더** (장수 많으면 contact-sheet montage 한 장) + self-contained `slides.html` (한 슬라이드=한 section)
  - `icon`: SVG 또는 이미지
  - `diagram`: mermaid / 직접 SVG / excalidraw + **렌더 PNG**
- `--artifact standalone` 면 위 산출을 자체 완결 `preview.html` 로도 emit (브라우저 바로 열림)
- **렌더 이미지 첨부** — 컴포넌트/화면을 렌더해 본 결과를 산출과 함께 제시 (live-preview 패리티)

### Phase 4: design-review

quick-tier (`--intensity quick`) 시 skip. 그 외:

Invoke Skill: `design-review` with the design path as args.

내부 **두 게이트**: ① `Agent(디자인팀, mode=verifier)` — 별도 컨텍스트에서 TWO-LAYER 루브릭으로 기계 판정 (Layer-1: 콘솔 에러·레이아웃 붕괴·토큰계약 0-tolerance; Layer-2: vision passrate). ② `Agent(디자인팀, mode=critic)` — 렌더 이미지를 직접 보고 6축 _품질_ 비평.

결과: `04_review/verifier.md` (verdict + breakage/vision_passrate/status + 실패 항목 reason) + `04_review/critique.md` (6축).

🔴 / verifier `needs_work` 발견 시:
- `design_state.yaml` 의 `phases.review: failed`
- 사용자에 보고 후 components phase 재호출 권장 (깨짐은 critic 전에 verifier 가 차단)

### Phase 5: design-handoff

Invoke Skill: `design-handoff` with the design path as args.

결과:
- `05_handoff/handoff.md` — 사용된 컴포넌트·토큰 위치, frontend 개발자가 import 할 path, 재현 가이드
- `05_handoff/exports/` — 요청·scope 적합 시 converters (⑤) 산출: PDF / 단일 HTML 번들 / PPTX (`convert.mjs`)
- autopilot-spec 에서 위임된 경우: 호출자에 결과 path 반환
