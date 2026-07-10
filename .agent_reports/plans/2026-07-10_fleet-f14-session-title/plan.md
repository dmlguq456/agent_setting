# F-14 구현 계획 — 세션 표시명 = 하네스 세션 제목 (표시층 전용)

- **사이클**: 2026-07-10 fleet-f14-session-title
- **스코프**: 표시층 전용. 식별자(`Session.slug`) 불변 · 매칭/정렬/그룹핑/nesting 로직 무접촉 · collector 필드 **순수 additive** (`Session.title` 신설).
- **근거 문서**: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.6 F-14 (prd.md:173–177), §5.
- **소스 계약 실측 결과** (본 계획 작성 중 확인 — execute 는 재검):
  - claude: `~/.claude/projects/<enc-cwd>/<sid>.jsonl` 안 `{"type":"ai-title","aiTitle":"…","sessionId":"…"}` 라인 실존 확인. 파일당 **여러 번** append 되며 값은 최신이 뒤. 라인의 `sessionId` 는 파일명 sid 와 **다를 수 있음**(resume/fork 시 원본 sid 유지) → sessionId 매칭으로 거르지 말고 **마지막 라인** 채택 (spec 지침과 일치).
  - opencode: `session` 테이블에 `title` 컬럼 존재(정식). 현행 `_query` 는 title 미포함.
  - codex: rollout `session_meta`(line 1) payload keys = `session_id,id,timestamp,cwd,originator,cli_version,source,thread_source,model_provider,base_instructions,git` — **제목성 필드 없음**. 본문의 `"name"`/`"summary"` 는 function-call/컨텐츠 잔여물이지 세션 제목 아님. → **현행 유지(title=None)**, F-3 결손 비대칭 동형.

---

## 1. 설계 요지 (한 문장)

collector 3종이 `Session.title`(Optional[str], 기본 None)을 채우고, render 의 **name zone 표시 지점 두 곳**(`_session_row`·`_session_row_2line`)에서만 `s.title or slug` 로 소비한다. slug 는 그대로 두고, 폭 자름은 **display-width(한글 2셀) 인지 tail-cut**(head 보존)로 한다. 그 외 모든 slug 참조(alert·legend·folded·매칭·정렬)는 무접촉.

---

## 2. 파일별 변경 지점

### 2.1 `tools/fleet/model.py` — Session 필드 신설 (additive)

- **위치**: `Session` dataclass, `slug` 필드 바로 아래 (model.py:132 부근).
- **변경**: 
  ```python
  title: Optional[str] = None   # harness 세션 제목(ai-title/DB title) — render name zone 전용, slug 대체표시. None → slug fallback
  ```
- **파급**: `to_dict()`=`asdict(self)` 이므로 `--json` 에 `title` 키가 **자동 additive** 노출 (별도 코드 없음). slug 값·의미 불변 → 불변식 #6 충족.
- **주의**: 필드 **추가만**. 기존 필드 순서·이름·기본값 변경 금지 (demo fixtures·테스트가 positional 아닌 keyword 로 생성하므로 추가는 안전).

### 2.2 `tools/fleet/collectors/claude.py` — ai-title tail 추출

- **위치**: `enrich()` (claude.py:101–135). transcript 경로는 이미 `_newest_transcript_mtime` 이 알고 있으나 mtime 만 반환 → **경로를 얻는 헬퍼가 필요**.
- **변경**:
  1. `_newest_transcript_path(home, cwd, sid)` 헬퍼 신설 — 현행 `_newest_transcript_mtime` 의 경로 선택 로직(우선 `<sid>.jsonl`, 없으면 proj dir 최신 jsonl)을 그대로 재사용/공유. mtime 헬퍼는 이 경로 헬퍼 위에 얹어 **중복 os 호출 최소화**(같은 경로를 두 번 stat 하지 않도록, `enrich` 에서 경로 1회 산출 후 mtime·title 둘 다 그 경로로).
  2. `_tail_ai_title(path, chunk=8192)` 헬퍼 신설 — codex.py `_tail_token_count`(codex.py:101) 패턴 차용:
     - `os.path.getsize` → `seek(max(0, sz-chunk))` → `read().decode("utf-8","replace")` → `splitlines()`; `start>0` 이면 첫 부분 라인 버림.
     - 뒤에서부터(또는 전체 스캔 후 last) `'"ai-title"' in ln` 인 마지막 라인 채택.
     - tolerant 파싱: `json.loads(ln)` 실패 시 무해 skip; 성공 시 `d.get("aiTitle")`. (regex fallback 은 선택 — json 실패가 드물어 우선 json-only, 필요 시 `re.search(r'"aiTitle"\s*:\s*"((?:[^"\\]|\\.)*)"', ln)` 추가.)
     - 값 정제: `strip()`; falsy 면 None; **무의미 기본 제목 거르기** — `^New session\b` 또는 ISO-only 패턴이면 None 반환(fallback). 
  3. `enrich()` 말미(§ liveness mtime 계산부, claude.py:129 부근)에서 경로가 있으면 `t = _tail_ai_title(path)`; `if t: sess.title = t`. 경로 부재(headless -p 자식 등)·추출 실패 → `sess.title` None 유지.
