# fleet v10 — code-test 재검증 (2회차, read-only)

판정: **YELLOW (좁혀짐)** — 결함 1~4 **전부 재현 확인·수정 성립**. 회귀 0, tolerant/write0/json additive/mirror 전부 유지.
잔여: execute가 "허용 가능한 기존 동작"으로 flag한 중복 degrade 카드는 **결함이며, 결함 1과 동일 버그 클래스의
두 번째 위치**다(수정 미완). 소스 무수정, 실세션 스폰 0.

---

## 1. 회귀

`python3 -m unittest discover -s tools/fleet/tests -t .` → **Ran 516, OK** (17.0s). 515 → 516 (+1), 회귀 0.

## 2. 결함 1 — **FIXED (live 재현 확인)**

이 사이클 자신의 record(`rt-27f7bc9ff152ba13`), live `--once --view process`:
```
BEFORE(1회차):  ▾ [code·dev] fleet-v10-process-view — no route record
                  plan › exec › test
AFTER (실측) :  ▾ [code·dev·standard] rt-27f7bc9f — 0/4 nodes ⚠ failed node
                  plan ✕ › execute ○ › test ○ › report ○
```
`--json`: `source:"record"`, `capability:"autopilot-code"`, nodes 4개
`[('plan','failed'),('execute','pending'),('test','pending'),('report','pending')]`.

**전 route가 record로 해소** — 1회차 6개 중 heuristic 5개 → 2회차 **heuristic 0개**:

| route_id | round1 | round2 |
|---|---|---|
| rt-1120bb39 / rt-27f7bc9f / rt-5e123969 / rt-70be9258 / rt-9ff8199b | heuristic | **record** |
| rt-41eef22d | record | record |

★ **1회차 진단의 사후 확증**: `/tmp/fleet-v9-route.json`·`/tmp/agent-note-d1-route.json`은 **지금도 실재한다**
(66549·12413 bytes). 즉 1회차의 heuristic은 파일 휘발이 아니라 **route_file 배선 결손**이 원인이었다는 진단이
정확했다. 파일이 멀쩡한데 5개가 미소비되고 있었다.

## 3. 결함 2 — **FIXED (종속 해소, live 재현)**
```
▸ [code·dev·standard] rt-1120bb39 — 4/4 nodes
▸ [spec·update·standard] rt-70be9258 — 3/3 nodes
```
전 노드 done route가 `▸` 1행 접힘으로 **live 도달**. 1회차에 "도달 불가"로 지적한 prd.md:309 성립.

## 4. 결함 3 — **FIXED** (마퀴 병렬 카드 정합)
```
▾ [lab·eval·standard] rt-6f5423d0 — 1/6 nodes  ⏳10m ⚠ failed node
  setup ✓10m
    ├ eval-asr ● 9m (Sonnet 5·medium)
    ├ eval-sep ✕ 3m
    └ eval-vad ○
```
`setup ○`(미기동) + 자식 active/failed의 **불가능한 DAG** 해소 → `setup ✓10m`, `0/6` → `1/6 nodes`.
done 부모 아래 active/failed/pending 자식 = 정합.

## 5. 결함 4 — **FIXED** (`⏳` L1)
`rt-2f5c79f5 — 1/4 nodes  ⏳15m` ↔ 자식 행 `⏳8m` — 같은 카드 내 표기 일원화. prd.md:307 문자 충족.
`⏳` 추가 후 **60/120/168 × {live, demo} 카드 라인 오버플로 0**(east_asian_width 독립 재구현 교차검증).

## 6. ★ Mutation 검증 — 새 테스트가 실제 회귀를 막는가

`/tmp` 완전 복제본(41M, rsync)에서 수정을 되돌려 실측. **워크트리 무수정.** 복제본 무변조 = 516 OK 확인 후 진행.
(각 mutation의 `test_mirror_parity` 실패는 canonical만 변조한 데 따른 산물 — 무시.)

| mutation | 되돌린 것 | 실패한 테스트 | 판정 |
|---|---|---|---|
| **M1** | `_scan_route_nodes`의 `route_file`/`route_hash` carry | `test_t1_13b_terminal_only_route_still_resolves_to_a_record_not_heuristic` | ✅ **잡는다** |
| **M2** | `resolve_records`의 node_evidence fallback 루프 | `t1_13b` + **`test_t3_5_all_done_route_defaults_to_one_line_fold`** + **`test_t3_9b_folded_completed_card_not_in_toggle_rows`** | ✅ **잡는다** |
| **M3** | `_route_card_l1`의 `⏳` → `_CLOCK` | (mirror만) — **0건** | ⚠️ **미보호** |
| **M4** | demo `_LAB_RID` setup seed | (mirror만) — **0건** | ⚠️ **미보호** |

