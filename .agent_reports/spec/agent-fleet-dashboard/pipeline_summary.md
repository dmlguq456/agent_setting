# agent-fleet-dashboard — Spec Pipeline Summary

- **Date**: 2026-07-01 (v1) · 2026-07-10 (v2) · 2026-07-12 (v3) · 2026-07-13 (v4/v5) · 2026-07-14 (v6) · 2026-07-15 (v7/v8)
- **Mode**: cli (터미널 TUI 도구)
- **Status**: spec v8 done (관제 신뢰성·세션 제어·분사 정책 연동) — F-25~F-27 구현은 별도 autopilot-code 사이클, F-28은 stage-dispatch v9 착륙 후
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

## v3 update (2026-07-12) — minor 5건 승격 흡수 + audit 반영

| Step | Action | Result |
|---|---|---|
| audit | minor 누적 5 도달 트리거 — spec↔코드 정합 전수 점검 (`_internal/audit/audit_2026-07-12T0910.md`) | 🔴 0 / 🟡 3 / 🟢 20 — forward 계약 15/15 코드 실재, 역-drift 는 문서측만 |
| update | v2 snapshot → `_internal/versions/v2/prd.md`, prd.md v3 | §4.7 신설(F-14~F-19 를 §4.6 에서 분리 — 섹션 의미 괴리 해소), §3 `--demo` 소급 등재, §9 모듈 트리 현행화(titles·refresh_title·memory·demo·tests), 🧠 글리프 위계 명문화, 확정 결정 v3 블록 |

- **Minor-log 리셋**: 아래 5건은 v3 에 흡수 완료 — 이력 보존용으로만 유지. 새 minor 카운트는 v3 기준 0 부터.

