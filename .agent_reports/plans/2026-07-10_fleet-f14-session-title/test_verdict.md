전 항목 검증 완료. 최종 보고를 정리합니다.

---

# code-test 검증 보고 — fleet F-14 (세션 표시명 = 하네스 제목)

## Verdict: **GREEN** ✅

표시-전용 불변식 7개 전부 유지. 회귀 없음. 소스 편집 없음(read-only).

---

## 항목별 실측 증거

### (a) 테스트 스위트 — 전체 green
```
python3 -m unittest discover -s tests -p "test_*.py"
→ Ran 63 tests ... OK
```
신규 `test_f14_title.py` = **13 tests OK** (ClipW 3, SessionRowTitle 5, ToDict 2, TailAiTitle 4). `test_dispatch.py` opencode title 회귀 2건 추가(컬럼 有/無) 포함. 기존 slug 단정 테스트 무변경 통과.

### (b) 라이브 실측 — `fleet.py --json` (17 세션)
- **ai-title 보유 claude 세션 → title 채워짐, slug 불변**: `worklog-board :: 'Review autopilot pipe spec…'`, `2026_ICML_TF_Restormer :: 'Open HTML file in VSCode locally'` — slug ≠ title 확인.
- **opencode DB title**: `shiny-wizard :: 'ICML demo talk 흐름 정리…'` (한글) 정상.
- **headless/무-ai-title 세션 → title=None, slug 유지**: 14개 row (`fleet-session-title-ce`, `agent-setting-2d` 등).
- **크래시 0** — 부재/파싱실패 경로 무해.

### (c) render 회귀 — 무영향
- no-curses import 정상: `sys.modules['curses']=None; import fleet.render` → **OK, `_clip_w` present**.
- F-14 diff에 `curses.A_*` 신규 참조 **0** (기존 참조는 전부 런타임 color-init 함수 내부, 무접촉).
- `FLEET_DEMO=1 --once` → 정상 렌더, **exit=0**.

### (d) 외부 API 표면 회귀 — dispatch API 무손상
- **`collectors/dispatch.py` 무접촉** (F-14 diff에 미포함).
- g9/g10 assert가 단정하는 `DispatchJob` 필드(`slug,key,mode,depth,harness,worker_role,capability_owner,parent_sid,parent_slug,is_child`) + `dispatch.collect()` **전부 실재**.
- ⚠️ **주의(evidence caveat, 결함 아님)**: g9/g10 `assert.sh`는 `$WORK $T` 인자 — live 크로스-하네스 디스패치가 생성하는 워크디렉토리 fixture(repo·jobs.log·codex json transcript)를 요구해 standalone 실행 불가. 이는 depth-2 read-only 워커 범위 밖(depth 3+ 디스패치 금지)입니다. F-14가 표시층만 건드리고 `dispatch.py`를 무접촉이므로 g9/g10 regression risk = 0 — API 표면 실재 검증으로 대체 확인.

### (e) 7개 불변식 grep 감사
| # | 불변식 | 결과 |
|---|---|---|
| 1 | slug 덮어쓰기 신규 없음 | ✅ `sess.slug=` 기존 2곳뿐 (opencode.py:137, claude.py:162) |
| 2 | 매칭/정렬/nesting title 무접촉 | ✅ `.title` 소비 = render.py:646·900 (name zone 2곳)뿐 |
| 3 | alert/legend/folded = slug | ✅ 해당 문맥에 `.title` 미등장 |
| 4 | 한글 double-width 폭 안전 | ✅ `used += _dw(shown)` (render.py:648), (f) 참조 |
| 5 | title 有/無 분리 커버 | ✅ test_session_row_title_present/absent 통과 |
| 6 | --json additive | ✅ title 채워진 3 row 전부 slug≠title, `slug==title` 오염 0 |
| 7 | jobs.log/statusline write 0 | ✅ diff에 신규 `open(w)`/`.write(`/jobs.log/statusline 라인 0 |

전수 감사: `.title` 대입 = claude.py:186·opencode.py:123 / 소비 = render.py:646·900 뿐. 정렬·그룹·매칭 키로 title 사용 없음.

### (f) 한글 title 폭 정렬
- `_dw(_clip_w(s, N)) <= N` **AND 반셀 절단 없음** — 경계 N=1~20, 혼합/단일/빈문자 전 케이스 **True**.
- 긴 한글 title name_seg `_dw=27 <= _NW_S-1=27` — branch 컬럼 정렬 유지.
- 테스트 커버: `test_clip_w_hangul_boundary`, `test_session_row_name_zone_width_is_display_width_aligned`, `test_session_row_2line_title_clipped_to_name2_max` 모두 통과.

---

## 요약
- **변경 파일**(검증 대상, diff 확인만): model.py(+1), render.py(+`_clip_w`/`_NAME2_MAX`/name-zone 2곳), collectors/claude.py(`_tail_ai_title` tail-scan), collectors/opencode.py(방어적 title 조회), tests/ 2파일.
- **RED/AMBER 결함 없음.** `_NAME2_MAX=40` 커밋됨(계획 §6 권장값). 유일 caveat는 (d) 드릴 full-integration이 워크디렉토리 fixture 부재로 standalone 미실행 — API 표면 무손상으로 대체 검증, regression risk 0.
- 소스 편집·파일 산출 없음. merge·worktree 정리는 conductor 몫.
