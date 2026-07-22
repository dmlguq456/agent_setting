# agent-fleet-dashboard — Spec Pipeline Summary

- **Date**: 2026-07-01 (v1) · 2026-07-10 (v2) · 2026-07-12 (v3) · 2026-07-13 (v4/v5) · 2026-07-14 (v6) · 2026-07-15 (v7/v8/v9/v10) · 2026-07-17 (v11) · 2026-07-20 (v12) · 2026-07-21 (v13) · 2026-07-22 (v14/v15/v16)
- **Mode**: cli (터미널 TUI 도구)
- **Status**: spec **v16 done; independent PASS** / dev **done** — common projection·arbitrary composed DAG·ctx/NOW subordinate line·bounded title quota를 `460b248f`로 main에 통합
- **Placement**: 별도 컴포넌트 `spec/agent-fleet-dashboard/` — 기존 `spec/prd.md`(Unified Memory System) 무수정.

## v16 update (2026-07-22) — common work projection + subordinate context

- Interactive main `Session`과 registered `DispatchJob`이 같은 additive `WorkProjection`을 소비한다. sealed route/node exact evidence가 우선이며, route tuple이 완전히 없는 행만 단일 artifact 후보로 stage label을 유도한다. 명시 tuple 불일치·복수 후보는 임의 최신 route를 고르지 않고 unknown/ambiguity로 남긴다.
- commit `e8938809`의 compose-on-demand route를 schema 그대로 읽어 arbitrary `nodes[].id/unit/depends_on/completion_gate/write_scope`, parallel sibling, fan-in을 그린다. composed record에 plan/exec/test/report 하드코딩을 적용하지 않는다.
- wide primary row의 확장 ctx gauge와 narrow/stack inline ctx를 폐기했다. live wide/narrow/stack 모두 identity 바로 아래 하나의 `ctx … [· NOW]` detail row를 사용하고 subtitle 부재는 ctx-only, context 부재는 `ctx —`, dead/stale는 row 생략으로 정직하게 강등한다.
- child dispatch의 title/NOW/context는 exact `(pid,proc_start)` 후 unique `(harness,realpath(cwd))`인 단일 association만 공유한다. PID reuse·cross-harness·복수 후보는 세 값 모두 거부하며 parent context는 상속하지 않는다.
- title/NOW worker의 현행 단일 예산은 concurrency 기본 3/최대 4, rolling starts 기본·최대 4/60s, main/child debounce 600/150s다. shared leases·start pool·kill switch·stale recovery·default Haiku no-tools·shell-free pluggable `FLEET_TITLE_COMMAND`/`FLEET_TITLE_MODEL` 경계를 유지하며 tests는 live provider를 호출하지 않는다.
- context pressure는 표시 신호로만 남고 intensity, route/depth, model/effort, QA, test, retry, gate, guard, definition of done과 직교한다. compaction에 따른 정상 수치 하락은 허용한다.

## v16 implementation closure (2026-07-22)

- canonical `tools/fleet/**`, byte-identical Claude mirror, shared model-worker governor 변경을 `460b248f`로 main에 fast-forward하고 origin/main에 push했다. main `Session`과 registered `DispatchJob`은 동일 `WorkProjection`을 소비하며 single/parallel composed node와 route progress를 같은 규칙으로 표시한다.
- strong `autopilot-code` continuation의 fresh cross-harness implementation review, `code-test`, `code-report`가 모두 PASS했다. 최종 증거는 `plans/2026-07-22_fleet-unified-stage-ui/{owner_handoff_final.md,test_logs/verification_final.md,pipeline_summary.md}`에 보존한다.
- 최신 main 재반영 후 Fleet **781/781**, compose-on-demand **9/9**, capability route **30/30**, hostile governor 환경 F-39 **6/6**, generated projections, canonical↔Claude mirror, provider-disabled group/process/JSON smoke를 재실행해 모두 통과했다.
- adaptation guard의 모든 negative sentinel과 원복 검사를 foreground에서 통과한 뒤 boundary가 exit 0을 반환했고, 재반영 후 standalone boundary도 exit 0과 동일한 전후 status를 확인했다. 문서화된 130-reference warning은 non-failing이다.

## v16 independent review correction (2026-07-22)

