# TEST_VERDICT — F-15 분사 row 재설계 + F-16 표시명 짧게

- **사이클**: 2026-07-10 fleet-f15-dispatch-rows
- **impl 커밋**: e3bddfd (branch `fleet-f15-dispatch-rows`)
- **검증자**: code-test worker (depth-2, deep reviewer)
- **검증 환경**: Python 3.8.10, no-pytest(unittest 사용), live fleet.py 실측 가능
- **날짜**: 2026-07-10

## 총평: **GREEN-with-notes** ✅

구현이 graduated verification(syntax→import→smoke→functional→integration + 런타임 관찰)을 통과했다. spec §4.6 F-15·F-16 의 실질 요구(탈가로화·옵션 1급 정렬 컬럼·done-folding·queued 오라벨 해소·title cap)가 **라이브로 실증**된다. 문서화된 execute 편차 2건(R8 arrow scope-out, 옵션 토큰 `_mq_tag` 재사용)은 **spec 요구를 미달로 남기지 않는 표시 토큰 수준의 cosmetic** 이라 ship 가능. 차단 결함 0. 편차 2건은 후속 토글 후보로만 기록.

---

## 체크리스트 결과 (실제 명령 + 출력)

### (a) tests green — **PASS**
```
$ python3 -m unittest discover -s tools/fleet/tests -v
Ran 88 tests in 0.219s
OK
```
- 88 tests 전량 GREEN (pytest 미설치 → unittest discover 등가 실행).
- 신규 `test_f15_rows.py` 22건(slug-stem·dedup-key·queued-liveness·folding·done-marker·title-cap·wide-row·layout-cutoff·live-stage-induction) 포함.
- 기존 `test_f14_title.py` 16건·`test_dispatch.py`·`test_f14_title` 회귀 없음. (repo-root 단독 `unittest test_f14_title` 는 import-path 미스로 error 나지만, `tools/fleet/tests` cwd + discover 양쪽서 GREEN — cwd 아티팩트일 뿐 실패 아님.)

### (b) live fleet.py 실측 — **PASS** (현재 fleet 상태가 이 사이클 자신을 그대로 렌더 = 최적 실증)
```
$ python3 tools/fleet/fleet.py --once            # 기본폭(narrow)
$ python3 tools/fleet/fleet.py --json | python3 -m json.tool   # JSON VALID
$ COLUMNS=160/100/60 python3 tools/fleet/fleet.py --once        # wide/narrow/stack 강제
```
- **JSON**: valid, top-keys `[sessions, jobs, summary]`. dispatch job 26필드 전량 존재(additive only, 필드 삭제·개명 0).
- **탈가로화 + 옵션 컬럼(wide, COLUMNS=160)**: conductor `fleet-f15` name-zone = slug 단독(괄호 옵션 태그 **부재**), 옵션은 model↔breadcrumb 사이 정렬 컬럼 `dev·std/owner/qa:~std`, breadcrumb `code: plan✓ › exec✓ › test`. 자식 `test fleet-f15-code-test` = name-zone 단계라벨(`test`)+slug, breadcrumb 슬롯 = `running`(micro-status, **부모 breadcrumb 복제 없음**). → P0-1 충족.
- **narrow(COLUMNS=100) 2-line 카드**: L1=정체성만, L2=경과+model+옵션+breadcrumb. 옵션이 이름 뒤로 가로 늘어지지 않고 L2 정렬 컬럼에 위치. → F-15a 충족.
- **stack(COLUMNS=60) 3-line**: L1 정체성 / L2 model+옵션 / L3 breadcrumb(자식은 micro-status). → 정상.
- **done 스테이지 자식 접힘**: jobs.log 상 `fleet-f15-code-plan`·`fleet-f15-code-execute` = done → breadcrumb `plan✓ exec✓` 로 흡수(자식 row 없음), `fleet-f15-code-test`(open+working) 만 자기 row. 3자식 중 working 1건만 표시. → F-15b 충족.
- **queued 오라벨 해소**: jobs.log 에 이 사이클 6엔트리(`open fleet-f15` conductor + plan/execute 각 open→done + `open fleet-f15-code-test`). conductor·test 는 registry `open` row 이나 transcript 활동 有 → **working(⠏/⠸)** 렌더, static `queued`/dead 아님. 유닛 `test_open_no_transcript_small_elapsed_is_queued`/`_large_elapsed_is_dead`/`_with_transcript_activity_is_working` 3분기 검증. → F-15c 충족.
- **F-16 title 클립**: session `Stage-dispatch Phase 2 작업 시작`(full 28 chars, `--json` 보존) → name-zone `Stage-dispatch Phase 2 …` tail-cut(head 보존, `_TITLE_MAX=24`). → F-16 충족.

