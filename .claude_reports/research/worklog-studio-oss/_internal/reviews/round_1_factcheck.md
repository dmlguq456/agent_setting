# QA fact-check — round 1 (thorough)

조사일 2026-06-23. 오케스트레이터가 핵심 픽 + "놀라운 주장"(rename·고star·archived)을 `gh api`(authenticated)로 재실측해 축 파일 주장과 verbatim 대조.

| repo | 축 파일 주장 | gh api 재실측(2026-06-23) | 일치 |
|---|---|---|---|
| agentclientprotocol/agent-client-protocol | 3,480 · Apache-2.0 · 2026-06 · archived No | ⭐3480 · Apache-2.0 · 2026-06 · false | ✅ |
| aaif-goose/goose | 50,057 · Apache-2.0 · No (block→aaif-goose 이전) | ⭐50058 · Apache-2.0 · 2026-06 · false | ✅ |
| continuedev/continue | 34,284 · Apache-2.0 · No | ⭐34285 · Apache-2.0 · 2026-06 · false | ✅ |
| earendil-works/pi | 64,881 · MIT (mariozechner/pi-mono→earendil 이전) | ⭐64886 · MIT · 2026-06 · false | ✅ rename 실재 확인 |
| sourcegraph/cody-public-snapshot | 3,802 · Apache-2.0 · **archived Yes(dead)** | ⭐3802 · Apache-2.0 · 2025-08 · **true** | ✅ dead 확인(채택 금지 근거) |
| codesandbox/sandpack | 6,167 · Apache-2.0 · push 2025-04(정체) | ⭐6167 · Apache-2.0 · 2025-04 · false | ✅ |
| vercel/chatbot | 20,517 · NOASSERTION | ⭐20517 · NOASSERTION · 2026-05 · false | ✅ |
| gradio-app/trackio | 1,542 · MIT | ⭐1542 · MIT · 2026-06 · false | ✅ |
| leeoniya/uPlot | 10,256 · MIT | ⭐10256 · MIT · 2026-04 · false | ✅ |
| dmtrKovalenko/odiff | 3,067 · MIT | ⭐3067 · MIT · 2026-06 · false | ✅ |
| VoltAgent/awesome-design-md | 92,362 · MIT | ⭐92363 · MIT · 2026-06 · false | ✅ 고star 실재(큐레이션 리스트 인기, 코드 의존 아님) |
| jonschlinkert/gray-matter | 4,459 · MIT | ⭐4459 · MIT · 2025-06 · false | ✅ |

**Verdict**: 🟢 날조 0. 모든 stars/license/archived/push 가 일치(±1~5 stars 는 실측 시점 라이브 드리프트). 핵심 검증 2건 — cody snapshot=archived(dead) 확인, pi/goose/ACP rename 실재 확인. 통념 정정(vercel artifacts=Pyodide non-iframe, wandb 대시보드 클로즈드)은 축 파일에 근거 기재됨.

**잔여 한계**: GitHub 비인증 API 한도(60/hr)는 4축 에이전트 실측으로 이미 소진 → 오케스트레이터 재검증은 `gh api`(인증) 경로로 수행. "내가 lift할 모듈 경로"의 일부는 에이전트가 README 근거 "추정" 표기한 것으로, 실제 구현 진입 시(autopilot-spec) 소스 직접 확인 필요.
