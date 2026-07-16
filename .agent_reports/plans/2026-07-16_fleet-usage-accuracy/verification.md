# verification log — fleet usage accuracy (v10 minor #3)

worktree `/home/Uihyeop/agent_setting-wt/fleet-usage-accuracy` · commit `85716394`

## 1. 신규 테스트 — `tools/fleet/tests/test_usage_source.py` (16 tests, OK)

네트워크 0(`usage_api.account_usage` mock) · 실세션 스폰 0 · live 쓰기 0(`CLAUDE_CONFIG_DIR`=tmp, tap fixture는 tempdir).

| 지시 케이스 | 테스트 | 결과 |
|---|---|---|
| ⓐ API 전-제로 + 신선 tap 양수 → tap 유지 | `test_a_zero_api_with_fresh_positive_tap_keeps_tap` (rl_7d==43, `_rl_api` 미표시) | OK |
| ⓑ API 양수 → API 우선 | `test_b_positive_api_still_authoritative` (11/22/fable 5) · `test_b_api_rows_bypass_tap_aggregation` (렌더 22%) | OK |
| ⓒ tap 2개 분화(0/43) → max 43 | `test_c_model_scoped_taps_report_the_max` · `test_c_row_shows_the_max_not_the_freshest_session` (freshest는 0%인 배치) | OK |
| ⓓ 전부 stale + API 전-제로 → 기존 거동 | `test_d_zero_api_with_only_stale_taps_overrides_as_before` (override 그대로) · `test_d_stale_taps_keep_the_last_row_instead_of_blanking` (43% 행 유지, `—` 없음 = 플리커 방지) | OK |
| ⓔ 소스 전무 → 기존 문구 | `test_e_no_source_keeps_the_existing_note` ("no usage api") | OK |

경계 보강 5건: tap mtime/resets 부착 + `--json`(asdict) 표면 불변, 신선 tap이 API와 같이 0이면 override(모순 없음 = 불신 이유 없음), 부분 버킷 양수는 전-제로 아님, 신선 tap 전무 → None, codex 세션은 집계 대상 아님.

## 2. mutation check (테스트 실효성)

| 되돌린 변경 | 결과 |
|---|---|
| override 가드 제거(`if au:`) | FAILED 1 — ⓐ가 잡음 |
| render tap-max 집계 제거(freshest-pick만) | FAILED 1 — ⓒ가 잡음 |
| 원복 | 16 OK |

## 3. 전체 회귀

`python3 -m unittest discover -s tools/fleet/tests -t .` → **572 tests OK, 회귀 0**.
기준선은 실측 **556**(지시서의 555는 v10 minor #2 착륙분 반영 전 수치) → +16 신규.
중간 1 FAIL은 mirror-drift 가드가 의도대로 미동기를 잡은 것(rsync 후 해소).

## 4. 렌더 스모크 (live)

`COLUMNS={60,120,168} python3 tools/fleet/fleet.py --once` — usage 행 존재, crash 0.
최대 표시 폭 60/120열 105 cols · 168열 142 cols(기존 60열 pulse/mem 넘침은 기지 결함, 범위 밖).

수정 효과 실측 — 같은 시각 신선 tap 3개가 `5h=2 7d=0` / `5h=2 7d=43` / `5h=2 7d=0`로 분화(freshest는 7d **0%**)한 상태에서 4틱 연속:

```
usage claude code   5h [────────   2%] ↻ 1h37m   7d [━━━─────  43%] ↻ 5d3h   (×4, 요동 0)
```

## 5. mirror parity

`rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/` 후
`diff -r --exclude=__pycache__` **무출력**, `test_mirror_parity` OK.

## 6. 스모크 중 관측 — 계약 범위 밖 잔여 결함 (미수정, 판단 요청)

`COLUMNS=60` 실행 1회에서 usage 행이 `5h 3% · 7d 0% · fable 1%`로 나옴 — 같은 시각 tap은 7d 43%.
해석: API가 **부분** 양수(5h 3%, fable 1%)에 7d만 0인 응답을 반환 → 규칙 ①의 "전-버킷 0"에 해당하지 않아 override가 적용되고 7d 43%가 0으로 덮임.
규칙 ①은 응답 단위(전-버킷 0)로 명시되어 있어 창구 단위 모순(API 7d 0 vs 신선 tap 7d 43)까지 확장하는 것은 이번 계약 밖 → 임의 확장하지 않고 보고만 함. 이후 4회 재실행에서는 재현되지 않음(관측 1회, 엔드포인트가 그 사이 실패/전-제로로 응답).
