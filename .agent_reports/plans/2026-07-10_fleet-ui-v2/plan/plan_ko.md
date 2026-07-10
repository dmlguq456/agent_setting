---
status: active
created: 2026-07-10
qa: standard
spec_significance: within-spec
---

# fleet UI v2 — stage-dispatch 관제 정합 + UI 가독성 (PRD v2 §4.5 · §4.6)

## 스펙 영향도 판정: `within-spec`

이 사이클은 **구현 사이클**이다. 청사진은 이미 `agent-fleet-dashboard` PRD v2 (2026-07-10)에
잠겼고(SD-F1~F4, F-9~F-13, §Next 1~4), 여기서는 그 계약을 `tools/fleet/` 코드로 실현할 뿐이다.
새 스펙 결정·계약 변경·범위 확장은 없다. 모델 스키마에 `effort`/`model_role` 필드를 더하는 것은
PRD §4.5 의 SD-F3 이 명시적으로 요구한 스펙 내(in-spec) 변경이며, "표시층만(display-layer-only)"
제약은 F-9~F-13 블록에만 적용된다(SD-F1~F4 는 collector·model 을 정식으로 건드린다).

## 목표

jobs.log 의 pipe 파서를 공백·콤마 어느 쪽으로 구분해도 받아들이도록 고치고(SD-F4), depth-2 스테이지
row 를 사람이 읽을 수 있는 단계명과 자기 model/effort 로 렌더한다(SD-F1~F3). 여기에 더해 dispatch
메타라벨·alert·status 어휘·footer·dead/stale row 를 읽기 좋게 다듬는다(F-9~F-13). 이 파이프 자신
(fleet-ui-v2)의 depth-2 스테이지 세션이 라이브 검증 fixture 역할을 한다.

---

## 현황 분석

### collectors/dispatch.py
- **`_parse_pipe_meta` (dispatch.py:51-72)**: pipe 의 여섯 번째 필드를 `key=value` 로 파싱.
  - 58번째 줄: `head = pipe.split("(", 1)[0]` — 구형 `code:dev(...)` 의 괄호 앞부분만 취함.
  - 61번째 줄: `eq_pos != -1 and (colon_pos == -1 or eq_pos < colon_pos)` 판별 조건이 신형
    (`key=value`)과 구형(`name:mode`)을 구분. **이 판별 조건은 유지한다.**
  - 63번째 줄: `for part in head.split(",")` — **콤마로만 구분**. 공백으로 구분된 행(2026-07-09
    실환경에서 관측)은 첫 key 의 value 가 나머지를 전부 빨아들여 잘못 파싱된다. 이것이 SD-F4 가
    고칠 대상이다.
  - **주의할 사실**: 라이브 jobs.log 100번째 줄에 `model_role=deep maker` 가 있다 — 표준 콤마 행
    _안쪽_ value 에 공백이 낀 경우다. 단순한 공백 분리로는 `deep maker` 가 쪼개진다.
- **`_parse_pipe` (dispatch.py:75-78)**: `_parse_pipe_meta` 를 감싸 (name, mode, qa, profile) 반환.
- **`_scan_jobs_log` (dispatch.py:686-742)**: jobs.log 행 → `DispatchJob`. 737번째 줄은 이미
  `model=meta.get("model")` 를 읽는다. **effort·model_role 은 읽지 않는다** — SD-F3 로 추가.
- **`_scan_processes` (dispatch.py:592-672)**: proc env `AGENT_DISPATCH_*` 를 읽음(624-639번째 줄).
  - **확인된 사실**: `adapters/claude/bin/dispatch-headless.py:386-392` 는 자식 env 로
    `AGENT_DISPATCH_DEPTH/INTENSITY/PARENT_SLUG/PARENT_SESSION_ID/WORKER_ROLE/OWNER/OWNER_HARNESS`
    만 내보낸다. **effort·model_role 은 env 로 나가지 않는다**(pipe 260번째 줄에만 실림:
    `model_source=…,model_role=…,model=…,effort=…`). 따라서 proc-scan 경로에서는 effort/model_role
    이 구조적으로 None → 부모 상속 폴백(SD-F3)이 여기 적용된다. jobs.log 경로가 1차 소스다.

