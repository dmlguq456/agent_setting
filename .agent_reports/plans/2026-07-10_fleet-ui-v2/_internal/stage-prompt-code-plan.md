역할: `code-plan` sub-skill을 Skill 도구로 호출해 아래 작업의 구현 plan을 작성한다.

## 작업
fleet UI 개선 — agent-fleet-dashboard PRD v2 §4.5(SD-F1~F4 stage-dispatch 관제 parity)·§4.6(F-9~F-13 UI 가독성) 구현.

## 필수 입력 (경로만 — 본문은 직접 Read)
- spec (v2): `.agent_reports/spec/agent-fleet-dashboard/prd.md` — §4.5, §4.6, §Next 1~4 절 중심으로 읽는다.
- 참고 spec: `.agent_reports/spec/stage-dispatch/prd.md` — SD-3(jobs.log 스테이지 row 계약)·SD-5(스테이지 model role) 절.
- 대상 코드: `tools/fleet/collectors/dispatch.py`, `tools/fleet/render.py`, `tools/fleet/model.py`, `tools/fleet/tests/`.

## 이번 사이클 범위 (PRD §Next 1~4, 순서대로 plan에 반영)
1. **SD-F4 pipe tolerant 파싱** (`collectors/dispatch.py`) — jobs.log pipe key=value 구분자를 공백/콤마 혼용 tolerant로 파싱. 콤마가 canonical(OPERATIONS §5.10 하드 계약)이므로 canonical 파싱은 유지하고 공백 구분 행에 대한 tolerance를 *추가*한다. 미지 key는 무시. 기존 테스트(`tests/test_dispatch.py`) 회귀 유지 + 2026-07-09 실측 공백-구분 행 fixture를 신규 테스트로 추가.
2. **SD-F1~F3 스테이지 row 렌더** (`render.py`):
   - SD-F1: `worker_role=code-plan/code-execute/code-test/code-report`(+`:phase-A` 류 접미) depth-2 row를 raw role 문자열 대신 단계명(`plan`/`exec`/`test`/`report`, 기존 `_PIPE_STAGES` breadcrumb 어휘 재사용 — 신규 어휘 발명 금지)으로 렌더. 접미는 dim으로 뒤에 표시. 현행 14자 중간잘림이 스테이지 워커에는 적용되지 않게.
   - SD-F2: depth-1 job이 `owner=autopilot-code` 스테이지 자식(depth-2, worker_role=code-*)을 가지면 conductor로 판정. conductor row의 stage breadcrumb(`code: plan › exec › test`) 하이라이트는 활성(live) 스테이지 자식과 일치해야 함(자식 실측 우선, `live_stage()` 산출물 유도는 fallback).
   - SD-F3: dispatch wrapper가 pipe에 싣는 `model_role=`/`model=`/`effort=`를 스테이지 row가 1급 표시. pipe 값 부재 시에만 parent effort 상속 표시로 fallback(dim + 상속 표기).
3. **F-9~F-13 가독성** (`render.py`):
   - F-9: 메타라벨 재배분 — role은 SD-F1 단계명 매핑 우선, 매핑 밖 role은 중간잘림 대신 뒤에서 자름(head 보존). drill 케이스 하드코딩 축약 맵을 `g\d+` 접두 추출 같은 일반 규칙으로 대체. 라벨 성분 우선순위: 폭 부족 시 `qa → intensity → role` 순으로 드롭(mode는 유지). `~` 유도값 접두는 유지 + legend에 1회 설명.
   - F-10: alert 행도 dispatch 행과 같은 compact 이름 경로 재사용. loop 잡의 `<case>-<ts>-<pid>` 꼬리 strip. 같은 종류 alert 다수면 개수 집계. 폭 초과는 우선순위 절단(dead > stale > ctx).
   - F-11: registry-only 잡의 raw status(`open`→`queued`, `running`→breadcrumb 미점등 트랙 기존 규칙 재사용)를 사람 어휘로. jobs.log 어휘 자체는 불변 — 표시층만.
   - F-12: `+N malformed jobs.log rows skipped`는 dim 강등. footer `w` 라벨의 stack 모드 누락 버그 수정(3-모드 전부 표기). legend는 화면에 실제 등장한 글리프만.
   - F-13: dead/stale row는 `— … — … —` 나열 대신 telemetry 셀 생략 + `last seen 2h` 1값으로 대체.
   - 적용 순서: 전부 표시층(render.py). collector 계약·모델 스키마는 SD-F4 외 불변.

## plan에 반드시 포함
- spec-significance verdict: `within-spec` (이미 PRD v2로 청사진 확정, 본 사이클은 구현).
- 검증 계획(code-test 단계 항목)에 다음을 명시할 것: 구현 후 `python3 tools/fleet/fleet.py --once` 및 `--json`으로 (a) 이 fleet-ui-v2 파이프 자체의 depth-2 스테이지 row(code-plan/code-execute/code-test/code-report)가 단계명 라벨로 뜨는지 (b) conductor row 집계가 맞는지 (c) 기존 렌더 회귀가 없는지 확인 — 이 파이프의 depth-2 row 자체가 라이브 검증 fixture다.
- 산출물 경로는 이미 `.agent_reports/plans/2026-07-10_fleet-ui-v2/` (T1: plan/, T2: dev_logs/·test_logs/, T3: _internal/)로 고정되어 있으니 그 경로에 작성한다.

## 완료 후
plan/plan.md, plan/plan_ko.md, plan/checklist.md 경로만 stdout에 요약 출력(대화 본문 인용 금지, 파일 경로와 한 줄 verdict만).
