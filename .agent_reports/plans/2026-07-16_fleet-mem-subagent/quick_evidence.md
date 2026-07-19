# fleet-mem-subagent — quick evidence

작업 트리: `/home/Uihyeop/agent_setting-wt/fleet-mem-subagent` (branch `fleet-mem-subagent`, origin/main 기준)
spec-significance: SPEC-SIGNIFICANT (F-19/F-29 표시 계약 변경) — 사용자 명시 이연, PRD는 수정하지 않음 (spec-read gate: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.7 F-19/F-29, §4.9 확인 완료).
배경: 두-평면 실험(`fleet-two-plane-demo` HEAD `2fb4bda1`, `tools/fleet/two_plane.py`)은 폐기. 채택분 2건(서브에이전트 가로 스트립·mem 레포별 카드)만 그 구현을 참고해 기존 보드에 이식했고, ctx 게이지 폭 조정과 model 컬럼 통합은 사용자의 별도 직접 요청(두-평면과 무관)이다.

**이어달리기 메모(재시도 계보)**: 1~3번(서브에이전트·메모리 레포별·ctx 게이지)은 이 브랜치의 선행 시도(`fleet-mem-subagent`, prompt 갱신으로 취소)가 이미 구현·커밋(`c316fc3e`)했다 — 그 커밋의 3-줄 handoff와 §1~3 본문은 원 저자 것 그대로 보존한다. 이 문서의 나머지(§4, 최종 테스트/캡처/커밋)는 갱신된 과제(4번 model 컬럼 통합 추가)를 이어받은 재시도가 작성했다.

## 1. 서브에이전트 (F-29)

- **버그 수정**: `tools/fleet/collectors/claude.py:197` — `_tail_subagents`가 `tool_use.name == "Task"`만 매칭해 현행 런타임("Agent")에서 항상 0건이던 것을 `name in ("Task", "Agent")`로 수정. 구 transcript("Task") 호환 유지.
- **표시 교체**: `render.py`의 `_subagent_row`(1행/서브에이전트, `├⚡`/`└⚡`)를 `_subagent_strip`(세션당 1행, `⚡ type ● elapsed · type ✓ elapsed …`)로 교체. 활성=normal weight, 완료=dim(기존 `a` 토글 계약 유지). 호출부 2곳(그룹 뷰 세션 루프, 과정 뷰 active-node pid-join) 모두 갱신.
- **배지 제거**: 세션 이름 뒤 `⚡N` suffix 배지(`_session_row`) 제거. legend 항목도 `⚡N sub-agents` → `⚡ sub-agent`로 갱신(스트립 자체가 인라인 카운트를 이미 보여줌).
- **들여쓰기**: `_SUBAGENT_IND = "  "` — 커넥터 없는 순수 인셋, 기존 dispatch 행(`"  ↳ "`)보다 얕음(테스트로 고정).

## 2. 메모리 레포별 (F-19 확장)

- **collector**: `tools/fleet/collectors/memory.py::collect()`에 additive `by_repo` 키 추가 — 오늘 이벤트 중 `cwd`(→ `model.project_of`) 또는 `project` 필드가 있는 행만 레포별로 그룹핑, 레포당 최근순. 두 필드 모두 없으면(현행 write-events.jsonl 실제 스키마) `by_repo == {}`로 정직 생략 — 저널 writer가 필드를 얹기 전까지는 board 표시도 자동으로 무음.
- **표시**: `render.py`에 `_mem_divider`(카드 틴트 위 dim `─` 룰) + `_mem_repo_rows`(최대 2행, `🧠 HH:MM ± tier/type actor ⟵ <source title> "snippet"`, `+`=lvl_g, `−`=dim 폴백) 추가. 그룹 렌더 루프에서 loops/orphans emit 직후·바디 틴트 loop 이전에 삽입해 카드 틴트를 자연히 물려받음. 이벤트 없는 레포는 구분선까지 전부 생략(healthy-silent). `sid`가 현재 알려진 세션과 매칭될 때만 출처 세션 제목 표시, 아니면 태그 자체 생략(추측 금지).
- 기존 `today`/`recent`/`alerts` 등 반환 키·집계는 불변(additive only).