### model.py
- **`DispatchJob` (model.py:152-181)**: `model` 필드는 있으나 **`effort` 없음, `model_role` 없음**.
  SD-F3 가 둘 다 요구.

### render.py
- **`_PIPE_STAGES["code"] = ["plan","exec","test"]` (render.py:486)**: 기존 breadcrumb 어휘.
  스테이지명 매핑에 재사용(SD-F1) — 새 어휘를 만들지 않는다.
- **`_stage_segs` (render.py:547-578)**: breadcrumb 렌더. 565번째 줄에서 알 수 없는 stage(`open`/
  `running`/key/"")는 트랙 전체를 미점등 처리한다. 576번째 줄 fallthrough `if stage: return
  [(stage, ...)]` 는 `open`/`running` 원문을 그대로 노출한다 → F-11 대상.
- **`_ROLE_SHORT` (render.py:687-697)**: `g6_worktree_dispatch→g6`, `g9_…→g9` 하드코딩 → F-9(b)
  에서 일반 정규식 규칙으로 교체. 라이브 drill 케이스에는 `g8b` 도 있다(테스트 fixture 참조).
- **`_short_role` (render.py:708-712)**: `_compact_dispatch_name(role, 14)` — 이미 뒷부분을
  잘라낸다(앞부분 보존). F-9(a) "앞부분 보존" 은 이미 충족되므로 확인만 하면 된다.
- **`_dispatch_role_suffix` (render.py:715-729)**: intensity/role/qa 성분을 조립한다. F-9(c) 의
  '폭이 모자랄 때 `qa → intensity → role` 순으로 버리는 우선순위'(mode 는 `_mq_tag` 소관이라
  유지)가 아직 없다 → 추가한다.
- **`_dispatch_row` (render.py:739-793) / `_dispatch_row_2line` (869-899) / `_dispatch_row_stack`
  (862-866)**: 세 레이아웃 모두 stage breadcrumb 을 `_stage_segs(key, stage, …)` 로 렌더한다
  (789/896번째 줄). conductor 집계(SD-F2)는 여기에 `stage_override` 를 끼워 넣는 자리다.
- **`_emit_dispatch_tree` (render.py:1236-1248)**: 자식 잡을 `job_children.get(job.slug, [])`
  로 재귀한다. conductor 의 depth-2 code-* 자식이 여기서 보인다 → SD-F2 활성 스테이지 계산 자리.
- **alert strip (render.py:1059-1075)**: `j.slug or j.key` 를 가공 없이 그대로 쓴다(1066/1068번째
  줄). F-10 대상.
- **`+N malformed` (render.py:1311-1313)**: 이미 `"dim"` 색 → F-12(a)는 확인만.
- **legend (render.py:1316-1326)**: 정적이다. F-12(c)는 화면에 실제로 등장한 글리프만 남기므로 →
  글리프 등장 여부 추적이 필요하다.
- **footer `wlbl` (render.py:1545)**: `"wide/narrow" if _LAYOUT=="auto" else "%s!"%_LAYOUT` —
  auto 라벨이 **stack 모드를 빠뜨린다**(3-모드 버그, F-12b).
- **`_session_row` (render.py:581-632) / `_dispatch_row`**: `dim_tel`(stale/dead)일 때 `—` 로
  채운 telemetry 셀(622-623번째 줄). F-13: stale/dead row 는 telemetry 셀을 생략하고
  `last seen <age>`(age 는 `s.mtime`/`elapsed_min` 에서 유도) 하나로 대체한다.
- **`_OFFSET` 모듈 전역 불변식 (render.py:14-26 docstring)**: `_build_lines` 는 절대 `_OFFSET`
  을 읽지 않는다 — plain/`--once` 경로를 보존하기 위해서다. 글리프 등장 추적은 `_build_lines` 안의
  지역 상태로만 두고 전역을 오염시키지 않는다.

### tests/test_dispatch.py
- 전부 hermetic 하다 — `procscan._ps_lines`, `os.readlink`, `read_environ`, `_dispatch_liveness`,
  `_job_liveness`, `_live_claude_cwds` 를 monkeypatch 한다. 신규 테스트도 같은 패턴을 지킨다.