### (c) drill g9/g10 — **정적 계약 확인 PASS** (full run 은 fixture 필요로 미실행)
- 위치: `~/.claude/loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/assert.sh`, `g10_claude_opencode_depth2_start/assert.sh`.
- 두 assert 모두 `fleet.collectors.dispatch.collect(jobs_path=)` 를 import 해 job 필드(`slug·key·mode·depth·harness·worker_role·capability_owner·parent_sid·parent_slug·is_child·status`) + jobs.log **6-field TSV / status∈{open,running} / comma-sep key=value pipe** 계약을 assert.
- **실행 불가 사유**: 두 케이스 모두 full autopilot-code dispatch cycle fixture(`$WORK/repo` + 실제 워커 기동·transcript)를 요구 → 독립 headless 환경서 재현 불가(depth-3 금지 계약상 워커 분사도 불가).
- **대체 검증(실행함)**: (1) impl diff 가 DispatchJob 26필드 전량 보존(삭제·개명 0), (2) `_scan_jobs_log(path, seen_slugs, seen_keys=None)` = **additive 시그니처**(기본값으로 하위호환), (3) `len(fields) != 6` 6-field 계약 line 747/811 불변, (4) `collect()`·`--json` 스키마 additive only. → g9/g10 이 의존하는 표면 전부 무접촉 → **GREEN 유지 판정**. 편집 세션 마무리에 `~/.claude/loops/drill/run.sh` 1회 발사는 main orchestrator 몫으로 권장.

### (d) Windows no-curses import path — **PASS**
```
$ python3 -c "import sys,types; sys.modules['curses']=types.ModuleType('curses'); \
  sys.path.insert(0,'tools'); import fleet.render as r"
IMPORT OK — no AttributeError; _A_BOLD=0 _A_DIM=0
```
- bare `curses`(A_* 무속성) 모듈 주입해도 module-level AttributeError 없음. `curses.A_*` 직접참조는 전부 `_init_colors`(함수 내부, curses 초기화 성공 시만) → 모듈로드 경로 클린. `_A_BOLD`/`_A_DIM` 폴백 정상.

---

## 편차 평가 (execute 문서화 2건)

### 편차 1 — R8 `↳` arrow redefinition scope-out: **ACCEPTABLE**
- 계획 P1-4/R8 은 top-level registry peer 는 무-arrow, `↳` 는 depth-2 nested 전용으로 재정의 예정이었으나 execute 가 scope-out.
- 라이브 관찰: 현재 `↳` = "session 의 dispatch 자식", 더 깊은 indent = depth-2 nested. 위계가 육안으로 명확히 읽힘(conductor `↳ fleet-f15`, 그 아래 무-arrow deep-indent `test fleet-f15-code-test`).
- **판정**: 원 불평(가로 sprawl·중복)의 근본 원인이 아니며, arrow 의미 재정의는 nice-to-have 정련. spec §4.6 요구 미달 없음. loops row 회귀도 없음(drill 표기 무영향).

