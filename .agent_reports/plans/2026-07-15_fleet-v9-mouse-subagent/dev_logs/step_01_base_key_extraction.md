# Step 1 — `_handle_base_key` 추출

## 변경
- `render.py`: `_loop`의 base-mode 키 블록(스크롤/`a`/`w`)을 `_handle_base_key(ch, body_h)`로 추출, `_handle_select_key` 옆(같은 curses-free 핸들러 구역)에 배치.
- `KEY_MOUSE` 분기는 넣지 않음(§1.1/§4.1 — Step 2가 별도 `_handle_mouse`로 소유). `_loop`의 마우스 처리는 그대로 유지(Step 2에서 교체 예정).
- `_loop` 호출부: `if _handle_base_key(ch, body_h): pass elif ch == curses.KEY_MOUSE: ...` — `r`/tick 로직은 `_loop`에 남김(변경 없음).

## 검증
```
python3 -m unittest discover -s tools/fleet/tests -q
→ Ran 416 tests, FAILED (failures=1) — 실패 1건은 test_mirror_parity(render.py 미러 드리프트, Step 6에서 rsync로 해소 예정). 그 외 415건 전부 OK, 신규 실패 0.
python3 tools/fleet/fleet.py --once | head -5   → 정상 렌더
```

## acceptance
- A1-1: 전체 테스트 416 유지 — 확인(미러 parity 1건은 Step 6 소관, §2.1에 명시된 기지 결함).
- A1-2: `_handle_base_key`는 `curses` 모듈 상수만 참조하며 순수 함수(헤드리스 호출 가능) — Step 5에서 실증 예정.

## 안전 규칙 준수 (§0)
실세션 스폰·시그널 0. 실행한 검증은 unittest discover + `--once` 스냅샷뿐.
