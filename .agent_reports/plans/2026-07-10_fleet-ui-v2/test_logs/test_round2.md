# Test round 2 — fleet UI v2 (SD-F1~F4, F-9~F-13) — execute-r2 원격검증

Stage: `code-test` (품질관리팀 test mode, graduated verification) · QA standard · depth 2 · branch `fleet-ui-v2`
Verified against execute round 2 remediation (commit `381cc92`, D1+D2 fixed & committed).
Inputs: `test_logs/test_round1.md`, `dev_logs/execute_round2.md`, `plan/plan.md`.

## Overall verdict: **PASS (all-green)** — round-1 결함 D1/D2 모두 해소, 무회귀 확인, 신규 결함 없음

execute-r2 가 D1(raw `code-*` stage-prefix 누출) + D2(픽스처 갭) 을 고쳤고, 본 라운드에서
전 항목 (a)~(e) 를 fixed 트리에서 재검증했다. 라이브·demo·wide·narrow 모든 렌더 경로에서
raw `code-*` 누출은 0 건, depth-2 스테이지 row 는 휴먼 스테이지명(`test:`/`exec:`/`plan:`/`report:`)
으로 렌더, conductor breadcrumd(`code: plan › exec › test`) 무회귀. **추가 remediation 라운드 불요.**

---

## Mandatory 항목별 판정

### (a) FULL tests green: **PASS**
```
cd tools && python3 -m unittest discover -s fleet/tests -v   → Ran 48 tests in 0.148s … OK
```
- **48/48 green** (round 1 과 동일 카운트 — execute-r2 는 assertion 강화 1건 + 픽스처 realism 만
  바꿔 카운트 불변). FAIL/ERROR 0.
- 신규/강화 클래스 전부 green: `TolerantPipeParsingTest`(5), `StageWorkerRenderTest`(2:
  stage-labels + g-case prefix), `ConductorBreadcrumbTest`, `AlertHumanizeTest`,
  `DepthTwoRegistryMetadataTest`(D5 canonical-comma 무회귀).

### (b) LIVE fixture re-verify — depth-2 스테이지 row 휴먼 스테이지명: **PASS**
```
python3 tools/fleet/fleet.py --once           → exit 0
python3 tools/fleet/fleet.py --json --once     → exit 0
```
이 파이프 자신의 depth-2 스테이지 세션(`fleet-ui-v2-test-r2`, key=`code-test`)이 라이브 fixture.

**증거 (narrow 2-line card, `--once`)**:
```
▍     ⠸ claude code fleet-ui-v2-test-… (dev·std/test/qa:~std)  fleet-ui-v2
▍   —               opus (high)            test: queued
```
- breadcrumb prefix = **`test:`** (휴먼화, `_STAGE_ROLE["code-test"]→"test"`), raw `code-test:` **아님**.
- role 태그 `test` (SD-F1), 자기 effort `opus (high)` 1급 표시(SD-F3), 상태 `queued`(F-11 open→queued).

**증거 (wide, `COLUMNS=200 --demo --once`)**:
```
▍     ⠹ claude code fle… (dev·std/test/qa:~std) fleet-ui-v2   opus (high)   test: queued   —
```
- wide 경로(`_dispatch_row`)도 `test: queued`. execute-r2 가 고친 두 번째 누출 지점
  (`_dispatch_row_2line`, narrow)과 함께 양쪽 경로 클린.

**`--json --once` 스키마 필드 (SD-F3 온전 전달)**:
```
fleet-ui-v2-test-r2 | key=code-test | depth=2 | worker_role=code-test | effort=high | model_role="deep reviewer"
fleet-ui-v2         | key=code      | depth=1 | worker_role=capability-owner | effort=medium | model_role="-"
```
- `model_role="deep reviewer"`(value-내부 공백)가 tolerant 파서로 안 깨지고 복원(SD-F4/R2 실증).

### (c) Conductor row 집계 무회귀: **PASS**
```
▍ ↳ ⠸ claude code   fleet-ui-v2 (dev·std/owner/qa:~std)  fleet-ui-v2
▍   —               opus (medium)          code: plan › exec › test
```
- depth-1 conductor(key=`code`, `_STAGE_ROLE` 밖 → `_stage_role_label`=(None,"") → raw-key fallback
  `"code"`)가 `code: plan › exec › test` breadcrumb 그대로 렌더. 활성 자식(code-test, working)의
  `test` 스테이지 하이라이트(SD-F2). round 1 대비 무회귀, raw code-* 누출 없음.
