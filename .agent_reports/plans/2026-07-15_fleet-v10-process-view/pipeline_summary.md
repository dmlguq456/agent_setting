# fleet v10 — 파이프라인 요약 (스테이지별 진행·판정)

> 사이클: `2026-07-15_fleet-v10-process-view` · 워크트리 `/home/Uihyeop/agent_setting-wt/fleet-v10-process-view` (브랜치 `fleet-v10-process-view`)
> 계약: `spec/agent-fleet-dashboard/prd.md` v10 §4.9 · intensity `standard` · qa `standard` · `spec_touch=false`
> 베이스라인 468 tests → 최종 **519 tests, OK** · 회귀 0

---

## 1. 스테이지 진행

| 스테이지 | 실행 경로 | 산출 | 판정 |
|---|---|---|---|
| **plan** | ordinal-1 (ancestor-broker) | `plan/plan.md` (622행), `_internal/plan_reviews/round_1.md` | ✅ 완료 — plan-review 반영 후 확정 |
| **execute** | ordinal-3 native-subagent (`fleet_visibility=degraded`) | `dev_logs/step_01`~`step_05`, `checklist.md` | ✅ 완료 — Step 1~5 |
| **test (1회차)** | ordinal-3 native-subagent | `test_logs/verification.md`, `test_logs/design_review_round_1.md` | 🟡 **YELLOW** — 결함 4건 |
| **execute (수정 패스 1)** | ordinal-3 native-subagent | `dev_logs/step_06_fix_pass_code_test_yellow.md` | ✅ 결함 1~4 수정 (516 tests) |
| **test (2회차)** | ordinal-3 native-subagent | `test_logs/verification_round_2.md` | 🟡 **YELLOW (좁혀짐)** — 수정 4건 확증, 신규 결함 1건 |
| **execute (수정 패스 2)** | ordinal-3 native-subagent | `dev_logs/step_07_fix_pass_round2_duplicate_card.md` | ✅ 중복 degrade 카드 수정 (519 tests) |
| **report** | ordinal-3 native-subagent | `pipeline_summary.md`, `final_report.md` | ✅ 본 문서 |

> **실행 경로 주석**: route record가 지정한 ordinal-1(브로커 경유) 경로는 브로커 인스턴스 롤오버로 사용 불가했다. execute/test/report는 record가 명시한 checked 순서에 따라 ordinal-3 native-subagent로 내려갔다 — 계약 이탈이 아니라 record가 예비한 폴백의 정상 소비다. 상세는 `final_report.md §5`.

---

## 2. 스텝별 구현 판정

| Step | 대상 | 산출물 | 테스트 | 판정 |
|---|---|---|---|---|
| **1** | F-28a route record 소비 | `tools/fleet/route.py` **신설**(337행), `collectors/dispatch.py` `_scan_route_nodes` 신설, `model.DispatchJob` +4필드, `fleet.py --json route` 키, 픽스처 `tests/fixtures/route/` 7종 | `test_f28_route.py` 20 | ✅ |
| **2** | F-28b route-aware breadcrumb | `render.py` `_stage_segs(route_seq=None)` additive, `_conductor_stage_override` route_node 우선, `_PIPE_STAGES` 존치 | `test_f28_breadcrumb.py` 6 | ✅ |
| **3** | F-30 과정 뷰 (신규 화면) | `render.py` `_build_process_lines`·`_route_card_*`·`_ROUTE_FOLD`/`_FOLDABLE`/`_FOLD_ROWS`, `fleet.py --view {group,process}` + `FLEET_VIEW`, `demo.py` route 잡 3건 | `test_f30_process_view.py` 15→18 | ✅ |
| **4a** | F-28c governor lease | `collectors/governor.py` **신설**(106행), pulse 인접 1행, `--json governor` 키 | `test_f28c_governor.py` 6 | ✅ |
| **4b** | F-28c run registry | `_internal/carryover.md` | — | ⏭️ **스킵 + 이월** (경로 발견 불가) |
| **5** | 통합 검증·미러 | `test_logs/`, `adapters/claude/tools/fleet/` 미러 | 전체 519 | ✅ |

**변경 표면**: 기존 5파일 수정(`render.py` +631, `collectors/dispatch.py` +87, `demo.py` +86, `fleet.py` +47, `model.py` +9 = 820 insertions / 40 deletions) + 신설 2모듈 + 신설 테스트 4파일(836행) + 픽스처 7종. 미러 `adapters/claude/tools/fleet/`에 byte-identical 동기.

