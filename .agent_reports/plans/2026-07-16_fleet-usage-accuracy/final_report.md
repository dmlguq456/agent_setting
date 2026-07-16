# fleet claude 사용량 정확성 — 최종 보고 (v10 minor #3)

- route: autopilot-code / dev / quick / depth-1 one-shot / tracked · 분사 0
- branch `fleet-usage-accuracy` commit `85716394` (merge/push는 main 담당)
- 산출물: `micro-plan.md` · `verification.md` · 본 보고

## 결과

세 규칙 모두 구현·검증 완료. **572 tests OK(기준선 556 → +16), 회귀 0**, mirror parity clean.
live 스모크에서 수정 효과 확인: 신선 tap 3개가 7d `0 / 43 / 0`으로 분화한 상태에서 보드는 4틱 연속 `5h 2% · 7d 43%`로 고정(수정 전이라면 freshest-pick이 7d 0%를 읽고 틱마다 요동).

## 변경 (4파일, +196행, canonical + adapter mirror)

| 파일 | 내용 |
|---|---|
| `collectors/claude.py` | tap 읽기 성공 시 ephemeral 증거 2개 부착 — `_rl_mtime`(tap 파일 자체 mtime), `_rl_tap_rs`(tap의 5h/7d resets_at, 지금까지 버려지던 값). `sess.mtime`은 transcript의 것이라 rate 필드가 언제 쓰였는지 말해주지 못함. 언더스코어 = `_transcript_path` 선례 → `--json`(asdict) 표면 불변, `sess.rl_rs`(API 소유) 무접촉 |
| `collectors/__init__.py` | 규칙 ① — `_usage_all_zero(au) ∧ _fresh_tap_positive(sessions)`이면 override skip. 아니면 기존대로 authoritative + `_rl_api` 표시. `TAP_FRESH_SEC=300` |
| `render.py` | 규칙 ② — `_claude_tap_usage()` 신설(신선 tap들의 창구별 max, resets는 각 max를 준 세션 값). freshest-pick 루프는 전 harness 공통 fallback으로 유지하고 claude 한정 사후 교체. `_rl_api` 행이 있으면 미적용(계정 공유값이라 이미 동일) |
| `tests/test_usage_source.py` | 신규 16건 (ⓐ~ⓔ + 경계 5) |

codex/opencode 경로, `usage_api.py`의 TTL/stale 로직, `--json` 스키마 모두 불변.

## 설계 판단 2건

- **`_claude_tap_usage()`가 None이면 기존 행이 그대로 선다.** 신선 tap이 없다고 meter를 비우는 건 사실이 아니라 플리커 — 규칙 ③의 "소스 전무 시 불변"과 같은 태도를 stale-only 상황에도 적용.
- **tap의 resets_at을 `sess.rl_rs`에 넣지 않았다.** 5h resets가 세션마다 다른 것이 실측이라, API-authoritative 행에 tap resets가 섞이면 틀린 ↻가 붙을 수 있음. tap resets는 tap-max 집계에서만 소비.

## 테스트 실효성

두 규칙 각각을 되돌리는 mutation을 넣어 ⓐ·ⓒ가 실제로 잡는 것을 확인(각 FAILED 1, 원복 후 16 OK). "테스트가 통과한다"가 아니라 "테스트가 이 결함을 잡는다"를 확인한 것.

## 판단 요청 — 계약 범위 밖 잔여 결함 1건 (미수정)

스모크 1회에서 usage 행이 `5h 3% · 7d 0% · fable 1%`로 관측됨(같은 시각 tap 7d 43%). API가 **부분** 양수(5h·fable만 양수, 7d만 0)로 응답하면 규칙 ①의 "전-버킷 0"에 걸리지 않아 override가 적용되고 7d 43%가 다시 0으로 덮인다. 즉 이번 수정은 **전-버킷 0 응답만** 막는다.

규칙 ①은 응답 단위로 명시되어 있어 창구 단위 모순(API 7d 0 vs 신선 tap 7d 43)까지 임의 확장하지 않았다. 확장하려면 spec 개정이 필요하며, 후보 규칙은 "창구별로, API 값이 0이고 같은 창구의 신선 tap이 양수면 그 창구만 tap 유지". 이후 4회 재실행에서는 재현되지 않아(엔드포인트가 실패 또는 전-제로 응답) **관측 1회** 근거임을 명시한다.