- **비용**: liveness 가 이미 같은 transcript 를 stat. tail 8KB read 1회 추가뿐 → tick 부담 미미(spec §4.6 비용 항목과 일치). 필요 시 후속 최적화로 mtime-키 캐시 여지만 주석에 남김(이번엔 미구현 — YAGNI).
- **headless 자식**: `is_child`(=-p) 세션은 transcript 에 ai-title 없음 → title None → slug 유지. 별도 분기 불필요(자연 fallback).

### 2.3 `tools/fleet/collectors/opencode.py` — DB title 컬럼 (tolerant)

- **위치**: `enrich()` (opencode.py:108–158). 현행 `_query`/`_COLS`(opencode.py:19) 는 title 미포함.
- **권장 방식 (기존 쿼리 무접촉, tolerant)**: 메인 `_query` 는 **그대로** 두고, row 확보 후 `sid` 로 title 만 별도 방어 조회:
  ```python
  if sid:
      try:
          tr = con.execute("SELECT title FROM session WHERE id=? LIMIT 1", (sid,)).fetchone()
          if tr and tr[0] and str(tr[0]).strip():
              sess.title = str(tr[0]).strip()
      except Exception:
          pass   # 구버전 DB에 title 컬럼 없음 → title None (tolerant, F-3)
  ```
  - 이 조회는 `con` 이 열려있는 try 블록 안(opencode.py:114–120)에서, 기존 `last_ctx` 계산 근처에 배치. `id` 는 PK라 비용 무시.
  - **대안(비권장)**: `_COLS` 에 `title` 추가 → 구버전 DB/테스트 fixture 스키마에서 `no such column` 로 전체 enrich 실패 위험. 방어 별도 조회가 회귀 안전.
- **무의미 제목 필터**: opencode title 도 동일하게 빈값/whitespace 만 거름(“New session” 류는 opencode엔 없음 — claude 전용).

### 2.4 `tools/fleet/collectors/codex.py` — 현행 유지 + 실측 절차 명시

- **변경 없음** (title None 유지). 
- **execute 단계 실측 절차**(본 계획이 명시, 실 확인은 execute):
  ```sh
  f=$(ls -t ~/.codex/sessions/*/*/*/rollout-*.jsonl | head -1)
  head -1 "$f" | python3 -c "import json,sys;print(list(json.loads(sys.stdin.read())['payload'].keys()))"
  grep -oh '"[a-z_]*title[a-z_]*"' "$f" | sort | uniq -c
  ```
  - 계획 작성 중 실측 결과 = 제목 필드 부재. execute 는 재확인 후 **없으면 codex.py 무변경**, 있으면 tail 파싱 추가(claude 패턴 재사용). 있다 해도 additive(`sess.title`)만.

### 2.5 `tools/fleet/render.py` — name zone 두 지점 + display-width tail-cut 헬퍼

- **신설 헬퍼** (기존 `_dw`(render.py:1561)/`_cw`(render.py:~1550) 위에 얹음):
  ```python
  def _clip_w(s, maxw, ellipsis="…"):
      """문자열을 display width maxw 이하로 tail-cut(head 보존). 한글 등 2셀 문자는
      셀 경계에서 안전하게 멈춤(반셀 절단 없음). 잘리면 끝에 … (width 1)."""
      s = s or ""
      if _dw(s) <= maxw:
          return s
      lim = maxw - (_cw(ellipsis) if ellipsis else 0)   # =maxw-1
      out, w = [], 0
      for ch in s:
          cw = _cw(ch)
          if w + cw > lim:
              break
          out.append(ch); w += cw
      return "".join(out) + (ellipsis if ellipsis else "")
  ```
  - 순수 head-preserving tail-cut(F-9). ellipsis 는 dispatch 이름(`_compact_dispatch_name`, render.py:713)과 일관. maxw≤1 등 극단은 방어(빈 문자열 반환 경로).

