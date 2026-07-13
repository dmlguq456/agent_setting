# 하네스 (claude-design-harness-spec.md 기반 구성)

본 pipeline 은 _"자기가 만든 결과물을 픽셀로 보고 고치는 피드백 루프"_ 를 본체로 한다. 구성 요소·위치:

| # | 컴포넌트 | 위치 | 역할 |
|---|---|---|---|
| ① | **Design MCP Server** | `~/.claude/tools/design-mcp/` (`mcp__design__*`) | preview·screenshot·getConsoleLogs·eval_js·view_image·image_metadata. 시각 피드백 루프의 본체 |
| ② | **Verifier subagent** | `Agent(디자인팀, mode=verifier)` | 별도 컨텍스트 독립 검수 — 2-layer 깨짐 게이트 + vision passrate (Layer-1: 콘솔·레이아웃·토큰 0-tolerance; Layer-2: 시각 일관성 passrate) |
| ③ | **디자인 규칙** | `roles/modes/design/_design_rules.md` | 슬롭 회피·비주얼 기본값·스케일·HTML 규약·변형 처리 (프롬프트) |
| ④ | **Scaffolds** | `~/.claude/scaffolds/` | deck_stage·tweaks_panel·device_frames·design_canvas·image_slot |
| ⑤ | **Converters** | `~/.claude/tools/design-mcp/convert.mjs` | PDF · 단일 HTML 번들 · PPTX |
| ⑥ | **Post-write hook** | `~/.claude/hooks/design-postwrite.sh` | design HTML 저장 시 콘솔 자동 체크 (`DESIGN_POSTWRITE_HOOK=0` 으로 opt-out) |

design-init 이 ① 를 자가 프로비저닝 (설치·등록·스모크). 부재로 멈추지 않는다 (스펙 §0.5).