---

## 3. 품질 경로 — 결함 발견·수정 이력

| # | 결함 | 발견 | 심각도 | 상태 | 회귀 테스트 |
|---|---|---|---|---|---|
| 1 | **route record가 live 경로에서 미소비** — `_scan_route_nodes` 증거가 `route_file`을 안 실어 record와 조인 불가 | test 1회차 | 🔴 blocking | ✅ FIXED (live 확증: heuristic 5개 → 0개) | `test_t1_13b_…` — **mutation M1/M2 확인** |
| 2 | 완료 route 1행 접힘 live 도달 불가 (결함 1 종속) | test 1회차 | 🔴 | ✅ FIXED (`rt-1120bb39` 4/4 · `rt-70be9258` 3/3 접힘) | `test_t3_5_…` — **M2 확인** |
| 3 | demo 병렬 카드가 불가능한 DAG 렌더 (`setup ○` 부모에 active 자식) | critic 🟡1 | 🟡 | ✅ FIXED (`setup ✓10m`, `1/6 nodes`) | `test_demo_seeds_lab_setup_node_as_done` — **M4 gap 후속 보강** |
| 4 | L1 경과에 `⏳` 글리프 누락 (spec 문자 이탈) | critic 🟡2 | 🟡 | ✅ FIXED | `test_l1_elapsed_uses_the_hourglass_glyph…` — **M3 gap 후속 보강** |
| 5 | **중복 degrade 카드** — 결함 1과 동일 버그 클래스 2번째 위치(`covered_slugs`가 live jobs만 순회) | test 2회차 | 🟡 blocking | ✅ FIXED (live: 중복 0회, `rt-27f7bc9f` 1회) | `test_conductor_not_duplicated_as_degrade_card…` — **mutation 확인** |

> execute는 결함 5를 "기존 동작, 허용 가능"으로 진단했고 code-test 2회차가 이를 **오진으로 반증**했다. 다만 execute가 스스로 flag해 판정을 요청한 것이므로 은폐는 없었다.
> mutation 검증은 `/tmp` 완전 복제본(41M)에서 수행 — 워크트리 무변조 확인 후 진행.

---

## 4. 불변식 (I1~I11) 최종 판정

| # | 불변식 | 판정 | 증거 |
|---|---|---|---|
| I1 | record 없는 환경 출력 == v9 | ✅ | v9(HEAD 79953fb4) `git archive` 동시 실행 → 정규화 후 렌더 diff **동일** |
| I2 | `route.load()` 어떤 입력에도 raise 0 | ✅ | 적대적 입력 **20종 + 11종**(node_evidence 경로) → raise 0 · Step 5 스윕 중 위반 1건(`TypeError`) 자진 발견·수정 |
| I3 | route record write 0 | ✅ | 정적 grep 0줄(canonical·mirror) + 동적 sha256/mtime/size 스냅샷 무변화 (**record 실제 로드 상태에서 재확인**) |
| I4 | 노드 점등은 자식 실측이 결정 (record는 레일만) | ✅ | T1-14(`●`>`✓`), T2-4(record만으론 점등 0) |
| I5 | `--json` 기존 키 불변 | ✅ | v9 vs v10: added=[`governor`,`route`], **REMOVED=[]**, `summary` 문자열 동일 |
| I6 | kill 도달 경로 = `_handle_prompt_key` 하나 | ✅ | `control.py` 무수정 · T3-10/T3-11 |
| I7 | `_FOLD_ROWS ∩ (_CLICK_ROWS ∪ _TOGGLE_ROWS) = ∅` | ✅ | 실 `_draw` 하네스: `_FOLD_ROWS=[5,10,18,21,24,27]`, `_CLICK_ROWS=[7]`, `_TOGGLE_ROWS=[]` → 교집합 ∅ (공허한 통과 아님) |
| I8 | governor lease가 세션/잡 카운트에 혼입 0 | ✅ | 별도 집계 · `test_f28c_governor.py` |
| I9 | 실세션 스폰·signal 0 | ✅ | 전 검증 픽스처/스냅샷 기반 |
| I10 | spec 미변경 | ✅ | `git status` — `spec/` 변경 0 |
| I11 | gate 통과를 `completion_gate=` 존재로 판정 안 함 | ✅ | `gate_passed` 키 전 페이로드 부재 확인 |

