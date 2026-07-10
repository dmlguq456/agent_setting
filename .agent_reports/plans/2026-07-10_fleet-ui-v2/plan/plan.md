---
status: done
created: 2026-07-10
qa: standard
spec_significance: within-spec
---

# fleet UI v2 — stage-dispatch 관제 parity + UI 가독성 (PRD v2 §4.5 · §4.6)

## Spec-significance verdict: `within-spec`

이 사이클은 **구현 사이클**이다. 청사진은 이미 `agent-fleet-dashboard` PRD v2 (2026-07-10)에
잠금됐고(SD-F1~F4, F-9~F-13, §Next 1~4), 여기서는 그 계약을 `tools/fleet/` 코드로 실현할 뿐이다.
새 스펙 결정·계약 변경·범위 확장은 없다. 모델 스키마에 `effort`/`model_role` 필드를 더하는 것은
PRD §4.5 SD-F3 이 명시적으로 요구한 in-spec 변경이며, "표시층만(display-layer-only)" 제약은
F-9~F-13 블록에만 적용된다(SD-F1~F4 는 collector·model 을 정식으로 건드린다).

## Goal

jobs.log pipe 파서를 공백/콤마 tolerant 로 만들고(SD-F4), 스테이지 depth-2 row 를 사람이 읽는
단계명·자기 model/effort 로 렌더하고(SD-F1~F3), dispatch 메타라벨·alert·status 어휘·footer·
dead/stale row 를 가독화한다(F-9~F-13). 이 파이프 자체(fleet-ui-v2)의 depth-2 스테이지 세션이
라이브 검증 fixture 가 된다.

---

## Current State Analysis

### collectors/dispatch.py
- **`_parse_pipe_meta` (dispatch.py:51-72)**: pipe 의 여섯 번째 필드를 `key=value` 로 파싱.
  - line 58: `head = pipe.split("(", 1)[0]` — OLD form `code:dev(...)` 의 괄호 앞부분만.
  - line 61: `eq_pos != -1 and (colon_pos == -1 or eq_pos < colon_pos)` 게이트가 신형(`key=value`)과
    구형(`name:mode`)을 구분. **이 게이트는 유지한다.**
  - line 63: `for part in head.split(",")` — **콤마 단일 구분**. 공백 구분 행(2026-07-09 wild 실측)은
    첫 key 의 value 에 나머지가 전부 흡수돼 오파싱된다. 이것이 SD-F4 의 대상.
  - **위험 사실**: 라이브 jobs.log line 100 에 `model_role=deep maker` 가 있다 — canonical
    콤마 행 _안_ 의 value 에 공백이 들어간 케이스. 순진한 whitespace split 은 `deep maker` 를 깬다.
- **`_parse_pipe` (dispatch.py:75-78)**: `_parse_pipe_meta` 래핑 → (name, mode, qa, profile).
- **`_scan_jobs_log` (dispatch.py:686-742)**: jobs.log 행 → `DispatchJob`. line 737 이미
  `model=meta.get("model")` 읽음. **effort·model_role 은 안 읽는다** — SD-F3 로 추가.
- **`_scan_processes` (dispatch.py:592-672)**: proc env `AGENT_DISPATCH_*` 읽음(line 624-639).
  - **확인된 사실**: `adapters/claude/bin/dispatch-headless.py:386-392` 는 자식 env 에
    `AGENT_DISPATCH_DEPTH/INTENSITY/PARENT_SLUG/PARENT_SESSION_ID/WORKER_ROLE/OWNER/OWNER_HARNESS`
    만 export 한다. **effort·model_role 은 env 로 안 나간다** (pipe line 260 에만 실림:
    `model_source=…,model_role=…,model=…,effort=…`). 따라서 proc-scan 경로에서는 effort/model_role
    이 구조적으로 None → parent-inherit fallback(SD-F3)이 여기 적용. jobs.log 경로가 1급 소스.

### model.py
- **`DispatchJob` (model.py:152-181)**: `model` 필드는 있으나 **`effort` 없음, `model_role` 없음**.
  SD-F3 가 둘 다 요구.

### render.py
- **`_PIPE_STAGES["code"] = ["plan","exec","test"]` (render.py:486)**: 기존 breadcrumb 어휘.
  스테이지명 매핑에 재사용(SD-F1) — 새 어휘 발명 금지.
