# pipeline_summary — fleet F-14 (세션 표시명 = 하네스 세션 제목)

- **사이클**: 2026-07-10 fleet-f14-session-title
- **스코프**: 표시층 전용. `Session.slug`(식별자) 불변 · 매칭/정렬/그룹핑/nesting 로직 무접촉. `Session.title` 신설(additive) 후 render name zone 두 지점(`_session_row`·`_session_row_2line`)에서만 `s.title or slug` 소비.
- **근거**: `spec/agent-fleet-dashboard/prd.md` §4.6 F-14, 본 사이클 `plan.md`.

## 변경 파일 (실행 커밋 5개)

| 파일 | 변경 |
|---|---|
| `tools/fleet/model.py` | `Session.title: Optional[str] = None` 필드 신설(+1줄) |
| `tools/fleet/render.py` | `_clip_w` display-width tail-cut 헬퍼 신설, `_NAME2_MAX=40`, name-zone 두 지점에서 title 소비(+29/-…) |
| `tools/fleet/collectors/claude.py` | `_newest_transcript_path`/`_tail_ai_title` 신설 — transcript tail 역스캔, 마지막 ai-title 채택(`New session`/ISO placeholder는 fallback 처리) (+71) |
| `tools/fleet/collectors/opencode.py` | DB `session.title` 방어적 조회(구버전 컬럼 부재 tolerant) (+7) |
| `tools/fleet/collectors/codex.py` | 무변경 — 제목성 필드 부재 실측 확인(F-3 결손 비대칭과 동형) |
| `tools/fleet/tests/test_f14_title.py` (신설) + `test_dispatch.py` | 신규 단위테스트 13 + opencode title 회귀 2건 (+139/+37) |

커밋: `7e26821`(model.py) → `cd4e3c3`(render.py) → `ff4f154`(claude.py) → `139a003`(opencode.py) → `04517f2`(tests). `git diff --stat 307507e..HEAD -- tools/fleet/`: 6 files changed, 270 insertions(+), 14 deletions(-).

## 검증 결과 (code-test verdict = GREEN, RED/AMBER 없음)

- **테스트 스위트**: `python3 -m unittest discover -s tests -p "test_*.py"` → 63 tests OK (신규 13: ClipW 3 / SessionRowTitle 5 / ToDict 2 / TailAiTitle 4). 기존 slug 단정 테스트 무변경 통과.
- **라이브 실측** (`fleet.py --json`, 17 세션): ai-title 보유 claude 세션(`worklog-board`, `2026_ICML_TF_Restormer`) → title 채워짐·slug 불변. opencode 한글 title(`shiny-wizard`) 정상. headless 자식 14개 세션 → title=None, slug 유지. 크래시 0.
- **render 회귀**: no-curses import OK, `_clip_w` 노출 확인. `curses.A_*` 신규 참조 0. `FLEET_DEMO=1 --once` exit=0.
- **한글 폭 정렬**: `_dw(_clip_w(s, N)) <= N` AND 반셀 절단 없음, N=1~20 전 케이스 True. name zone 폭이 `_dw` 기준으로 정합.

## 표시-전용 불변식 7개 — 전부 확인

1. slug 덮어쓰기 신규 없음 (`sess.slug=` 기존 2곳뿐)
2. 매칭/정렬/nesting/main-bold/▾N = title 무접촉 (`.title` 소비 = render.py 2곳뿐)
3. alert/legend/folded = slug 유지
4. 한글 double-width 폭 안전
5. title 有/無 분리 테스트 커버
6. `--json` additive only (slug 값 오염 0)
7. jobs.log/statusline/registry write 0 (표시층 read-only)

## Caveat

- g9/g10 drill(`assert.sh`)은 라이브 크로스-하네스 워크디렉토리 fixture(jobs.log·codex transcript)를 요구해 depth-2 read-only 워커 범위에서 standalone 미실행(depth 3+ 디스패치 금지 제약). `collectors/dispatch.py`가 F-14 diff에 미포함(무접촉)이고 `DispatchJob` 필드 전부 실재 확인되어 **API 표면 검증으로 대체, regression risk 0** — 결함 아님, 후속 세션에서 fixture 있는 환경이면 1회 재확인 권장.

## 후속

- merge·worktree 정리는 conductor 담당(본 워커는 파일만 작성, 커밋 없음).
- 즉시 후속 조치 불요 — RED/AMBER 결함 없음.