- D5 클래스(test_dispatch.py:459-647)에 표준 콤마 pipe 파싱 테스트가 있다 — SD-F4 관용 파서가
  이들을 회귀시켜서는 안 된다.

---

## 변경 계획

phase 순서는 PRD §Next 1→4 를 따른다. Phase 1(파서) → Phase 2(스키마+collector+스테이지 row) →
Phase 3(가독성) → Phase 4(검증). 같은 Phase 안의 독립 step 은 병렬로 실행할 수 있다(표시함).

### Phase 1 — SD-F4: pipe 관용 파싱 (collectors/dispatch.py) [render 가 여기 의존 → 먼저]

- **Step 1.1** — `_parse_pipe_meta` 를 **이어붙임(continuation) 토크나이저** 로 교체한다
  (dispatch.py:58-68).
  - `head.split(",")`(63번째 줄)를 다음 알고리즘으로 대체한다:
    1. `head` 를 `re.split(r"[,\s]+", head)` 로 토큰화한다(빈 토큰 제거).
    2. 순회하면서 `=` 를 **포함하는** 토큰은 새 `(k, v)` 쌍을 시작한다(`k, v = tok.split("=", 1)`).
    3. `=` 가 없는 토큰은 **직전 쌍의 value 에 공백으로 이어붙인다**(continuation). 직전 쌍이
       없으면 무시한다.
  - 이 알고리즘은 (a) 표준 콤마 `a=1,b=2` (b) value 에 공백이 낀 `model_role=deep maker,model=opus`
    → `deep maker` 복원 (c) 공백 구분 `a=1 b=2` (d) 둘의 혼용 을 모두 올바로 처리한다.
  - **`eq_pos < colon_pos` 판별 조건(61번째 줄) 유지** — 신형/구형 구분용. head 계산(58번째 줄,
    `split("(",1)[0]`)도 유지한다.
  - 알 수 없는 key 는 기존대로 fields dict 에 저장하되 아무도 읽지 않는다(무시) — 바꿀 필요 없다.
  - `fields["_name"]`(67번째 줄)과 반환 계약은 그대로 둔다.
- **Step 1.2** — dispatch.py 상단에 토크나이저 정규식 상수(예: `_PIPE_TOK = re.compile(r"[,\s]+")`)
  를 추가한다(모듈 로드 시 한 번만 컴파일). `import re` 는 이미 있다(20번째 줄).

### Phase 2 — SD-F1~F3: 스키마 + collector + 스테이지 row

- **Step 2.1** (model.py) — `DispatchJob` 에 필드 두 개를 추가한다(model.py:178 뒤):
  - `effort: Optional[str] = None` — dispatch 실행 effort (pipe 의 `effort=`; None 이면 부모 상속)
  - `model_role: Optional[str] = None` — 포터블 model role (pipe 의 `model_role=`; SD-5 관제)
  - dataclass 의 기본값 필드 뒤쪽에 추가한다(필드 순서 유지, 모든 필드에 default 가 있어 위치인자
    호출에 영향 없음).
  - **의존**: Phase 3 의 render 가 이 필드를 읽으므로 Phase 2 가 Phase 3 앞에 온다.
- **Step 2.2** (dispatch.py) — `_scan_jobs_log` 의 `DispatchJob(...)` 생성부(732-741번째 줄)에
  `effort=meta.get("effort")`, `model_role=meta.get("model_role")` 를 추가한다.
  `model=meta.get("model")` 는 이미 있다. **Step 1.1 의 관용 파서 덕분에 `model_role=deep maker`
  가 온전히 복원된다.**
- **Step 2.3** (dispatch.py) — `_scan_processes` 의 `DispatchJob(...)` 두 곳(630-640, 664-671번째
  줄)에 방어적으로 `effort=env.get("AGENT_DISPATCH_EFFORT")`,
  `model_role=env.get("AGENT_DISPATCH_MODEL_ROLE")` 를 추가한다. **현재 wrapper 는 이 env 를
  내보내지 않으므로 None 이 정상이다**(폴백 경로). 앞으로 wrapper 가 확장될 때를 대비하고 계약을
  대칭으로 맞추려는 것. [2.2/2.3 은 2.1 완료 뒤 병렬]