- **`_stage_segs` (render.py:547-578)**: breadcrumb 렌더. line 565 에서 미지 stage(`open`/`running`/
  key/"")는 whole-track-unlit. line 576 fallthrough `if stage: return [(stage, ...)]` 가 raw
  `open`/`running` 을 그대로 노출 → F-11 대상.
- **`_ROLE_SHORT` (render.py:687-697)**: `g6_worktree_dispatch→g6`, `g9_…→g9` 하드코딩 → F-9(b)
  일반 정규 규칙으로 교체. 라이브 drill 케이스엔 `g8b` 도 있음(테스트 fixture 참조).
- **`_short_role` (render.py:708-712)**: `_compact_dispatch_name(role, 14)` — 이미 tail-cut
  (head 보존). F-9(a) "head 보존"은 이미 충족(확인만).
- **`_dispatch_role_suffix` (render.py:715-729)**: intensity/role/qa 파트 조립. F-9(c) 폭 부족 시
  드롭 우선순위 `qa → intensity → role`(mode 는 별도 `_mq_tag` 라 유지) 없음 → 추가.
- **`_dispatch_row` (render.py:739-793) / `_dispatch_row_2line` (869-899) / `_dispatch_row_stack`
  (862-866)**: 세 레이아웃 모두 stage breadcrumb 을 `_stage_segs(key, stage, …)` 로 렌더
  (line 789/896). conductor 집계(SD-F2)는 여기에 stage_override 를 넣는 지점.
- **`_emit_dispatch_tree` (render.py:1236-1248)**: 자식 잡을 `job_children.get(job.slug, [])`
  로 재귀. conductor 의 depth-2 code-* 자식이 여기서 보인다 → SD-F2 active-stage 계산 지점.
- **alert strip (render.py:1059-1075)**: `j.slug or j.key` raw 사용(line 1066/1068). F-10 대상.
- **`+N malformed` (render.py:1311-1313)**: 이미 `"dim"` 색 → F-12(a)는 확인만.
- **legend (render.py:1316-1326)**: 정적. F-12(c)는 화면 실제 등장 글리프만 → glyph-appearance
  추적 필요.
- **footer `wlbl` (render.py:1545)**: `"wide/narrow" if _LAYOUT=="auto" else "%s!"%_LAYOUT` —
  auto 라벨이 **stack 모드를 누락**(3-모드 버그, F-12b).
- **`_session_row` (render.py:581-632) / `_dispatch_row`**: `dim_tel`(stale/dead) 시 `—`-채운
  telemetry 셀(line 622-623). F-13: stale/dead row 는 telemetry 셀 생략 + `last seen <age>`
  (age = `s.mtime`/`elapsed_min` 유도) 하나로 대체.
- **`_OFFSET` 모듈 전역 불변식 (render.py:14-26 docstring)**: `_build_lines` 는 절대 `_OFFSET`
  을 읽지 않는다 — plain/`--once` 경로 보존. glyph-appearance 추적은 `_build_lines` 안 로컬
  상태로만(전역 오염 금지).

### tests/test_dispatch.py
- 전부 hermetic — `procscan._ps_lines`, `os.readlink`, `read_environ`, `_dispatch_liveness`,
  `_job_liveness`, `_live_claude_cwds` 를 monkeypatch. 신규 테스트도 동일 패턴 준수.
- D5 클래스(test_dispatch.py:459-647)에 canonical-comma pipe 파싱 테스트가 있음 — SD-F4
  tolerant 파서가 이들을 회귀시키면 안 된다.

---

## Change Plan

phase 순서는 PRD §Next 1→4 를 따른다. Phase 1(파서) → Phase 2(스키마+collector+스테이지 row) →
Phase 3(가독성) → Phase 4(검증). Phase 내 독립 step 은 병렬 실행 가능(표시).

### Phase 1 — SD-F4: pipe tolerant 파싱 (collectors/dispatch.py) [render 가 여기 의존 → 먼저]