**1회차 지적 해소 확인**: T3-5/T3-9b는 이제 `jobs=[]` + terminal node_evidence(프로덕션 실형태)에 묶여 있고,
M2에서 **실제로 실패한다**. 1회차의 "프로덕션이 만들 수 없는 상태를 통과시킨다"는 해소됐다.
M1이 T3-5를 안 깨는 것은 결함이 아니다 — T3-5는 node_evidence를 직접 구성해 render 층을 보고, dispatch 층의
carry는 t1_13b가 `jobs_route.log` 픽스처 → `collect()` 경로로 덮는다(층별 분담, 정합).

**잔여**: 결함 3·4는 고쳐졌으나 **테스트가 없다** — 되돌려도 스위트가 통과한다. 향후 편집이 조용히 되돌릴 수 있다.
(demo 픽스처·글리프라 심각도는 낮음. 🟢)

## 7. tolerant 3사유 — node_evidence fallback이 hash 검증을 우회하지 않는가 (중점 3)

구조: fallback도 `load(rf, expect_hash=rh, expect_id=rid)` — jobs 경로와 **동일 검증 시그니처**.
행위 실측(node_evidence 경로 전용 공격, 11종):

| 입력 | resolve | view.source |
|---|---|---|
| 유효 record + 정확한 hash | **record** | record |
| **본문 변조**(stored hash стale) | None | **heuristic** |
| 유효 record + **WRONG expect_hash** | None | **heuristic** |
| 유효 record + **WRONG expect_id** | None | **heuristic** |
| `synth_broken_hash` / `synth_bad_schema` | None | heuristic |
| **부재** / garbage json | None | heuristic |
| route_file=None / 12345 / 디렉토리 | None | heuristic |

→ **부정 입력이 record로 승격된 사례 0건, raise 0건.** hash·id 검증 우회 없음, 조용한 degrade 유지.
prd.md:302의 3사유(부재·파싱 실패·hash 불일치) **회귀 0**.

## 8. write 0 (중점 4)

- 정적 G3: canonical·mirror 4파일 **0줄**.
- 동적: 픽스처 8종 + **실 record 전량**(`.dispatch/logs/*.route.json`, `/tmp/fleet-v9-route.json`,
  `/tmp/agent-note-d1-route.json`, `/tmp/agent-note-v93-route.json`)의 sha256+mtime+size 스냅샷 →
  3폭×{live,demo} 렌더 + `--json` + 전체 스위트 실행 → **전부 무변화**.
  ★ 이번엔 record가 **실제로 로드되는** 상태에서의 write 0이므로 1회차보다 강한 증거다.

## 9. `--json` additive (중점 5) · mirror (중점 7)

v9 베이스라인(HEAD 79953fb4 `git archive`) vs 현재: 최상위 `added=[governor, route]`, **REMOVED=[]**,
`sessions[]` 키 증감 0, `jobs[]` +4 삭제 0, `summary` **문자열 동일**, `gate_passed` 부재.
mirror: `diff -r` 차이 0 + `test_mirror_parity` OK.

## 10. ★ 새 degrade 카드 판정 — **결함이다** (execute의 진단은 틀렸다)

live 실측 (두 카드가 **같은 화면에 2행 간격**):
```
▾ [code·dev·standard] rt-27f7bc9f — 0/4 nodes ⚠ failed node     ← 이 파이프라인의 record 카드
  plan ✕ › execute ○ › test ○ › report ○
  …
▾ [code·dev] fleet-v10-process-view — no route record            ← 같은 파이프라인의 conductor
  plan › exec › test
```

### execute 주장 대조
| 주장 | 판정 |
|---|---|
| "degrade 카드가 수정 이전에도 있었다" | **사실** — 1회차 캡처에 3회(폭당 1회) 출현 |
| "수정 이전과 달라진 것 없다" | **거짓** — 1회차 캡처의 `rt-27f7bc9f` 출현 **0회**. record 카드가 신규이므로 **중복 자체가 이번 수정으로 발생** |
| "conductor의 **표시 이름을 공유하는** route 미보유 잡 때문" | **오진** — 이름 공유가 아니다. 그 잡은 conductor **본인**(`fleet-v10-process-view`, depth=1, role=conductor, route_id=None)이다 |
| "결손 원칙상 허용 가능" | **불가** — 아래 |

