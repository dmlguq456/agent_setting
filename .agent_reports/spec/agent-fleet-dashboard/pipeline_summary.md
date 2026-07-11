# agent-fleet-dashboard — Spec Pipeline Summary

- **Date**: 2026-07-01 (v1) · 2026-07-10 (v2)
- **Mode**: cli (터미널 TUI 도구)
- **Status**: spec done (v2)
- **Placement**: 별도 컴포넌트 `spec/agent-fleet-dashboard/` — 기존 `spec/prd.md`(Unified Memory System) 무수정.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| research | 기술 tap 매핑 조사 (Explore) | `research/agent-fleet-dashboard/01_tap_mechanics.md` | 하네스별 discovery·tap·liveness, file-cited + jobs.log open/running 버그 발견 |
| research | prior-art 스캔 (경량 web) | `research/agent-fleet-dashboard/00_prior_art.md` | herdr 정체(실OSS 멀티플렉서, 채택X) + 규모 작음 → 얇게 직접 빌드 + curses 확정 |
| spec | PRD 작성 (lean) | `prd.md` v1 | intake skip(입력 충분), 단일 mode cli, scaffold 이월 |

## 주요 결정 (locked)
- F-1 외부 관찰자(zero-injection), 유일 write=우리 소유 statusline per-session tap.
- F-2 3계층(프로세스 스캔 백본 + 하네스별 passive enrichment + curses) · 2섹션(fleet + dispatch).
- F-3 하네스 비대칭 허용(opencode rate-limit·effort 결손 칸 —).
- F-4 statusline.sh 확장 → `~/.claude/.statusline/<sid>.json` per-session(단일 파일 덮어쓰기 해소).
- F-5 dispatch uncapped + jobs.log `{open,running}` tolerant (어휘 버그 동반 정리 권고).
- F-6 herdr 4-상태 어휘 + 기존 liveness 재사용(herdr 자체 채택 X).
- F-7 zero-dep python curses, tmux 세로 사이드 페인 런처.
- F-8 sparkline·herdr 소켓·커스터마이즈 후순위(스코프 밖).

## v2 update (2026-07-10) — drift 흡수 + stage-dispatch parity + UI 가독성

| Step | Action | Result |
|---|---|---|
| 정보 수집 | 현행 `tools/fleet/` 전수 실측 (Explore, file:line-cited) + `spec/stage-dispatch/prd.md` SD-3·§9-13 대조 + jobs.log wild 행 실측 | drift 목록 + parity 갭 + wild pipe 구분자 오파싱 발견 |
| update | v1 snapshot → `_internal/versions/v1/prd.md`, prd.md v2 덮어쓰기 | §4 [v2 기준선] 신설(07-01~07-10 진화 소급 승인), §4.5 SD-F1~F4, §4.6 F-9~F-13, §0.5 F-1 확장, §3 `w` 키, §6 wild drift 행 |

- 계기: 사용자 "fleet UI 최적화·개선 — 워크플로우를 못 따라감 + 아쉬운 점 다수" (2026-07-10). drift CLEAR 판정 → 자율 진행.
- 핵심 결정: 스테이지 row 단계명 라벨(SD-F1) / conductor breadcrumb 자식 실측 연동(SD-F2) / 스테이지 자기 model·effort(SD-F3) / pipe 공백·콤마 tolerant(SD-F4) / 가독성 5건(F-9~F-13).

## Next
`/autopilot-code --mode dev --intensity standard "fleet UI 개선 — PRD v2 §4.5·§4.6"` (worktree, conductor 분사 — 파이프 자체가 SD-F1~F3 라이브 검증 fixture). 순서 = PRD v2 §Next 1~4.

## Minor-log
- 2026-07-10 (v2 minor #1): §4.6 에 **F-14 (세션 표시명 = 하네스 세션 제목)** 추가 — 사용자 요청("fleet 세션명만이라도 요약된 것으로"). 소스 실측(claude `ai-title` transcript 라인·opencode `session.title`) + 공식 문서 확인(진행형 auto-retitle 하네스 미지원 → fleet 표시층 담당). 구현 = fleet-ui-v2 수확 후 후속 사이클 (render/model 파일 겹침 → 큐잉).
- 2026-07-11 (v2 minor #4): §4.6 에 **F-18 (loop·drill·mem-워커 귀속 정밀화)** 추가 — 사용자 점검 요청 + drill 실발사 실측 2종(runner 이중 표시 dedup 갭 / mem distiller·curator·refresher 워커가 부모 cwd·env 상속으로 세션 자식·drill 그룹 오귀속). environ 마커(MEM_DISTILL·FLEET_TITLE_REFRESH) 태깅 + case명·cwd 상관 dedup. 구현 = fleet-f18 사이클.
- 2026-07-10 (v2 minor #3): §4.6 에 **F-17 (라이브 제목 refresher — sidecar + no-tools haiku 워커)** 추가, F-16 영어 실현을 F-17 1차로 재지정 — 사용자 승인("haiku 같은 거 써서 agent로… 알아서"). transcript 직접 쓰기는 위험 판정(라이브 원본·내부 포맷·zero-injection 위반) → fleet 소유 sidecar + statusline debounce 트리거 + D-14 no-tools 패턴. 구현 = F-15 수확 후 사이클.
- 2026-07-10 (v2 minor #2): §4.6 에 **F-15 (분사 row 레이아웃 재설계)** + **F-16 (표시명 짧게·영어)** 추가 — F-14 출하 직후 사용자 피드백 4건("가로로 늘어짐이 최대 불만" / "옵션은 중요 관찰 요소, 숨기지 말고 잘 설계" / "워크플로우에 맞게 더 최적화" / "queued 오라벨 의문"). F-9(c) 성분-드롭 접근을 F-15 재배치로 대체. queued 오라벨 = registry-only liveness 유도로 해소. 구현 = fleet-f15 사이클.

## Version History
- v1 (2026-07-01): 초기 PRD. research 2건 근거.
- v2 (2026-07-10): drift 흡수([v2 기준선]) + stage-dispatch 관제 parity(SD-F1~F4) + UI 가독성(F-9~F-13). snapshot = `_internal/versions/v1/prd.md`.