- **Step 1.1** — `_parse_pipe_meta` 를 **continuation tokenizer** 로 교체 (dispatch.py:58-68).
  - `head.split(",")`(line 63) 를 다음 알고리즘으로 대체:
    1. `head` 를 `re.split(r"[,\s]+", head)` 로 토큰화(빈 토큰 제거).
    2. 순회하며 `=` 를 **포함하는** 토큰은 새 `(k, v)` 쌍 시작(`k, v = tok.split("=", 1)`).
    3. `=` 없는 토큰은 **직전 쌍의 value 에 공백-join 하여 이어붙임**(continuation). 직전 쌍이
       없으면 무시.
  - 이 알고리즘이 (a) canonical 콤마 `a=1,b=2` (b) value-공백 `model_role=deep maker,model=opus`
    → `deep maker` 복원 (c) 공백구분 `a=1 b=2` (d) 혼용 을 모두 올바로 처리.
  - **`eq_pos < colon_pos` 게이트(line 61) 유지** — 신형/구형 구분. head 계산(line 58,
    `split("(",1)[0]`)도 유지.
  - 미지 key 는 기존대로 fields dict 에 저장하되 아무도 안 읽음(무시) — 변경 불필요.
  - `fields["_name"]`(line 67) 및 반환 계약 불변.
- **Step 1.2** — dispatch.py 상단에 tokenizer 정규식 상수(예: `_PIPE_TOK = re.compile(r"[,\s]+")`)
  추가(모듈 로드 1회 컴파일). `import re` 는 이미 있음(line 20).

### Phase 2 — SD-F1~F3: 스키마 + collector + 스테이지 row

- **Step 2.1** (model.py) — `DispatchJob` 에 두 필드 추가 (model.py:178 뒤):
  - `effort: Optional[str] = None` — dispatch runtime effort (pipe `effort=`; None→parent-inherit)
  - `model_role: Optional[str] = None` — portable model role (pipe `model_role=`; SD-5 관제)
  - dataclass 기본값 뒤쪽에 추가(field order 유지, 모든 필드 default 有 → 위치인자 호출 무영향).
  - **의존**: Phase 3 render 가 이 필드를 읽으므로 Phase 2 는 Phase 3 앞.
- **Step 2.2** (dispatch.py) — `_scan_jobs_log` 의 `DispatchJob(...)` 생성(line 732-741)에
  `effort=meta.get("effort")`, `model_role=meta.get("model_role")` 추가. `model=meta.get("model")`
  는 이미 있음. **Step 1.1 tolerant 파서 덕에 `model_role=deep maker` 가 온전히 복원됨.**
- **Step 2.3** (dispatch.py) — `_scan_processes` 의 두 `DispatchJob(...)`(line 630-640, 664-671)에
  방어적으로 `effort=env.get("AGENT_DISPATCH_EFFORT")`, `model_role=env.get("AGENT_DISPATCH_MODEL_ROLE")`
  추가. **현재 wrapper 는 이 env 를 export 하지 않으므로 None 이 정상**(fallback 경로). 미래
  wrapper 확장 대비 + 계약 대칭. [Step 2.1 과 2.2/2.3 은 2.1 완료 후 병렬]
- **Step 2.4** (render.py) — SD-F1 스테이지명 매핑 헬퍼 신설. `_PIPE_STAGES`(line 486) 근처에:
  - `_STAGE_ROLE = {"code-plan":"plan","code-execute":"exec","code-test":"test","code-report":"report"}`
    상수 추가. (`report` 는 code-report sub-skill 단축명 — 다른 어휘 발명 금지.)
  - `_stage_role_label(worker_role)` → `(base_label, suffix)`: `worker_role` 에서 `:phase-…`
    접미 분리 → base 를 `_STAGE_ROLE` 로 매핑(매핑 밖이면 None 반환 → 기존 `_short_role` 경로).
    suffix 는 있으면 `:phase-A` 형태로 반환.
- **Step 2.5** (render.py) — `_short_role`(line 708-712) 을 스테이지-aware 로:
  - 먼저 `_stage_role_label(value)` 시도 → base 매핑되면 `base` (+ suffix 는 호출부에서 dim
    으로) 반환. 매핑 안 되면 현행 `_ROLE_SHORT`/`_compact_dispatch_name(role,14)` 유지.
  - **F-9(b)**: `_ROLE_SHORT`(line 687-697)에서 `g6_worktree_dispatch`/`g9_…` 두 하드코딩
    엔트리 제거. `_short_role` 에 일반 규칙 추가: `re.match(r"^(g\d+[a-z]?)", value)` 매치되면
    그 prefix(예 `g6`,`g8b`,`g9`) 반환. (drill 케이스마다 코드 수정하는 구조 제거.)
- **Step 2.6** (render.py) — `_dispatch_role_suffix`(line 715-729)에서 스테이지 suffix(`:phase-A`)를
  role 뒤 dim 성분으로 붙이도록 조정(있을 때만). SD-F1 "접미는 뒤에 dim". [2.4 완료 후]
