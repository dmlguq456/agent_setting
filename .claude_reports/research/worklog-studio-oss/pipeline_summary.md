# Research Survey Pipeline Summary: worklog-studio-oss

- **Date**: 2026-06-23
- **Query**: worklog 디자인/실험 스튜디오를 위한 OSS 선행 조사 (에이전트-백엔드 + local-first + 하네스 재사용 렌즈), 4축
- **Mode**: technology (GitHub OSS 레포 조사로 적응 — 학술 paper 파이프 대신 WebSearch + GitHub API 실측)
- **Depth**: medium (후보 전수 평가 ~28종)
- **QA**: thorough (오케스트레이터 gh api 재실측 fact-check 통과)
- **Status**: done
- **From-Stage**: N/A (신규)

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | 4축 OSS 조사 | topic: worklog-studio-oss · mode technology |
| 1.5 | Scope clarification | skip | 브리프 50자↑·mode 명시·제약 명시 → skip 조건 충족 |
| 2–3 | 4축 병렬 조사 (general-purpose ×4) | 28 후보 카드 | 각 에이전트 GitHub API(curl) 메타데이터 실측 + README/소스 fetch |
| 4a | Synthesis (00_briefing) | 1 capstone | 축별 1픽 추천표 + 크로스-축 조립도 + OD/OCD 델타 |
| 4b | QA fact-check | 🟢 날조 0 | 12 핵심 repo gh api 재실측 ↔ 축 파일 verbatim 일치 |

## Artifacts
- 축 카드: `axis1_bridge.md` · `axis2_preview.md` · `axis3_tracking.md` · `axis4_manifest_design.md`
- 종합: `00_briefing.md` (축별 1픽표 + 조립도 + OD/OCD 델타 + 리스크/탈락 후보 + 다음 파이프)
- QA: `_internal/reviews/round_1_factcheck.md`

## 축별 1픽 (요약)
| 축 | 1픽 | license |
|---|---|---|
| 1 브리지 | Zed ACP (프로토콜) + goose/continue 보완 | Apache-2.0 |
| 2 프리뷰 | Sandpack(self-host) + onStreamPart/renderify | Apache-2.0 |
| 3 추적 | Trackio sqlite_storage.py + uPlot | MIT/MIT |
| 4 허브·검증 | gray-matter+DESIGN.md / odiff exit-code | MIT/MIT |

## Decision Points
| Step | Decision | Response | Action |
|---|---|---|---|
| 1.5 | scope clarify? | skip(자명) | 자율 진행 |
| pipeline shape | 학술 paper 파이프 vs OSS 레포 조사 | OSS 적응 | WebSearch+GitHub API, 4축 커스텀 포맷 |
| 4b | QA 재실측 경로 | 비인증 한도 소진 → gh api | 인증 경로로 12 repo 재검증, 통과 |

## 다음 파이프라인
`/autopilot-spec --mode app "worklog 디자인/실험 스튜디오 — ACP 브리지 + Sandpack 프리뷰 + Trackio·uPlot 추적 + gray-matter manifest·odiff 검증"` → 확정 후 `/autopilot-code --mode dev`