- **Step 2.4** (render.py) — SD-F1 스테이지명 매핑 헬퍼를 새로 만든다. `_PIPE_STAGES`(486번째 줄)
  근처에:
  - `_STAGE_ROLE = {"code-plan":"plan","code-execute":"exec","code-test":"test","code-report":"report"}`
    상수를 추가한다. (`report` 는 code-report sub-skill 의 단축명 — 다른 어휘를 만들지 않는다.)
  - `_stage_role_label(worker_role)` → `(base_label, suffix)`: `worker_role` 에서 `:phase-…`
    접미를 떼어내고 → base 를 `_STAGE_ROLE` 로 매핑한다(매핑에 없으면 None 반환 → 기존
    `_short_role` 경로). suffix 는 있으면 `:phase-A` 형태로 반환한다.
- **Step 2.5** (render.py) — `_short_role`(708-712번째 줄)을 스테이지를 인식하도록 고친다:
  - 먼저 `_stage_role_label(value)` 를 시도해 → base 가 매핑되면 `base` 를 반환한다(suffix 는
    호출부에서 dim 처리). 매핑되지 않으면 현행 `_ROLE_SHORT`/`_compact_dispatch_name(role,14)` 를
    유지한다.
  - **F-9(b)**: `_ROLE_SHORT`(687-697번째 줄)에서 `g6_worktree_dispatch`/`g9_…` 하드코딩 엔트리
    두 개를 제거한다. `_short_role` 에 일반 규칙을 추가한다: `re.match(r"^(g\d+[a-z]?)", value)`
    가 매치되면 그 prefix(예: `g6`,`g8b`,`g9`)를 반환. (drill 케이스마다 코드를 고쳐야 하는
    구조를 없앤다.)
- **Step 2.6** (render.py) — `_dispatch_role_suffix`(715-729번째 줄)에서 스테이지 suffix
  (`:phase-A`)를 role 뒤에 dim 성분으로 붙이도록 조정한다(있을 때만). SD-F1 의 '접미는 뒤쪽에
  dim'. [2.4 완료 뒤]
- **Step 2.7** (render.py) — **SD-F2 conductor breadcrumb 집계**.
  - `_emit_dispatch_tree`(1236-1248번째 줄)에서 conductor row 를 렌더하기 전에 자식 stage 를
    계산한다: `kids = job_children.get(job.slug, [])` 중 `worker_role` 이 `code-*` 이고 depth==2
    인 것들. active 는 liveness=="working" 인 자식의 worker_role → `_STAGE_ROLE` 로 매핑한 stage.
    active 가 없으면(사이 구간) `job.stage`(conductor 의 `live_stage()` 유도값)로 폴백한다.
  - 계산한 `stage_override` 를 `_dispatch_row`/`_dispatch_row_2line`/`_dispatch_row_stack` 에
    새 optional 파라미터로 넘긴다 → `_stage_segs(key, stage_override or stage, …)`(789/896번째 줄)
    에서 쓴다. override 가 None 이면 현행 동작 그대로다(회귀 안전).
  - breadcrumb 어휘는 `_PIPE_STAGES["code"]=["plan","exec","test"]` 그대로다 — active 가 `report`
    면 `code` 트랙(plan/exec/test) 밖이다. 이때 `_stage_segs` 는 seq 에 없는 stage 라
    fallthrough(576번째 줄) `if stage: return [(stage, _cur_key(0))]` 를 타고 **밝은 단독 `report`
    토큰**을 낸다(현행 fallback — 'dim track' 이 아님). 실행자가 결정할 점: 이 단독 토큰 표시를
    그대로 받아들이거나, `report` 를 트랙 뒤 dim 단계로 명시 처리한다. 최소안은 현행 단독 토큰을
    그대로 받아들이는 것.