- fresh sealed route `rt-ad63f931daa3d317`, distinct node `review-final`, attempt `att-d2ed37a7e670783b91a3ff5ee5010bb691f4b6bfcf8f854e`의 독립 deep review는 RF-01~RF-08 중 RF-03의 오래된 F-28 문구와 추가 내부 모순 IC-01~IC-04 때문에 `FAIL`을 반환했다. 원본 `verdict.json`과 새 `verdict-final.json`은 모두 보존한다.
- canonical spec transaction은 교정 전 PRD를 `_internal/versions/v16/prd.md`에 byte-exact snapshot하고, active F-28 fallback을 explicit-tuple fail-closed로 통일했다.
- `AGENT_SESSION_ROLE=worker`를 scheduler 제외가 아닌 귀속 증거로 한정하고, mem/title/app-server/dead/stale 및 transcript 없는 비대화식 내부 행만 제외한다. 일반 registered dispatch child는 내부 태그가 없고 대화 transcript가 있으면 150초 debounce 대상이다.
- fresh route `rt-044c1a9810207b09`, node `review-final-2`의 후속 독립 review는 본문 eligibility는 정정됐지만 F-24 acceptance 한 줄이 옛 blanket exclusion을 유지한 IC-02 잔여로 `FAIL`했다. 같은 minor transaction에서 acceptance를 동일 predicate로 정합했고 `verdict-final-2.json`은 보존한다.
- fresh route `rt-c143657c8d95cb73`, node `review-final-3`, attempt `att-ccb1a37608ee193da6405ccba1458f43f3887b02b7f451f2`의 세 번째 독립 review는 RF-01·02·05~08과 IC-03·04를 닫았지만, active F-15/F-28b/F-30 legacy fallback 문구와 OpenCode blanket trigger exclusion 때문에 `FAIL`했다. `verdict-final-3.json`은 앞선 verdict와 함께 불변 보존한다.
- 후속 canonical minor transaction은 stage authority를 `WorkProjection.stage_label` 하나로 통일하고 `live_stage()`를 완전한 route-tuple 부재+exact-one plan-dir인 legacy adapter로 제한했다. breadcrumb/process-card/고정-stage fallback도 같은 경계로 통일하고, 명시 tuple의 record 부재·무효·불일치는 unknown/ambiguity로 고정했다.
- OpenCode를 포함한 모든 일반 registered conversational child는 하네스와 무관하게 F-24의 동일 predicate와 150초 debounce를 적용한다. native title은 provider 실패·미호출 fallback일 뿐 scheduler 제외 근거가 아니다.
- fresh sealed route `rt-9dbc66f49a9ff927`, node `review-final-4`, attempt `att-2457a340994052f76dfcc9be73a98939e11261fcccff6130`의 독립 deep review가 RF-01~RF-08, IC-01~IC-04, 전체 내부 정합성, 구현 준비성, acceptance boundary를 모두 `PASS`했다. durable verdict는 `reviews/spec/fleet-unified-stage-ui/verdict-final-4.json`, exact completion evidence는 `.dispatch/completion/rt-9dbc66f49a9ff927/review-final-4.json`이며 앞선 FAIL verdict는 모두 보존한다.
- current TITLE 계약을 3~6단어·최대 40자로 단일화하고 v6/v9 길이를 명시적 역사값으로 전환했다. `Next`는 v16 F-36~F-39 구현·§4.12 hermetic 검증만 남겼다.
- 이 교정은 specification-only이며 source 구현·commit·push는 수행하지 않았다. dev는 독립 final PASS 전후 모두 pending이다.

## v16 transaction and assurance

