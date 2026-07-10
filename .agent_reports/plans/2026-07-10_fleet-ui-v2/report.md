# Cycle Report — fleet UI v2 (stage-dispatch 관제 parity + UI 가독성, PRD v2 §4.5·§4.6)

Stage: `code-report` (depth-2 headless, worker_role=code-report, owner=autopilot-code) · QA standard · branch `fleet-ui-v2`

## 개요

`agent-fleet-dashboard` PRD v2 (`ae8c165`, 2026-07-10)에 잠금된 두 계약을 `tools/fleet/` 코드로 실현한
구현 사이클. 신규 스펙 결정 없음(within-spec) — SD-F1~F4(스테이지 관제 parity)와 F-9~F-13(가독성 폴리시)
둘 다 청사진에 이미 명시된 항목.

- **SD-F1~F4** — jobs.log pipe 파서 공백/콤마 tolerant화, depth-2 스테이지 row 사람이 읽는 라벨
  (`plan`/`exec`/`test`/`report`)로 렌더, conductor breadcrumb 이 활성 depth-2 자식 스테이지를
  하이라이트, `DispatchJob`에 `effort`/`model_role` 1급 필드 추가.
- **F-9~F-13** — dispatch 메타라벨 width-drop 우선순위, alert 집계/tail-strip, status 어휘 휴먼화,
  legend 조건부 glyph, dead/stale row `last seen <age>` 셀 압축.

체크리스트 29/29 완료 (`plan/checklist.md`).

## 사이클 아크

| 단계 | 커밋 | 결과 |
|---|---|---|
| plan | (checklist in `8eca886`) | 29항목 plan/checklist 확정, spec-significance=within-spec |
| execute Phase 1-2 | `ceb286c` | tolerant 파서 + stage-dispatch 스키마(SD-F1~F4) 구현 |
| execute Phase 3 | `c9abfa1` | 가독성 폴리시(F-9~F-13) 구현 |
| execute Phase 4 | `8eca886` | 신규 유닛 테스트 12건 추가, 48/48 green, plan 산출물 committed |
| test round 1 | `62db3f1` | 48/48 green이나 **FAIL** — D1(raw `code-*` prefix 누출), D2(test 픽스처 갭) 발견 |
| execute round 2 | `381cc92` | D1(render.py 2개 경로) + D2(test fixture) 수정, fail-before/pass-after 회귀증명 |
| test round 2 | `e6f51bf` | **PASS (all-green)** — D1/D2 해소, 무회귀, 신규 결함 0 |

## 결함 → 원인 → 정정 아크 (D1/D2)

### D1 — depth-2 스테이지 row breadcrumb 에 raw capability key 누출 (medium, display-layer)

- **발견**: test round 1, item 3(a) — 라이브 렌더에서 `code-test:` 가 그대로 노출, SD-F1
  "raw code_execute/code-test 금지" 계약 위반. role 태그(`test`)·effort(`opus (high)`)는 정상.
- **근본원인**: `tools/fleet/render.py` 의 `_dispatch_row`(wide, 당시 line ~857-858)와
  `_dispatch_row_2line`(narrow card, ~972-973) **두 경로 모두** `j.key`(=capability)를 휴먼화 없이
  `key + ": "` 로 그대로 방출. depth-2 스테이지 워커의 key 는 항상 `code-plan`/`code-execute`/
  `code-test`/`code-report` 이므로 계통적 결함.
- **정정** (`381cc92`): 기존 SD-F1 helper `_stage_role_label(worker_role)` 을 raw `key` 에도 재사용
  (`code-execute→exec` 등 `_STAGE_ROLE` 매핑, 미지 key 는 raw-key fallback 유지). 두 렌더 경로 동일 적용.
  conductor breadcrumb(`key="code"`, `_STAGE_ROLE` 밖)은 영향 없음 — 의도대로 그대로 렌더.