- **Step 2.8** (render.py) — **SD-F3 스테이지 자기 model/effort 1급 표시**.
  - `_dispatch_row` 의 model slot(781번째 줄): `_model_cell(j.model or parent_model, parent_effort, …)`
    을 `_model_cell(j.model or parent_model, j.effort or parent_effort, …)` 로 바꾼다 — 자기
    effort 를 우선하고, 없으면 부모 상속으로 폴백. `_dispatch_row_2line`(893번째 줄)도 동일하다.
  - **폴백 시각 구분**: 자기 effort(`j.effort`)면 정상, 부모 상속 폴백(`parent_effort` 사용)이면
    dim + 상속 표기. `_model_cell` 은 이미 dispatch row 에서 `dim=True` 다; 상속 여부를 구분하려면
    effort 성분에 `~` 접두(유도값 컨벤션 재사용)를 붙이거나 별도 dim 키를 둔다. 최소 구현:
    `eff = j.effort or (parent_effort and "~"+parent_effort)` 로 유도값에 `~` 를 표기 → legend 의
    `~` 설명(F-9d)과 일관된다. [Step 2.1 의 필드 존재에 의존]

### Phase 3 — F-9~F-13: 가독성 (render.py, 표시층만)

- **Step 3.1** — **F-9(c) 드롭 우선순위**. `_dispatch_role_suffix`(715-729번째 줄)가 폭 인자를
  받아 `qa → intensity → role` 순으로 성분을 버리게 한다(mode 는 `_mq_tag` 소관이라 유지). 조립한
  parts 가 가용폭을 넘으면 이 순서대로 제거한다. [F-9(a) 앞부분 보존은 `_compact_dispatch_name`
  이 이미 충족 — 확인만.]
- **Step 3.2** — **F-9(d) `~` legend**. legend(1316-1326번째 줄)에 `~` 유도값 설명을 한 줄
  추가한다(`~ derived` 류). 단 F-12(c) 글리프 등장 규칙과 맞춘다 — `~` 는 텍스트라 항상 표기해도
  된다.
- **Step 3.3** — **F-10 alert 가독화** (1059-1075번째 줄).
  - job 이름은 `_compact_dispatch_name` 경로를 재사용하고 + loop 잡의 `<case>-<ts>-<pid>` 꼬리를
    잘라낸다(정규식 `-\d{8,}-\d+$` 제거 헬퍼).
  - 같은 종류의 alert 가 여러 개면 묶는다: `⚠ 2 dead jobs: a·b`. dead/stale/ctx 세 버킷으로 나눠
    집계한다.
  - 폭을 넘으면 조용히 잘라내지 말고 `dead > stale > ctx` 우선순위로 절단한다. [독립 step]
- **Step 3.4** — **F-11 raw status 어휘 정리** (`_stage_segs` 565-578번째 줄).
  - 576번째 줄 fallthrough 전에: `stage == "open"` → `queued` 로 바꿔 표기한다.
  - `stage == "running"` → 트랙 전체 미점등(기존 565번째 줄 규칙 재사용 — `("", key, "open",
    "running")` 집합에 running 이 이미 포함돼, seq 가 있으면 미점등 트랙이 된다. seq 가 없는 key
    만 fallthrough). seq 가 없는 key 의 `running` 은 `queued` 처럼 원문 노출을 막기 위해 dim 트랙
    미점등으로 처리한다.
  - jobs.log 의 status 어휘 자체는 그대로 둔다 — 표시층만 손댄다. [독립 step, 3.6·conductor 와
    `_stage_segs` 를 공유하니 순서 주의: 2.7 이후]
- **Step 3.5** — **F-12(b) footer 3-모드**. `wlbl`(1545번째 줄)을
  `"wide/narrow/stack" if _LAYOUT=="auto" else ("%s!"%_LAYOUT)` 로 바꾼다 — auto 가 세 모드를
  전부 이름 붙이게. [독립 step]
- **Step 3.6** — **F-12(a)** `+N malformed`(1313번째 줄)는 이미 dim → **확인만** 하고, 바꿀 게
  없으면 넘어간다.
- **Step 3.7** — **F-12(c) legend 글리프 등장 추적**. `_build_lines` 안에서 실제로 emit 된
  글리프를 지역 set 에 모으고(세션/잡 row 를 만들 때 쓴 glyph char 기록), legend(1316-1326번째 줄)
  는 그 set 에 든 글리프만 출력한다. **`_OFFSET` 불변식 준수** — 추적은 `_build_lines` 지역
  변수로만 하고 모듈 전역은 건드리지 않는다. plain/`--once` 경로도 같은 `_build_lines` 라
  자동으로 일관된다. [설계가 크지 않다 — 표시 규칙을 다듬는 범위. glyph 수집이 복잡하면 최소안:
  항상 나오는 working/idle/dispatch 는 유지하고, 조건부 glyph(detached/stale/dead/🚧/▾N)만
  등장할 때 추가한다.]
  `[decision: significant — legend 추적 방식이 _build_lines 반환 계약에 지역 상태를 더함; plain 경로 회귀 없어야]`