## 3. context 게이지 폭

- `render.py`의 `_wide_name_width` 내부 계산을 `_wide_slack(term_width)` 한 곳으로 추출(fixed_row/framing 공식 중복 제거)하고, 신설 `_wide_ctx_width(term_width)`가 같은 slack에서 이름 컬럼이 `_NAME_WIDE_MAX`(40) 상한에 걸린 뒤 남는 여유를 ctx 게이지로 돌림 — wide 레이아웃에서만 적용, narrow/stack 불변.
- `_session_row(ctx_width=None)` 신규 파라미터(기본값 = 레거시 `_CTX_W=24`) — wide 레이아웃 호출부(1곳)만 `_wide_ctx_width(term_width)`를 넘김. `─` 대시 폴백 경로도 동일 폭 적용.

## 4. model 컬럼 → harness 필드 통합 (사용자 확정, 재시도가 추가한 과제)

- **컬럼 폐지**: 세션·분사(dispatch) WIDE 행의 별도 model 컬럼(`_MW`)을 폐지하고 harness 필드에 괄호로 합쳤다 — `claude code (Fable 5 · xhigh)`. narrow/stack(2줄 카드, L2에 자기 model 셀)는 이번 병합 범위 밖(불변) — 해당 레이아웃은 옵션 열거 방식이 근본적으로 다르고 과제 문구도 `_HW`/`_NAME_COL`/컬럼 헤더 등 WIDE 전용 개념만 지시했다.
- **신규 헬퍼**: `render._harness_model_cell(harness, model, effort, width, hkey, dim, unknown)` — harness 텍스트는 기존 `hb_*`/`h_*`(또는 dispatch의 dim) 색 유지, 괄호 안 model은 `_model_key`(기존 `_model_cell` 패밀리색), effort는 `_eff_key`(기존 히트램프색), `" · "` 구분자는 dim. model 값이 없으면 괄호 전체 생략(정직 결손, F-3). 항상 정확히 `width` 셀로 채워지며, 폭이 빠듯하면 이름을 잘라내되(`_model_cell` 선례와 동일 관용구) **끝에 최소 1칸 여백을 항상 남겨** 이름 컬럼과 붙어버리는 충돌(`_NAME_GAP` 선례와 동형)을 막는다.
- **폭 상수**: `_HW`(=16, bare 배지 폭)는 narrow/stack·dispatch-prefix 계산용으로 그대로 두고, WIDE 전용 `_HMW`(=32, harness+model 병합 폭)를 신설. `_NAME_COL = 4 + _HMW`로 재정의하되 `_NW_S`(=28, 세션 이름 컬럼 폭)는 상수로 고정해 레거시/헤르메틱 호출부(터미널 폭 미지정)의 이름 폭을 정확히 보존했다. `_wide_slack`의 `fixed_row` 계산에서 `_MW` 항을 제거 — 통합으로 해방된 폭이 3번 항목의 ctx 게이지/이름 컬럼 slack으로 자동 흡수된다(과제 문구 "4번의 model 컬럼 통합으로 생기는 slack도 게이지가 흡수" 그대로 확인).
- **컬럼 헤더**: `_col_head` — `harness (model · effort)`로 교체, 별도 `model` 헤더 제거.
- **호출부**: `_session_row`(dead/stale은 harness 텍스트만, model/effort 생략 — F-13과 동형) · `_dispatch_row`(잡 자기 model/effort 1급, 부재 시 부모 effort `~` 접두 폴백 — SD-F3 유지, dead/stale도 동일하게 생략). 두 행 모두 `_NAME_COL`이 동일해 세션→분사 name 컬럼 시작이 계속 일치함을 전용 테스트로 고정.
- **기존 테스트 갱신 1건**: `tests/test_f26_registry.py::test_wide_row_never_exceeds_the_capped_name_zone` — harness 필드가 이제 여러 세그먼트(harness 텍스트+괄호+패딩)로 나뉘므로 고정 인덱스(`segs[4:]`) 가정이 깨져, "harness+model 블록이 정확히 `_HMW` 셀"이라는 새 불변식으로 폭을 동적으로 건너뛰도록 수정(같은 이름 컬럼 폭 불변 검증 의도는 그대로).

