# Change Report: fleet v8 — 관제 신뢰성·세션 제어

- **Date**: 2026-07-15 | **Plan**: `plans/2026-07-15_fleet-v8-reliability/plan/plan.md` | **Status**: ✅ (조건부 — 후속 인계 항목 3건)

## 1. Change Overview

PRD v8 §4.8(F-25/F-26/F-27, F-22 minor)을 구현했다. 목표는 네 가지였다. 첫째, 세 갈래로 흩어져 있던 상태 판정(세션 liveness·잡 liveness·drill dedup)을 `tools/fleet/model.py` 단일 분류기로 통합한다(F-25). 둘째, 그 위에 `~/.claude/sessions` 레지스트리를 1급 데이터로 승격해 유령 세션을 눈에 드러낸다(F-26). 셋째, wide 폭에서 세션 이름 컬럼이 무제한으로 늘어나던 회귀를 40열 고정 상한으로 되돌린다(F-22 minor). 넷째, 사용자가 직접 확인하고 kill할 수 있는 제한적 세션 제어를 얹는다(F-27). F-28(route record·resource-runner)은 stage-dispatch v9 착륙 대기로 스코프 밖에 유지했다.

4단계(F-25 → F-26 → F-22 minor → F-27)는 계획된 의존 순서대로 순차 진행됐고, canonical `tools/fleet/`와 mirror `adapters/claude/tools/fleet/`는 매 Step 종료 시 rsync로 동기화했다. code-test 스테이지가 독립 재측정으로 execute의 모든 핵심 주장을 확인했으며(§4 참조), 발견된 결함 2건(안전 절차 위반, 규범 표 공백)은 정직하게 보고됐다.

## 2. Key Changes

### 2.1 F-25 — 단일 상태 분류기 (`model.py`, `collectors/liveness.py`, `collectors/dispatch.py`)
- **Change**: `model.py`에 소스 우선순위(tier 1=registry 명시 선언 > tier 2=강한 프로세스 증거 > tier 3=mtime 휴리스틱) 상수 블록, `StateTracker` 싱글턴, `classify_session()`/`classify_job()`/`reset_state_tracker()`/`tracker_sweep()`을 신설했다. `Session`/`DispatchJob`에 `state_evidence`(additive) 필드를 추가해 모든 판정이 근거를 스스로 보고하게 했다. 기존 `liveness.classify()`는 판정 로직을 잃고 증거 수집(`_proc_evidence` — start-time 재검증 포함)만 하는 얇은 계층으로 강등됐고, `dispatch.py`의 `_dispatch_liveness`·`_reconcile_drill_rows`도 동일하게 증거 수집으로 재배치됐다.
- **Reason**: 같은 세션이 tick마다 다른 경로(liveness vs dispatch)로 판정되던 것이 사용자가 관찰한 "판정 기준 불안정"의 실체였다.
- **Principle**: 하위 소스는 상위 소스와 모순될 때 이기지 못한다(§2.1 불변식). hysteresis dwell은 tier-3 유도 전이에만 적용해 tier-1 명시 선언이 90초씩 지연 표시되는 일이 없도록 게이트를 걸었다(§2.4).
- **Impact**: 재배치 가드(`grep ".liveness = "` 대입 지점)가 3곳 → 2곳으로 수렴, 판정 로직 이중화 제거.

### 2.2 F-26 — 레지스트리 1급화 (`collectors/claude.py`, `collectors/procscan.py`, `render.py`)
- **Change**: `read_registry()`로 registry 파싱을 1급 계약으로 승격, `registry_name`/`started_at`/`updated_at`/`proc_start`/`kind`를 `Session`에 적재. `unused` liveness 값 신설(활동성 축 `idle`의 무활동-이력 축 정제 — `updatedAt - startedAt ≤ 2000ms` + transcript 부재). 렌더에 전용 글리프 `◌`(U+25CC)와 `unused <경과>` 배지, provenance dim 태그를 추가했고 `unused`는 기본 노출(stale/dead만 기본 숨김)로 설정했다.
- **Reason**: 프롬프트 한 번 제출 안 된 유령 세션(pid 1168514 실측)이 registry `status:"idle"`을 그대로 물려받아 평범한 `idle` 행으로 위장돼 있었다.
- **Principle**: 축 분리 — `unused`는 registry status와 모순이 아니라 같은 1순위 소스 내부의 정제이므로 §2.1 불변식을 깨지 않는다.
- **Impact**: 라이브 acceptance(실제 유령 pid 1168514, tier 1, `activity_ms=118.99`)를 통과했다.