- **Step 3.8** — **F-13 dead/stale last-seen** (`_session_row` 620-623번째 줄 + `_dispatch_row`).
  - `dim_tel`(stale/dead) row: telemetry 셀(ctx gauge + `—` 나열) 대신 `last seen <age>` 하나로.
    age 는 (now - `s.mtime`)/60 에 `fmt_min` 을 적용하거나 `s.elapsed_min` 로 폴백. `_model_cell`·
    gauge 셀을 이 한 값으로 치환한다.
  - **'명시적 —/없음' 규칙(F-3)은 LIVE row 에만 적용** — dead/stale 은 결손을 나열하지 말고
    last-seen 으로 대체.
  - app_server/detached 는 F-13 대상이 아니다(stale/dead 만) — `dim_tel` 조건을 stale/dead 로
    좁혀 적용한다(app_server/detached 는 현행 유지). [독립 step 이지만 _session_row/_dispatch_row
    를 넓게 건드려 → 3.3/3.4 와 파일이 겹치므로 순차 권장]

### Phase 4 — 검증 (아래 검증 방법 섹션 실행)

---

## 리스크

- **R1 (SD-F4 회귀)**: 관용 파서가 D5 표준 콤마 테스트(test_dispatch.py:543-647,
  `capability=…,mode=…,qa=…,depth=…,parent=…,worker_role=…,owner=…`)를 깨서는 안 된다. 이어붙임
  토크나이저는 `=` 가 있는 토큰을 항상 새 쌍으로 시작하므로 콤마로만 된 행은 기존과 같은 결과여야
  한다 — 신규 fixture 외에 **기존 D5 전부 회귀 통과** 를 반드시 확인한다.
- **R2 (value 내부 공백)**: `model_role=deep maker` 는 표준 콤마 행 _안쪽_ 의 공백이다. 단순한
  공백 분리로는 이게 깨진다 — 이어붙임 방식만 안전하다. 반드시 전용 fixture 로 검증한다.
- **R3 (legend 글리프 추적)**: F-12(c) 추적이 plain/`--once` 경로를 깨서는 안 된다. `_OFFSET`
  불변식(`_build_lines` 는 `_OFFSET` 을 읽지 않음)을 지킨다 — 추적 상태는 `_build_lines` 지역에만
  둔다.
- **R4 (conductor stage_override)**: override 기본값이 None 이라 현행 dispatch row 는 전부 회귀
  안전하다. active 자식 계산이 `job_children` 이 없을 때(conductor 가 아닐 때) None 을 반환하는지
  확인한다.
- **R5 (SD-F3 proc-scan None)**: proc-scan 경로는 effort/model_role 이 구조적으로 None 이다
  (wrapper 가 내보내지 않음). 버그가 아니라 폴백이 정상 동작하는 것 — jobs.log 경로가 1차 소스다.
  테스트에서 이 비대칭을 명시한다.
- **R6 (`_stage_segs` 공유)**: F-11(3.4)·SD-F2(2.7)·SD-F1(2.4)이 모두 `_stage_segs`/stage 어휘를
  건드린다 → 같은 함수 편집이 충돌하지 않도록 2.7 → 3.4 순서로, 한 커밋 안에서 정합을 맞춘다.
- **R7 (double-width 정렬)**: 스테이지명(plan/exec/test/report)은 ASCII 라 정렬이 안전하다. `~`
  접두도 ASCII 다. 새 glyph 없음.