- v15 current state를 `_internal/versions/v15/prd.md`에 byte-exact snapshot하고, 누락돼 있던 component-local v14 snapshot을 authoritative `_internal/versions/v21/agent-fleet-dashboard/prd.md`에서 복원한 뒤 canonical pipeline lock 안에서 PRD/state/summary를 함께 갱신했다.
- strong `autopilot-spec` route는 research → independent plan review → PRD transaction으로 materialize했다. research artifact는 `shards/spec-research/fleet-unified-stage-ui/research.md`, review artifact는 `reviews/spec/fleet-unified-stage-ui/verdict.json`이며, 첫 review의 RF01~RF08을 모두 본 v16 계약에 흡수했다.
- standard/general QA 정책은 selected independent review와 final verify를 요구하며, 정책상 1 deep + 2 fast reviewer 및 1 fast fact-checker가 권고됐다. 첫 등록형 depth-2 review의 FAIL은 불변 보존했고 같은 route/node를 재사용하지 않았다. 각 교정 뒤 distinct sealed route/node/attempt로 재검토했으며 `review-final-4`의 independent PASS가 최종 spec gate를 닫았다.
- canonical root 밖 primary `.spec-grounding` marker는 worker sandbox에서 쓸 수 없어 worktree-local marker로 capability guard를 확인했다. strict hook-trust check는 설치된 trust가 없어 실패했지만 normal checked headless dispatch는 지원됐고, 이 제약을 parity/support 주장으로 확대하지 않았다.
- final verification은 current source baseline 167/167, compose-route 9/9, spec-transaction 3/3(총 179/179)을 통과했다. 모든 검증은 fixture/fake-clock 경계였고 default/custom live title provider 호출은 0회다. v15 snapshot SHA-256은 `5b0097064c38f705054797f2af29007baf2251ec1eb66b68296d9f771a7ddf57`이다. 이 baseline은 현행 source 회귀만 증명하며 v16 구현은 dev pending이다.

| Review finding | Resolution in v16 |
|---|---|
| RF-01 | F-17/F-33의 wide-only NOW·inline ctx를 명시 폐기하고 F-37a 한 detail row+live/missing/stale/dead truth table로 통일. |
| RF-02 | F-32를 F-37b 단일 child association에 귀속; `(pid,proc_start)` 우선, unique harness+cwd만 fallback, PID reuse/cross-harness/복수 후보 전체 거부. |
| RF-03 | F-28a와 locked decision을 개정해 explicit invalid tuple은 unknown/ambiguity로 고정하고 artifact fallthrough 금지; record/registry field authority 분리. |
| RF-04 | F-36d와 acceptance matrix에 artifact 후보 1/0/복수 및 합성 금지, invalid tuple+plausible artifact 충돌 픽스처 추가. |
| RF-05 | F-17/F-23/locked F-23을 F-39 단일 수치로 교체하고 custom wrapper no-tools 책임 경계 명시. |
| RF-06 | F-38과 acceptance에서 numeric decrease를 허용하고 missing/stale/malformed/source-sequence regression만 unknown 처리. |
| RF-07 | authoritative v14 복원, byte-exact v15 snapshot, v16 header/history/Next/state/summary 동시 갱신, dev pending 전환. |
| RF-08 | `projection.py` 소유권과 collectors → model → WorkProjection → render/JSON 흐름을 module tree·Mermaid에 반영. |

## v15 carried-forward state (2026-07-22)

- 기존 uncommitted v15 F-19/F-35f 변경(sync/migrate 신규 흡수의 `add`/literal `sync`, logical cwd, no historical backfill)을 그대로 보존했다. v16은 그 상태 위의 명시적 사용자 승인 개정이며 v15 snapshot SHA는 transaction evidence에 고정한다.

## v14 update (2026-07-22) — portable unit/compositional route projection

- topology registry schema v3, immutable route schema v2, dispatch contract v3의 서로 다른 버전 축과 sealed `unit_catalog_digest`/`composed`/node unit metadata를 명시했다.
- `assigned_contract`·`unit`·`worker_type`·`model_role`을 분리하고 `worker_role`을 legacy-only fallback으로 고정했다.
- wrapper pipe/env, Fleet model/collector/route JSON/render, memory journal 문서 정합을 F-35 구현 범위로 확정했다.
- Codex native subagent와 non-interactive exec, Claude subagent/background/agent-team/non-interactive 표면을 구분했다. `claude agents --json` agent-view 연동은 문서화된 잔여 확장이다.

## v14 implementation closure (2026-07-22)

