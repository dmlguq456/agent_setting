# F-18 검증 보고 (code-test)

- **verdict**: **PASS**
- **범위**: F-18a(drill 이중 표시 dedup) · F-18b(mem-워커 오귀속 차단)
- **원칙**: read-only 검증(소스 무수정). plan §"검증 계획" V1~V5 전부 실행.
- **결과 요약**: 신규 14 + 회귀 125 = **139/139 green**, 스모크 3종 exit 0, 임포트 표면 무결, 불변식 6종 전부 준수.

---

## (a) tests 전체 green

| 대상 | 명령 | green/total |
|---|---|---|
| 신규 F-18 | `python3 -m unittest fleet.tests.test_f18_attribution -v` | **14/14** |
| 회귀 (F-14~F-17·dispatch) | `python3 -m unittest fleet.tests.test_f15_rows fleet.tests.test_f17_title_refresh fleet.tests.test_dispatch fleet.tests.test_f14_title -v` | **125/125** |
| 전체 discovery | `python3 -m unittest discover -s fleet/tests -p 'test_*.py'` | **139/139** |

- 신규 14 = `ProcscanTaggingTest`(4: MEM_DISTILL/FLEET_TITLE_REFRESH→True, 무마커/권한실패→False degrade) · `RenderMemExclusionTest`(3: 기본 제외+🧠 legend / `a`-토글 mem row / mem-only fold+전역 total) · `DrillCaseExtractionTest`(4: slug·cwd 추출·비-drill None) · `DrillReconcileTest`(3: 매칭 병합+liveness/pid 흡수 / case 미스매치 2행 유지 / cwd 가드).
- discovery 139 = 회귀 125 + 신규 14. `tools/fleet/tests` 하위 다른 테스트 파일 없음(test_dispatch/f14/f15/f17/f18 전부 포함).

## (b) 라이브 스모크

| 명령 | 결과 |
|---|---|
| `python3 -m fleet.fleet --once` | exit 0, 크래시 없음. mem-워커·drill 미노출(현재 라이브 세션에 mem-워커/drill 실행 없음 — 정상) |
| `python3 -m fleet.fleet --once --all` | exit 0, 크래시 없음. a-토글 동치 경로 정상 렌더 |
| `python3 -m fleet.fleet --json \| ...('mem_worker' in sessions[0])` | **`mem_worker key: True`** — additive 노출 확인 |

- **F-18a/F-18b 라이브 관찰 불가 → mock fixture 단위검증으로 충족**: 현재 워크트리에 살아있는 drill runner·mem-distiller 프로세스가 없어 병합/제외가 라이브 board 에 나타나지 않음. plan 이 명시한 대로 `test_f18_attribution` 의 mock registry/environ fixture 가 이 경로를 단위검증(병합 3케이스·태깅 4케이스·render 제외 3케이스 전부 PASS)하므로 계약 충족. 🧠 legend 도 살아있는 mem-워커가 있을 때만 뜨는 조건부라 미출현이 정상.

## (c) drill 임포트 표면 회귀 없음

```
python3 -c "import fleet.collectors.dispatch as d; print(d._drill_case_from_slug, d._reconcile_drill_rows, d.collect)"
→ <function _drill_case_from_slug ...> <function _reconcile_drill_rows ...> <function collect ...>
```
- 신규 심볼 임포트 정상, 기존 `collect` 시그니처 불변 — drill g9/g10/g_stage_dispatch assert 의 `fleet.collectors.dispatch` 파이썬 임포트 무결.

## (d) no-curses import OK

```
python3 -c "import fleet.render; print('render import (no curses tty) OK')" → OK
```
- tty/curses 초기화 없이 render 모듈 임포트 성공.

---

## 불변식 확인 (전부 준수)

| 불변식 | 판정 | 근거 |
|---|---|---|
| DispatchJob 필드 additive only | ✅ | `git diff model.py` — DispatchJob 무변경. F-18a 는 기존 `pid`/`elapsed_min`/`liveness` 재사용 |
| Session 신규 필드 = mem_worker 1개 | ✅ | model.py:148 `mem_worker: bool = False` 만 추가, `to_dict()`(asdict) 자동 노출 |
| `--json` additive only | ✅ | (b) `mem_worker key: True`, 기존 key 불변 |
| registry(jobs.log) 무write | ✅ | `_reconcile_drill_rows` 는 메모리 객체(`r.pid`/`r.liveness`)만 mutate, 파일 write 없음 |
| render.py 모듈 레벨 `curses.A_*` 신규 참조 없음 | ✅ | `grep -nE '^[a-zA-Z_].*curses\.A_' render.py` → 없음. 모든 `curses.A_*` 는 `_init_colors()` 내부(line 156~281). 신규 mem 스타일은 전부 등록된 `"dim"` 재사용 |
| nt `_scan_disk` mem_worker default False | ✅ | procscan.py:162 주석 + `Session(...)` 에 mem_worker 미전달 → dataclass default False. environ 판독 불가 경로 무해 degrade |
| F-14~F-17 계약 유지 | ✅ | 회귀 125/125 PASS. mem_worker 는 추가 필터로만 개입, 기존 usage/title/분사/detached row 로직 불변 |

---

## 발견된 결함

**없음.** 구현이 plan.md 정본과 execute_summary 를 정확히 반영. 모든 검증 항목 green, 소스 수정 불필요.

- 참고(결함 아님): 라이브 board 에 mem-워커/drill 병합 시각 증거는 이번 세션에 해당 프로세스가 없어 관찰 불가 — mock fixture 로 계약 검증됨. 실운영에서 distiller·drill 동시 실행 시 육안 확인 여지는 남음(플랜 §리스크 "동명 case 동시 2런" 항목과 동일한 후속 관찰 대상).
