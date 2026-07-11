# F-18 구현 실행 요약 (code-execute)

plan.md 정본 그대로 구현 완료 — Phase 1(F-18b) → Phase 2(F-18a) 순서.

## 변경 파일

1. **`tools/fleet/model.py`** — `Session.mem_worker: bool = False` 1필드 추가 (line 148, `branch` 뒤, additive). `to_dict()` 자동 노출.

2. **`tools/fleet/collectors/procscan.py`**
   - `scan()`(line 213~231): 기존 `is_child` 판독 지점에서 `env = read_environ(pid)` 로 1회 read 재사용, `mem_worker = env.get("MEM_DISTILL") == "1" or env.get("FLEET_TITLE_REFRESH") == "1"` 계산 후 `Session(...)` 에 `mem_worker=mem_worker` 추가.
   - `_scan_disk()`(nt 경로, line 162~163): environ 판독 불가 주석 추가, `Session(...)` 에 `mem_worker` 미전달 → default `False` 유지.

3. **`tools/fleet/collectors/dispatch.py`**
   - line 45~62: `_DRILL_SLUG_RE`/`_DRILL_CWD_COMP_RE` 정규식 + `_drill_case_from_slug`/`_drill_case_from_cwd` 헬퍼 신규.
   - `collect()` 앞(line ~840): `_reconcile_drill_rows(jobs)` 신규 헬퍼 — registry row(정본) + proc drill loop job 매칭 시 1행 병합, proc 의 pid/liveness 흡수.
   - `collect()` 본체: liveness 계산 루프 직후, F-15c(a) 재도출 앞에 `jobs = _reconcile_drill_rows(jobs)` 1줄 호출 삽입.

4. **`tools/fleet/render.py`**
   - `_build_lines()` 진입부: `n_mem_total`/`mem_by_group` 원본 세션 기준 집계 후, `sessions` 필터에 `not (mem_worker and not _SHOW_ALL)` 조건 추가(is_child 필터 확장).
   - `_live_h`(usage 행), `_real`(pulse census): `not getattr(s, "mem_worker", False)` 조건 추가.
   - 그룹 header 조립부: 🚧 worktree badge 뒤에 `🧠 N` group badge 삽입(`"dim"` 스타일 재사용).
   - legend 조립부: `n_mem_total` 이 있으면 `🧠 %d mem` 전역 total 항목 추가.
   - `_group_key_session` 바로 뒤에 `_mem_row(s, layout)` 헬퍼 신규(전 스타일 `"dim"` 1-line).
   - 세션 emit 루프(`_sort_group_sessions(shown)`) 초입에 mem_worker 분기 — `_mem_row` 호출 후 `continue`.

5. **`tools/fleet/tests/test_f18_attribution.py`** — 신규. `ProcscanTaggingTest`(마커 태깅 4케이스) · `RenderMemExclusionTest`(기본 제외/legend/토글/mem-only fold 3케이스) · `DrillCaseExtractionTest`(slug/cwd 추출 4케이스) · `DrillReconcileTest`(병합/미스매치/cwd가드 3케이스) = 총 14 테스트, 전부 PASS.

## Sanity 검증 결과

- `python3 -c "import fleet.collectors.dispatch, fleet.collectors.procscan, fleet.model, fleet.render"` → OK.
- `python3 -m fleet.fleet --json >/dev/null` → 크래시 없음, exit 0. sessions[0] 에 `mem_worker` key additive 확인.
- `python3 -m unittest fleet.tests.test_f18_attribution -v` → 14/14 PASS.
- `python3 -m unittest fleet.tests.test_f15_rows fleet.tests.test_f17_title_refresh fleet.tests.test_dispatch fleet.tests.test_f14_title -v` → 125/125 PASS (F-14~F-17 계약 회귀 없음).
- `python3 -c "import fleet.collectors.dispatch as d; print(d._drill_case_from_slug, d._reconcile_drill_rows, d.collect)"` → 심볼 임포트 정상(drill g9/g10/g_stage_dispatch assert 무결성).
- `python3 -m fleet.fleet --once` / `--once --all` → 둘 다 크래시 없음, 모듈 레벨 `curses.A_*` 신규 참조 없음(`grep curses.A_ render.py` 결과 전부 기존 `_init_colors()` 함수 내부).

## 불변식 체크리스트 확인

- DispatchJob 신규 필드 없음(F-18a 는 기존 pid/liveness 재사용) — 확인.
- Session 신규 필드는 mem_worker 1개뿐 — 확인.
- `--json` additive only, registry(jobs.log) 무write(`_reconcile_drill_rows` 는 메모리 객체만 mutate) — 확인.
- render.py 모듈 레벨 `curses.A_*` 신규 참조 없음, `"dim"` 재사용 — 확인.
- `_scan_disk`(nt) `mem_worker` default False 유지, import 경로 회귀 없음 — 확인.
- F-14~F-17 회귀 테스트 125/125 PASS — 확인.
- drill 임포트 심볼(`_drill_case_from_slug`, `_reconcile_drill_rows`, `collect`) 시그니처 유지 — 확인.

커밋은 하지 않음 (code-report 스테이지에서 처리).
