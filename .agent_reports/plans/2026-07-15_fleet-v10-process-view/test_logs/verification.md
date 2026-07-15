# fleet v10 — code-test 검증 로그 (mode=qa/test, read-only)

판정: **YELLOW** — 회귀 0·안전 불변식 전부 성립. 단 F-28a record 소비가 **live 경로에서 부분 미실현**이며,
그 결과 prd.md:309 "완료 route 1행 접힘"이 실사용에서 도달 불가. T3-5는 프로덕션이 만들 수 없는 상태를 통과시킨다.

소스 무수정(read-only 준수). 실세션 스폰·signal 0 (I9) — 전 검증 픽스처/스냅샷 기반.

---

## 1. 회귀 (V1)

```
python3 -m unittest discover -s tools/fleet/tests -t .   ->  Ran 515 tests, OK  (17.3s)
```
베이스라인 검산(주장 신뢰 아님): 신규 4파일 실측 = 20+6+15+6 = **47** → 515 − 47 = **468** = plan 베이스라인 일치.
**회귀 0 확인.**

## 2. I1 회귀 — v9 대비 실제 렌더 diff

HEAD(79953fb4) = v9 베이스라인(작업 전량 미커밋) → `git archive`로 추출해 동시 실행.
`COLUMNS=120 --once` 그룹 뷰 v9 vs v10 raw diff = **스피너 애니메이션 프레임 3행뿐**.
정규화(스피너·경과·게이지) 후 → **완전 동일**. I1 성립.

## 3. `--json` additive (V4) — before/after 실측

| | v9 | v10 |
|---|---|---|
| top keys | `jobs, memory, sessions, summary` | `governor, jobs, memory, route, sessions, summary` |
| 삭제된 키 | — | **0** |
| `jobs[]` 키 | (기존) | +`route_file/route_hash/route_id/route_node` (삭제 0) |
| `sessions[]` 키 | (기존) | 추가·삭제 **0** |
| `summary` | `{by_harness:{claude:4,codex:4}, dispatch_count:2, session_count:8}` | **문자열 동일** |

`gate_passed` 전 페이로드 부재 → I11 성립. **additive 보증 실측 완료.**

## 4. route record write 0 (I3)

- 정적(G3): `grep -nE "open\(.*['\"]w|write_text|os\.replace|\.write\("` → canonical·mirror 양쪽 **0줄**.
  `route.py`/`governor.py`의 `open()`은 전부 read 모드(`encoding=` only). subprocess/spawn 0.
- 동적: 픽스처 8종 + **live record**의 sha256 + mtime + size를 스냅샷 → `--json`·3폭×2뷰 렌더·전체 스위트 실행 →
  **content·mtime·size 전부 무변화**. write 0 정적·동적 이중 증명.

## 5. tolerant fallback 실측 (I2) — 20종 적대적 입력

부재·garbage·빈 파일·절단 json·hash 불일치·미래 스키마·expect_hash/id 불일치·list/str json·nodes 형태 오류·
디렉토리·None·int·dict·bytes·null byte·권한거부(`/proc/1/mem`)·`/dev/null`
→ **전부 `None` 반환, raise 0**. I2가 강건하게 성립(플랜이 요구한 "어떤 입력에도" 수준 충족).

## 6. mirror parity (V5)

`diff -r --exclude=__pycache__ tools/fleet/ adapters/claude/tools/fleet/` → 차이 0.
`test_mirror_parity` OK. 신규 `route.py`·`governor.py`·테스트 4종·`fixtures/route/*` 전부 byte-identical.

## 7. 픽스처 정합 (실측 기반인가)

- `real_claude_staged.json` = live `/.dispatch/logs/fleet-v10-process-view.route.json`와 **byte-identical 원문 복사** ✓
- `synth_parallel_lab.json` = 실제 3-way fan-out + fan-in. `node_order` → `[[setup],[eval-asr,eval-sep,eval-vad],[aggregate],[report]]` ✓, self-hash 일치 ✓
- 이 사이클 자신의 record(rt-27f7bc9ff152ba13) hash 재계산 == stored ✓

## 8. governor (F-28c) — 독립 검증

