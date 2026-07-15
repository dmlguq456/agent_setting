# Step 5 — 스크롤 회귀 테스트 신설 (F-27 회귀 예산 0의 증명)

## 변경
신규 `tools/fleet/tests/test_scroll_regression.py` — Step 1이 추출한 `_handle_base_key`를 curses 없이 직접 호출해 회귀 예산 0을 실행 가능한 형태로 고정.

- `BaseModeScrollTest` (6): ↑↓/jk/PgUp/PgDn/Home·g/End·G/`a`/`w` 전부 base 모드에서 무변경 동작.
- `ScrollIsolationTest` (4, §7.1의 결정된 경계 그대로):
  1. `test_base_mode_keeps_arrow_keys_when_nothing_is_selected` — 회귀 예산 0의 **실제 범위**: 아무것도 선택하지 않은 사용자는 방향키 100% 유지.
  2. `test_select_mode_intentionally_takes_arrow_keys` — 선택 모드가 방향키를 **의도적으로** 커서에 쓴다(v8부터의 기존 계약, 침범 아님).
  3. `test_mouse_click_does_not_disturb_scroll_offset` — Step 2 마우스 클릭이 `_OFFSET`을 흔들지 않음.
  4. `test_prompt_does_not_leak_keys_to_scroll` — 프롬프트 처리 경로가 `_OFFSET`을 건드리지 않음.

## 검증
```
python3 -m unittest tools.fleet.tests.test_scroll_regression -v   → Ran 10 tests, OK
python3 -m unittest discover -s tools/fleet/tests -q               → Ran 468 tests. FAILED(failures=1) — 유일한 실패는 test_mirror_parity(신규 tests/test_scroll_regression.py 미러 드리프트, Step 6에서 rsync). 그 외 467건 OK, 신규 실패 0.
```

## acceptance
- A5-1: 6개 base 키 전부 고정, curses 없이 실행(hermetic) — `BaseModeScrollTest` 확인.
- A5-2: `ScrollIsolationTest` 4개가 §7.1의 결정된 경계를 고정 — (a) 아무것도 선택 안 된 base 모드는 방향키 100% 유지 (b) 선택 모드는 방향키를 의도적으로 커서에 씀(침범 아님, v8부터의 계약) (c) 마우스 클릭이 `_OFFSET`을 흔들지 않음 (d) 프롬프트가 스크롤로 키를 흘리지 않음.
- **A2-6 최종 판정 (Step 2에서 이관됨, §1.1 합의대로)**: base 모드 한정 스크롤 회귀 0 — **본 스텝의 `BaseModeScrollTest` + `ScrollIsolationTest`(1)로 증명 완료**.

## 안전 규칙 준수 (§0)
실세션 스폰·시그널 0. `curses.KEY_UP` 등은 실제 curses 상수를 그대로 참조하나 `curses.wrapper`/실 화면 없이 순수 함수 호출만 수행.
