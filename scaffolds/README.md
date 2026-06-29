# Design scaffolds

Reusable starting points so the agent never re-draws bezels, deck shells, or tweak panels by
hand. Component ④ of `claude-design-harness-spec.md`. Each is a self-contained HTML file the
agent **copies into the design artifact folder** and fills in — then renders & verifies via the
Design MCP visual loop.

| scaffold | file | 용도 | 핵심 |
|---|---|---|---|
| `deck_stage` | `deck_stage/deck_stage.html` | 슬라이드 덱 | 1920×1080 고정 캔버스 자동 스케일(레터박싱) · 키보드 내비(← → Space Home End) · 슬라이드 카운터 · print→PDF (1 슬라이드=1 페이지) · 스피커노트 슬롯 |
| `tweaks_panel` | `tweaks_panel/tweaks_panel.html` | 변형(variant) 처리 | host 프로토콜(패널은 CSS 변수만 set) · localStorage 영속화 · 큐레이션 스와치(자유 피커 X). **새 버전 요청 = 파일 늘리지 말고 여기 트윅 추가** |
| `device_frames` | `device_frames/device_frames.html` | 목업 베젤 | `.ios-frame`(폰: 노치·상태바·홈 인디케이터) + `.browser-frame`(데스크탑 크롬: 트래픽 라이트·주소창). 순수 CSS |
| `design_canvas` | `design_canvas/design_canvas.html` | 2+ 옵션 비교 | 반응형 grid, 옵션별 라벨. 방향 탐색 시 |
| `image_slot` | `image_slot/image_slot.html` | 이미지 placeholder | drag-drop + 클릭 업로드, localStorage 영속화. **이미지를 SVG 로 위조하지 말고** 이걸로 자리만 |

## 사용 흐름

1. design-components 가 scope·요청에 맞는 scaffold 를 골라 design 폴더로 복사
   (예: `slide` → `deck_stage.html` → `03_components/slides/slides.html`).
2. 예시 블록을 실제 콘텐츠로 교체 (주석의 HOW TO USE 참조).
3. Design MCP `preview` → `getConsoleLogs` → `screenshot` → `view_image` 로 렌더 검증.
4. handoff 단계에서 converters (`~/.claude/tools/design-mcp/convert.mjs`) 로 PDF/PPTX/번들 출력.

## 규약

- 모든 scaffold 는 외부 빌드 의존 0 (브라우저로 바로 열림) — standalone artifact 패리티.
- 본문 ≥ 24px(덱) / 히트타깃 ≥ 44px(모바일) 등 스케일 규칙은 `roles/modes/design/_design_rules.md`.
- 모두 렌더 검증 완료 (deck_stage·tweaks_panel·device_frames·image_slot·design_canvas, 콘솔 에러 0).