## 테스트

- 회귀 전체 + 신규 계약: `python3 -m unittest discover -s tools/fleet/tests -p "test_*.py"` → **604 tests, OK**(1~3번의 587 + 4번 신규 17). 미러 재동기(`rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/`) 후 재실행, `test_mirror_parity` 포함 통과.
- 신규 파일: `tools/fleet/tests/test_harness_model_merge.py`(17 tests) — `_harness_model_cell` 단위(모델 없음 패딩, model+effort 괄호, effort 없이 구분자 생략, 긴 이름 클립+여백 보장, harness 미상 폴백 문자 설정 가능, 색상이 기존 `_model_key`/`_eff_key` 재사용), 컬럼 헤더 문구, 세션 행(병합·중복 model 텍스트 없음·model 없을 때 괄호 생략·dead 행은 harness만·name 컬럼이 `_NAME_COL`에서 시작), 분사 행(자기 model/effort·부모 effort `~` 폴백·dead 행 harness만·세션 행과 동일 name 컬럼 시작), 168/200/400폭 오버플로 없음.
- 1~3번 회귀 테스트(`test_f29_subagents.py`/`test_f19_memory.py`/`test_wide_ctx_gauge.py`)는 이번 4번 변경 후에도 전부 통과 — §1~3의 계약이 4번으로 깨지지 않았음을 확인.

## 60/120/168열 캡처 diff

`COLUMNS=<w> python3 tools/fleet/fleet.py --demo --once`로 3단계 캡처: **base**(main, 4건 전무) → **task1-3**(`c316fc3e`, 1~3번만) → **task1-4**(현재, 1~4번 전부). `--demo`는 실 라이브 세션과 fixture를 병합하므로 스피너 글리프·경과 시간·실 usage API 수치는 실행마다 자연 변동 — 클록 노이즈로 마스킹 후 diff(정규식으로 `Nh Nm`류·스피너 글리프 치환; `⠿` 자체가 실제 스피너 프레임이라 일부 diff에 마스킹 잔여 노이즈가 남지만 구조적 변경이 아님을 육안 확인).
- **base → task1-3 diff**(선행 시도가 §1~3에서 이미 확인 — 이번 재시도는 그 결과를 재검증하지 않고 신뢰).
- **task1-3 → task1-4 diff**(이번 재시도가 4번을 고립 검증하기 위해 `git stash`로 4번 변경만 임시 제거 후 재캡처):
  - **60열(stack)/120열(narrow)**: 구조적 diff 0건 — 스피너 글리프·`AGE>` 마스킹 잔여·실 usage 수치(±1%) 변동뿐(4번은 wide 전용이므로 무관). 120열 diff는 5줄(ctx% 1건 실 데이터 변동)뿐.
  - **168열(wide)**: 헤더가 `harness | ... | model | ...` → `harness (model · effort) | ...`로, 모든 세션·분사 행에서 별도 model 컬럼이 사라지고 harness 괄호로 흡수됨을 확인. 동시에 ctx 게이지 바 폭이 전 행에서 일관되게 확장(예: 48%→49% 실데이터 변동을 감안해도 채움폭 자체가 32열→39열급으로 확장) — 3번이 4번의 해방폭을 흡수한다는 설계 그대로. 그 외 구조적 변경 없음(행 순서·그룹·글리프 종류 불변).
  - 원본 캡처: `/tmp/fleet_task13/w{60,120,168}.txt`(task1-3) · `/tmp/fleet_task14/w{60,120,168}.txt`(task1-4) · `/tmp/fleet_task14/diff_w{60,120,168}.txt`(마스킹 diff) — 세션 임시 경로, 커밋 대상 아님.