- **R8 (토크나이저 전제)**: 이어붙임 토크나이저의 유일한 실패 양상은 `=` 가 없는 토큰이 아니라
  그 반대다 — value 내부 공백 뒤의 토큰이 우연히 `=` 를 포함하면 새 key 로 잘못 인식된다
  (`notes=foo bar=baz` → `bar=baz` 가 별도 쌍으로). 실제로는 writer(dispatch-headless.py:260)가
  필드마다 `key=` 를 내보내고 pipe 필드 어휘가 닫혀 있어(알려진 key 집합) 터지지 않지만, 이 전제
  (닫힌 어휘 + writer 가 `key=` 접두를 방출)를 SD-F4 구현 주석에 명시한다.

---

## 검증 방법

### 단위 테스트 (hermetic, monkeypatch — 신규 테스트도 같은 패턴)
```
cd tools && python3 -m unittest fleet.tests.test_dispatch -v
```
- **기존 전부 회귀 통과** (특히 D5 표준 콤마 파싱 test_dispatch.py:459-647).
- **신규 테스트 (추가)**:
  - (a) `test_parse_pipe_space_separated_row` — 2026-07-09 공백 구분 행 fixture
    (`a=1 b=2 c=3`) → 각 key 가 독립적으로 파싱되는지 확인.
  - (b) `test_parse_pipe_value_internal_space` — `model_role=deep maker,model=opus` →
    `fields["model_role"]=="deep maker"`, `fields["model"]=="opus"` (value 내부 공백 보존).
  - (c) `test_parse_pipe_unknown_key_ignored` — 알 수 없는 key 가 섞인 행이 crash 없이 알려진
    key 만 반환하고, 알 수 없는 key 는 무시(읽히지 않음)한다.
  - (d) `test_stage_worker_rows_render_stage_labels` — worker_role ∈ {code-plan, code-execute,
    code-test, code-report} 인 depth-2 row 가 각각 plan/exec/test/report 라벨로 렌더되는지(원문
    `code_execute` 는 등장하지 않음). `render._build_lines` 또는 `_dispatch_row` 텍스트로 assert.
  - (e) `test_conductor_breadcrumb_aggregates_active_child_stage` — depth-1 code conductor +
    depth-2 code-execute(working) 자식 → conductor breadcrumb 이 `exec` 를 하이라이트. 자식이
    done 이고 사이 구간이면 conductor 의 `live_stage` 로 폴백.
  - (f) `test_alert_humanize_aggregates_and_strips_tail` — loop 잡의 `<case>-<ts>-<pid>` 꼬리를
    잘라내고 + 같은 종류가 여러 개일 때 집계(`⚠ 2 dead jobs: a·b`)하는지 확인.
- **회귀 fixture 갱신**: `_ROLE_SHORT` 에서 g6/g9 를 제거했으므로, 기존 g9 단축형에 의존하는
  테스트(실제 위치는 test_dispatch.py:467-535 의 `g9_cross_harness_depth2_dispatch` 케이스들;
  참고로 test_dispatch.py:72-80 은 `raw_role==slug` null 로직이라 g6/g9 매핑과 무관)가 일반 규칙
  (`^(g\d+[a-z]?)`)으로도 여전히 `g9`/`g8b` 를 내는지 확인하고 필요하면 갱신한다.

### 렌더 smoke + LIVE 관제 실증
```
python3 tools/fleet/fleet.py --once
python3 tools/fleet/fleet.py --json
```
- (a) **이 fleet-ui-v2 파이프 자신의 depth-2 스테이지 row**(code-plan/code-execute/code-test/
  code-report)가 스테이지명(plan/exec/test/report)으로 렌더되는지 — 이 파이프의 depth-2 세션이
  라이브 fixture 다.
- (b) **conductor row**(fleet-ui-v2 capability-owner)의 breadcrumb 집계가 활성 스테이지 자식과
  일치하는지.
- (c) 기존 render 회귀 없음(usage 헤더·pulse·그룹 카드·folded·legend·footer 정상).
- `--json` 에서 스테이지 잡의 `effort`/`model_role` 필드가 채워져 나오는지 확인.

---

## 결정 지점

- **Step 3.7** `[decision: significant]` — legend 글리프 등장 추적이 `_build_lines` 에 지역 상태를
  더한다. plain/`--once` 경로 회귀와 `_OFFSET` 불변식이 걸려 있으므로, 복잡해지면 최소안(조건부
  glyph 만 등장할 때 추가)으로 줄인다. 회귀 위험은 실행자가 판단한다.
