# agent-fleet-dashboard — Spec Pipeline Summary

- **Date**: 2026-07-01 (v1) · 2026-07-10 (v2) · 2026-07-12 (v3) · 2026-07-13 (v4/v5) · 2026-07-14 (v6) · 2026-07-15 (v7/v8)
- **Mode**: cli (터미널 TUI 도구)
- **Status**: spec **v10 done** (F-28 구현 확정 + F-30 과정 뷰 설계 — topology/route 착륙으로 전제 충족) — v9 구현 완료(테스트 468) · v10 구현 사이클 착수
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
- v10 (2026-07-15): F-28a~c 구현 확정(route record tolerant 소비·route-aware breadcrumb·조건부 run/governor) + F-30 처리-과정 뷰 설계 확정(`p` 토글·route 카드·DAG 흐름·마우스 접기). 전제 = stage-dispatch v11 구현 착륙(`f5f3949f`), 실측 record 스키마 기반. snapshot = `_internal/versions/v9/prd.md`.
- v9 (2026-07-15): minor 6건 흡수(취소선 정리·minor-log 리셋) + audit 🟡 2건 해소(F-25 규범 매핑 표 삽입·§10 control.py 노드) + F-27 마우스 1급 재설계(행 클릭·클릭 확정, 키보드 폴백) + F-30 종착 비전 등재(dispatch·서브에이전트 처리 과정 시각화). snapshot = `_internal/versions/v8/prd.md`. audit = `_internal/audit/audit_2026-07-15T1734.md`.
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