픽스처 주입(live pid / 죽은 pid / **starttime 불일치 = PID 재사용**) 3 lease →
`collect()` → `{'active': 1, 'cap': 5, 'classes': {'dispatch': 1}}`.
죽은 lease·재사용 pid **둘 다 메모리에서 배제**, `state.json` 무변화. plan §6a의 까다로운 요구 정확히 충족.
live 실측 `active=1, cap=5` → healthy 무음(절반 미만 숨김)으로 행 미출력 — 설계대로.

## 9. I7 (마우스 맵 배타) — 실 `_draw` 하네스 독립 검증

`FakeScreen` + demo 데이터로 `_draw` 실행 후 실제 맵 관측:
`_FOLD_ROWS=[5,10,18,21,24,27]`, `_CLICK_ROWS=[7]`, `_TOGGLE_ROWS=[]` → 교집합 **∅**.
fold 맵이 비어 있지 않음(공허한 통과 아님) 확인. I7 성립.

## 10. ★ 핵심 결함 — F-28a record 소비가 live에서 부분 미실현

### 증상 (live 재현)
```
$ COLUMNS=120 python3 tools/fleet/fleet.py --once --view process
  ▾ [code·dev] fleet-v10-process-view — no route record
    plan › exec › test
```
이 사이클 **자신의** route record가 degrade 카드로 떨어진다. `--json`도 동일:
`{"route_id":"rt-27f7bc9ff152ba13","source":"heuristic","capability":null,"progress":{"done":0,"total":0}}`

### 반증 — record는 멀쩡하다
terminal 행(`fleet-v10-plan`, status=done)의 **자기 pipe 값 그대로** 호출:
```python
route.load(meta["route_file"], expect_hash=meta["route_hash"], expect_id=meta["route_id"])
-> dict, capability=autopilot-code, topology=staged, nodes=['plan','execute','test','report']
   hash 재계산 == stored: True
```
즉 **부재도 파싱 실패도 hash 불일치도 아니다**. prd.md:302가 조용한 fallback을 허용한 3가지 사유 중
어느 것에도 해당하지 않는데 fallback이 일어난다 — tolerant degrade가 **기능 결손을 가리고 있다**.

### 근인 (필드 1개)
- `_scan_route_nodes`(dispatch.py)는 terminal 행을 살리지만 `route_id`/`route_node`만 담고 **`route_file`을 담지 않는다**.
- `route.resolve_records(jobs)`는 **live `jobs`만** 순회한다. `route_file`은 live 잡에만 있다.
- → route의 route-carrying 행이 전부 terminal이면 record 경로를 아무도 모른다 → `records`에 없음 →
  `build_views`가 `_heuristic_view(rid, [])` → `source=heuristic, nodes=[], 0/0`.

**아이러니**: `_scan_route_nodes`는 plan §3.3이 "설계상 가장 놓치기 쉬운 지점"이라며 `✓ 완료`를 그리려고 만든 장치다.
그런데 같은 pass가 `route_file`을 버려서 그 증거가 **record와 조인될 수 없다** — 증거는 보존됐으나 고아가 됐다.

### 영향 범위
| 상황 | 결과 |
|---|---|
| 같은 route에 live 노드가 1개라도 있음 | 정상 (rt-41eef22d: `plan ✓ › execute ● › test ✓ › report ○` — ✓ 글리프 동작) |
| route 전 노드 done (**prd.md:309 완료 접힘**) | **degrade 카드 — 도달 불가** |
| 스테이지 사이 공백(conductor만 생존) | **degrade 카드** ← 본 사이클 실측 케이스 |

### T3-5는 프로덕션이 만들 수 없는 상태를 통과시킨다
T3-5는 done route에 `route_file`을 든 `liveness="idle"` 자식 잡을 주입한다. 그러나 done 노드의 행은
`_scan_jobs_log`가 classification **이전에 버린다**(종단 행 폐기) — 그런 잡은 실전에 존재할 수 없다.
재현:
```python
route.collect_views([], node_evidence={RID: {4개 노드 전부 done}})
-> source=heuristic, capability=None, progress={'done':0,'total':0}, nodes=0
```
→ T3-5의 `4/4 nodes` 접힘 카드는 **테스트 하네스 안에서만 존재**한다.

**수정 방향(구현은 dev-team)**: `_scan_route_nodes` 증거에 `route_file`(+가능하면 `route_hash`) 1필드 추가하고
`resolve_records`가 jobs ∪ node_evidence를 순회. 부수효과 낮음(로드는 mtime 캐시). T3-5는 live 경로
(`jobs=[]` + terminal evidence)로 재작성해야 회귀를 실제로 막는다.