- **narrow-card 경로 재발견**: wide 경로 수정 후 `--demo` 라이브 재검증 중 narrow 카드에서도 동일
  누출 확인 → 같은 라운드에서 두 번째 지점까지 함께 수정.

### D2 — 유닛 테스트 픽스처가 D1 을 못 잡던 갭 (low, test gap)

- **발견**: test round 1 item 2(d) — `StageWorkerRenderTest.test_stage_worker_rows_render_stage_labels`
  가 depth-2 job 을 `key="code"`(conductor의 track key)로 생성, 실제 라이브 key(`code-test` 등)와
  달라 D1 을 유닛 레벨에서 놓침.
- **정정** (`381cc92`): 픽스처를 `key=worker_role`(실제 capability)로 교체 + 강화 assertion
  `assertNotIn(worker_role + ":", text)` 추가. `git stash` 로 render.py 만 되돌려 재실행 →
  `'code-plan:' unexpectedly found` FAIL 확인, `stash pop` 후 재실행 green — fail-before/pass-after
  으로 가드 유효성 실증.

## 최종 검증 (test round 2, PASS all-green)

- **Unit**: `python3 -m unittest discover -s fleet/tests -v` → **48/48 green**, FAIL/ERROR 0.
  D5 canonical-comma 회귀 가드 포함 전 클래스 green.
- **D1 비재발 grep**: `--once`/`--demo --once`/`COLUMNS=200 --demo --once` 3경로에서
  `grep -nE 'code-(plan|execute|test|report):'` → **0 매치** (wide+narrow 모두).
- **라이브 재검증**: depth-2 스테이지 row `test: queued`(휴먼화, raw 아님), conductor
  `code: plan › exec › test`(무회귀), `--json` 에서 `effort=high`/`model_role="deep reviewer"`
  (value-내부 공백) tolerant 파서로 온전 전달.
- **F-9~F-13 회귀 없음**: 메타라벨 width-drop, alert tail-strip/집계, status 어휘, legend 조건부
  glyph, dead/stale `last seen` 셀 — 전부 육안 확인, round 1 대비 무변화.
- **Exit codes**: `--once`/`--json --once`/`--demo --once` 전부 0, `py_compile` 전체 clean.

## 변경 파일 (커밋별)

| 커밋 | 변경 |
|---|---|
| `ceb286c` | `tools/fleet/collectors/dispatch.py`, `tools/fleet/model.py`, `tools/fleet/render.py`, `plan/checklist.md` |
| `c9abfa1` | `tools/fleet/render.py` (F-9~F-13 폴리시) |
| `8eca886` | `tools/fleet/tests/test_dispatch.py`(+12), plan/`_internal` 산출물, `dev_logs/execute_round1.md` |
| `62db3f1` | `test_logs/test_round1.md` |
| `381cc92` | `tools/fleet/render.py`(D1 두 경로), `tools/fleet/tests/test_dispatch.py`(D2), `dev_logs/execute_round2.md` |
| `e6f51bf` | `test_logs/test_round2.md`, `_internal/stage_prompts/code-test-r2.prompt.txt` |

## 잔여/한계

- 없음. test round 2 verdict 가 "추가 remediation 라운드 불요"로 명시적으로 사이클 종결.
- proc-scan 경로(`_scan_processes`)는 구조적으로 effort/model_role 을 env 로 못 받아 parent-inherit
  fallback(`~` prefix)을 쓴다 — PRD v2 설계상 의도된 제약이며 jobs.log 경로가 1급 소스이므로 결함 아님.

## Artifact index

- Plan: `plan/plan.md`, `plan/checklist.md`
- Dev logs: `dev_logs/execute_round1.md`, `dev_logs/execute_round2.md`
- Test logs: `test_logs/test_round1.md`, `test_logs/test_round2.md`
- 본 리포트: `report.md`
- Pipeline ledger: `pipeline_summary.md`
