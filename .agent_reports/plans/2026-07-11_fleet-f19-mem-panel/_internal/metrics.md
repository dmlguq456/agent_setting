# SD-17 separability judgment — fleet F-19 memory panel

- **판정**: 비분리(inline) — depth-2 스테이지(code-plan/execute/test/report) 분사 대신 depth-1
  conductor 세션 안에서 직접 구현.
- **근거**: 산출물 표면이 하나의 좁은 수직 슬라이스로 강결합 — `collectors/memory.py`(신규,
  독립적으로 계약 확정 불가: render 소비 형태를 먼저 확정해야 반환 스키마가 고정됨) →
  `render.py`(_build_lines/`_draw`/`render_once`/`_loop` 4개 콜사이트 동시 threading) →
  `fleet.py`(--json additive 키) → `tests/test_f19_memory.py` 가 전부 동일 세션 안에서 스키마
  합의를 되먹임하며 진행됨(boundary-결합, SD-17 비분리 조건과 일치). 별도 세션으로 쪼개면
  각 세션이 스키마 draft 를 놓고 파일 핸드오프만으로 재조정해야 해 왕복 비용이 구현 비용을
  넘어섬.
- **분리 가능했던 부분**: 없음 — 단일 기능 파일 3개(신규 1 + 기존 2 수정) + 테스트 1개로
  스코프가 이미 작음(3중 의무 (b) in-session 병렬 워커도 불필요 판단).
- **결과**: 기존 139 tests 회귀 없음(discover 156 OK) — `python3 -m unittest discover -s
  tools/fleet/tests`.