---

## 5. prd.md §4.9 요구별 최종 대조

| 요구 | 최종 판정 | 비고 |
|---|---|---|
| F-28a read-only 로드 + hash 검증 후 부착 | ✅ | hash 재계산 == stored (실측 record 2건) |
| F-28a tolerant (부재·파싱실패·hash불일치 → 조용한 fallback) | ✅ | 31종 적대적 입력 raise 0 · 부정 입력의 record 승격 0건 |
| F-28a mtime 키 캐시 | ✅ | T1-8/T1-9 |
| F-28a `--json route` additive | ✅ | |
| F-28a **record 소비 실제 성립** | ✅ | 1회차 ⚠️부분 → 결함 1 수정 후 **heuristic 0개** |
| F-28b record DAG breadcrumb | ✅ | 4단 `plan›execute›test›report` 렌더 |
| F-28b 자식 실측 우선 점등 (SD-F2) | ✅ | |
| F-28b record 없는 잡 기존 breadcrumb 유지 | ✅ | I1 |
| F-30 `p` 토글 진입 + footer 표기 | ✅ | `w`와 직교 |
| F-30 카드 L1 `[cap·mode·intensity] rt- — n/m nodes ⏳경과` | ✅ | 1회차 ⚠️`⏳` 누락 → 결함 4 수정 |
| F-30 L2 글리프 `✓`/`●`/`○`/`✕` | ✅ | 4상태 전부 실렌더 |
| F-30 병렬 분기 세로 들여쓰기 + fan-in | ✅ | 3-way fan-out + fan-in |
| F-30 마우스 접기·펼치기 | ✅ | I7 |
| F-30 완료 route 기본 1행 접힘 | ✅ | 1회차 ❌도달 불가 → 결함 2 수정 후 live 도달 |
| F-30 실패 노드 자동 펼침 + 적색 | ✅ | |
| F-30 degrade 카드 (빈칸 아님) | ✅ | 중복 1건(결함 5) 수정 완료 |
| F-30 `tracked_gate_evidence`는 `a`에서만 dim | ⚠️ **대체** | 소스 참조 0건 → `a`는 completion gate **이름**만 표시. **사용자 판단 사항** |
| F-28c governor lease 1행 | ✅ | 죽은 lease + PID 재사용 배제, write 0 |
| F-28c run registry 스킵 + 이월 | ✅ | "부재"가 아닌 **"발견 불가"**로 구분 기록 |

---

## 6. 정직한 결손 · 이월

| 항목 | 사유 | 상태 |
|---|---|---|
| **completion gate 통과 증거** | `completion_gate=`는 launch 시점 선언(실측 반증 2건: 미시작 노드·죽은 노드가 "통과"로 판정됨). `<evidence>.completion.json` 마커는 repo 전역 **0건** | 결손 유지 — **추측 구현 거부**. `_internal/carryover.md §1` |
| **`tracked_gate_evidence`** | 소스 참조 0건 | 미구현 — 사용자 판단 사항 |
| **detached run registry 관측** | `--registry`가 caller-supplied required 인자, canonical 기본 경로 부재, live 파일 0건, record에 해당 kind 노드 0건 | 스킵 + 이월. `_internal/carryover.md §2` |
| critic 🟡3 (degrade 카드 시각 무게) | 스코프 밖 | 이월 (결함 5 해소로 체감 완화) |
| critic 🟢4 (footer 접기 힌트) | 스코프 밖 | 이월 |

---

## 7. 최종 검증 명령 (report 스테이지 재확인)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v10-process-view
python3 -m unittest discover -s tools/fleet/tests -t .     # → Ran 519 tests, OK (17.2s)
```

| 게이트 | 결과 |
|---|---|
| 전체 회귀 | **519 tests, OK** (468 + 51) — report 스테이지 재실행 확인 |
| mirror parity | `diff -r` 차이 0 · `test_mirror_parity` OK |
| G3 정적 read-only 게이트 | 0줄 (canonical·mirror 4파일) |
| 3폭 × 2뷰 카드 오버플로 | 0 (60/120/168 × group/process) |
| `--json` additive | 삭제 키 0 · `gate_passed` 부재 |
</content>
</invoke>