- **Step 2.7** (render.py) — **SD-F2 conductor breadcrumb 집계**.
  - `_emit_dispatch_tree`(line 1236-1248)에서 conductor row 를 렌더하기 전에 자식 stage 계산:
    `kids = job_children.get(job.slug, [])` 중 `worker_role` 이 `code-*` 이고 depth==2 인 것들.
    active = liveness=="working" 인 자식의 worker_role → `_STAGE_ROLE` 매핑 stage. active 가
    없으면(갭 구간) `job.stage`(conductor 의 `live_stage()` 유도값) fallback.
  - 계산된 `stage_override` 를 `_dispatch_row`/`_dispatch_row_2line`/`_dispatch_row_stack` 에
    새 optional 파라미터로 전달 → `_stage_segs(key, stage_override or stage, …)`(line 789/896)
    에서 사용. override None 이면 현행 동작 불변(회귀 안전).
  - breadcrumb 어휘는 `_PIPE_STAGES["code"]=["plan","exec","test"]` 그대로 — active 가 `report`
    면 `code` track(plan/exec/test) 밖이다. 이때 `_stage_segs` 는 seq 에 없는 stage 라
    fallthrough(line 576) `if stage: return [(stage, _cur_key(0))]` 로 **밝은 lone `report`
    토큰**을 낸다(현행 fallback — "dim track" 아님). 실행자 결정: 이 lone-token 표시를 그대로
    수용하거나, `report` 를 track 뒤 dim 단계로 명시 처리. 최소안은 현행 lone-token 수용.
- **Step 2.8** (render.py) — **SD-F3 스테이지 자기 model/effort 1급 표시**.
  - `_dispatch_row` model slot(line 781): `_model_cell(j.model or parent_model, parent_effort, …)`
    를 `_model_cell(j.model or parent_model, j.effort or parent_effort, …)` 로 — 자기 effort 우선,
    부재 시 parent-inherit fallback. `_dispatch_row_2line`(line 893)도 동일.
  - **fallback 시각 구분**: 자기 effort(`j.effort`)면 정상, parent-inherit fallback(`parent_effort`
    사용)이면 dim + 상속 표기. `_model_cell` 은 이미 dispatch row 에서 `dim=True`; 상속 여부를
    구분하려면 effort 성분에 `~` 접두(유도값 컨벤션 재사용) 또는 별도 dim 키. 최소 구현:
    `eff = j.effort or (parent_effort and "~"+parent_effort)` 로 유도값 `~` 표기 → legend 의
    `~` 설명(F-9d)과 일관. [Step 2.1 필드 존재에 의존]

### Phase 3 — F-9~F-13: 가독성 (render.py, 표시층만)

- **Step 3.1** — **F-9(c) 드롭 우선순위**. `_dispatch_role_suffix`(line 715-729)에 폭 인자를
  받아 `qa → intensity → role` 순으로 성분을 드롭(mode 는 `_mq_tag` 소관이라 유지). 조립된
  parts 가 가용폭 초과 시 순서대로 제거. [F-9(a) head 보존은 `_compact_dispatch_name` 이 이미
  충족 — 확인만.]
- **Step 3.2** — **F-9(d) `~` legend**. legend(line 1316-1326)에 `~` 유도값 1회 설명 추가
  (`~ derived` 류). 단 F-12(c) glyph-appearance 규칙과 조율 — `~` 는 텍스트라 항상 표기 OK.
- **Step 3.3** — **F-10 alert humanize** (line 1059-1075).
  - job 이름을 `_compact_dispatch_name` 경로 재사용 + loop 잡 `<case>-<ts>-<pid>` 꼬리 strip
    (정규식 `-\d{8,}-\d+$` 제거 헬퍼).
  - 같은 종류 alert 다수면 집계: `⚠ 2 dead jobs: a·b`. dead/stale/ctx 세 버킷 분리 집계.
  - 폭 초과 시 조용한 클립 대신 우선순위 절단 `dead > stale > ctx`. [독립 step]
- **Step 3.4** — **F-11 raw status 어휘** (`_stage_segs` line 565-578).
  - line 576 fallthrough 전에: `stage == "open"` → `queued` 로 humanize.
  - `stage == "running"` → whole-track-unlit(기존 line 565 규칙 재사용 — `("", key, "open",
    "running")` 집합에 이미 running 포함되어 seq 있으면 unlit track. seq 없는 key 만 fallthrough).
    seq 없는 key 의 `running` 은 `queued` 처럼 raw 노출 방지 위해 dim track 미점등 처리.
  - jobs.log status 어휘 자체는 불변 — 표시층만. [독립 step, 3.6 conductor 와 `_stage_segs`
    공유하니 순서 주의: 2.7 이후]