- `--demo` 의 다른 conductor 들(`stage-dispatch-phase2`, `demo-feat-x`, `demo-review`, `demo-spec`)도
  각각 `code:`/`review:`/`spec:` track breadcrumb 정상.

### (d) D1 비재발 — raw `code-(plan|execute|test|report):` grep: **PASS (ZERO 매치)**
```
python3 tools/fleet/fleet.py --once       | grep -nE 'code-(plan|execute|test|report):'  → 0 매치 (exit 1)
python3 tools/fleet/fleet.py --demo --once | grep -nE 'code-(plan|execute|test|report):'  → 0 매치 (exit 1)
COLUMNS=200 fleet.py --demo --once         | grep -cE 'code-(plan|execute|test|report):'  → 0
```
- `--once`(라이브 실 fixture)·`--demo --once`(narrow)·wide 3 경로 모두 **raw code-* 누출 0**.
  D1 계통적 결함(모든 depth-2 스테이지 워커) 완전 해소.

### (e) Render 회귀 — F-9~F-13 가독성: **PASS**
```
python3 -m py_compile tools/fleet/*.py tools/fleet/**/*.py   → py_compile OK
python3 tools/fleet/fleet.py --demo --once                    → exit 0 (전체 레이아웃 육안)
```
round 1 대비 무회귀 육안 확인:
- **F-9(a~d)** dispatch 메타라벨 `(dev·std/test/qa:~std)`·`(loop/drill·q/g6/qa:~q)` head 보존
  tail-cut(`…`), drop-priority 폭 적응, g6 일반 prefix 규칙(`drill-g6-worktree`→`g6`) 동작,
  `~` derived 마커(`Opus 4.8 (~xhigh)`, `glm-5.2 (~low)`) legend 와 일관.
- **F-10** alert humanize: `alert ⚠ stale demo-orphan`(tail-strip) 정상.
- **F-11** status 어휘: `test: queued`(open→queued), `plan: done`, `spec: spec › design › dev` 휴먼화.
- **F-12(a)** `+2 malformed jobs.log rows skipped`(dim) · **(c)** legend glyph-appearance:
  `--once` 는 `○ detached · stale` 미노출, `--demo`(해당 상태 有)만 추가 등장 — 조건부 글리프 정상.
- **F-13** dead/stale/detached row 셀 처리 무변화. column header(`SESSIONS narrow · press w to cycle`),
  model cell, breadcrumb, legend 모두 intact.

### D2 가드 spot-check — 강화 assertion present: **PASS**
`tools/fleet/tests/test_dispatch.py:722`:
```python
self.assertNotIn(worker_role + ":", text)   # the exact D1 leak shape (강화됨)
self.assertNotIn(worker_role, text)          # pre-existing
```
- 픽스처가 `key=worker_role`(realistic capability, test_dispatch.py:714)로 바뀌어 라이브 shape 재현.
  execute-r2 로그의 fail-before/pass-after 회귀증명(`git stash` render.py → `'code-plan:' unexpectedly
  found` FAIL)은 커밋된 트리에서 재현 가능한 유효 가드로 확인.

---

## 결함 요약

| # | 심각도 | 내용 |
|---|---|---|
| — | — | **신규 결함 없음.** round-1 D1(render.py raw prefix)·D2(test gap) 모두 해소·무회귀. |

## 검증 명령/결과 요약
```
cd tools && python3 -m unittest discover -s fleet/tests -v   # Ran 48 tests … OK
python3 tools/fleet/fleet.py --once                          # exit 0, stage row "test: queued", conductor "code: plan › exec › test"
python3 tools/fleet/fleet.py --json --once                   # exit 0, effort=high/model_role="deep reviewer" 전달
python3 tools/fleet/fleet.py --demo --once                   # exit 0, F-9~F-13 무회귀, 조건부 글리프 등장
python3 tools/fleet/fleet.py --once|--demo --once | grep -E 'code-(plan|execute|test|report):'  # 0 매치 (D1 비재발)
COLUMNS=200 python3 tools/fleet/fleet.py --demo --once        # wide 경로도 raw 누출 0
python3 -m py_compile tools/fleet/*.py tools/fleet/**/*.py    # compile OK
```

## Artifact
- 본 리포트: `.agent_reports/plans/2026-07-10_fleet-ui-v2/test_logs/test_round2.md`