- **지점 A — `_session_row` (1-line, render.py:642–657)**: 현행
  ```python
  slug_show = slug[: min(len(slug), _NW_S - 1)]
  segs.append((slug_show, name_key)); used += len(slug_show)
  ```
  →
  ```python
  name_txt = s.title or slug
  shown = _clip_w(name_txt, _NW_S - 1)
  segs.append((shown, name_key)); used += _dw(shown)   # ← char 수 아닌 display width
  ```
  - **핵심**: `used` 를 `len` → `_dw` 로 교체 (불변식 #4). 이후 `▾N`·gate tag 예산 검사(`used + 3 <= _NW_S`, `used + len(gtag) <= _NW_S`)와 최종 패딩(`" " * (_NW_S - used)`)이 **display width 기준**으로 정합 → 한글 title 이어도 branch 컬럼 정렬 유지. (▾N·gtag 는 ASCII라 `len`==`_dw`, 그대로 둠.)
  - `slug` 지역변수(render.py:625)는 **그대로 유지** — name zone 외 미사용이나, 다른 유지보수자 혼동 방지 위해 `slug` 계산 라인은 건드리지 않고 `name_txt` 만 신설.

- **지점 B — `_session_row_2line` (2-line, render.py:896)**: 현행
  ```python
  l1 = [..., (_pad(hn, _HW), hkey), (slug, name_key)]
  ```
  → `(slug, name_key)` 를 `(_clip_w(s.title or slug, _NAME2_MAX), name_key)` 로. 
  - 2-line 은 고정 branch 컬럼이 없어(뒤에 `"  "+br` 이어짐) title 이 길면 branch 를 밀어 draw `lim` 에서 잘림 → **완만한 상한** `_NAME2_MAX`(신설 상수, 권장 40셀) 로 tail-cut. slug-only 현행도 길면 그대로 흘렀으나, title(한글) 대비 상한 도입이 카드 붕괴 방지. **display 결정** — execute 는 이 상수값을 커밋 전 노출.
  - stack/narrow 변형(`_session_row_stack`·`_stack_split`)은 `_session_row_2line` 을 재사용하므로 **자동 반영**, 별도 변경 없음.

- **비접촉 확인(render.py 내 slug 다른 소비처 — 전부 유지)**:
  - alert 행(`_alert_*`, render.py:1156–1160): job/slug 기반 compact — **title 미사용** (불변식 #3).
  - folded/집계·legend·section title(render.py:1300+): slug/registry 교차참조 — 무접촉.
  - 매칭·nesting·정렬·main-bold(sid)·▾N 카운트: title 을 키로 쓰는 코드 **신설 안 함** (불변식 #2). title 은 오직 위 A·B 두 세그먼트에서만 읽음.

---

## 3. 단계별 구현 순서 (execute 용)

1. **model.py**: `Session.title` 필드 추가. (`--json` 스모크: `python -m fleet --json | python -c "import json,sys;print('title' in json.load(sys.stdin)['sessions'][0])"` — 세션 있을 때 True.)
2. **render.py**: `_clip_w` 헬퍼 추가 → 지점 A(`used` 를 `_dw` 로) → 지점 B(`_NAME2_MAX`). demo 렌더 확인: `FLEET_DEMO=1 python -m fleet --once`.
3. **collectors/claude.py**: `_newest_transcript_path` + `_tail_ai_title` + `enrich` 연결. 실 세션에서 `--json` 에 title 채워지는지 확인.
4. **collectors/opencode.py**: 방어적 title 조회 추가.
5. **collectors/codex.py**: 실측 절차 재확인 → 결과 따라 무변경(예상) 또는 additive 파싱.
6. **테스트**: §5 회귀·신규 케이스 추가.
7. 한글 title 폭 정렬 육안 검증(§4 #4).

---

## 4. 표시-전용 불변식 검증 체크리스트 (7개 — code-test 가 확인)

| # | 불변식 | 검증 방법 | 기대 |
|---|---|---|---|
| 1 | `Session.slug` 덮어쓰기 금지, title 은 신규 필드 | `grep -n 'sess.slug\s*=' collectors/*.py` — claude(native name), opencode(slug col) 기존 2곳 **외 신규 없음**. title 대입만 추가. | slug 대입 지점 불변, `sess.title=` 신설만 |
| 2 | 매칭·nesting·그룹핑·정렬·main-bold·▾N·fold = title 무접촉 | `grep -rn '\.title' render.py collectors/dispatch.py collectors/procscan.py` → 소비처가 **render name zone 2곳뿐**. `project_of`/liveness rank/recency/sid-bold 로직에 title 부재 확인. | title 참조 = render A·B 만 |
| 3 | alert 행·legend·folded 집계 = slug 유지 | `_alert_*`/legend/section 빌더에 `.title` 미등장 (grep). demo 에서 alert 행이 slug/compact 로 렌더. | alert/legend 에 제목 안 뜸 |
| 4 | 한글 double-width 폭 안전 | 한글 title fixture 로 1-line 렌더 → branch 컬럼 정렬 유지. `_clip_w` 단위테스트: `_dw(_clip_w("한글가나다라마바사", 6)) <= 6` 이고 반셀 절단 없음. `used` 가 `_dw` 인지 코드 확인. | 정렬 깨짐 없음·경계 안전 |
| 5 | slug 표시 단정 테스트: 제목 有/無 분리 커버 | §5 신규 테스트 — title None → slug 표시, title 有 → title 표시. | 두 케이스 통과 |
| 6 | collector·--json = additive only | `--json` 스키마에 slug 불변 + title 키 추가만. g9/g10 assert.sh(=`fleet.collectors.dispatch` 의 `DispatchJob.slug` 단정)는 Session.title 무관 → 영향 0. collector 필드 이름/의미 불변. | slug 값에 제목 안 섞임 |
| 7 | jobs.log·statusline·registry write 0 | `grep -rn 'open(.*w\|\.write(\|jobs.log\|statusline' 변경 diff` → 신규 write 없음(전부 read-only enrich). | 표시층 전용 |

---

## 5. 테스트 계획

- **신규 단위테스트** (`tests/` — test_dispatch.py 또는 신설 `test_f14_title.py`):
  1. `test_clip_w_ascii_tailcut`: `_clip_w("abcdefgh", 5)` → head 보존 + `…`, `_dw(result) <= 5`.
  2. `test_clip_w_hangul_boundary`: 한글 혼합 → `_dw(result) <= maxw`, 반셀 절단 없음(마지막 문자 온전).
  3. `test_session_row_title_present`: `Session(..., slug="repo-ab12cd34", title="개발 서버 시작")` → `_session_row` 세그먼트 name zone 에 title 텍스트 존재, slug 부재. `used`/padding 이 `_dw` 로 정렬(총 name zone 폭 == `_NW_S`).
  4. `test_session_row_title_absent`: title=None → name zone 에 slug 표시(현행 회귀 보전).
  5. `test_json_title_additive`: `Session(...).to_dict()` 에 `title` 키 존재 + slug 값 불변.
- **claude 추출 테스트**: 임시 `projects/<enc>/<sid>.jsonl` 에 ai-title 라인 여러 개 write → `_tail_ai_title` 이 **마지막** 값 반환. `"New session - 2026-..."` → None. 깨진 json 라인 섞여도 tolerant.
- **opencode 테스트**: 기존 DB fixture(test_dispatch.py:212 CREATE TABLE)에 **title 컬럼 있는 버전**과 **없는 버전** 둘 — 있으면 title 채움, 없으면 예외 삼키고 None(회귀 없음).
- **회귀 스위트**: `python -m pytest tests/ -q` (또는 `python -m unittest discover tests`) 전체 green. 특히 기존 slug 단정 테스트(test_dispatch.py 의 DispatchJob.slug 계열)는 **무변경 통과**여야 함(Session.title 은 별개 필드).
- **drill 회귀**: `~/.claude/loops/drill/cases_growing/g9*/g10*` 는 `DispatchJob.slug` API 단정 — Session.title 추가와 무관, 통과 예상. execute 후 1회 확인 권장.
- **육안**: `FLEET_DEMO=1 python -m fleet --once` + 실 세션에서 한글 title 이 name zone 에 뜨고 branch 정렬 유지.

---

## 6. 리스크·경계

- **stale mtime 캐시 미도입**: tick 당 tail read 1회는 저비용. 세션 다수(수십)여도 8KB read × N — 부담 미미. 후속 최적화 여지만 주석.
- **ai-title 포맷 버전 드리프트**: 공식 “내부 포맷·변경 가능” 입장 → json/필드 부재를 **전부 tolerant**(부재=None=slug fallback). 회귀 없음 원칙.
- **`_NAME2_MAX` 값**: display 결정 — execute 가 커밋 전 노출(권장 40셀, 카드 폭 대비 조정 가능).
- **비고정 sessionId**: ai-title 라인 sessionId ≠ 파일 sid 사례 확인됨 → sessionId 매칭 안 함, 파일=세션 단위이므로 마지막 라인 채택으로 충분.