## Minor-log (v2 시대 — v3 에 흡수 완료, 이력 보존)
- 2026-07-11 (v2 minor #5): §4.6 에 **F-19 (메모리 관측 패널)** 추가 — 사용자 확정("fleet에 memory 기능 추가", 방향 논의 후 추천안 승인). 소스 = Unified Memory System PRD v15 Cluster J write-events.jsonl(D-37)+graveyard tail, `collectors/memory.py` 신설(read-only·tolerant·additive), 🧠 요약행+`a` 토글 상세+alert 편입(ceiling·distill 무소식). F-18b(워커 태깅)와 상보 — 워커(프로세스)와 효과(이벤트). 구현 = Cluster J 저널 사이클과 병렬 가능(표면 비겹침, 저널 부재 시 graveyard-only degrade). ⚠️ **minor 누적 5 도달 — 컨벤션상 `/audit` 점검 권장 시점** (다음 major 때 v3 로 minor 5건 흡수 고려).
- 2026-07-10 (v2 minor #1): §4.6 에 **F-14 (세션 표시명 = 하네스 세션 제목)** 추가 — 사용자 요청("fleet 세션명만이라도 요약된 것으로"). 소스 실측(claude `ai-title` transcript 라인·opencode `session.title`) + 공식 문서 확인(진행형 auto-retitle 하네스 미지원 → fleet 표시층 담당). 구현 = fleet-ui-v2 수확 후 후속 사이클 (render/model 파일 겹침 → 큐잉).
- 2026-07-11 (v2 minor #4): §4.6 에 **F-18 (loop·drill·mem-워커 귀속 정밀화)** 추가 — 사용자 점검 요청 + drill 실발사 실측 2종(runner 이중 표시 dedup 갭 / mem distiller·curator·refresher 워커가 부모 cwd·env 상속으로 세션 자식·drill 그룹 오귀속). environ 마커(MEM_DISTILL·FLEET_TITLE_REFRESH) 태깅 + case명·cwd 상관 dedup. 구현 = fleet-f18 사이클.
- 2026-07-10 (v2 minor #3): §4.6 에 **F-17 (라이브 제목 refresher — sidecar + no-tools haiku 워커)** 추가, F-16 영어 실현을 F-17 1차로 재지정 — 사용자 승인("haiku 같은 거 써서 agent로… 알아서"). transcript 직접 쓰기는 위험 판정(라이브 원본·내부 포맷·zero-injection 위반) → fleet 소유 sidecar + statusline debounce 트리거 + D-14 no-tools 패턴. 구현 = F-15 수확 후 사이클.
- 2026-07-10 (v2 minor #2): §4.6 에 **F-15 (분사 row 레이아웃 재설계)** + **F-16 (표시명 짧게·영어)** 추가 — F-14 출하 직후 사용자 피드백 4건("가로로 늘어짐이 최대 불만" / "옵션은 중요 관찰 요소, 숨기지 말고 잘 설계" / "워크플로우에 맞게 더 최적화" / "queued 오라벨 의문"). F-9(c) 성분-드롭 접근을 F-15 재배치로 대체. queued 오라벨 = registry-only liveness 유도로 해소. 구현 = fleet-f15 사이클.

## Version History
- v1 (2026-07-01): 초기 PRD. research 2건 근거.
- v2 (2026-07-10): drift 흡수([v2 기준선]) + stage-dispatch 관제 parity(SD-F1~F4) + UI 가독성(F-9~F-13). snapshot = `_internal/versions/v1/prd.md`.
- v3 (2026-07-12): minor 5건(F-14~F-19) 승격 흡수 — §4.7 분리 + audit 🟡 3건 반영(§3 --demo·§9 현행화·글리프 위계). snapshot = `_internal/versions/v2/prd.md`. audit = `_internal/audit/audit_2026-07-12T0910.md`.
- v4 (2026-07-13): F-20 Codex dynamic usage-window runtime-currentness 계약. snapshot = `_internal/versions/v3/prd.md`.
- v5 (2026-07-13): F-21 Codex native state DB title + JSONL fallback, cross-harness neutral title sidecar/provider. Claude-only refresher/`slug` fallback 계약 폐기. snapshot = `_internal/versions/v4/prd.md`.
- v6 (2026-07-14): F-22 terminal-width-responsive session name zone + longer responsive sidecar title contract; F-23 recursive-storm containment. snapshot = `_internal/versions/v5/prd.md`.
- v7 (2026-07-15): F-24 portable worker attribution(`AGENT_SESSION_ROLE=worker`) + Codex rollout fd 소유권 단일화. snapshot = `_internal/versions/v6/prd.md`. (본 항목은 v8 update 시점 소급 기록 — v7 사이클이 summary 동기를 누락.)
- v8 (2026-07-15): F-25 상태 판정 단일 모델(소스 우선순위·hysteresis·state_evidence) + F-26 interactive 세션 레지스트리 1급(unused 배지·provenance) + F-27 제한적 세션 제어(kill+정리, Non-goal 부분 반전, 사용자 확인) + F-28 분사 정책 연동 계약 선고정(route record/topology 소비, 구현 후행). §0.5 경계 개정(자동 제어 0·사용자 개시 제어만). snapshot = `_internal/versions/v7/prd.md`.

## v6 update (2026-07-14) — responsive session title width + recursive-storm containment

- 사용자 요청에 따라 F-16의 20~24열 고정 세션명 상한을 F-22 반응형 계약으로 대체했다.
- wide는 telemetry/time/inset을 먼저 예약한 뒤 남는 폭을 세션 name column에 주고, narrow/stack은 suffix를 예약한 실제 L1 예산을 사용한다.
- dispatch 이름은 F-15 compact 상한을 유지해 긴 분사 slug가 다시 지배하지 않으며, sidecar provider는 8~12단어·최대 96자의 구체적인 영어 제목을 저장한다.
- 같은 날 live Fleet scheduler가 앞선 distill 폭풍의 내부 세션 backlog까지 title 대상으로 삼으면서 provider 세션이 다시 수집되는 재귀 chain이 발생했다(관찰 최대 title chain 216, Claude 계열 프로세스 607). per-session lock은 서로 다른 sid 폭발을 막지 못했다.
- F-23은 internal/child/app-server graph cut, cross-process provider 동시성 기본 2(하드 최대 4), rolling 600초 start budget 기본 4(하드 최대 16), env/state kill switch, SIGKILL stale-slot 회수를 모든 ingress에 강제한다. 검증은 provider 없는 200-session fixture로만 수행한다.
- 구현 검증: focused title/render 87 tests, canonical Fleet full suite 236 tests, canonical↔Claude mirror parity, shell syntax, adaptation boundary 통과. live provider smoke는 수행하지 않았고 `<title-state-root>/.refresh-disabled`를 유지한다.

## v5 implementation closure (2026-07-13)

- Codex current title source corrected by real-runtime smoke: newest versioned state DB
  `threads.title` wins; `session_index.jsonl` remains compatibility fallback.
- neutral sidecar/provider and live-only scheduler shipped for Claude/Codex; default Haiku,
  shell-free custom wrapper supported.
- verification: fleet suite 187/187, syntax/compile, `--json`/`--once` real smoke,
  canonical/Claude mirror parity. Adaptation-boundary comparison added zero new failures.

## v8 update (2026-07-15) — 관제 신뢰성 + 세션 제어 + 분사 정책 연동

| Step | Action | Result |
|---|---|---|
| 실측 | herdr 유령 세션(pid 1168514) fleet `--json` 대조 — proc 백본은 잡지만 title None 익명 idle 행 | 가시성 갭 확정(이름·unused·provenance 부재) |
| 실측 | `--once` 3회 crash 0 + 전체 스위트 247 tests OK | "버그"가 아니라 판정 기준 층위 문제로 진단 확정 |
| 진단 | 상태 판정 휴리스틱 층(F-15/F-18/F-24 + mtime 창) 우선순위 암묵 → 사용자 체감 "기준 불안정" | F-25 단일 상태 모델로 재설계 결정 |
| 사용자 확인 | 제어 범위 / 상태 모델 접근 / 연동 타이밍 3문 | kill+정리만 · 전면 재설계 · 계약 선고정+구현 후행 |
| update | v7 snapshot → `_internal/versions/v7/prd.md`, prd.md v8 | §4.8 신설(F-25~F-28), §0.5 경계 개정, Non-goals 부분 반전, 확정 결정 v8 블록, Next 구현 순서 |

- 계기: 사용자 결정 4건(2026-07-15) — 직접 세션 제어 / 반쪽짜리 해소·전향적 확장 / 판정 기준 불안정 / 분사 정책 연동 1급 UI.
- 타 세션 조율: stage-dispatch PRD v10 작업(별도 세션 진행 중)과 파일 표면 비겹침 확인 — F-28은 그 결과물(route record/topology registry)의 소비 계약만 선고정.

## Next
`/autopilot-code --mode dev --intensity standard "fleet 관제 신뢰성·세션 제어 — PRD v8 §4.8 F-25→F-26→F-27"` (worktree, conductor 분사). F-28 구현은 stage-dispatch v9 registry/route record 착륙 후 별도 phase.

## Minor-log (v8 기준 — 누적 2/5)
- 2026-07-15 (v8 minor #1): **제목 provider 길이 축소 소급 동기** — 사용자 요청("요약을 좀 더 짧게")으로 코드가 먼저 4~8단어·64자로 변경됨(`80c492e9`, refresh_title.py). spec F-17/F-22의 "8~12단어·96자" 문구를 소급 동기. spec-first 순서 위반의 사후 교정 기록.
- 2026-07-15 (v8 minor #2): **F-22 wide name zone 고정 상한 복원** — 사용자 피드백("session 길이를 맞춤형으로 늘린 건 오히려 별로"). wide 레이아웃 세션 제목 컬럼에 고정 상한(기본 40 display cols) 도입, slack 재배분 폐지. narrow/stack 예산·안전 클립·dispatch compact 상한 불변. 구현 = v8 구현 사이클에 편입.