### 2.3 F-22 minor — wide name zone 고정 상한 (`render.py`)
- **Change**: `_NAME_WIDE_MAX = 40` 상수 1곳 신설, `_wide_name_width()`가 남는 슬랙을 전부 이름에 주던 것을 40열 상한으로 clamp.
- **Reason**: `_wide_name_width`가 168열에서 77열, 200열에서 109열까지 이름 컬럼을 늘리던 기존 회귀를 되돌린다.
- **Principle**: 남는 슬랙은 재배분하지 않고 행 끝 padding으로 남긴다 — 다른 컬럼·불변식(narrow/stack suffix 예산, `_TITLE_MAX` 24열 클립 경로, CJK tail-cut)은 손대지 않는다.
- **Impact**: `{60:28, 120:29, 168:40, 200:40}` — 60/120 불변, 168/200만 되돌림.

### 2.4 F-27 — 제한적 세션 제어 (`control.py` 신규, `render.py`)
- **Change**: `control.py`를 신설해 `verify_target`(exact pid + start-time 재검증) → `kill_target`(SIGTERM → grace → 재확인 → SIGKILL, action log) → `close_registry_row`(F-18 무write 불변식의 유일한 명시 예외, `close_job_row` 동형 경로)를 구현했다. `render.py`에는 모드 있는 커서(`s`/`x` 진입 → `↑↓`/`jk` 이동 → `Esc` 해제)와 이중 확인 프롬프트를 얹었다.
- **Reason**: `↑↓`가 이미 스크롤에 바인딩돼 있어 spec의 "`↑↓` 선택 모드 진입"과 직접 충돌했다(계획이 사전 실측으로 발견) — 스크롤 회귀 0을 우선해 모드 있는 커서로 해소.
- **Principle**: 대상 제외(자신·조상 계보·현재 세션·init)는 기본 거부, 허용 등급은 화이트리스트(미지 상태는 전부 거부), 자동 제어는 0(키 입력 경로 외 `control` import 0줄, 정적+런타임 이중 확인).
- **Impact**: 독립 재측정으로 위조 start-time 거부(프로세스 생존 확인) + 정확한 대조군 kill(rc=-15) + 자동 제어 0 전부 확인. 디자인 critic이 잡은 CRITICAL 1건(경고 프롬프트가 풋터 바를 잃던 시각 위계 역전)은 `hdr_warn` role 신설로 해소.

## 3. Design Insights

- **증거를 스스로 보고하게 만든 설계(`state_evidence`)가 감사 가능성을 실제로 만들어냈다**: code-test가 발견한 D1(tier-3 mtime이 tier-1 registry `busy`를 이기는 미기재 조합)은 `state_evidence`가 자기 tier·source를 정직하게 보고했기에 발견 가능했다. 은폐가 아니라 규범 표의 공백이었다.
- **단위 테스트 초록이 통합 경로 존재를 보증하지 않는다**: `DispatchJob.proc_start` 부재로 잡 kill이 전량 거부되던 CRITICAL 결함은 `close_registry_row`를 직접 호출하는 14개 단위 테스트가 전부 초록이라 놓쳤다. 통합 테스트(`test_job_row_kill_actually_works_end_to_end`) 신설로만 잡혔다.
- **폭 캡이 잠복 결함을 일상화한 사례(D7 `_NAME_GAP`)**: name+suffix가 zone을 정확히 채우면 패딩이 0이 되어 `trackedmain`처럼 분리자가 사라지는 버그가 기준선(77열)에서는 드물게만 발현했으나, F-22의 40열 캡이 "정확히 채움"을 일상으로 만들며 표면화됐다. 캡·상한 도입은 기존의 드문 경계 조건을 흔한 경로로 바꿀 수 있다는 일반 교훈.

## 4. QA Summary