### 편차 2 — 옵션 토큰 `_mq_tag`/`_dispatch_profile` 재사용: **ACCEPTABLE**
- 계획 R2/P2-13 은 통일 토큰 `mode·qa:<lvl>·int:<lvl>` 신설을 명시했으나, execute 는 기존 `dev·std/owner/qa:~std`(= `mode·intensity/role/qa:level`) 포맷 재사용.
- 이 포맷은 (a) conductor·자식 **양쪽 동일 컬럼 정렬**로 렌더(`dev·std/owner/…` vs `dev·std/test/…`), (b) role(owner/test) 정보를 **추가로** 담아 planned 포맷보다 오히려 정보 풍부, (c) `~` = derived/inherited qa 표기.
- spec §4.6 실질 요구 = "옵션을 숨기지 말고 정렬된 1급 자리로(가로 늘어짐 제거)". 이 요구는 **충족**(옵션이 model 뒤 고정 컬럼/L2 에 정렬, 성분 드롭 없음). P2-13 의 "uniform token·intensity 비대칭 제거" 는 plan 수준 정련 wording 이지 spec 요구 아님.
- **판정**: spec 요구 미달 아님. 단 plan 설계와 시각 토큰이 달라 후속 "uniform option token" 토글 후보로 기록.

**종합**: 두 편차 모두 spec intent 내 수용 가능, 미달 spec 요구 **0건**.

---

## 불변식 회귀 점검 — 전부 PASS

| 불변식 | 결과 | 근거 |
|---|---|---|
| collector 공개 필드 계약(additive only) | ✅ | DispatchJob 26필드 전량 보존, 삭제·개명 0. `--json` 스키마 additive. |
| jobs.log 6-field TSV / status(open/running) / key=value pipe | ✅ | `len(fields)!=6` line 747/811 불변, `_scan_jobs_log` additive 시그니처. |
| jobs.log·statusline·registry write 0 | ✅ | e3bddfd diff 에 해당 경로 부재; 검증 중 실행 후 `git status` clean(stray write 0). |
| render.py 모듈레벨 `curses.A_*` 직접참조 금지 | ✅ | (d) no-curses import 무크래시, A_* 는 `_init_colors` 내부만. |
| F-14 불변식(Session.slug/title·ai_title·alert 무접촉) | ✅ | diff 는 title clip 예산(`min(_NAME2_MAX,_TITLE_MAX)`)만 변경, slug/title/tail_ai 로직 무접촉. test_f14 16건 GREEN. |
| dedup 키 정규화 = 표시/매칭 로직(계약 변경 아님) | ✅ | `_slug_stem`/`(_norm_cwd,stem)` 은 매칭 헬퍼, `DispatchJob.slug` 값·의미 무변경. |
| 색 규율·새 hue 축 금지(옵션·queued glyph dim) | ✅ | 옵션 전량 dim 컬럼, queued glyph `◦` dim(신규 hue 없음). |

---

## 발견 결함

**차단(RED) 결함: 없음.**

경미(비차단, 후속 후보):
1. **[low] 옵션 토큰 포맷이 plan P2-13 uniform-token 설계와 상이** (`dev·std/owner/qa:~std` vs planned `dev·qa:std·int:std`). spec 미달 아님(편차 2 참조). *제안*: 후속 사이클서 uniform token 토글 도입 시 default-elision(ask-4)과 함께 재검토.
2. **[info] drill g9/g10 full run 미실행**(fixture 필요). 정적 계약 검증으로 GREEN 유지 판정했으나, 지침 게이트 완결을 위해 main orchestrator 가 `~/.claude/loops/drill/run.sh` 1회 발사 권장.

---

## 검증 명령 요약
```
python3 -m unittest discover -s tools/fleet/tests -v          # 88 GREEN
python3 tools/fleet/fleet.py --once                            # narrow 실측
python3 tools/fleet/fleet.py --json | python3 -m json.tool     # JSON VALID, 26필드 additive
COLUMNS=160/100/60 python3 tools/fleet/fleet.py --once         # wide/narrow/stack 3-layout
python3 -c "...bare curses inject...; import fleet.render"     # no-curses import OK
git status --short                                             # clean (write 0)
```
