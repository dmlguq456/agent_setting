# code-plan 스테이지 과업 — fleet F-18 구현 plan 작성

너는 fleet F-18 구현 사이클의 **code-plan** 스테이지다 (deep maker). 코드를 정독하고 상세 구현 plan 을 작성해라. **구현은 하지 마라** — plan 문서만.

## 컨텍스트
- 워크트리: `/home/Uihyeop/agent_setting-wt/fleet-f18-attribution` (브랜치 `fleet-f18-attribution`).
- 청사진: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.6 **F-18** (2026-07-11 minor #4, within-spec).
- 대상 코드: `tools/fleet/` — 특히 `collectors/procscan.py`, `collectors/dispatch.py`, `render.py`, `model.py`, `tests/`.

## 구현 대상 2종

### F-18a — drill runner 이중 표시 dedup
같은 drill 실행이 두 row 로 뜬다:
- (i) proc-scan loop job: key=`drill`, cwd=`/tmp/drill-<case>-XXXX/...`
- (ii) lib-runner registry row: slug=`drill-<harness>-<case>-<ts>-<pid>` (매 실행 고유)

slug 불일치로 기존 dedup(동일 slug skip)이 안 걸린다. **해소**: case명 + cwd 상관으로 매칭해 registry row 를 정본으로 1행 병합, proc 는 liveness/pid 소스로 흡수. 매칭 = registry slug 에서 case명 추출 + proc cwd 의 `/tmp/drill-<case>-` 상관.
- 선례: `model.py` 의 `project_of` drill 정규식 `drill-(.+)-[^-/]+$` 가 case 추출 선례. F-15 의 proc↔registry 정합과 같은 계열 — 매칭 키만 drill 명명으로 확장.

### F-18b — mem-워커 오귀속
distiller/curator(`claude -p`, env `MEM_DISTILL=1`)·F-17 refresher(env `FLEET_TITLE_REFRESH=1`) 세션이 부모 cwd·env 상속으로:
- (i) 부모 세션 자식 `↳` 로 떴다 수분 내 사라짐
- (ii) drill fixture cwd 면 `drill:<case>` 그룹으로 오귀속

**해소**: procscan 이 `/proc/<pid>/environ` 에서 이 마커(`MEM_DISTILL`, `FLEET_TITLE_REFRESH`)를 읽어(같은 user — `collectors/dispatch.py` 의 AGENT_DISPATCH_* environ 읽기 선례 재사용) 세션에 `mem_worker` 태그 → 기본 표시에서 제외(pulse 카운트·그룹 row 미포함), 그룹/legend 에 `🧠N` 요약만, `a` 토글 시 dim row(라벨 `mem`) 노출.
- 오귀속 차단이 1차 목적 — 태깅 실패(권한·race) 시 현행 표시 유지(무해 degrade).

## 불변식 (반드시 준수)
- collector 필드·`--json` **additive only** (drill g9/g10 assert 가 `fleet.collectors.dispatch` 를 파이썬 임포트 — 기존 필드 의미 불변).
- registry **무write**.
- `render.py` 모듈 레벨 `curses.A_*` 금지 (`_A_BOLD`/`_A_DIM` 폴백 사용).
- Windows no-curses import 경로 회귀 없음 — procscan 의 nt 분기(`_scan_disk` 경로)에도 태깅 적용 여부 판단해 명시.
- F-14~F-17 계약 유지.

## 산출물
- plan 파일: `.agent_reports/plans/2026-07-11_fleet-f18-attribution/plan.md` (기획팀 표준 형식 — 단계별 구현, 대상 파일·함수·정확한 변경, 검증 계획 포함).
- 각 단계는 실행 스테이지가 그대로 구현할 수 있을 만큼 구체적으로 (파일·함수·정규식·자료구조).
- environ 읽기·mem_worker 태그 전파 경로(procscan→model→render), F-18a 병합 지점(어느 collector/model 함수에서 proc↔registry 병합하는지)을 명확히.

plan.md 를 작성하고, 완료 시 작성한 파일 경로와 핵심 설계 결정 3~5줄 요약을 반환해라.