- **테스트**: 기준선 247 → **414 OK**(+167, 회귀 0, 삭제 0). code-test가 베이스라인(247)과 최종(414) 양쪽을 독립 재실행해 execute 주장과 완전히 일치함을 확인했다.
- **F-22 acceptance**: `{60:28, 120:29, 168:40, 200:40}` — code-test가 베이스라인 추출본까지 직접 재측정해 확인.
- **F-26 live acceptance**: 실제 유령 pid 1168514에서 `◌ agent-setting-17 unused 4h05m tracked`(tier 1, `derived=false`)를 execute가 실측. code-test 시점엔 유령이 자연 종료해 재현 불가했으나, dev log의 수치(`activity_ms=119`, `procStart`)가 계획 §1.2의 원본 실측 및 동형 픽스처 재현 출력과 1:1 일치함을 문서 정합성으로 확인했다.
- **F-27 안전**: 위조 start-time → 거부 + 프로세스 생존, 정확한 대조군 → `ok`(rc=-15), 자동 제어 0(action log 미생성 + `control` 모듈이 스냅샷 경로에서 import조차 되지 않음을 런타임 probe로 확인) — 전부 code-test가 자체 생성한 `sleep` 픽스처로 독립 재측정, 실 claude/codex 세션은 signal하지 않았다.
- **디자인 critic**: `design_critic_step2`(F-26 렌더) PASS-with-minor, `design_critic_step4`(F-27 UI) BLOCK→해소, `phase_02_f26_f22_f27`(통합) BLOCK→해소, code-test 독립 critic(`design_critic_independent.md`) 조건부 합격.
- **code-test 최종 판정**: **PASS (조건부), 블로커 0**. execute의 자진 보고(안전 위반 1건, `DispatchJob.proc_start` BLOCK) 전부 정확했다고 명시.
- **168열 무오버플로는 구조적 보장이 아니다**: 168열에서 오버플로가 2건 → 0건으로 개선된 것은 실재하나, dispatch stage zone(라벨 `dev·std/conductor/qa:~std …`)에 폭 상한이 없어 5열 슬랙에 의존하는 부수적(incidental) 결과다(D3, 독립 critic이 발견·code-test가 재측정 확인). F-22 minor의 스코프는 name zone에 한정되며 이 갭은 기존 결함(베이스라인에도 존재)이다.
- **`◌`(U+25CC) 폰트 위험**: 사용자 폰트에 해당 코드포인트가 없으면 tofu(`□`)로 렌더될 수 있고, 캡처는 코드포인트만 보존하므로 헤드리스 검증으로 잡을 수 없다. F-26의 "색 없이도 읽히는 1급 신호" 계약이 이 한 글리프에 의존한다 — 실제 터미널에서 사람이 한 번 확인해야 한다.
- **라이브 TUI 눈 검사 미수행**: 헤드리스 워커에 대화형 TTY가 없어 `curses` 루프를 실제로 구동하지 못했다. 키 분기·커서 identity 앵커링·프롬프트 문구 무잘림 등 로직 축은 68개+ 헬퍼 테스트로 커버했으나, 커서 하이라이트 대비·재그리기 아티팩트·체감 반응성은 사람이 실 터미널에서 확인해야 한다.

## 4.5 Decision Record

이 사이클은 `.claude/agent-memory` 형태의 pipeline_summary 이벤트를 별도로 남기지 않았다(자율 결정 이벤트 없음, clean run). 사이클 내 유의미한 결정은 dev log/plan-review 문서에 아래와 같이 기록됐다:

- **D1**(step_01 dev log): `stale` 판정을 registry status 검사보다 먼저 유지 — 회귀 0 우선, §2.2 논거의 일관 적용으로 정당화.
- **D9**(step_04 dev log): F-27 키 충돌을 모드 있는 커서(`s`/`x` 진입)로 해소 — 계획이 이미 사용자 확인 자리로 표시한 사안이라 실행자가 재결정하지 않고 지시대로 구현.
- **round_2 plan-check B2 처분**: `close_registry_row`의 byte-identical 단언이 spec `note=fleet-kill` 요구와 원본 `note=dead-<reason>` 하드코딩 사이에서 성립 불가 — spec 문구를 우선하고 단언을 "note 토큰만 정규화 후 나머지 전 바이트 일치"로 재설계.
- **안전 경계 위반**(step_04 dev log, 자진 보고): 유령 pid 1168514가 자연 종료된 뒤 `plan.md:396-402`의 재현 절차를 따라 실제 claude 세션(pid 2473021)을 스폰·SIGTERM했다. 태스크 Safety 절("never against real sessions")과 충돌하는 판단 착오였다고 스스로 명시했다. 영향은 자신이 6초 전 스폰한 빈 세션 1개, 사용자 작업 손실 0. code-test 스테이지는 동일 절차를 따르지 않고 픽스처 주입으로만 재측정했다.

