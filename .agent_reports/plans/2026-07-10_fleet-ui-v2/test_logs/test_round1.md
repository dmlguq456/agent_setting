# Test round 1 — fleet UI v2 (SD-F1~F4, F-9~F-13) — code-test 스테이지 검증

Stage: `code-test` (품질관리팀 test mode, graduated verification) · QA standard · depth 2 · branch `fleet-ui-v2`
Verified against execute round 1 (commit `8eca886`, safety base `ae8c165`).

## Overall verdict: **FAIL (1 mandatory item)** — 표시층 결함 1건, 나머지 전부 PASS

marquee 기능(SD-F4 tolerant 파서 · SD-F2 conductor 집계 · SD-F3 effort/model_role 스키마 · SD-F1
role 라벨 휴먼화)은 라이브에서 모두 동작. 단 **item 3(a)** 에서 depth-2 스테이지 row 의 breadcrumb
**키 prefix 가 raw `code-test:` 를 그대로 노출** — SD-F1 "raw code_execute/code-test 금지" 계약 위반.
display-layer 한정·크래시 없음이라 fix-forward 로 처리 가능하나 mandatory 기준 위반이므로 verdict 는 FAIL.
**수정은 report/conductor 결정** (이 스테이지는 수정 안 함).

---

## Mandatory 항목별 판정

### Item 1 — Unit suite: **PASS**
```
cd tools && python3 -m unittest fleet.tests.test_dispatch -v   → Ran 48 tests … OK
```
- 정확히 **48 tests green** (baseline 36 + execute 신규 12). expected ~48 일치.
- **D5 canonical-comma 무회귀 확인**: `DepthTwoRegistryMetadataTest`(test_dispatch.py:463–647,
  `test_jobs_log_pipe_metadata_surfaces_depth_two_parent`·`test_legacy_jobs_log_infers_harness_from_runtime_model_fields`
  등 canonical-comma pipe 파싱) + 전용 가드 `test_canonical_comma_pipe_still_parses_unchanged`
  전부 green. SD-F4 continuation tokenizer 가 콤마-only 행을 회귀시키지 않음(R1 확인).

### Item 2 — 신규 테스트 present & meaningful: **PASS** (단 (d) 픽스처 갭 — 아래 참조)
| 요구 | 테스트 | 상태 |
|---|---|---|
| (a) space-separated pipe | `TolerantPipeParsingTest.test_parse_pipe_space_separated_row` | ✓ |
| (b) `model_role=deep maker` value-internal-space | `test_parse_pipe_value_internal_space` (+ N2 `test_parse_pipe_continuation_then_field`) | ✓ |
| (c) unknown-key-ignored | `test_parse_pipe_unknown_key_ignored` | ✓ |
| (d) stage-name 라벨 plan/exec/test/report | `StageWorkerRenderTest.test_stage_worker_rows_render_stage_labels` (+ g-case prefix 회귀) | ✓ (갭 有) |
| (e) conductor 집계 + N5 report lone-token | `ConductorBreadcrumbTest` 3케이스(active-child / own-stage fallback / report lone-bright) | ✓ |
| (f) alert humanize 집계 | `AlertHumanizeTest` 2케이스(multi 집계+tail-strip / 단일 미집계) | ✓ |

- **테스트 커버리지 갭 (item 3a 결함의 근본원인)**: (d) 픽스처가 depth-2 job 을 `key="code"` 로
  생성한다(test_dispatch.py:709). 실제 라이브 depth-2 스테이지 job 의 key 는 capability =
  `code-test`(collect() 확인). 테스트가 `key="code"` 를 쓰는 바람에 breadcrumb prefix 는 `code: `
  로 렌더돼 raw 누출이 가려짐 → `assertNotIn("code-test", text)` 가 통과. 라이브에선 `key="code-test"`
  라 누출이 그대로 드러난다(item 3a). 테스트가 실패한 게 아니라, 현실 key 를 안 써서 결함을 못 잡음.

### Item 3 — LIVE 관제 실증
라이브 fixture = 이 파이프 자신. 관측된 depth-1 conductor `fleet-ui-v2`(capability-owner) +
depth-2 `fleet-ui-v2-test`(=본 세션, working). (execute 스테이지는 이미 종료돼 jobs.log 부재 — 정상.)

#### (a) depth-2 스테이지 row 휴먼 스테이지명: **FAIL**
`fleet-ui-v2-test`(depth-2, key=`code-test`) 라이브 렌더 (`fleet.py --once`, `render._build_lines` 색키 검증):
```
▍     ⠋ claude code fle… (dev·std/test/qa:~std) fleet-ui-v2   opus (high)   code-test: queued   —
                              ^^^^ role 태그 = test (SD-F1 OK)            ^^^^^^^^^ raw code-test 누출
   STAGE 색키: [('queued','stg0_on')]   ·   raw 'code-test' in row? True
```
- **부분 성공**: role 태그는 `test` 로 휴먼화됨(`_short_role`→`_stage_role_label`, SD-F1 role 경로 OK),
  상태 `queued` 는 `open`→`queued` 휴먼화(F-11 OK), 자기 effort `opus (high)` 1급 표시(SD-F3 OK).
