# Plan Review — fleet UI v2 (round 1)

- 대상: `plan/plan.md`, `plan/checklist.md`
- QA level: standard · within-spec 구현 사이클
- 검토자: 품질관리팀 (plan-review, lightweight independent)
- 기준선: `python3 -m unittest fleet.tests.test_dispatch` → **현재 36 tests OK** (실행 확인)

## Verdict: 실행 가능 (BLOCKING 없음)

파일:라인 인용은 대부분 실제 코드와 일치하고, 핵심 알고리즘(SD-F4 tokenizer, SD-F2 conductor
breadcrumb)은 논리적으로 건전하다. 아래는 전부 **non-blocking** — 실행 전 수정하면 좋지만
전체 test suite 를 돌리는 검증 절차가 이미 안전망이라 실행을 막지 않는다.

---

## BLOCKING issues

없음.

---

## Non-blocking notes

### N1. (Q4) 회귀 테스트 인용 라인이 틀렸다 — 실제 g9 테스트는 467–535
plan Verification(line 249–251)과 checklist 이 `_ROLE_SHORT` g6/g9 제거의 회귀 대상으로
`test_dispatch.py:72-80` 을 지목하는데, 그 자리는 `test_loop_dispatch_profile_omits_duplicate_case_role`
로 **g6/g9 매핑과 무관**하다 — `raw_role == slug` 일 때 role 을 null 로 만드는
`_dispatch_role_suffix`(render.py:717–718) 로직만 검증한다. g6/g9 제거해도 이 테스트는 영향 없다.

실제로 g9 short-form 에 의존하는 테스트는 **test_dispatch.py:467–535** 의 4개 (`loop/drill·g9`
assert, 예: line 476/492/505/528). 이들이 `_short_role("g9_cross_harness_depth2_dispatch") == "g9"`
를 요구한다. 다행히 일반 규칙 `re.match(r"^(g\d+[a-z]?)", ...)` 은 "g9" 를 그대로 뽑아내므로
**회귀 없음**(확인함). 다만 plan 이 실행자를 엉뚱한 테스트로 안내하니 인용을 467–535 로 교정할 것.
g6 render 매핑을 직접 assert 하는 테스트는 없다(546–569 는 `_scan_jobs_log` 파싱 레벨).
`g8b`(245/266/274 도 파싱 레벨)는 현재 `_ROLE_SHORT` 에 없어 축약이 안 되는데 일반 규칙 도입 후
"g8b" 로 축약됨 — 이는 회귀가 아니라 개선(신규 동작).

### N2. (Q1) tokenizer 는 `deep maker` 에 정확, D5 에 비회귀 — 단 continuation 토큰에 `=` 가 없다는 전제
- `model_role=deep maker` → `re.split(r"[,\s]+", ...)` = `["model_role=deep","maker",...]`.
  "maker" 는 `=` 없음 → 직전 value 에 join → `"deep maker"` 복원. **정확.** ✓
- D5 canonical `k=v,k=v,...` → 모든 토큰이 `=` 보유 → 각자 새 쌍 → 기존과 동일 결과. **비회귀.** ✓
- **실질 failure mode**: continuation(=`=`-없는) 토큰이 아니라, _value-내부 공백 뒤에 오는 토큰이
  우연히 `=` 를 포함_ 하면 새 key 로 오인식된다 (예 `notes=foo bar=baz` → `bar` 를 새 key 로).
  현재 pipe writer(dispatch-headless.py:260, plan line 44 에 문서화)가 **모든 필드를 `key=value`
  로만 방출**하고 필드 vocabulary 가 닫혀 있어(capability/mode/qa/depth/parent/worker_role/owner/
  model_source/model_role/model/effort/profile/intensity) 실제로 발생하지 않는다. 즉 tokenizer 의
  안전성은 "writer 가 필드마다 항상 `key=` 를 붙인다"는 계약에 의존한다. plan Risks 에 이 전제를
  한 줄 명시하고, 신규 테스트 (b) 에 `model_role=deep maker` 뿐 아니라 continuation 뒤 필드가
  정상 파싱되는 케이스를 함께 넣으면 좋다.

### N3. (Q2) 호출부 커버리지 — 온전함, 단 두 가지 확인
- **SD-F1 (`_short_role`)**: worker_role 은 render.py:716 한 곳에서만 읽히고 `_short_role` 은
  719 한 곳에서만 호출된다 → `_dispatch_role_suffix` → `_dispatch_profile` → `_dispatch_row`(765)
  및 `_dispatch_row_2line`(877) 양쪽 레이아웃 모두 경유. **단일 chokepoint, 누락 없음.** ✓