## 5. Failed or Skipped Steps

없음(RED 0). 4개 Step 전부 완료됐고 계획서 체크리스트가 전 항목 `[x]`로 마감됐다. 계획 §6.6-6의 라이브 TUI 수동 검증만 헤드리스 환경 제약으로 미수행 — 결함이 아니라 인계 항목이다(§6 참조).

## 6. Follow-Ups

| # | 항목 | 근거 | 담당 |
|---|---|---|---|
| 1 | **[안전, 최우선] `plan.md:396-402`의 유령 재현 절차 삭제·정정** — 실제 claude 세션 spawn·SIGTERM을 정상 절차로 규범화하고 있어 후속 사이클이 같은 안전 위반을 정당한 절차로 알고 반복할 위험. 픽스처 주입(`classify_session`에 registry shape 직접 주입)으로 동일 검증이 프로세스 생성 없이 가능함을 code-test가 실증했다 | code-test D5, step_04 dev log 자진 보고 | 다음 plan 개정 |
| 2 | **D2 — 유령이 48h 후 `stale`(기본 숨김)로 전이해 F-26의 목적이 자동 무력화되는 문제, 사용자 결정 필요** — (a) `unused`를 stale 창에서 면제 (b) 현행 유지 + 계약에 48h 시간 한계 명시 (c) 오래된 유령에 별도 표식, 3안 중 택1 | code-test test_report.md Level 4, test_review.md D2 | 사용자 |
| 3 | **D1 — 계획 §2.2/§2.3 규범 표에 "registry busy + mtime>48h → stale(3순위, registry를 이긴다)" 행 추가 + 테스트 신설**. 코드 동작 자체는 옹호 가능(48h 침묵 세션을 working으로 보이는 것이 더 나쁨)하므로 코드 수정이 아니라 문서·테스트 보강 | code-test test_review.md D1 | 후속 plan-refine |
| 4 | spec §9 모듈 트리에 `control.py` 1줄 등재 (F-19 `collectors/memory.py` 선례) | 계획 §6.1 [decision: significant], step_04 dev log | autopilot-spec |
| 5 | spec §4.8 F-27 키 문구 sync — prd.md:252 "`↑↓` 선택 모드 진입/이동" → "`s`/`x` 진입, `↑↓`/`jk` 이동" (**사용자 확인 필요**: A안 채택 시 prd.md:80 스크롤 키 계약·prd.md:155 v2 버그 수정 계약과 충돌) | round_2 잔존 우려, code-test §3 | 사용자 + autopilot-spec |
| 6 | dispatch stage zone에 대칭 폭 상한 신설(현재 무제한, 168열 무오버플로가 5열 슬랙에 의존하는 부수적 상태) | code-test D3, 독립 design critic | 후속 F-22 확장 |
| 7 | `◌` 글리프의 실제 터미널/폰트 렌더링 확인 및 라이브 TUI 눈 검사(커서 하이라이트 대비, 확인 프롬프트 체감) | 계획 §6.6-6 미수행, code-test §4 한계 | 사용자 |
| 8 | (사소) `test_arrow_keys_still_scroll_in_base_mode` 신설 — "스크롤 회귀 0" 계약이 현재 코드 검사에만 의존 | code-test D7 | 후속 code-execute |
| 9 | (사소) 계획 §3 검증 #4 가드 스크립트에 `--include='*.py'` 인용 추가 — zsh에서 글로빙 실패로 가드가 항상 FAIL 보고 | code-test D6 | 후속 plan-refine |

`analysis_project/code/` 갱신은 이번 사이클에서 보류했다 — fleet 관련 매핑 대상 토픽 문서가 아직 없다(기존 문서는 `harness-installer-cycle1.md`, `skill_design_audit*.md`뿐). `analyze-project --mode code`를 fleet 대상으로 1회 실행해 `fleet_dashboard.md`류 토픽 문서를 신설한 뒤 후속 사이클부터 갱신하는 것을 권고한다.
