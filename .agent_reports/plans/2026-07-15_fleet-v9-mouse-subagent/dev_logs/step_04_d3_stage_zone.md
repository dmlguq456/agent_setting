# Step 4 — D3: dispatch stage zone 대칭 폭 상한

## 변경 (render.py)
- `_STAGE_ZONE_MAX = 30` 신설 — `_NAME_WIDE_MAX`/`_DISPATCH_NAME_MAX`/`_PROFILE_MAX`와 같은 idiom(한 상수, 한 곳). 실측 현재 최대치 24("code: plan › exec › test", 실 라이브 보드에서 `_dispatch_stage_segs` 전수 측정)에 여유를 두고 최소값 선정 — 회귀 0 우선(§4.6 참고).
- `_stage_segs(key, stage, working, max_width=None)`: `max_width` 지정 시 `_drop_past_stages`로 **활성 스테이지 이전(과거, ✓ 예정)** 항목을 가장 이른 것부터 성분 통째로 접는다(구분자 포함) — SD-F2(prd.md:164) "정보 가치는 지금 어디, 과거 아님". 활성/미래 스테이지는 드롭 대상에서 제외(마지막 방어선).
- `_dispatch_stage_segs`: SD-F1 분기(role 접두 + breadcrumb)에서 breadcrumb에 `max_width = _STAGE_ZONE_MAX - prefix폭`을 넘겨 과거 스테이지 우선 드롭 → 그래도 초과하면 **접두어 전체를 드롭**(F-9(c) 성분 통째 드롭, 중간 tail-cut 금지). 접두 없는 분기도 동일 상한 적용.
- depth≥2 분기(짧은 단일 토큰 "running"/stage명/`[]`)는 무변경 — 항상 상한 이내.

## 검증
```
python3 -m unittest discover -s tools/fleet/tests -q
→ Ran 458 tests. FAILED(failures=1) — 유일한 실패는 test_mirror_parity(render.py + 신규 tests/test_d3_stage_zone.py 미러 드리프트, Step 6에서 rsync). 그 외 457건 OK, 신규 실패 0.

python3 -m unittest tools.fleet.tests.test_d3_stage_zone -v   → Ran 6 tests, OK
  - test_cap_lives_in_exactly_one_constant, test_stage_zone_never_exceeds_the_cap,
    test_long_conductor_label_is_dropped_not_tail_cut, test_active_stage_survives_when_past_stages_drop,
    test_168_no_overflow_is_structural_not_incidental, test_short_rows_are_unaffected

for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once | awk ...; done
→ width=60 over:16  120 over:0  168 over:7   (v8 베이스라인과 문자수 기준 동일값)
```

**정본은 `_dw()` 기반 단위 테스트다(plan.md §6 명시 — awk length는 참고 지표)**: 168폭에서 char-length가 168을 넘는 7개 행을 개별 확인 — 6개는 세션 이름 zone(다른 컬럼, 이 스텝 스코프 밖) 오버플로이고, dispatch conductor 행 1개(D3 대상)는 `render._dw()` 실측 **162**로 168 이내임을 직접 확인(awk length가 이모지/스피너 문자를 실제 표시폭과 다르게 세는 인코딩 아티팩트). D3 자체의 구조적 무오버플로는 `test_168_no_overflow_is_structural_not_incidental`(인위적으로 무제한 role-suffix를 넣어도 상한 준수)로 고정.

## acceptance
- A4-1: `_STAGE_ZONE_MAX` 상수 1개, 한 곳 — `test_cap_lives_in_exactly_one_constant`.
- A4-2: 168열 무오버플로가 구조적(인위적 긴 스테이지 라벨 fixture에서도 경계 미초과) — `test_168_no_overflow_is_structural_not_incidental`, `test_stage_zone_never_exceeds_the_cap`.
- A4-3: 드롭은 성분 단위(중간 tail-cut 0), 활성 스테이지 보존 — `test_long_conductor_label_is_dropped_not_tail_cut`, `test_active_stage_survives_when_past_stages_drop`.
- A4-4: 회귀 0 — `test_short_rows_are_unaffected`(실측 24폭 케이스, 드롭 미발동, 출력 무변경).
- A4-5(정직성 조건): 168 오버플로 0을 **이제 구조적 보장으로 말할 수 있다** — 단 60폭은 여전히 legend/mem/usage 요약 행 원인(D4, 본 스텝 스코프 밖)으로 미충족이며 보고에 명시함.

## 리스크 처분
- R4-1(상한 과소 → 회귀): 실측 기반 최소값(24+여유=30) 채택 + `test_short_rows_are_unaffected`로 고정.
- R4-2(60폭 미해결): 본 스텝 스코프 밖(§9 D4) — stage zone 원인 자체는 60폭에서도 구조적으로 해소되나(같은 cap 적용), legend/mem/usage 요약 행의 별개 원인은 잔존.

## 안전 규칙 준수 (§0)
실세션 스폰·시그널 0. 전부 fixture DispatchJob + `--once` 스냅샷.