- 세 하네스 wrapper의 `unit` pipe/env 전달, Fleet model/collector/route JSON/render, legacy row 호환, memory `cwd` 문서 정합을 `a4f7f040`으로 main에 통합했다.
- focused 225, Fleet full 744, wrapper 39, public JSON smoke, canonical↔Claude mirror, syntax와 adaptation boundary가 통과했다.
- 사용자 확인에 따라 기존 stage 순서/레이아웃은 이번 사이클에서 변경하지 않았다.
- Codex 등록형 headless는 사용자 소유 runtime profile activation 실패로 사용하지 못했으며 native-owner fallback과 독립 audit로 보강했다. 최신 main의 model-effort 정책과 portable-guard fixture 기대값 불일치 1건은 Fleet 외부 잔여로 기록했다.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| research | 기술 tap 매핑 조사 (Explore) | `research/agent-fleet-dashboard/01_tap_mechanics.md` | 하네스별 discovery·tap·liveness, file-cited + jobs.log open/running 버그 발견 |
| research | prior-art 스캔 (경량 web) | `research/agent-fleet-dashboard/00_prior_art.md` | herdr 정체(실OSS 멀티플렉서, 채택X) + 규모 작음 → 얇게 직접 빌드 + curses 확정 |
| spec | PRD 작성 (lean) | `prd.md` v1 | intake skip(입력 충분), 단일 mode cli, scaffold 이월 |

## v13 update (2026-07-21) — live stable session/group order

- `v12/prd.md`에 기존 PRD를 snapshot한 뒤, live TUI에서 계속 보이는 그룹과 세션 행의 상대 위치를 run-local anchor로 보존하도록 계약을 추가했다.
- 새 live run 및 stateless `--once`/`--json`은 기존 snapshot sort를 유지한다. 신규 가시 행은 survivor 뒤에 append하고, 사라진 행은 anchor에서 prune한다.
- 상태 분류, 그룹 membership, filtering/folding, selection identity, scroll, process view, dispatch ordering, visual layout은 범위 밖이며 불변이다. 후속 구현은 bounded stable-order state와 이 경계를 회귀 테스트한다.

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
- v11 (2026-07-17): 두-평면 실험 폐기 후 채택분 소급 등재 — F-29 표시(가로 스트립·인셋 위계)·수집(Task→Agent·비동기 발사≠완료) 개정, F-19 레포별 카드 행(+D-37 저널 `cwd` 동기), F-17 분사 세션 요약 전면 적용, F-32 분사 행 제목 입양, F-33 harness(model·effort) 통합+ctx 게이지 확장, F-34 표시 문법 정리(qa·`~` 표시 폐기, ↳ 사다리). 구현 선행(2026-07-16 사용자 연쇄 확정, main 착륙 완료)·등재 후행. snapshot = `_internal/versions/v10/prd.md`.
- v12 (2026-07-20): exact dispatch terminal evidence·namespace heartbeat expiry·Codex task lifecycle 우선·unmatched depth-2 canonical parity reliability minor. snapshot = `_internal/versions/v11/prd.md`.
- v13 (2026-07-21): live session/group stable-order anchor. snapshot = `_internal/versions/v12/prd.md`.
- v14 (2026-07-22): portable unit catalog·compositional route metadata·legacy worker_role/runtime surface 경계. component-local snapshot = `_internal/versions/v13/prd.md`; 누락 v14 copy는 v16 transaction에서 authoritative aggregate snapshot으로 복원.
- v15 (2026-07-22): F-19/F-35f sync/migrate 신규 흡수의 `add`/literal `sync`, logical cwd, no historical backfill. snapshot = `_internal/versions/v15/prd.md` (v16 transaction 직전 byte-exact current state).
- v16 (2026-07-22): F-36~F-39 common `WorkProjection`, arbitrary composed DAG, all-layout `ctx … [· NOW]` subordinate line, conservative title quota increase, context/intensity orthogonality. v14/v15 snapshot repair + PRD/state/summary transaction.
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

## v11 update (2026-07-17) — 두-평면 폐기 + 기존-보드 강화 소급 등재