- **Step 3.5** — **F-12(b) footer 3-모드**. `wlbl`(line 1545) 을
  `"wide/narrow/stack" if _LAYOUT=="auto" else ("%s!"%_LAYOUT)` 로 — auto 가 세 모드 전부 명명.
  [독립 step]
- **Step 3.6** — **F-12(a)** `+N malformed`(line 1313) 이미 dim → **확인만**, 변경 없으면 skip.
- **Step 3.7** — **F-12(c) legend glyph-appearance 추적**. `_build_lines` 안에서 실제 emit 된
  글리프를 로컬 set 에 수집(세션/잡 row 생성 시 사용한 glyph char 기록), legend(line 1316-1326)
  는 그 set 에 든 글리프만 출력. **`_OFFSET` 불변식 준수** — 추적은 `_build_lines` 로컬 변수로만,
  모듈 전역 X. plain/`--once` 경로도 같은 `_build_lines` 라 자동 일관. [설계 substantial 하지
  않음 — 표시 규칙 정제 범위. glyph 수집이 복잡하면 최소안: 항상 등장하는 working/idle/dispatch
  는 유지, 조건부 glyph(detached/stale/dead/🚧/▾N)만 등장 시 추가.]
  `[decision: significant — legend 추적 방식이 _build_lines 반환 계약에 로컬 상태를 더함; plain 경로 회귀 없어야]`
- **Step 3.8** — **F-13 dead/stale last-seen** (`_session_row` line 620-623 + `_dispatch_row`).
  - `dim_tel`(stale/dead) row: telemetry 셀(ctx gauge + `—` 나열) 대신 단일 `last seen <age>`.
    age = `fmt_min` on (now - `s.mtime`)/60 또는 `s.elapsed_min` fallback. `_model_cell`·gauge
    셀을 이 한 값으로 치환.
  - **"explicit —/없음" 규칙(F-3)은 LIVE row 에만** — dead/stale 은 결손 나열 대신 last-seen.
  - app_server/detached 는 F-13 대상 아님(stale/dead 만) — `dim_tel` 조건을 stale/dead 로 좁혀
    적용(app_server/detached 는 현행 유지). [독립 step이나 _session_row/_dispatch_row 광범위 →
    3.3/3.4 와 파일 겹침, 순차 권장]

### Phase 4 — 검증 (아래 Verification 섹션 실행)

---

## Risks

- **R1 (SD-F4 회귀)**: tolerant 파서가 D5 canonical-comma 테스트(test_dispatch.py:543-647,
  `capability=…,mode=…,qa=…,depth=…,parent=…,worker_role=…,owner=…`)를 깨면 안 된다. continuation
  tokenizer 는 `=` 있는 토큰을 항상 새 쌍으로 시작하므로 콤마-only 행은 기존과 동일 결과여야
  한다 — 신규 fixture 외에 **기존 D5 전부 regress-green** 확인 필수.
- **R2 (value-내부 공백)**: `model_role=deep maker` 는 canonical 콤마 행 _안_ 의 공백이다.
  순진한 whitespace-split 은 이걸 깬다 — continuation 방식만 안전. 반드시 전용 fixture 로 검증.
- **R3 (legend glyph-tracking)**: F-12(c) 추적이 plain/`--once` 경로를 깨면 안 된다. `_OFFSET`
  불변식(`_build_lines` 는 `_OFFSET` 미독) 존중 — 추적 상태는 `_build_lines` 로컬로만.
- **R4 (conductor stage_override)**: override None 기본값으로 현행 dispatch row 전부 회귀 안전.
  active-child 계산이 `job_children` 없을 때(비-conductor) None 반환 확인.
- **R5 (SD-F3 proc-scan None)**: proc-scan 경로는 effort/model_role 이 구조적으로 None
  (wrapper 미export). 이건 버그 아니라 fallback 정상 — jobs.log 경로가 1급. 테스트에서 이
  비대칭을 명시.
- **R6 (`_stage_segs` 공유)**: F-11(3.4)·SD-F2(2.7)·SD-F1(2.4) 이 모두 `_stage_segs`/stage
  어휘를 건드림 → 같은 함수 편집 충돌 방지 위해 2.7 → 3.4 순서, 한 커밋 내 정합.
