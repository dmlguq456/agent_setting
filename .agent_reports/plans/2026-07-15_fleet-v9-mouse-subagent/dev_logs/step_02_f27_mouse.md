# Step 2 — F-27 마우스 1급 재설계

## 변경 (render.py)
- 상태: `_CLICK_ROWS`(screen_y → `_SELECTABLE` entry), `_PROMPT_HITS`(`[(row,x0,x1,"kill"|"cancel")]`) 신설. `_TOGGLE_ROWS`와 같은 지점(`_draw` 최상단)에서 리셋(§4.1 패턴).
- `_click_target_excluded(e)`: rung 3 클릭 시점 1회 `control.is_excluded()` 적용(§4.2.1). `_draw`는 절대 호출하지 않음.
- `_draw`: 행 렌더 루프에서 `line_idx = _OFFSET+row`가 `_SELECTABLE`(★ `_live_targets()` 아님)의 `line`과 일치하면 `_CLICK_ROWS[row]=entry`. 푸터 렌더 후 `_prompt_hit_boxes()`로 `_PROMPT_HITS` 재구축(프롬프트 없으면 빈 리스트 — 매 draw 재계산).
- `_getmouse_xy()`: `curses.getmouse()`를 `(mx,my)` 또는 `(None,None)` 매칭 쌍으로 정규화 — 🟡5 `mx` unbound 크래시 방지.
- `_handle_mouse(mx,my)`: curses-free 순수 함수, rung 1(프롬프트 히트박스만) → rung 2(`_TOGGLE_ROWS`) → rung 3(`_CLICK_ROWS`: 재클릭=kill 요청/다른 행=이동, 신규 선택도 동일 분기) → rung 4(해제). kill/cancel 버튼은 `control.kill_target`을 직접 부르지 않고 `_handle_prompt_key(ord("y"/"Y"/ESC))`를 재생 — 키보드와 단일 경로 공유(§4.1).
- `_prompt_button_segs`/`_prompt_variants`/`_prompt_hit_boxes`: `[cancel] [kill]`(confirm) / `[KILL] [cancel]`(confirm2·escalate, 좌표 반전 §4.4) 버튼 세그먼트. `_prompt_variants`가 "버튼 포함 rung" 다음에 "같은 텍스트, 버튼 없는 rung"을 끼워 넣어 — 버튼이 안 들어가도 이름(텍스트)을 먼저 보존(§4.5, 키보드 우선). 마지막 rung은 항상 버튼 포함(폭 보장). 히트박스는 `[0,w)` 교집합 + 부분 클리핑 버튼 미등록.
- `_loop`: `KEY_MOUSE` 분기를 `_handle_mouse` 호출로 교체. **`_PROMPT is not None` 블록 내부**(§4.4.1 규범 — `_handle_prompt_key`와 나란히)와 base-mode 블록 양쪽에서 `_getmouse_xy()`→`_handle_mouse()` 호출, 두 경로 모두 다음 `getch` 전에 `_draw`를 거침(불변식 충족).
- `_footer_segs`: 폭 ≥100일 때만 "click row ·" 힌트 1개 추가(R2-3 opt-in 원칙, 키보드 힌트 우선순위 불변).

## 검증
```
python3 -m unittest discover -s tools/fleet/tests -q
→ Ran 437 tests. FAILED(failures=1) — 유일한 실패는 test_mirror_parity(render.py + 신규 tests/test_f27_mouse.py 미러 드리프트, Step 6에서 rsync). 그 외 436건 OK, 신규 실패 0.

python3 -m unittest tools.fleet.tests.test_f27_control -v   → Ran 82 tests, OK (마우스 추가가 기존 F-27 안전 계약을 우회하지 않음)
python3 -m unittest tools.fleet.tests.test_f27_mouse -v     → Ran 21 tests, OK (신규 MouseSelectionTest×10, MousePromptTest×10, NoAutomaticControlTest×1)

for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once; done   → 3폭 정상 렌더
python3 tools/fleet/fleet.py --json > /tmp/v9_step2.json && python3 -c "...len(d['sessions'])"   → json ok 8

폭 오버플로 실측(참고 지표, awk length): 60→16 120→1 168→8.
git stash로 Step 2 이전 상태와 대조: 60→16(동일) 120→0 168→7 — 동일 코드로 재측정 시 168은 7건으로 일치(라이브 세션 목록이 두 실행 사이 변동해 1건 차이 발생, 실제 오버플로 라인 내용은 Step 2 전/후 바이트 단위로 동일함을 직접 diff로 확인). 즉 **Step 2가 신규 오버플로를 만들지 않았다** — 기존 7건은 전부 dispatch-stage breadcrumb 폭 초과(D3, Step 4 스코프)이며 프롬프트 푸터(--once에서는 그려지지 않음)와 무관.
```

## 디자인팀 critic
`/tmp/v9_step2_{60,120,168}.txt`에 프롬프트 푸터 텍스트 프리뷰(--once로는 그려지지 않으므로 `_prompt_segs` 직접 호출로 부록) 첨부 후 critic 요청. 결과는 `_internal/dev_reviews/design_critic_step2.md`에 별도 기록.

## acceptance
- A2-1~A2-6: `test_f27_mouse.py` 20건 + 기존 `test_f27_control.py` 82건으로 고정. A2-6(스크롤 회귀)은 Step 5에서 최종 판정(§1.1/§7.1 합의대로).
- A2-5 안전계약 표: exact pid 재검증(`test_second_click_does_not_reach_kill_target`) · 이중확인(`test_working_session_click_needs_second_confirm`) · 자동제어0(`NoAutomaticControlTest`, grep 가드) · action log/registry는 기존 `test_f27_control` 스위트 무변경 재사용.

## 안전 규칙 준수 (§0)
실세션 스폰·시그널 0. `curses.getmouse`/`doupdate`는 전부 `mock.patch`, kill 경로는 `control.kill_target`/`render._do_kill` mock 스파이로 검증. 실 프로세스·실 시그널 없음.