- **사전 존재 오버플로(4번과 무관, 회귀 아님)**: `lab-project/demo-lab-conductor`(harness 미상 route 컨덕터) 행이 168열에서 실측 display-width 기준 이미 base부터 168열을 넘겼다(`render._dw` 측정: base 182 → task1-4 175, 오히려 4번 이후 7칸 감소). 이 fixture의 stage breadcrumb(`eval-asr › eval-sep✕ › eval-vad › aggregate › report`)이 `_STAGE_ZONE_MAX` 폭 제한을 타지 않는 별도 코드경로(route-driven breadcrumb, harness 없음) 문제로, 이번 4개 과제 스코프 밖 — 새로 만든 결함 아님을 확인만 하고 미수정.

## 미검증/이연

- `by_repo` 실제 표시는 write-events.jsonl 저널 writer가 `cwd`/`project` 필드를 얹어야 라이브로 관측 가능 — 이번 사이클 스코프 밖(과제 지시대로 collector만 확장, writer는 불변).
- PRD §4.7 F-19/F-29 표시 계약 변경(및 이번에 추가된 4번 model-컬럼 통합)의 정식 등재는 사용자 결정대로 별도 사이클로 이연.
- `lab-project/demo-lab-conductor` 행의 168열 사전 존재 오버플로(위 참조) — 4개 과제 스코프 밖, 별도 이슈로 남김.

artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_fleet-mem-subagent/quick_evidence.md
verdict: PASS
blocker: none

## 5. 분사 행 제목 입양 (수확 후 메인 세션이 직접 추가 — 사용자 2026-07-16 후속 요청의 표시 절반)

- **배경**: main `218752e7`이 title refresher의 `is_child` 스킵을 제거해 haiku 요약 에이전트가 모든 분사 세션에 붙게 됨(스케줄 절반). 그러나 분사 행 이름은 `j.slug`만 사용해 제목이 화면에 도달하지 못함 — 이 표시 절반을 이 브랜치에 얹음.
- **collector 조인**: `collectors/__init__.py::_adopt_child_titles(sessions, jobs)` — enrich가 이미 해석한 자식 Session의 사이드카 제목을 그 자식을 대표하는 DispatchJob 행으로 복사. pid 동등이 강한 조인, harness+realpath(cwd)가 jobs.log 행 폴백(동일 cwd에 titled 자식 2명이면 거부 — F-26 오귀속 금지). `collect_all`에서 `_mark_dispatch_child_sessions` 직후 방어적으로 호출. 추가 IO 0(세션 enrich 결과 재사용), cross-harness.
- **model**: `DispatchJob.title` additive 필드(기본 None = 기존 slug 정체성 그대로).
- **render**: `_dispatch_row`/`_dispatch_row_2line`(stack은 2line 경유)의 이름 소스를 `title or slug or key`로 — 세션 행과 동일한 title → name → slug 체인. 이름 존 예산·클립(`_compact_dispatch_name`)·stage 라벨 합성 불변.
- **테스트**: `tests/test_dispatch_child_titles.py` 10건(pid 조인, cwd 조인, harness 불일치 거부, 동일 cwd 모호성 거부, 무제목 불변, 메인 세션 제목 비입양, wide 제목 우선/slug 폴백, 장문 클립+행 길이 불변, narrow 카드) — 전체 스위트 **614 tests, OK**(미러 재동기 후, mirror parity 포함).
- **데모 diff**: 조인 전후 168열 `--demo --once` — 데모 잡은 title=None이므로 구조적 diff 0(라이브 usage 수치·알림 해소 노이즈뿐).
- **라이브 검증(스트립·수확 중 확인)**: 실제 Explore 서브에이전트 1건 발사 → 본 세션 행 아래 `⚡ Explore ✓ 0m · …` 표시 확인(Task→Agent collector 수정의 end-to-end 증거).
