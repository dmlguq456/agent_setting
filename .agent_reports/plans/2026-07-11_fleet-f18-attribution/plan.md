# F-18 구현 plan — loop·drill·mem-워커 귀속 정밀화

- **청사진**: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.6 F-18 (2026-07-11 minor #4, within-spec)
- **워크트리/브랜치**: `/home/Uihyeop/agent_setting-wt/fleet-f18-attribution` (`fleet-f18-attribution`)
- **대상**: `tools/fleet/{model.py, collectors/procscan.py, collectors/dispatch.py, render.py, tests/}`
- **구현 대상 2종**: F-18a(drill 이중 표시 dedup) · F-18b(mem-워커 오귀속 차단)

두 건은 독립적이라 **Phase 1(F-18b) → Phase 2(F-18a)** 순서로 나눠 구현·검증한다 (역순도 무방; 서로 다른 seam). Phase 1 은 `procscan→model→render` 세로 경로, Phase 2 는 `dispatch.collect()` 병합 한 지점.

---

## 0. 불변식 체크리스트 (매 단계 준수 — 완료 후 재확인)

- [ ] collector 필드·`--json` **additive only** — 기존 필드 의미 불변. 신규는 `Session.mem_worker`(default False) 1개뿐. `DispatchJob` 필드 추가 없음(F-18a 는 기존 `pid`/`liveness` 재사용).
- [ ] registry(`jobs.log`) **무write** — F-18a 는 읽기·메모리 병합만.
- [ ] `render.py` 모듈 레벨 `curses.A_*` 금지 — 새 스타일 키는 기존 `_A_DIM`/`_A_BOLD` 폴백 또는 이미 등록된 `_COLOR["dim"]` 재사용.
- [ ] Windows no-curses import 경로 회귀 없음 — 태깅은 `/proc/<pid>/environ` 기반이라 `procscan.scan()`(POSIX) 에만 적용; `_scan_disk()`(nt) 경로는 마커 판독 불가 → `mem_worker=False` default 유지 (§1.2 명시).
- [ ] F-14~F-17 계약 유지 — usage 행·title(F-14/17)·분사 row(F-15)·detached·child-job 표시 로직 불변, mem_worker 는 **추가 필터**로만 끼어든다.
- [ ] drill g9/g10/g_stage_dispatch assert 가 `fleet.collectors.dispatch` 를 파이썬 임포트 → 임포트·기존 함수 시그니처 불변 확인.

---

## Phase 1 — F-18b: mem-워커 태깅·기본 제외

**목표**: distiller/curator(`MEM_DISTILL=1`)·F-17 refresher(`FLEET_TITLE_REFRESH=1`) 세션이 부모 cwd·env 상속으로 (i) 부모 밑 `↳` 자식으로 뜨거나 (ii) drill fixture cwd 면 `drill:<case>` 그룹으로 오귀속되는 것을 차단. procscan 이 environ 마커로 태깅 → 기본 표시에서 제외, 그룹/legend 에 `🧠N` 요약, `a` 토글 시 dim `mem` row.

전파 경로: **`procscan.scan()` (태깅) → `model.Session.mem_worker` (필드) → `render._build_lines()` (제외·요약·토글) → `fleet.py --json` (`to_dict` 자동 노출)**.

### Step 1.1 — `model.py`: `Session.mem_worker` 필드 추가

`tools/fleet/model.py`, `Session` dataclass (line 119~148). 마지막 enrichment 필드군 뒤(예: `branch` line 147 아래)에 additive 로 추가:

```python
    mem_worker: bool = False   # F-18b: memory distiller/curator(MEM_DISTILL) 또는 F-17 refresher(FLEET_TITLE_REFRESH) 세션 — 기본 표시 제외, 🧠N 요약으로만
```

- `to_dict()`(asdict)로 `--json` 에 자동 노출 → additive.

### Step 1.2 — `procscan.py`: environ 마커 판독·태깅

`tools/fleet/collectors/procscan.py`. `read_environ(pid)`(line 31~42) 는 이미 존재 — 재사용 (dispatch collector 의 AGENT_DISPATCH_* environ 판독과 동일 선례). `is_child` 판독(line 215)에서 이미 `read_environ(pid)` 를 호출하므로 **같은 env dict 를 재사용해 추가 subprocess/read 없이** 마커를 본다.

`scan()` 의 POSIX 루프(line 215 부근) 수정:

```python
        env = read_environ(pid)                       # 1회 read 재사용
        is_child = comm == "claude" and env.get("CLAUDE_CODE_CHILD_SESSION") == "1"
        mem_worker = env.get("MEM_DISTILL") == "1" or env.get("FLEET_TITLE_REFRESH") == "1"
```

그리고 `Session(...)` 생성(line 217~227)에 `mem_worker=mem_worker,` 추가.

- 마커 값 확정(코드 실측):
  - `MEM_DISTILL=1` — distiller/curator 재귀가드 (여러 hook 이 이 값으로 판별; `hooks/mem-distill-dispatch.sh:212` 가 `MEM_DISTILL=1` 로 worker 분사).
  - `FLEET_TITLE_REFRESH=1` — F-17 refresher (`tools/fleet/refresh_title.py:153` 이 subprocess env 에 주입).
  - `MEM_DISTILL_WORKER`(worker 실행파일명)은 마커 아님 — 판독 대상 제외.
- **degrade 계약**: `read_environ` 은 권한 실패/race 시 `{}` 반환 → `mem_worker=False` → 현행 표시 유지(무해). 오귀속 차단이 1차 목적이라 태깅 실패는 "현상 유지"로 안전 fallback.
- **nt 분기 명시**: `_scan_disk()`(line 132~174) 는 `/proc` 없는 Windows/MSYS 경로 — environ 판독 불가. `Session(...)` 생성 시 `mem_worker` 를 넘기지 않아 default `False` 유지 (마커 판독 미적용). curses/신규 import 없음 → Windows import 경로 회귀 없음. 주석 1줄로 "nt 경로는 environ 마커 판독 불가, mem_worker 태깅 미적용(무해 degrade)" 명시.

### Step 1.3 — `render.py`: 기본 표시에서 제외 (pulse·usage·fold·shown)

`tools/fleet/render.py` `_build_lines()`(line 1145~). mem_worker 세션을 **집계·그룹·표시에서 제외**하되, `_SHOW_ALL` 이면 노출(Step 1.5). 손대는 지점:

1. **전역 mem 카운트** (is_child 필터 line 1153 **이전**에 계산 — is_child 마커를 상속한 mem 워커도 세기 위함):
   ```python
   n_mem_total = sum(1 for s in sessions if getattr(s, "mem_worker", False))
   ```
   (`_build_lines` 진입 직후, line 1152 주석 위)

2. **그룹핑 제외** — `sessions = [s for s in sessions if not s.is_child]`(line 1153) 를 확장:
   ```python
   sessions = [s for s in sessions
               if not s.is_child and not (getattr(s, "mem_worker", False) and not _SHOW_ALL)]
   ```
   → 기본은 mem 워커가 그룹 구성·row 에서 빠져 `drill:<case>`/부모 그룹을 부풀리지 않음. `_SHOW_ALL` 이면 남아 Step 1.5 에서 dim row 로.

3. **pulse census** (`_real`, line 1232): mem 워커 제외 (그룹핑 단계에서 이미 빠졌으면 중복 무해하지만 명시적으로):
   ```python
   _real = [s for s in sessions if not s.app_server and not getattr(s, "mem_worker", False)]
   ```
   → working/idle/detached 카운트에 mem 미포함. (`sessions` 는 위 2번 필터 후이므로 기본 경로에선 이미 제외됨 — `_SHOW_ALL` 시 census 오염 방지용 이중 안전.)

4. **usage 행 `_live_h`** (line 1195): mem 워커가 harness usage 행을 살리지 않도록 제외:
   ```python
   _live_h = set(s.harness for s in sessions
                 if s.liveness not in ("stale", "dead") and not s.app_server
                 and not s.is_child and not getattr(s, "mem_worker", False))
   ```

5. **fold 판정 `live_sessions`** (line 1330): mem 워커가 group 을 unfold 시키지 않도록 (기본 경로에선 2번에서 이미 group_sessions 에서 빠짐 → 자동 충족; `_SHOW_ALL` 은 fold 자체가 off 라 무관). **추가 편집 불필요** — 2번 필터가 상류에서 처리. (주석으로 근거 남김.)

> 순수 mem-워커만 있는 그룹은 group_sessions 가 비어 fold/미생성 → drill/프로젝트 그룹 오귀속·oscillation(수분 내 나타났다 사라짐) 소멸. 이것이 F-18b 의 1차 목적.

### Step 1.4 — `render.py`: `🧠N` 그룹 badge + legend 요약

1. **그룹 header badge** — group 별 mem 워커 수를 세어 header 에 `🧠N` 부착. group fold 판정 전(line 1322 루프 안, `group_sessions` 는 이미 mem 제외됨)에서 **원본 세션에서 group 별 mem 수를 별도 map 으로** 계산해야 한다. `_build_lines` 상단(그룹핑 루프 line 1156 이전)에서 project_of 로 mem 워커를 group_key 별 집계:
   ```python
   mem_by_group = {}
   for s in [x for x in sessions_all_incl_mem if getattr(x, "mem_worker", False)]:
       mem_by_group[_group_key_session(s)] = mem_by_group.get(_group_key_session(s), 0) + 1
   ```
   여기서 `sessions_all_incl_mem` = is_child 필터·mem 필터 **적용 전** 원본(진입 시 파라미터 사본). Step 1.3-1 의 `n_mem_total` 계산과 같은 소스에서 파생.

   그런 뒤 header 조립부(line 1426 `head_segs += [(name, _name_key), ("/", "dim")]` 뒤, 🚧 worktree badge line 1428 부근과 나란히):
   ```python
   _nmem = mem_by_group.get(name, 0)
   if _nmem:
       head_segs += [(" 🧠 %d" % _nmem, "dim")]
       _seen_glyphs.add("mem")
   ```
   - `🧠` 는 이미 `_WIDE`(line 1647) 등록 글리프 → 폭 계산 정상.
   - 스타일 키는 기존 `"dim"`(=`curses.A_DIM` 등록, line 279) 재사용 → 모듈 레벨 `curses.A_*` 신규 참조 없음.

2. **legend 요약** — `_seen_glyphs` 에 `"mem"` 이 있으면 legend(line 1576~1592)에 한 항목:
   ```python
   if "mem" in _seen_glyphs:
       legend += [("🧠", "dim"), (" mem worker   ", "dim")]
   ```
   (worktree `🚧 N` 항목 line 1590~1591 와 같은 조건부 패턴.)

   > 순수 mem-only 그룹은 fold 되어 header badge 가 안 뜰 수 있으므로, **전역 count 도 legend 에 노출**해 folded/mem-only 케이스에서도 존재가 보이게 한다. `n_mem_total` 을 활용:
   > ```python
   > if n_mem_total:
   >     legend += [("🧠 %d" % n_mem_total, "dim"), (" mem   ", "dim")]
   > ```
   > (위 2안 중 **전역 count 버전 하나만** 채택 — group badge 와 중복 방지. group badge(🧠N)는 활성 그룹 컨텍스트, legend 는 board 전역 총계로 역할 분리. 둘 다 유지하되 legend 는 전역 총계 버전으로.)

### Step 1.5 — `render.py`: `a` 토글 시 dim `mem` row 노출

`_SHOW_ALL`(=`a` 키 토글, line 1888~1889) 이면 mem 워커가 Step 1.3-2 필터를 통과해 `shown`(line 1343)에 포함된다. 세션 emit 루프(line 1499 `for s in _sort_group_sessions(shown):`)에서 mem 워커를 **전용 dim row** 로 라우팅 — 3개 레이아웃 세션 렌더러(`_session_row`/`_2line`/`_stack`)에 mem 인지 로직을 심는 대신, 루프 초입에서 분기:

```python
        for s in _sort_group_sessions(shown):
            if getattr(s, "mem_worker", False):
                lines.extend(_mem_row(s, layout))   # dim, 라벨 'mem'
                _seen_glyphs.add("mem")
                continue
            ...  # 기존 경로
```

신규 헬퍼 `_mem_row(s, layout)` (grouping assembler 근처, 예: line 1084 부근 정의):

```python
def _mem_row(s, layout="wide"):
    """F-18b: mem-worker 세션의 dim 1-line — 기본 숨김, `a` 토글 시만. 라벨 'mem'."""
    name = _clip_w(s.title or s.slug or (s.harness or "?"), 40)
    seg = [("  🧠 ", "dim"), ("mem ", "dim"),
           (name, "dim"), ("  ", None),
           ((s.harness or "—"), "dim"), ("  ", None),
           (fmt_min(s.elapsed_min), "dim")]
    return [seg]
```

- 전 스타일 `"dim"` — 활성 row 와 확실히 구분. tint/bold 미적용(`_sess_bold_ids` 에 넣지 않음 — mem 루프는 `continue` 로 그 블록을 건너뜀).
- `_mem_row` 는 `_srow`(None=wide)와 무관하게 항상 1-line 반환 (레이아웃별 분기 불요 — dim 요약이라 단순 유지). layout 파라미터는 향후 narrow 조정 여지로만 받아둠.

---

## Phase 2 — F-18a: drill runner 이중 표시 dedup

**목표**: 같은 drill 실행이 (i) proc-scan drill loop job(`key="drill"`, source="proc")과 (ii) lib-runner 가 `jobs.log` 에 쓴 registry row(slug=`drill-<adapter>-<case>-<ts>-<pid>`, source="jobs")로 **두 번** 뜬다. slug 불일치로 기존 dedup(동일 slug / F-15c cwd+stem)이 안 걸림. **registry row 를 정본으로 1행 병합, proc 는 liveness/pid 소스로 흡수.**

병합 지점: **`dispatch.collect()`** (line 822~883) — proc_jobs·log_jobs 를 이미 합치고 liveness 를 계산하는 유일한 seam. 신규 헬퍼 `_reconcile_drill_rows(jobs)` 를 liveness 루프(line 872~873) **뒤**에 1회 적용.

### 근거 사실 (코드 실측)

- registry slug 포맷: `loops/lib-runner.sh:70 _loop_registry_slug()` → `raw="drill-$adapter-$case_id-$(date -u +%Y%m%d%H%M%S)-$$"`, `[^A-Za-z0-9_.-]→-` 정규화. 즉 **`drill-<adapter>-<case>-<14자리 ts>-<pid>`**, adapter∈{claude,codex,opencode} 소문자, case 는 `[A-Za-z0-9_.-]`(예 `g_stage_dispatch`, `g10_claude_opencode_depth2_start`).
- registry worktree(col 4=cwd): `run_case_on_adapter` 의 `$repo` = `$WORK/repo` = **`/tmp/drill-<case>-<rand>/repo`** (`run.sh:135 mktemp -d "/tmp/drill-$c-XXXX"`). open→done 둘 다 이 경로. done 은 `_scan_jobs_log` 에서 status 필터로 제외 → registry row 는 **open/running 중(=proc 살아있을 때)만** 표시.
- proc drill loop job: `dispatch._scan_processes()` 의 `elif loop:` 분기(line 680~712) → `key="drill"`, `capability_owner="drill"`, `slug=current_case or "drill"`, `worker_role=current_case`, source="proc".
- 선례: `model.project_of` drill 정규식 `drill-(.+)-[^-/]+$`(line 102) 가 cwd 컴포넌트 case 추출 선례. `_norm_cwd`(realpath, line 543)·F-15c `seen_keys` 가 proc↔registry 정합 선례.

### Step 2.1 — `dispatch.py`: drill case 추출 헬퍼 2종

`tools/fleet/collectors/dispatch.py` 상단 정규식군(line 28~42) 근처에 추가:

```python
_DRILL_SLUG_RE = re.compile(r"^drill-[a-z]+-(.+)-\d{14}-\d+$")   # registry slug → case
_DRILL_CWD_COMP_RE = re.compile(r"^drill-(.+)-[^-]+$")           # /tmp/drill-<case>-<rand> 컴포넌트 → case (project_of 선례)


def _drill_case_from_slug(slug):
    """registry slug 'drill-<adapter>-<case>-<ts>-<pid>' → case (없으면 None)."""
    m = _DRILL_SLUG_RE.match(slug or "")
    return m.group(1) if m else None


def _drill_case_from_cwd(cwd):
    """cwd 경로 컴포넌트 중 '/tmp/drill-<case>-<rand>' 의 case (없으면 None)."""
    for comp in (cwd or "").split("/"):
        if comp.startswith("drill-"):
            m = _DRILL_CWD_COMP_RE.match(comp)
            if m:
                return m.group(1)
    return None
```

- ts 는 정확히 14자리(`%Y%m%d%H%M%S`)라 greedy `(.+)` 가 case 를 안전히 흡수하고 `-\d{14}-\d+$` 가 ts+pid 를 앵커. case 내부 언더스코어/하이픈 보존.
- cwd 컴포넌트: mktemp 의 `-XXXX` 는 하이픈 없는 alnum → `-[^-]+$` 가 rand, `(.+)` 가 case.

### Step 2.2 — `dispatch.py`: registry 정본 병합 pass

`collect()` 의 liveness 루프(line 871~873) **직후**, F-15c(a) 재도출(line 878~) **앞**에 삽입:

```python
    jobs = _reconcile_drill_rows(jobs)
```

신규 헬퍼(`collect` 앞에 정의):

```python
def _reconcile_drill_rows(jobs):
    """F-18a: 같은 drill 실행의 registry row(정본)와 proc loop job(중복)을 1행으로.

    match = registry slug 의 case명 == proc drill job 의 case명, 그리고 registry cwd 가
    '/tmp/drill-<case>-' 임(cwd 상관). 병합 시 registry row 를 남기고 proc 의 pid·liveness 를
    흡수(live proc = ground truth), proc row 는 제거. registry 무write.
    """
    # registry drill rows: source=jobs & slug 이 drill 패턴 & cwd 가 /tmp/drill-<case>-
    reg_by_case = {}
    for r in jobs:
        if r.source != "jobs":
            continue
        case = _drill_case_from_slug(r.slug)
        if not case:
            continue
        if _drill_case_from_cwd(r.cwd) != case:      # cwd 상관 가드 (/tmp/drill-<case>- 확인)
            continue
        reg_by_case.setdefault(case, r)              # 첫 registry row 정본
    if not reg_by_case:
        return jobs
    drop = set()
    for p in jobs:
        if p.source != "proc" or p.key != "drill":
            continue
        case = _drill_case_from_cwd(p.cwd) or p.worker_role or (p.slug if p.slug != "drill" else None)
        r = reg_by_case.get(case)
        if r is None:
            continue
        # registry 정본에 proc 의 liveness/pid 흡수
        if r.pid is None:
            r.pid = p.pid
        if r.elapsed_min is None:
            r.elapsed_min = p.elapsed_min
        if p.liveness in ("working", "idle") and r.liveness in ("queued", "stale", "dead", "unknown"):
            r.liveness = p.liveness                  # live proc = ground truth
        drop.add(id(p))
    if not drop:
        return jobs
    return [j for j in jobs if id(j) not in drop]
```

- **정본=registry**, proc 흡수·제거 → 1행. registry slug(`drill-<adapter>-<case>-<ts>-<pid>`)는 렌더 시 기존 `_compact_dispatch_name`/`_ALERT_TAIL`(line 1255)이 `-<ts>-<pid>` 꼬리를 이미 정리하므로 표시명 깨끗.
- **cwd 상관 가드**: `_drill_case_from_cwd(r.cwd) == case` 로 registry row 가 진짜 `/tmp/drill-<case>-` 실행임을 확인 → 동명 case 의 무관한 registry-only 행 오병합 방지 (F-15c "both must match" 보수성 계승).
- **proc case 도출 fallback**: proc loop job 의 cwd 가 `/tmp/drill-*` 가 아닐 수도 있어(runner 프로세스는 launch cwd) `worker_role`(=current_case)·`slug` 로 폴백. 정합 실패(case None/미스매치) 시 **병합 안 하고 양쪽 유지**(무해 — 현행과 동일 표시).
- **liveness 흡수**: proc 가 live(working/idle)인데 registry 가 terminal/stale/queued 로 계산됐으면 live 신호 채택. 그 외엔 registry 자체 transcript liveness 유지.
- registry **무write** — 메모리 객체만 수정.

---

## 검증 계획

### V1. 신규 unit test — `tools/fleet/tests/test_f18_attribution.py`

기존 hermetic 패턴(test_f15_rows.py: `mock`/`tempfile`, sys.path 삽입) 답습. no live proc, environ/`_ps_lines`/`_scan_jobs_log` 는 monkeypatch.

**F-18b (procscan 태깅)**
- `read_environ` monkeypatch 로 `{"MEM_DISTILL":"1"}` → `scan()` Session `mem_worker is True`.
- `{"FLEET_TITLE_REFRESH":"1"}` → True. 마커 없음 → False.
- `read_environ`={} (권한 실패 모사) → mem_worker False (degrade).

**F-18b (render 제외·요약·토글)**
- mem_worker Session 1 + 일반 working Session 1 을 `_build_lines` 에 → 기본: pulse working 카운트에 mem 미포함, mem row 미출력, legend/그룹 header 에 `🧠` 등장.
- `set_show_all(True)` 후 → mem row(`mem` 라벨·dim) 등장.
- 순수 mem-only 그룹 → 기본 fold(그룹 row 미생성), legend `🧠 N` 전역 count 노출.

**F-18a (case 추출)**
- `_drill_case_from_slug("drill-claude-g_stage_dispatch-20260711160000-12345") == "g_stage_dispatch"`.
- `_drill_case_from_cwd("/tmp/drill-g_stage_dispatch-Ab3d/repo") == "g_stage_dispatch"`.
- 비-drill slug/cwd → None.

**F-18a (병합)**
- registry DispatchJob(source="jobs", slug="drill-claude-CASE-<ts>-<pid>", cwd="/tmp/drill-CASE-x/repo", pid=None) + proc DispatchJob(source="proc", key="drill", worker_role="CASE", cwd="/tmp/drill-CASE-x/repo", pid=999, liveness="working") → `_reconcile_drill_rows` 결과: **1행**(registry), `pid==999`, `liveness=="working"`, proc row 제거.
- case 미스매치(다른 CASE) → 2행 유지(병합 안 함).
- registry cwd 가 `/tmp/drill-` 아님 → 병합 안 함(가드).

### V2. 기존 회귀

```
cd tools && python3 -m unittest fleet.tests.test_f15_rows fleet.tests.test_f17_title_refresh \
    fleet.tests.test_dispatch fleet.tests.test_f14_title -v
```
- 전부 PASS 유지 (F-14~F-17 계약 불변 확인).

### V3. drill assert 임포트 무결성 (g9/g10/g_stage_dispatch)

```
cd tools && python3 -c "import fleet.collectors.dispatch as d; \
    print(d._drill_case_from_slug, d._reconcile_drill_rows, d.collect)"
```
- `fleet.collectors.dispatch` 임포트·기존 심볼 시그니처 불변 확인 (drill g9/g10 assert 가 이 모듈을 파이썬 임포트).

### V4. `--json` additive 확인

```
python3 -m fleet.fleet --json | python3 -c "import sys,json; d=json.load(sys.stdin); \
    assert 'mem_worker' in d['sessions'][0] if d['sessions'] else True; print('ok')"
```
- Session 에 `mem_worker` key 추가(additive), 기존 key 불변. 라이브 환경에 drill/mem 워커 있으면 육안으로 1행·제외 확인.

### V5. 스모크 — 렌더 크래시 없음

```
python3 -m fleet.fleet --once            # 기본 (mem 제외, 🧠 요약)
python3 -m fleet.fleet --once --all      # a-토글 동치 (mem dim row 노출)
```
- 모듈 레벨 `curses.A_*` 미참조(폴백 사용) 재확인 — no-curses 임포트로 `--json`/`--once` 정상.

---

## 리스크·degrade 요약

| 리스크 | 완화 |
|---|---|
| environ 판독 권한 실패/race | `read_environ`→`{}`→`mem_worker=False`→현행 표시(무해 degrade). 오귀속 차단이 1차 목적이라 안전 fallback. |
| Windows(_scan_disk) 마커 판독 불가 | default False 유지, 태깅 미적용 명시 — import 경로·기능 회귀 없음. |
| drill proc cwd 가 `/tmp/drill-*` 아님(runner launch cwd) | proc case 를 `worker_role`/`slug` 로 폴백; 정합 실패 시 병합 안 하고 양쪽 유지(현행 동일). |
| 동명 case 동시 2런 | registry cwd `/tmp/drill-<case>-<rand>` 가 런별 고유 → cwd 상관 가드로 분리(현재 case-name-primary 매칭은 첫 registry 정본에 병합; 동시 2런 완전 분리가 필요하면 executor 가 tmp-root 컴포넌트까지 키에 포함 — test V1 에 케이스 추가 여지). |
| registry 정본 slug 노이즈(`-<ts>-<pid>`) | 렌더 `_ALERT_TAIL`/`_compact_dispatch_name` 이 기존에 꼬리 정리. |

---

## 편집 파일 요약

1. `tools/fleet/model.py` — `Session.mem_worker: bool = False` 1필드 (additive).
2. `tools/fleet/collectors/procscan.py` — `scan()` environ 마커 태깅(기존 `read_environ` 재사용), `_scan_disk` nt 미적용 주석.
3. `tools/fleet/collectors/dispatch.py` — `_DRILL_SLUG_RE`/`_DRILL_CWD_COMP_RE`·`_drill_case_from_slug`/`_drill_case_from_cwd`·`_reconcile_drill_rows` 신규 + `collect()` 1줄 호출.
4. `tools/fleet/render.py` — `_build_lines` mem 제외·`🧠N` badge·legend·`_mem_row` 헬퍼·`a`-토글 분기.
5. `tools/fleet/tests/test_f18_attribution.py` — 신규 테스트.