## 11. prd.md §4.9 요구별 대조표

| 요구 | 판정 | 근거 |
|---|---|---|
| F-28a read-only 로드 + hash 검증 후 부착 | ✅ | T1-4·live hash 재계산 일치, G3 write 0 |
| F-28a **tolerant** (부재·파싱실패·hash불일치 → 조용한 fallback) | ✅ | 20종 적대적 입력 raise 0 |
| F-28a mtime 키 캐시 (tick당 재파싱 차단) | ✅ | T1-8/T1-9, `_CACHE` (mtime,size) 키 |
| F-28a `--json` `route` 키 additive | ✅ | v9/v10 실측 diff — 삭제 0 |
| F-28a **record 소비가 실제로 성립** | ⚠️ **부분** | §10 — live 노드 부재 시 유효 record가 미소비 |
| F-28b record DAG로 breadcrumb 생성 | ✅ | `_route_stage_segs`, `_PIPE_STAGES` 대체. rt-41eef22d 4단 렌더 확인 |
| F-28b **자식 실측 우선** 점등 (SD-F2) | ✅ | T1-14(`●`>`✓`), T2-4(record만으론 점등 0) |
| F-28b record 없는 잡 기존 breadcrumb 유지 | ✅ | I1 렌더 diff 동일 |
| F-30 진입 `p` 토글 + footer 표기 | ✅ | `p group view` 세그 확인, `w`와 직교 |
| F-30 카드 L1 `[cap·mode·intensity] rt- — n/m nodes ⏳경과` | ⚠️ | **`⏳` 글리프 누락** — `1/4 nodes  15m` (§critic 🟡2) |
| F-30 L2 글리프 ✓/●/○/✕ | ✅ | 4상태 전부 실렌더 확인 |
| F-30 병렬 분기 세로 들여쓰기 | ✅ | `├ eval-asr / ├ eval-sep / └ eval-vad` 3-way + fan-in |
| F-30 마우스 접기·펼치기 | ✅ | I7 실맵 배타, T3-8 |
| F-30 완료 route 기본 1행 접힘 | ❌ **도달 불가** | §10 — live에서 완료 route는 degrade 카드가 된다 |
| F-30 실패 노드 자동 펼침 + 적색 | ✅ | `⚠ failed node` + `✕` 자동 펼침 렌더 확인 |
| F-30 degrade 카드 (빈칸 아님) | ✅ | `— no route record` + 휴리스틱 breadcrumb |
| F-30 `tracked_gate_evidence`는 `a`에서만 dim | ⚠️ **대체** | 소스 참조 **0건**. `a`는 completion **gate 이름** 표시. dev_log §82-87에 근거와 함께 공개 disclose됨 → 사용자 판단 필요 |
| F-28c governor lease 1행 | ✅ | 죽은 lease·PID 재사용 배제, write 0, 무음 임계 |
| F-28c run registry 스킵 + 이월 | ✅ | carryover.md — "부재"가 아닌 "발견 불가" 구분까지 정직 |
| I9 실세션 스폰 0 | ✅ | 본 검증 전량 픽스처/스냅샷 |
| I10 spec 미변경 | ✅ | `git status` — spec/ 변경 0 |

## 12. 잘한 결정 (유지 권장)

- **`completion_gate=` = launch 선언이지 통과 증거가 아니다**(§3.3.1)를 실측 반증으로 잡아내고,
  없는 근거로 ✓를 그리는 대신 정직한 결손으로 남긴 것 — prd.md:292 정신 그대로. `gate_passed` 부재를 실측 확인했다.
- **governor 죽은 lease 필터**: read-only이면서 PID 재사용(starttime 대조)까지 막았다. `5/5` 거짓말을 구조적으로 차단.
- **run registry 스킵**을 "부재"가 아니라 "발견 불가"로 정밀하게 구분해 이월 — 추측 경로 스캔 유혹을 거부했다.
- **I2 위반 자진 발견·수정**(`abspath(123)` TypeError) — 계약을 "현실적 입력"으로 축소 해석하지 않았다.
- `_FOLD_ROWS`/`_TOGGLE_ROWS` 텍스트 하이재킹(`folded`/`hidden` 어휘) 회피 — T3-9b로 못박았다.