### 진짜 근인 = **결함 1과 동일한 버그 클래스, 두 번째 위치**
`render.py:1923`:
```python
covered_slugs = {j.parent_slug for j in jobs
                 if j.route_id in route_views_by_id and j.parent_slug}
```
**`jobs`(live)만 순회한다.** route_id를 든 자식 `fleet-v10-plan`은 `done` → `_scan_jobs_log`가 classification
전에 폐기 → live `jobs`에 없다. 실측:
```
live jobs = [('fleet-v10-process-view', route_id=None, depth=1)]
covered_slugs = set()          ← 비어 있다
conductor 제외됨? False        ← 그래서 degrade 카드가 뜬다
```
즉 결함 1이 고친 "terminal 행이 사라져 live jobs만으로는 부족하다"는 **바로 그 가정**을,
`resolve_records`는 고쳤지만 `covered_slugs`는 **그대로 두었다**. 수정이 절반만 적용됐다.

### 결함인 근거
1. **코드 자신의 계약 위반** — `_degrade_candidates` 독스트링(render.py:1842-1845)이 이 중복을 명시적으로
   금지한다: *"the depth-1 CONDUCTOR of a route whose route_id lives on one of ITS children would
   otherwise show up a SECOND time as a bare degrade card right next to its own real route card."*
   설계 선택이 아니라 **작동하지 않는 방어 로직**이다.
2. **prd.md:310 결손 원칙 비대상** — 결손 카드는 record가 *진짜 없는* 잡을 위한 것이다. 이 파이프라인은
   record가 있고, fleet이 **2행 위에 그 record를 그리고 있다**.
3. **F-28의 존재 이유에 정면 위배** — prd.md:286의 "정책 따로 표시 따로"의 기준 불일치 제거가 F-28 목적인데,
   한 파이프라인을 "rt-27f7bc9f·4노드·plan ✕"와 "no route record"로 **동시에 두 번, 모순되게** 진술한다.
   사용자에게는 별개 작업 2개로 오인된다(중복 오인 소지 = 실재).

### 수정 방향 (dev-team; 결함 1과 같은 1필드 형태)
evidence에 parent 링크가 없다 — 실측 evidence 키:
`['completion_gate','effort','harness','model','note','pid','route_file','route_hash','slug','status','ts']`.
→ `_scan_route_nodes`가 같은 pipe 행에서 이미 파싱 중인 **`parent`를 1필드 더 싣고**(결함 1의 `route_file`
carry와 동형·추가 I/O 0), `covered_slugs`를 `jobs ∪ node_evidence`로 계산. 회귀 테스트는 M2와 같은 형태
(`jobs=[conductor만]` + terminal evidence → degrade 카드 0)로 묶어야 한다.

## 11. 잔여 이슈
1. **중복 degrade 카드** (§10) — 결함 1의 미완 부분. 🟡
2. 결함 3·4에 **회귀 테스트 없음** (M3/M4 무검출). 🟢
3. `tracked_gate_evidence` 미구현 / completion-gate 통과 증거 결손 — **재지적 아님**, 정직한 disclose 상태의 사용자 판단 사항.
4. critic 🟡3(degrade 카드 시각 무게)·🟢4(fold 힌트) — 스코프 밖. 단 §10 중복이 해소되면 🟡3의 체감도 함께 줄어든다.

## 12. 잘한 점
- 결함 1 수정이 **정확히 진단대로 최소 표면**(1필드 carry + fallback 루프)으로 들어갔고, 검증 시그니처를
  jobs 경로와 동일하게 유지해 **hash 우회를 만들지 않았다** — 11종 공격으로 확인.
- T3-5/T3-9b를 프로덕션 실형태로 재작성했고 **M2에서 실제로 실패한다** — 지적을 형식이 아니라 실질로 반영.
- `plan ✕`(note=dead-plan-done 실측 반영)을 꾸미지 않고 정직하게 표시 — §3.3.1 정신 유지.
- 중복 카드를 **스스로 flag**해 판정을 요청했다(진단은 틀렸으나 은폐하지 않았다).
