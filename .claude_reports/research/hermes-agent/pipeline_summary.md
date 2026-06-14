# Research Survey Pipeline Summary: Hermes Agent (벤치마킹)
- **Date**: 2026-06-15
- **Query**: Nous Research Hermes Agent 심층 기술 해부 + Claude Code 세팅 벤치마킹 갭 분석 (+ 보안 축: OpenClaw 취약점 vs Hermes 보완 주장)
- **Mode**: technology
- **Depth**: deep
- **QA**: adversarial (quality + fact-check + claim-verify, round 1 + 정정 라운드)
- **Status**: done

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | technology/deep | topic: hermes-agent |
| 2 | 정찰 + 축별 1차 소스 조사 (Agent ×4) | 4 cards | axis1 아키텍처 / axis2 loop·self-improve / axis3 memory / axis4 security |
| 3 | 보고서 합성 (Agent ×2) | 8 reports | technology 템플릿 → 벤치마킹 deliverable 적응 |
| 4 | adversarial QA (Agent ×3 병렬) | 🔴 0 | quality 🟡6 / factcheck 🔴0 / claimverify 0 killed·4 abstain(이미 격리) |
| 4b | 정정 라운드 (Agent ×1) | 🟡 3건 해소 | GHSA CVSS swap·confidence 일관성·auto-memory 수치 확정 |
| 5 | pipeline summary | 본 파일 | |

## 주요 정정 (브리프 → 1차 소스)
- "47 tools" → 70+ tools / ~28 toolsets (버전 drift; "tools"≠"skills 166개")
- Atropos = **training-time RL environments framework** (weight 학습; Hermes 런타임에 미통합). 런타임 self-improvement = weight 고정 + skill/memory 축적.
- Honcho = **Plastic Labs 외부 FastAPI 서비스** (dialectic user modeling, 사후 비동기 reasoning)
- auto-memory(우리) = "빈 레이어 0개" 아님 → 메모리 dir 15 / 인덱스 14 / 파일 58, 단 `.claude` config repo cwd만 빈 레이어(per-cwd 특성)
- "Hermes가 OpenClaw 보안 전부 보완·완전 안전" = ❌ 기각 (SEO산 비교, Hermes SECURITY.md 본인이 "in-process 방어는 containment 아님" 명시)
- OpenClaw = 실재 프로젝트(Peter Steinberger, github.com/openclaw/openclaw), CVE-2026-25253(1-click RCE 8.8) 등 1차 검증

## Artifacts
- Cards: cards/axis{1,2,3,4}_*.md
- Reports: 00_briefing ~ 07_security (8개)
- Reviews: _internal/reviews/round_1_{quality,factcheck,claimverify}.md

## Next Pipeline
- 채택 결정 시: 지침 문서 수정 = 직접 Edit + drill 회귀테스트 / 새 루프·스킬 신설 = autopilot-spec → autopilot-code
- **북극성 PRD** (자율 에이전트 플러그인 → 설치 프로그램, 먼 미래): `/autopilot-spec` — 본 research + 07_security 체크리스트가 필수 입력. 별도 세션 권장.