## Minor-log (v9 기준 — 누적 0/5. 아래 v8 시대 6건은 v9에 흡수 완료 — 이력 보존)
- 2026-07-15 (v8 minor #6): **cross-harness 분사 orphan 오귀속 해소** — 사용자 관찰("codex가 분사시킨 세션이 orphan으로 빠짐"). 원인 = 3어댑터 래퍼가 §5.10 pipe 계약의 parent_cwd를 전부 누락(계약 위반) + Codex는 실제 세션 id를 env로 못 얻어 합성 parent_sid만 기록. 수정 = 래퍼 3종이 parent 문맥 존재 시 parent_cwd 기록/env 주입(fleet 읽기 측 cwd-매칭 nest는 기존 코드 재사용, 신규 휴리스틱 0). SD-15 conformance 3종 PASS.
- 2026-07-15 (v8 minor #5): **v8 구현 후속 spec 동기 2건** — (a) kill 조작 키 확정: `↑↓` 직접 진입 원안이 스크롤 바인딩과 충돌해 `s`/`x` 진입→`↑↓`/`jk` 이동→`Esc` 해제로 구현·사용자 확인. (b) §9 모듈 트리에 `control.py` 등재 + `model.py` 설명 현행화. 근거 = fleet-v8-reliability final report follow-up #4·#5.
- 2026-07-15 (v8 minor #4): **unused의 stale 창 면제** — 사용자 결정. 유령 세션은 mtime이 스폰 시각 고정이라 48h 창이 F-26 목적을 자동 무력화 → 살아있는 한 `unused` 유지, 종료는 존재 축 담당. 면제는 unused 한정(사용 세션의 침묵→stale 불변). 구현 = main 직접(commit 참조), 테스트 2건 신설(416 OK).

- 2026-07-15 (v8 minor #3): **F-29 (native 서브 에이전트 호출 관측)** 추가 — 사용자 확정("서브 에이전트 호출 현황도 fleet에"). enrichment 전용(proc 백본 비대상), 소스 = OpenCode DB parent_id/agent(실측)·Claude transcript isSidechain+tool_use 짝·Codex threads probe 필요. 세션 밑 `└⚡` 서브 행 + `⚡N` 배지, 활성만 기본 표시, pulse 카운트 분리. 구현 = v8 사이클 수확 후 후속.
- 2026-07-15 (v8 minor #1): **제목 provider 길이 축소 소급 동기** — 사용자 요청("요약을 좀 더 짧게")으로 코드가 먼저 4~8단어·64자로 변경됨(`80c492e9`, refresh_title.py). spec F-17/F-22의 "8~12단어·96자" 문구를 소급 동기. spec-first 순서 위반의 사후 교정 기록.
- 2026-07-15 (v8 minor #2): **F-22 wide name zone 고정 상한 복원** — 사용자 피드백("session 길이를 맞춤형으로 늘린 건 오히려 별로"). wide 레이아웃 세션 제목 컬럼에 고정 상한(기본 40 display cols) 도입, slack 재배분 폐지. narrow/stack 예산·안전 클립·dispatch compact 상한 불변. 구현 = v8 구현 사이클에 편입.

## v8 implementation closure (2026-07-15)

- `plans/2026-07-15_fleet-v8-reliability` 사이클(conductor 분사, plan→exec→test→report 완주)로 F-25 단일 상태 분류기(state_evidence·hysteresis), F-26 레지스트리 1급(unused `◌`·provenance), F-22 minor(40열 캡), F-27 세션 제어(s/x 커서·kill·action log) 구현. 테스트 247→416, 회귀 0, main 머지 `fleet-v8-reliability` 브랜치 보존.
- harvest 후속 처리: 위험 재현 절차 철회 주석(plan.md, 안전 위반 자진 신고 대응), unused stale 면제(minor #4), kill 키 spec 동기(minor #5), cross-harness orphan 래퍼 정합(minor #6).
- 사용자 눈 검사 잔여: `◌` 글리프 폰트 렌더 / kill 조작 체감 → "마우스로 처리" 방향 접수(2026-07-15), v9 재설계 입력.
- audit `_internal/audit/audit_2026-07-15T1734.md`: 🔴 1(본 동기로 해소) / 🟡 2(어휘 매핑 표·§10 다이어그램 — v9 흡수 대상).

## v9 update (2026-07-15) — minor 흡수 + audit 해소 + 마우스 kill + 종착 비전

| Step | Action | Result |
|---|---|---|
| audit | minor 6/5 초과 트리거 — spec↔코드 정합 전수 (audit_2026-07-15T1734) | 🔴 1(상태 신선도 — 즉시 동기화) / 🟡 2 / 🟢 12 |
| update | v8 snapshot → `_internal/versions/v8/prd.md`, prd.md v9 | 매핑 표(D1 규범 행 포함)·§10 다이어그램·취소선 정리·F-27 마우스 개정·F-30 등재 |

- 사용자 방향 2건 반영: "그냥 마우스로 처리"(kill 조작) / "dispatch·서브에이전트 처리 과정 시각화가 진짜 목표"(F-30).
- 구현 사이클(v9): ① F-27 마우스 ② F-29 서브에이전트 관측 ③ stage zone 폭 상한·스크롤 회귀 테스트.

## v10 update (2026-07-15) — 처리-과정 시각화 설계 확정

| Step | Action | Result |
|---|---|---|
| 전제 확인 | topology registry·capability-route.py·broker 실재 + 실 route record(agent-note d1) 스키마 실측 | schema_version 1, nodes DAG·gate 증거·route_hash 링크 확인 |
| update | v9 snapshot → `_internal/versions/v9/prd.md`, prd.md v10 | §4.9 신설(F-28a~c·F-30 설계), 확정 결정 v10, Next v10 순서 |

- v9 구현 사이클 완료 반영(마우스 kill·서브에이전트 관측·폭 상한, 468 tests). 글리프 이탈 1건을 독립 검증이 되돌린 사례 기록은 plans/2026-07-15_fleet-v9-mouse-subagent/final_report.md.

## v10 implementation closure (2026-07-16)

- `plans/2026-07-15_fleet-v10-process-view` 사이클(conductor 분사, plan→execute→test→report 완주)로 F-28a route record tolerant 소비(`route.py` 신설, write API 없음), F-28b record 기반 breadcrumb(하드코딩 3단 → 실제 노드 이름·순서, "record는 레일, 점등은 실측"), F-30 처리-과정 뷰(`p` 키/`--view process` — DAG fan-out/fan-in·노드→세션→서브에이전트 중첩·마우스 접기), F-28c governor lease 관측(`collectors/governor.py`, 죽은 lease·PID 재사용 배제) 구현. 테스트 468→519, 회귀 0, main 머지 943b6aba.
- 검증이 잡은 잠복 결함 2건: 종단 행 증거 스캔이 `route_file` 미탑재 → 완료 route가 "no route record"로 오탐(tolerant fallback이 결손을 은폐); 동일 가정("살아 있는 잡만 보면 된다")의 두 번째 위치에서 중복 카드. 모두 live 실측으로 수정 확인(heuristic 5→0), mutation 테스트로 회귀 테스트 실효성 검증.
- 정직한 결손(구현하지 않기로 결정): completion gate 통과 표시(`—` — 통과 증거가 시스템에 부재, dispatch 규약 변경 필요), run registry 관측(canonical 경로 부재 — "없다"가 아니라 "찾을 수 없다"). 이월 = `plans/2026-07-15_fleet-v10-process-view/_internal/carryover.md`.
- 별건 인프라 발견 2건(fleet 범위 밖, 상위 보고): dispatch 브로커 head-of-line blocking(`dispatch-broker.py:510` 전역 락 하 동기 실행 — 실측 12분 전 fabric 차단), immutable route record가 mutable `broker_instance` 고정(브로커 롤오버 시 ordinal-1 hop 영구 불가 — 이 사이클 자신이 ordinal-3 폴백으로 열화 수행).
- 판단 대기: `--view` CLI 표면 유지 여부(spec은 `p`만 확정), gate 통과 마커 규약(stage-dispatch 계약 변경), 브로커 HOL blocking 우선순위.

- 2026-07-16 (v10 minor #1): **F-30 비대화식 투영 확정** — v10 구현이 검증 목적으로 추가한 `--view {group,process}` CLI + `FLEET_VIEW` env를 사용자 확정으로 등재. `p` 토글과 전역 상태 하나를 공유(별도 코드 경로 없음). 판단 대기 3건 중 1건 해소("전부다 작업 해줘").
- 2026-07-16 (v10 minor #2): **F-30 gate 통과 표시 재개** — stage-dispatch v13(SD-56)이 completion marker를 실사용 착륙(저장소 최초 4건), v10 carryover §1의 재개 조건 충족. 증거 소스 = canonical `.dispatch/completion/<route_id>/<node_id>.json`, 판정 = marker 존재+route_id/hash 일치, 부재 = 무주장. 구현 = quick 사이클 분사.
- 2026-07-16 (v10 minor #3, **철회**): ~~claude 사용량 소스 신뢰 규칙 개정~~ — "OAuth 엔드포인트가 성공-제로로 진짜 값(tap 7d 43%)을 가린다"는 진단으로 quick 사이클(구현·검증 완료, branch 85716394)까지 갔으나, **merge 직후 사용자 재확인 + 재실측으로 진단이 반전**되어 push 전 전량 철회(reset, branch/worktree 제거). 진실: 주간 카운터가 실제로 초기화됐고 API의 0%가 정확했으며, 43%는 **파일 mtime은 신선하지만 내용물(rate_limits)은 초기화 이전 마지막 응답의 낡은 값**인 tap이었다(재실측: API 5h 4%/7d 1% = 활성 세션 tap들과 일치, 43% tap만 outlier). 남는 교훈 2가지를 기록으로 보존: ⓐ statusline tap의 payload 신선도는 파일 mtime으로 판별 불가(tick마다 재기록되나 rate_limits는 마지막 inference 시점) — tap 기반 판단은 이 함정을 전제할 것 ⓑ 철회된 사이클이 관측한 "API 응답 단위 일관성"(부분-양수 응답)은 이제 정상 동작으로 재해석. 사이클 산출물은 `plans/2026-07-16_fleet-usage-accuracy/`에 RETRACTED 표기로 보존.
- 2026-07-16 (v10 minor #4): **F-31 (분사 세션 rolling 요약 관측)** 추가 — 사용자 확정("엄청 가벼운 에이전트로 로그 요약을 계속… fleet에 반영"). transcript jsonl delta → 결정론 watcher(cursor·케이던스·governor storm containment) → cheap-tier no-tools 요약 워커(D-14 관용구) → 피드 JSONL → 세션 행 dim 서브 행(과정 뷰 카드 재사용). 요약은 표시 전용(F-25/SD-58 분류 불개입)·zero-injection·tolerant. 구현 = 별도 autopilot-code 사이클(지연·토큰 비용 실측이 완료 기준).