- **두-평면 실험 폐기 결정 기록**: F-30 방향의 별도 "두-평면 문법" 가안(브랜치 `fleet-two-plane-demo`, HEAD `2fb4bda1`, 13라운드 사용자 반복)을 2026-07-16 사용자가 폐기 — "결국 기존과 비교해서 뭐가 나아진건데 / 시각적으로 하나도 안 들어온다 / 전부 다 버리고 메모리·서브에이전트만 기존 fleet에". 브랜치는 결정 기록으로 보존(머지 금지), 채택분만 기존 보드에 이식.
- **구현 트레일(전부 main 착륙, 2026-07-16)**: `plans/2026-07-16_fleet-mem-subagent/`(quick 사이클: 스트립·레포 mem·게이지·model 통합) + main 직접 후속 커밋 연쇄(`218752e7` 요약 에이전트 분사 적용, `109f1a27` 제목 입양, `a2dd70d4` 사다리·qa·`~`·구분자, `8e547828` 비동기 판정, `37f60079` 저널 cwd, `f7fcbc00`·`b4c02e9b`·`2c184e4c` 인셋·스트립·사다리 미세 조정 — 사용자 라이브 관찰 연쇄 피드백). 테스트 519→624, 회귀 0, 전 항목 라이브 검증(실 서브에이전트·실 분사·실 mem 이벤트).
- **진단 교훈 2건**(재발 방지 기록): ⓐ 비동기 Agent 발사는 즉시 launch-ack tool_result가 달린다 — 페어링 기반 활성 판정은 비동기 시대에 구조적으로 0건이 된다(F-29 수집 개정으로 해소). ⓑ "안 보인다" 불만의 원인이 코드가 아니라 관측 표면일 수 있다 — 사용자 TUI가 `--demo`(합성 픽스처 모드)로 떠 있었고, 구코드 프로세스가 하나 더 있었다. 재발 방지: 표시 불만 진단은 `ps`로 대상 프로세스의 시작 시각·플래그 확인부터.
- **잔여**: F-31(rolling 요약)은 미착수 그대로(F-32 제목 입양이 거친 버전을 선제공). 코드 주석의 임시 명칭 "F-4 (v11)"는 F-33으로 정정 완료.

- 2026-07-19 (v11 minor #1): **F-17 제목+부제 통합 — F-31 대체** — 사용자 확정("제목이랑 내용을 함께, 한번에" + "제목은 오히려 더 압축, 부제 느낌으로"). 같은 haiku 호출이 TITLE(3~6단어·40자)+NOW(대화 언어 1문장) 반환, 사이드카 summary additive·신선 15분, dim 부제 서브 행(스트립 위·무음·F-13), 분사 디바운스 150s. F-31 watcher 설계는 미구현 대체(재개 조건: 장수명 세션 실수요). 구현 = plans/2026-07-19_fleet-title-subtitle quick 사이클, 660 tests, main 288206fa. 라이브 검증: 실세션 제목 압축+한국어 부제 표시 확인.
- 2026-07-19 (v11 minor #2): **tracked/untracked 게이트 배지 퇴역** — 하네스 전역 tracked/untracked 모드 폐기(사용자 결정 "굳이 의미가 있나"→"없애는 방향이 맞다"; 근거 = 실사용 0·정보량 0·상시 tracked 라벨의 healthy-silent 위반, 유일 기계 효과였던 생성순서 게이트는 성숙 프로젝트에서 구조적 불발)에 따라 그룹 헤더 게이트 배지·세션 행 게이트 태그·wide 태그 공간 예약을 표시 계약에서 제거, 대체 표식 없음. route-record `tracked_gate_evidence` 스키마·spec-read 게이트는 불변. 구현 = plans/2026-07-19_tracked-retirement standard 사이클(worker `452690ff`+harvest fix, 152+8 files, main merge `84dcdf34`), fleet 664 tests·portable-guards 355/355·라이브 스모크 게이트 워드 0건.
- 2026-07-20 (v11 minor #3): **제목 생성 시작 예산 10→16 상향** — TUI 재시작 직후 일괄 refresh burst가 창당 상한(10/600s)에 걸려 신규 세션 제목이 지연되는 배압을 사용자 지시로 해소("16까지 상향"). `DEFAULT_START_LIMIT=16`(=MAX, env `FLEET_TITLE_MAX_STARTS` 상한 불변), 동시 2·600s 창·디바운스 불변.

## v17 hotfix (2026-07-23) — context 선두 + 콜론 구분

- detail row를 `context <gauge> <value>: NOW` 순서로 고정했다.
- `normal|tight|critical` band 이름은 숨기고 퍼센트 숫자는 dim으로 낮추되,
  기존 telemetry와 gauge threshold 색상은 유지한다.
- NOW가 없으면 콜론 없는 context-only 행을 유지하고, context 값이 없으면
  빈 gauge와 `—`를 유지한다. stage/DAG·worker 계약은 변경하지 않는다.
- 이전 단계는 `v16-context-first`, `v17-subtitle-first`,
  `v17-colored-percentage`에 보존했다.