- **SD-F2 (stage_override)**: `_dispatch_row_stack`(862)는 `_dispatch_row_2line` 에 위임할 뿐이므로
  새 param 을 stack → 2line 으로 **forward** 만 하면 됨. 실제 stage_override 계산·주입 지점은
  `_emit_dispatch_tree`(1236)이며 여기서 `_jrow(...)`(1239) 또는 `_dispatch_row(...)`(1242) 호출에
  param 을 실어야 한다 — plan Step 2.7 이 세 함수를 다 나열하나 "_emit_dispatch_tree 호출부에
  주입"이 실제 wiring 자리임을 명시하면 실행자가 놓치지 않는다.
- **SD-F3 (effort)**: line 781·893 만 고치면 stack 은 2line 경유로 자동 커버. ✓

### N4. (Q3) conductor breadcrumb 로직 — 건전함
`_emit_dispatch_tree`(1236)는 **job 자신의 row 를 먼저 렌더**(1238–1244)한 뒤 자식으로 재귀
(1245, `job_children.get(job.slug, [])`)한다. `job_children` 은 enclosing closure 변수라 row 렌더
_이전_ 에 `kids = job_children.get(job.slug, [])` 로 접근 가능하다. depth-2 code-* 자식은 이미
line 1245 재귀가 순회하므로 conductor.slug 아래로 정상 keying 되어 있음이 보장된다. **접근성·타이밍
문제 없음.** active 계산(`liveness=="working"` 인 code-* 자식 → `_STAGE_ROLE`)도 자식 객체 필드로
가능. override None 기본값이라 비-conductor row 는 현행 불변(R4 타당).

### N5. (Q5) report breadcrumb — 기능상 OK, plan 문구가 실제 동작과 불일치
`report` 는 `_PIPE_STAGES["code"]=["plan","exec","test"]` 밖이다. `stage_override="report"`,
key="code" 로 `_stage_segs` 진입 시: seq 존재·"report" not in seq·("","code","open","running")에도
없음 → **fallthrough line 576–577** → `[("report", _cur_key(0))]` = `stg0_on` 로 **밝은 단일
"report" 토큰**을 낸다. plan(line 148–150)은 이를 "dim track 표시"로 서술하는데 실제로는 dim track
이 아니라 lone bright 토큰이다. 기능적으로는 보고 단계를 "report" 로 명시하니 수용 가능하나,
plan 문구가 코드 동작을 오기술 → 실행 시 (i) lone "report" 토큰을 그대로 수용하거나 (ii) report 를
명시 처리(예: plan›exec›test 전부 done + report 하이라이트)할지 결정하고, 결정에 맞게 prose 정정.
신규 테스트 (e) 에 "자식 done + report active" 케이스의 기대 렌더를 못박아 둘 것.

### N6. (Q4) 검증 커맨드 — 구체적·실행 가능
- `cd tools && python3 -m unittest fleet.tests.test_dispatch -v` → 실제 36 tests OK 확인. ✓
- `python3 tools/fleet/fleet.py --once` / `--json` → 두 flag 모두 argparse 에 존재
  (fleet.py:35/44), `--json` 은 `_snapshot_json`(64)로 collector 결과 방출 → `effort`/`model_role`
  필드는 `DispatchJob.to_dict()`(model.py:180, `asdict`)로 자동 노출되므로 Step 2.1 필드 추가만으로
  `--json` 검증이 성립. ✓ 단 `--json` snapshot 이 두 신규 필드를 실제로 직렬화하는지
  (`_snapshot_json` 이 to_dict 전체를 담는지) 는 실행 시 눈으로 한 번 확인 권장.

---

## 잘 된 점

- Current State Analysis 가 file:line 을 실제 코드와 일치시켜 검증 부담을 크게 줄였다 —
  `_parse_pipe_meta` 게이트(dispatch.py:61), `_stage_segs` fallthrough(576), `DispatchJob` 필드
  부재, footer wlbl 3-모드 버그(1545) 모두 실측과 일치.
- SD-F4 tokenizer 를 순진한 whitespace-split 대신 continuation 방식으로 잡은 것이 `deep maker`
  edge case 의 핵심을 정확히 짚었고, R1/R2 로 회귀·value-공백 위험을 분리 문서화했다.
- Phase 의존 순서(파서 → 스키마 → render), R6 의 `_stage_segs` 공유 편집 충돌 경계(2.7→3.4),
  `_OFFSET` 불변식(R3) 준수까지 회귀 표면을 성실히 커버했다.
- override None 기본값 / proc-scan None fallback(R5) 등 "현행 동작 불변" 안전장치가 일관.

## 실행 전 권장 (전부 non-blocking)
1. N1 — 회귀 테스트 인용을 `test_dispatch.py:72-80` → `467-535` 로 교정.
2. N2 — Risks 에 "writer 가 필드마다 `key=` 방출" 전제 한 줄 + continuation 뒤 필드 파싱 테스트.
3. N5 — report breadcrumb 동작 결정(lone token 수용 vs 명시 처리) + prose 정정 + 테스트 (e) 확장.
4. N3 — Step 2.7 에 "_emit_dispatch_tree 호출부가 stage_override 주입 자리, stack 은 forward" 명시.
