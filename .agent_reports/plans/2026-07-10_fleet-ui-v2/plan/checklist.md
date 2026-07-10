# Checklist — fleet UI v2 (PRD v2 §4.5 · §4.6)

Safety commit: ae8c1657e66fb6b282b4923ef75e46c411aa11c2

## Phase 1 — SD-F4 pipe tolerant 파싱 (collectors/dispatch.py)
- [x] 1.1 `_parse_pipe_meta` continuation tokenizer 교체 (split `[,\s]+`, `=`-없는 토큰은 직전 value 에 공백-join)
- [x] 1.1 `eq_pos < colon_pos` 게이트 + `head=split("(",1)[0]` 유지
- [x] 1.2 tokenizer 정규식 상수 추가(모듈 1회 컴파일)

## Phase 2 — SD-F1~F3 스키마 + collector + 스테이지 row
- [x] 2.1 model.py `DispatchJob` 에 `effort`/`model_role` 필드 추가 (default None)
- [x] 2.2 dispatch.py `_scan_jobs_log` 에 `effort=meta.get("effort")`, `model_role=meta.get("model_role")`
- [x] 2.3 dispatch.py `_scan_processes` 두 생성부에 env-기반 effort/model_role(방어적, None 정상)
- [x] 2.4 render.py `_STAGE_ROLE` 상수 + `_stage_role_label` 헬퍼 (code-plan→plan/…/report, `:phase` 접미 분리)
- [x] 2.5 render.py `_short_role` 스테이지-aware + `_ROLE_SHORT` g6/g9 제거 + 일반 규칙 `^(g\d+[a-z]?)`
- [x] 2.6 render.py `_dispatch_role_suffix` 스테이지 suffix dim 표기 (전체 profile 태그가 이미 dim 이라 별도 색 분리 불필요 — 결정 기록)
- [x] 2.7 render.py SD-F2 conductor breadcrumb — `_emit_dispatch_tree` active-child stage 계산 → `stage_override`
- [x] 2.8 render.py SD-F3 자기 model/effort 1급 + parent-inherit fallback `~` 표기 (`_dispatch_row`/`_2line`)

## Phase 3 — F-9~F-13 가독성 (render.py 표시층)
- [ ] 3.1 F-9(c) 드롭 우선순위 `qa→intensity→role` (mode 유지)
- [ ] 3.2 F-9(d) legend `~` 유도값 1회 설명
- [ ] 3.3 F-10 alert humanize — 꼬리 strip + 종류별 집계 + 우선순위 절단(dead>stale>ctx)
- [ ] 3.4 F-11 `_stage_segs` — `open`→`queued`, seq-없는 `running` dim track (status 어휘 불변)
- [ ] 3.5 F-12(b) footer `wlbl` 3-모드(`wide/narrow/stack`)
- [ ] 3.6 F-12(a) `+N malformed` dim 확인만
- [ ] 3.7 F-12(c) legend glyph-appearance 추적 (`_build_lines` 로컬, `_OFFSET` 불변식 준수) [decision: significant]
- [ ] 3.8 F-13 dead/stale row telemetry 생략 + `last seen <age>` (live row 만 explicit —)

## Phase 4 — 검증
- [ ] Unit: `cd tools && python3 -m unittest fleet.tests.test_dispatch -v` 전부 green
- [ ] 신규 (a) space-separated pipe fixture
- [ ] 신규 (b) `model_role=deep maker` value-internal-space fixture
- [ ] 신규 (c) unknown-key-ignored fixture
- [ ] 신규 (d) stage-name label (code-plan/execute/test/report)
- [ ] 신규 (e) conductor breadcrumb 집계
- [ ] 신규 (f) alert humanize 집계
- [ ] Smoke: `python3 tools/fleet/fleet.py --once` — 이 파이프 depth-2 스테이지 row 단계명 렌더
- [ ] Smoke: `python3 tools/fleet/fleet.py --json` — 스테이지 잡 effort/model_role 채워짐
- [ ] conductor row breadcrumb = 활성 스테이지 자식 일치 + 기존 render 회귀 없음
