# fleet 데모 모드 — two-plane 가안 뷰 (quick, additive)

## 진입점

`--demo two-plane` (기존 문법 그대로 유지, `--demo`를 `nargs="?"`로 확장):
- `fleet.py --demo` (인자 없음) → 기존 `True` 그대로 (역호환, byte-identical)
- `fleet.py --demo two-plane` → two-plane 가안 뷰
- `fleet.py --demo --once` → `--once`가 값으로 삼켜지지 않음(argparse가 `-`로 시작하는 토큰은
  옵션값으로 소비하지 않음 — 별도 테스트로 확인: `test_demo_flag_does_not_swallow_a_following_option`)

`--view group|process`처럼 별도 choices 플래그를 추가하는 대신 `--demo`의 변형으로 넣은 이유:
이 뷰는 실제 라이브 데이터 위에서 켜는 필터가 아니라 **픽스처 전용 화면**이라, `--demo`의
값 공간을 확장하는 쪽이 "데모 픽스처 모드의 변형"이라는 과제 설명과 그대로 맞는다.

## 추가한 곳

- **`tools/fleet/two_plane.py`** (신규) — 픽스처(Session/DispatchJob 그대로 재사용) + 빌더.
  그리드 평면은 `render._session_row` / `_session_row_2line` / `_session_row_stack`을
  layout에 맞춰 그대로 호출(수정 없음). 과정 평면(⚡ 인셋 행, ▸ 레일 행, 캔버스 breadcrumb,
  노드-앵커 ⚡, 레포별 mem 행)은 이 모듈의 전용 빌더가 담당하되, 색 키(`stgN_on/off`,
  `hb_*`/`h_*`, `lvl_g`/`lvl_r`, `dim`)·폭 계산(`_pad`/`_dw`/`_clip_w`)·tint sentinel
  (`_TINT_BODY_HOT`/`_TINT_BODY`)·`_ROW_BOLD`·`_pulse_segs`/`_mem_summary_segs`/`_gauge_segs`/
  `_pct_key`/`_col_head`는 전부 render.py의 실제 함수를 그대로 가져다 쓴다(문자열 조립로
  색·정렬을 재발명하지 않음).
- **`tools/fleet/render.py`** — `_TWO_PLANE_DEMO` 플래그 + `set_two_plane_demo()` 세터,
  `_build_lines()` 최상단에 한 곳의 분기(`_PROCESS_VIEW` 분기와 동일한 관용구)만 추가.
  플래그 기본값 `False` → 이 분기는 `--demo two-plane`이 아니면 절대 타지 않는다.
  `_branch_seg`/`_session_row` 자체는 건드리지 않았다 — `⎇` 글리프는 two_plane.py의
  `_with_branch_glyph()`가 반환된 세그먼트 리스트를 후처리로 감싸 넣는다(그리드 엔진 공유
  함수는 무수정).
- **`tools/fleet/fleet.py`** — `--demo` argparse를 `store_true` → `nargs="?", const=True`로,
  `main()`에 `two_plane_demo = args.demo == "two-plane"` 분기 + `render.set_two_plane_demo(...)`
  한 줄.