- **R7 (double-width 정렬)**: 스테이지명(plan/exec/test/report)은 ASCII 라 정렬 안전. `~` 접두도
  ASCII. 신규 glyph 없음.
- **R8 (tokenizer 전제)**: continuation tokenizer 의 유일 failure mode 는 `=`-없는 토큰이 아니라
  그 반대 — value-내부 공백 뒤 토큰이 우연히 `=` 를 포함하면 새 key 로 오인식된다
  (`notes=foo bar=baz` → `bar=baz` 가 별도 pair). 실제로는 writer(dispatch-headless.py:260)가
  필드마다 `key=` 를 방출하고 pipe field vocabulary 가 닫혀 있어(known key 집합) 안 터지지만,
  이 전제(닫힌 vocabulary + writer 가 `key=` 접두 방출)를 SD-F4 구현 주석에 명시한다.

---

## Verification

### Unit tests (hermetic, monkeypatched — 신규 테스트도 동일 패턴)
```
cd tools && python3 -m unittest fleet.tests.test_dispatch -v
```
- **기존 전부 regress-green** (특히 D5 canonical-comma 파싱 test_dispatch.py:459-647).
- **신규 테스트 (추가)**:
  - (a) `test_parse_pipe_space_separated_row` — 2026-07-09 공백구분 행 fixture
    (`a=1 b=2 c=3`) → 각 key 독립 파싱 확인.
  - (b) `test_parse_pipe_value_internal_space` — `model_role=deep maker,model=opus` →
    `fields["model_role"]=="deep maker"`, `fields["model"]=="opus"` (value 내부 공백 보존).
  - (c) `test_parse_pipe_unknown_key_ignored` — 미지 key 포함 행이 crash 없이 알려진 key 만
    반환, 미지 key 는 무시(읽히지 않음).
  - (d) `test_stage_worker_rows_render_stage_labels` — worker_role ∈ {code-plan, code-execute,
    code-test, code-report} depth-2 row 가 각각 plan/exec/test/report 라벨로 렌더(raw
    `code_execute` 등장 X). `render._build_lines` 또는 `_dispatch_row` 텍스트 assert.
  - (e) `test_conductor_breadcrumb_aggregates_active_child_stage` — depth-1 code conductor +
    depth-2 code-execute(working) 자식 → conductor breadcrumb 이 `exec` 하이라이트. 자식 done +
    갭이면 conductor `live_stage` fallback.
  - (f) `test_alert_humanize_aggregates_and_strips_tail` — loop 잡 `<case>-<ts>-<pid>` 꼬리
    strip + 같은 종류 다수 집계(`⚠ 2 dead jobs: a·b`) 확인.
- **회귀 fixture 갱신**: `_ROLE_SHORT` 에서 g6/g9 제거했으므로 기존 g9 short-form 의존 테스트
  (실제 위치 test_dispatch.py:467-535 의 `g9_cross_harness_depth2_dispatch` 케이스들; 참고로
  test_dispatch.py:72-80 은 `raw_role==slug` null 로직이라 g6/g9 매핑과 무관)가 일반 규칙
  (`^(g\d+[a-z]?)`)으로 여전히 `g9`/`g8b` 를 내는지 확인·필요 시 갱신.

### Render smoke + LIVE 관제 실증
```
python3 tools/fleet/fleet.py --once
python3 tools/fleet/fleet.py --json
```
- (a) **이 fleet-ui-v2 파이프 자신의 depth-2 스테이지 row** (code-plan/code-execute/code-test/
  code-report)가 스테이지명(plan/exec/test/report)으로 렌더되는지 — 이 파이프의 depth-2 세션이
  라이브 fixture.
- (b) **conductor row**(fleet-ui-v2 capability-owner)의 breadcrumb 집계가 활성 스테이지 자식과
  일치하는지.
- (c) 기존 render 회귀 없음(usage 헤더·pulse·그룹 카드·folded·legend·footer 정상).
- `--json` 은 스테이지 잡의 `effort`/`model_role` 필드가 채워져 나오는지 확인.

---

## Decision Points

- **Step 3.7** `[decision: significant]` — legend glyph-appearance 추적이 `_build_lines` 에 로컬
  상태를 더한다. plain/`--once` 경로 회귀·`_OFFSET` 불변식이 걸려 있으므로, 복잡해지면 최소안
  (조건부 glyph 만 등장 시 추가)으로 축소. 실행자가 회귀 위험 판단.