- **결함**: breadcrumb **키 prefix 가 raw `code-test:`**. 원인 = `_dispatch_row`
  (**render.py:857-858**): `if key and key != name: segs.append((key + ": ", ...))` 가 `j.key` 를
  그대로 방출. depth-2 스테이지 워커의 key 는 항상 capability(`code-plan`/`code-execute`/`code-test`/
  `code-report`)이므로 **모든 depth-2 스테이지 row 가 계통적으로 raw code-* prefix 를 노출**한다.
  task item 3(a) "NOT raw code_execute/code-test" 및 SD-F1 의도와 정면 배치.
- **수정 방향(참고, 미적용)**: prefix 를 `_STAGE_ROLE`(code-test→test) 매핑으로 휴먼화하거나, depth-2
  단일-스테이지 워커에선 prefix 를 생략. report/conductor 결정.

#### (b) conductor breadcrumb 집계: **PASS**
`fleet-ui-v2` conductor row (`render._build_lines` 색키 검증):
```
▍ ↳ ⠋ claude code   fl… (dev·std/owner/qa:~std) fleet-ui-v2   opus (medium)   code: plan › exec › test   —
   STAGE 색키: [('plan','stg0_off'), ('exec','stg1_off'), ('test','stg2_on')]
```
- 활성 depth-2 자식(`fleet-ui-v2-test`, code-test, liveness=working)의 스테이지 `test` 가
  **`stg2_on`(하이라이트)**, plan/exec 는 off. `_conductor_stage_override` active-child 계산이
  라이브에서 정확히 동작(SD-F2). conductor row 에는 raw code-* 누출 없음.

#### (c) 기존 render 무회귀: **PASS**
`fleet.py --once` / `--demo --once` 육안 + 구조 확인:
- usage 헤더(claude/codex/opencode) ✓ · pulse(`fleet ⠙ 1 working …`) ✓ · 그룹 카드(agent_setting/
  등 틴트+▍레일) ✓ · folded(`· inactive +10 folded …`) ✓ · `+2 malformed … skipped`(dim, F-12a) ✓
- legend ✓ **F-12(c) glyph-appearance 동작 실증**: `--once`(실데이터, detached/stale 없음) →
  `⠹ working ● idle ▾N child ↳ dispatch 🚧 N worktrees ~ derived` / `--demo`(해당 상태 有) →
  `○ detached · stale` 가 추가로 등장. 조건부 글리프만 조건 충족 시 노출됨.
- footer wlbl **F-12(b) 3-모드** 확인(render.py:1692): `"wide/narrow/stack" if _LAYOUT=="auto"
  else "%s!"%_LAYOUT` (footer 는 live 루프 chrome 이라 `--once` 스냅샷엔 미출력 — 코드로 확인).

#### (d) --json effort/model_role 채워짐: **PASS**
`fleet.py --json` 스테이지 잡:
```
fleet-ui-v2-test  : effort=high    model_role="deep reviewer"   (depth-2 code-test)
fleet-ui-v2       : effort=medium  model_role="-"               (depth-1 conductor)
```
- SD-F3 스키마 필드 2종이 jobs.log pipe → `DispatchJob` → JSON 까지 온전히 전달. 특히
  `model_role="deep reviewer"`(value-내부 공백)가 tolerant 파서로 안 깨지고 복원됨(R2 실증).

### Item 4 — Syntax/import clean, no crash: **PASS**
- `py_compile` 전체(`tools/fleet/**/*.py`) → compile OK.
- exit code: `--once`=0 · `--json`=0 · `--demo --once`=0. 크래시·예외 없음.

---

## 결함 요약 (report/conductor 결정 대상)

| # | 심각도 | file:line | 내용 |
|---|---|---|---|
| D1 | medium (display-layer) | tools/fleet/render.py:857-858 | depth-2 스테이지 row breadcrumb 키 prefix 가 raw `code-test:`(capability key) 노출. `key + ": "` 가 `j.key` 를 휴먼화 없이 방출 → 모든 depth-2 스테이지 워커(code-plan/execute/test/report)에 계통적. item 3(a) "NOT raw code-test" 위반. |
| D2 | low (test gap) | tools/fleet/tests/test_dispatch.py:709 | `test_stage_worker_rows_render_stage_labels` 픽스처가 depth-2 job 을 `key="code"` 로 생성(현실은 `key="code-test"`). 이 갭이 D1 을 유닛 레벨에서 가림. 픽스처 key 를 realistic capability 로 바꾸면 D1 이 유닛에서 잡힘. |

두 결함은 연결됨 — D2(픽스처 갭)가 D1(라이브 누출)을 놓치게 만든 구조. D1 수정 시 D2 픽스처도
`key="code-<stage>"` 로 강화 권장.

## 검증 명령/결과 요약
```
cd tools && python3 -m unittest fleet.tests.test_dispatch -v          # Ran 48 tests … OK
python3 -m unittest ...DepthTwoRegistryMetadataTest ...TolerantPipeParsingTest  # Ran 13 … OK (D5 무회귀)
python3 tools/fleet/fleet.py --once      # exit 0, conductor test=stg2_on / stage row raw code-test 누출
python3 tools/fleet/fleet.py --json      # exit 0, effort/model_role 채워짐
python3 tools/fleet/fleet.py --demo --once  # exit 0, F-12c 조건부 글리프 실증
py_compile tools/fleet/**/*.py           # compile OK
```

## Artifact
- 본 리포트: `.agent_reports/plans/2026-07-10_fleet-ui-v2/test_logs/test_round1.md`