- **`tools/fleet/tests/test_two_plane_demo.py`** (신규, 19 케이스) — CLI 파싱, 플래그
  기본값 회귀(0 변경 검증 2건), 확정 문법 10개 조항 중 실제로 텍스트로 드러나는 항목(#1~#9)
  각각에 대한 단정, `two_plane.build_lines()` 직접 단위 테스트.
- `adapters/claude/tools/fleet/`(어댑터 미러) — `rsync -a --delete --exclude='__pycache__'
  tools/fleet/ adapters/claude/tools/fleet/`로 재동기(기존 `test_mirror_parity.py`가 요구).

## 기본 동작 변경 0 검증

- `render._TWO_PLANE_DEMO`는 모듈 로드시 `False`; `test_flag_defaults_false`,
  `test_normal_build_lines_ignores_two_plane_module_when_flag_is_false`,
  `test_setting_flag_true_then_false_restores_normal_output`으로 회귀 0을 코드로 고정.
- 수동 대조: `git stash`로 변경 전 코드를 살려 `--demo --once`/`--once` 출력을 캡처 후
  스택 팝하여 재비교 — 라이브 프로세스(실제 이 세션 자신 포함) 상태가 두 실행 사이에
  실제로 바뀌어(spinner 프레임, 실제 세션 유무) 텍스트 자체는 달랐지만, 차이는 전부
  "실행 시점의 라이브 상태" 기인이지 코드 변경 기인이 아님을 diff로 확인(스피너 프레임
  `⠋→⠼`, 실제 SR_CorrNet_DSC 세션의 등장/그룹 정렬 순서 변화 — 둘 다 시계/프로세스 목록
  의존, `--demo two-plane`/render.py의 새 분기와 무관). 결정론적 회귀 보증은 위 3개
  단위 테스트가 담당.

## 3폭 캡처 (`--demo two-plane --once`)

### 60열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠋ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

  SESSIONS   two-plane demo

● agent_setting/
  ⠋ claude code     fleet UI two-plane … tracked  ⎇ main
    2h14m           opus (high)            
                    [━━━━━━━━──────────  42%]
   │   ⚡ Explore   "fleet 제목 파… ● 2m51s
   │   ⚡ Explore   "렌더 구조·stag… ✓ 4m04s
   │
   ├─▸ claude code  🔧 code · usage-accuracy  "usage 소스 신… (thr · ~thorough)  ⏳ 20m
   │    plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
   │                └ exec:B ● 3m (claude·sonnet·med)
   │        ⚡ 개발팀       "usage tap fres… @exec ● 1m12s
   │        ⚡ Explore   "usage tap 스키… @exec:B ✓ 48s
   │
   └─▸ codex  🔧 code · rate-window  "rate-window 헤… (quick · gpt·med)  ● 4m

  ● codex           usage probe rat… tracked  ⎇ wt-usage
    41m             gpt (medium)           
                    [━━━───────────────  18%]
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked  ⎇ main
    1h02m           opus (medium)          
                    [━━━━━━────────────  31%]
   ▸ claude code  loop:note "오전 수집분 다…  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

### 120열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠙ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

  SESSIONS   two-plane demo

● agent_setting/
  ⠙ claude code     fleet UI two-plane demo tracked  ⎇ main
    2h14m           opus (high)            [━━━━━━━━──────────  42%]
   │   ⚡ Explore   "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인" ● 2m51s
   │   ⚡ Explore   "렌더 구조·stage 존·mem 표시 조사" ✓ 4m04s
   │
   ├─▸ claude code  🔧 code · usage-accuracy  "usage 소스 신뢰 규칙 구현" (thr · ~thorough)  ⏳ 20m
   │    plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
   │                └ exec:B ● 3m (claude·sonnet·med)
   │        ⚡ 개발팀       "usage tap freshness 파서 구현" @exec ● 1m12s
   │        ⚡ Explore   "usage tap 스키마 사전 조사" @exec:B ✓ 48s
   │
   └─▸ codex  🔧 code · rate-window  "rate-window 헤더 재검증" (quick · gpt·med)  ● 4m

  ● codex           usage probe rate-window tracked  ⎇ wt-usage
    41m             gpt (medium)           [━━━───────────────  18%]
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked  ⎇ main
    1h02m           opus (medium)          [━━━━━━────────────  31%]
   ▸ claude code  loop:note "오전 수집분 다이제스트"  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

### 168열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠹ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

    harness         session                                 branch        model                      context / stage   time     

● agent_setting/
  ⠹ claude code     fleet UI two-plane demo tracked         ⎇ main        opus (high)                ━━━━━━━━━━──────────────  42%    2h14m
   │   ⚡ Explore   "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인" ● 2m51s
   │   ⚡ Explore   "렌더 구조·stage 존·mem 표시 조사" ✓ 4m04s
   │
   ├─▸ claude code  🔧 code · usage-accuracy  "usage 소스 신뢰 규칙 구현" (thr · ~thorough)  ⏳ 20m
   │    plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
   │                └ exec:B ● 3m (claude·sonnet·med)
   │        ⚡ 개발팀       "usage tap freshness 파서 구현" @exec ● 1m12s
   │        ⚡ Explore   "usage tap 스키마 사전 조사" @exec:B ✓ 48s
   │
   └─▸ codex  🔧 code · rate-window  "rate-window 헤더 재검증" (quick · gpt·med)  ● 4m

  ● codex           usage probe rate-window tracked         ⎇ wt-usage    gpt (medium)               ━━━━────────────────────  18%      41m
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked                  ⎇ main        opus (medium)              ━━━━━━━─────────────────  31%    1h02m
   ▸ claude code  loop:note "오전 수집분 다이제스트"  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

(참고: `--once`는 색을 전혀 입히지 않는 순수 텍스트 스냅샷이 기존 설계 — `render._plain()`이
tint/bold sentinel과 color_key를 전부 버리고 텍스트만 합친다. 그래서 위 캡처는 무채색이며,
이는 기존 `fleet.py --once`/`--demo --once` 전부와 동일한 기존 계약이다.)

## 확정 문법 10개 조항 대조

1. 두 평면 — ✓ 세션 그리드는 `_session_row*` 그대로, 자식은 별도 인셋/레일 행.
2. ⚡ 서브에이전트 — ✓ 커넥터 없는 인셋, `⚡N` 배지 미표시(`test_no_subagent_count_badge_on_the_session_row`).
3. ▸ 분사 — ✓ `├─▸`/`└─▸`, 하네스 평명도, 🔧, 잡 계약 괄호.
4. 캔버스 — ✓ 기존 breadcrumb ` › ` 재사용, stgN 팔레트, exec:B 보조행.
5. 노드-앵커 ⚡ — ✓ `@exec`/`@exec:B` 태그.
6. mem 레포별 — ✓ agent_setting 카드 하단 2행, worklog-board는 무음, 상단은 집계 1행
   (`_mem_summary_segs` 재사용).
7. 세션 그리드 ⎇ — ✓ `_with_branch_glyph()`가 이 뷰에서만 후처리로 삽입,
   `_branch_seg` 원본은 `test_branch_glyph_is_scoped_to_two_plane_only`로 무수정 확인.
8. 폰트 위계 — ✓ 메인 세션 `_ROW_BOLD`, 분사 하네스 텍스트 `hb_*`(평명도), 완료 항목만 dim.
9. loop 잡 — ✓ `loop:note ... queued · next 18m` (부모 없음, worklog-board 카드 소속).
10. chrome 불변 — ✓ `_BADGE_TEXT` 평문, tint sentinel(`_TINT_BODY_HOT`/`_TINT_BODY`) 재사용,
    흰 바/cyan 바 신설 없음, cost 표시 없음. footer(키캡 바)는 `--once` 자체가 원래
    그리지 않는 영역이라 손대지 않음.

## 테스트 결과

```
$ python3 -m unittest discover -s tools/fleet/tests -t .
Ran 575 tests in ~17s
OK
```
(기존 556 + 신규 19; 어댑터 미러 재동기 후 `test_mirror_parity`도 통과.)

## 커밋

브랜치 `fleet-two-plane-demo`에 커밋 완료(푸시 없음).

---

## r2 — 후속 수정 2건 (quick, 같은 브랜치)

### 변경 1: 트리 격자 → ↳ 화살표

`tools/fleet/two_plane.py`에서 세로 스파인(`│`)·레일 커넥터(`├─`/`└─`)를 전부 제거하고,
render.py 실제 dispatch 행이 이미 쓰는 `↳` 스폰 화살표(`_dispatch_prefix`,
"user pick over ├─/└─ tree bars" 주석과 동일 결정)로 대체:

- ▸ 분사 실체 행: `_ARROW_PREFIX = "   ↳ "` (3칸 들여쓰기 + 화살표) — `▸`가 5번째 컬럼에 착지.
- ⚡ 서브에이전트 행(세션 직속): `_AGENT_IND = "     "` (공백 5칸) — `⚡`도 동일하게 5번째 컬럼.
- 캔버스 행 + 노드-앵커 ⚡: `_NODE_IND = " " * 8` (▸ 블록 하위 한 단계).
- 캔버스 내부 `└ exec:B …` 보조행: `_SUBNODE_IND = " " * 10` (캔버스보다 한 단계 더 깊음, 커넥터
  자체는 승인된 프리뷰대로 유지).
- 서브에이전트/분사 행 사이의 구분용 빈 `│`행은 `None`(빈 줄)으로 대체 — 스파인 없이도 시각적
  여백은 유지.
- `test_no_tree_lattice_survives_in_this_view`로 `│`/`├─`/`└─` 전무를 단정.

**kind-글리프 컬럼 리듬 수정**: `render._pad`는 파이썬 문자 수 기준이라 "개발팀"(3자·6셀)이
"Explore"(7자·10셀)보다 적은 디스플레이 셀로 패딩되어 컬럼이 어긋났다. `_pad_dw()`(신규, 이
파일 전용 — `r._dw`/`r._clip_w` 조합, 엔진 테이블 무수정)를 `_agent_line()`의 `agent_type`·
desc·anchor 필드에 적용해 셀 폭 기준으로 고정. `test_kind_glyph_column_aligns_across_ascii_and_cjk_agent_types`,
`test_node_anchored_status_column_aligns_across_siblings`로 같은 레벨 형제 행의 desc/anchor/
상태 컬럼이 동일 디스플레이-컬럼에서 시작함을 실측 단정(120열에서 desc 시작 컬럼 92,
@태그 컬럼 95, 상태 글리프 컬럼 105로 두 쌍 모두 일치 확인).

### 변경 2: bold는 메인 세션 행 전용

`_ROW_BOLD`(메인 세션 행) 외 이 뷰의 모든 bold 소스를 평명도 키로 교체(엔진 색 테이블
무수정, 기존 non-bold 키 재사용):

- 캔버스 활성 노드: `stgN_on`(bold) → `_STAGE_PLAIN = ("eff_high","fam_opus","lvl_g","g_idle","fam_fable")`
  (엔진 stage 팔레트 순서 0~4=blue·cyan·green·yellow·magenta와 인덱스 일치). done/pending은
  기존 `stgN_off`(dim) 그대로.
- ▸ 행의 `🔧 <key>`·글리프: 동일 `_STAGE_PLAIN` 인덱스(usage-accuracy=index1 cyan,
  rate-window=index0 blue).
- 캔버스의 `exec:B` 보조행: `stg1_on` → `_STAGE_PLAIN[1]`(exec 노드와 같은 cyan).
- 그룹 헤더(활성, agent_setting): 글리프 `g_work`(bold) → `lvl_g`(평명도 green, blink-off
  프레임은 기존 `g_work_off` dim 유지), 이름 `grp_hot`(bold green) → `grp_live`(평명도
  green, 색 유지·bold만 제거 — 엔진에 이미 존재하는 키).
- 그룹 헤더(비활성, worklog-board): 이름 `grp`(bold, 색 없음) → `None`(지킬 색이 애초에
  없었으므로 bold만 제거).
- 부수 발견(사용자 3항목 나열엔 없었으나 동일 규칙 위반이라 함께 정리): 범례 행의
  `("●","g_work")` → `("●","lvl_g")`(이 행은 재사용 엔진 chrome이 아니라 이 뷰 자체 코드),
  mem 이벤트 `−` 글리프의 `lvl_r`(bold red, 엔진에 평명도 red 키가 없어 대안 없음) →
  `dim`(엔진 테이블 미수정 제약상 최선의 낙하지점). **미변경(의도적)**: 상단 인텔존
  `_pulse_segs`(`"N working"`의 `g_work`)는 render.py의 실제 공유 함수를 그대로 호출하는
  chrome이라 원 계약("chrome 불변", 재사용 함수 무수정)상 이 뷰 전용 bold 규칙을 적용하지
  않음.
- `BoldScopeTest` 3건(캔버스, ▸ 행, 그룹 헤더)이 색 키 레벨로 `stgN_on`/`grp_hot`/`g_work`/
  `grp` 부재 + `fam_opus`/`eff_high`/`grp_live` 존재를 단정(헤드리스 실행이라 curses 속성이
  아니라 `(text, color_key)` 세그먼트의 키 문자열로 검증).

### 3폭 재캡처 (`--demo two-plane --once`)

#### 60열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠦ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

  SESSIONS   two-plane demo

● agent_setting/
  ⠦ claude code     fleet UI two-plane … tracked  ⎇ main
    2h14m           opus (high)            
                    [━━━━━━━━──────────  42%]
     ⚡ Explore   "fleet 제목 파…  ● 2m51s
     ⚡ Explore   "렌더 구조·stag… ✓ 4m04s

   ↳ ▸ claude code  🔧 code · usage-accuracy  "usage 소스 신… (thr · ~thorough)  ⏳ 20m
        plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
          └ exec:B ● 3m (claude·sonnet·med)
        ⚡ 개발팀    "usage tap fres… @exec     ● 1m12s
        ⚡ Explore   "usage tap 스키… @exec:B   ✓ 48s

   ↳ ▸ codex  🔧 code · rate-window  "rate-window 헤… (quick · gpt·med)  ● 4m

  ● codex           usage probe rat… tracked  ⎇ wt-usage
    41m             gpt (medium)           
                    [━━━───────────────  18%]
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked  ⎇ main
    1h02m           opus (medium)          
                    [━━━━━━────────────  31%]
   ▸ claude code  loop:note "오전 수집분 다…  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

#### 120열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠏ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

  SESSIONS   two-plane demo

● agent_setting/
  ⠏ claude code     fleet UI two-plane demo tracked  ⎇ main
    2h14m           opus (high)            [━━━━━━━━──────────  42%]
     ⚡ Explore   "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인"     ● 2m51s
     ⚡ Explore   "렌더 구조·stage 존·mem 표시 조사"                                     ✓ 4m04s

   ↳ ▸ claude code  🔧 code · usage-accuracy  "usage 소스 신뢰 규칙 구현" (thr · ~thorough)  ⏳ 20m
        plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
          └ exec:B ● 3m (claude·sonnet·med)
        ⚡ 개발팀    "usage tap freshness 파서 구현"                                        @exec     ● 1m12s
        ⚡ Explore   "usage tap 스키마 사전 조사"                                           @exec:B   ✓ 48s

   ↳ ▸ codex  🔧 code · rate-window  "rate-window 헤더 재검증" (quick · gpt·med)  ● 4m

  ● codex           usage probe rate-window tracked  ⎇ wt-usage
    41m             gpt (medium)           [━━━───────────────  18%]
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked  ⎇ main
    1h02m           opus (medium)          [━━━━━━────────────  31%]
   ▸ claude code  loop:note "오전 수집분 다이제스트"  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

#### 168열
```
  usage claude code   [━━━━━━━─────  62%]  ↻ 2h11m · 5h window
        codex         [━━──────────  18%]  weekly 43%
  fleet ⠙ 1 working   ● 2 idle   ↳ 3 jobs (2 working)
  🧠 mem  +4 added(3w·1d) · 0 expired · 1 pruned · last distill 45m
─────

    harness         session                                 branch        model                      context / stage   time     

● agent_setting/
  ⠙ claude code     fleet UI two-plane demo tracked         ⎇ main        opus (high)                ━━━━━━━━━━──────────────  42%    2h14m
     ⚡ Explore   "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인"     ● 2m51s
     ⚡ Explore   "렌더 구조·stage 존·mem 표시 조사"                                     ✓ 4m04s

   ↳ ▸ claude code  🔧 code · usage-accuracy  "usage 소스 신뢰 규칙 구현" (thr · ~thorough)  ⏳ 20m
        plan ✓12m › exec ● 8m (claude·haiku·med) › test ○ › report ○
          └ exec:B ● 3m (claude·sonnet·med)
        ⚡ 개발팀    "usage tap freshness 파서 구현"                                        @exec     ● 1m12s
        ⚡ Explore   "usage tap 스키마 사전 조사"                                           @exec:B   ✓ 48s

   ↳ ▸ codex  🔧 code · rate-window  "rate-window 헤더 재검증" (quick · gpt·med)  ● 4m

  ● codex           usage probe rate-window tracked         ⎇ wt-usage    gpt (medium)               ━━━━────────────────────  18%      41m
 🧠 14:02 + durable/project distiller  "fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴"
 🧠 13:47 − working/expired curator    "usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)"

○ worklog-board/
  ● claude code     주간 보드 정리 tracked                  ⎇ main        opus (medium)              ━━━━━━━─────────────────  31%    1h02m
   ▸ claude code  loop:note "오전 수집분 다이제스트"  queued · next 18m

  ● working   ● idle   ⚡ sub-agent   ▸ pipeline   ✓ done   ○ pending
```

### 기본 동작 변경 0 재검증

- `render._TWO_PLANE_DEMO` 기본값·복원 회귀 테스트 3건 그대로 통과(수정 없음).
- CLI 대조: `fleet.py --demo --once`(bare) 실행 결과가 기존 PROCESS VIEW 픽스처 그대로임을
  육안 확인 — two_plane.py 변경분은 `render.set_two_plane_demo(True)`일 때만 타는 경로라
  bare `--demo` 출력엔 영향 없음.

### 테스트 결과

```
$ python3 -m unittest discover -s tools/fleet/tests -t .
Ran 581 tests in ~17s
OK
```
(r1의 575 + 신규 6 — `BoldScopeTest` 3건, `test_no_tree_lattice_survives_in_this_view`,
`test_kind_glyph_column_aligns_across_ascii_and_cjk_agent_types`,
`test_node_anchored_status_column_aligns_across_siblings`; 기존 `test_dispatch_rows_use_rail_connectors_and_capability_glyph`는
새 모양에 맞춰 `test_dispatch_rows_use_the_spawn_arrow_and_capability_glyph`로 대체.
어댑터 미러 재동기(`rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/`)
후 `test_mirror_parity`도 통과.)

### 커밋 (r2)

같은 브랜치 `fleet-two-plane-demo`에 이어서 커밋(푸시 없음).
