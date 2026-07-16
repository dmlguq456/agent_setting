# micro-plan — fleet claude 사용량 정확성 (v10 minor #3)

- route: autopilot-code / dev / quick / depth-1 one-shot / tracked
- worktree: `/home/Uihyeop/agent_setting-wt/fleet-usage-accuracy` (branch `fleet-usage-accuracy`)
- 규범: `spec/agent-fleet-dashboard/pipeline_summary.md` "2026-07-16 (v10 minor #3)" 규칙 ①②③

## 진단 (실측 재확인)

- `collectors/__init__.py:97-113` — `usage_api.account_usage()`가 truthy이기만 하면 claude 세션의 rl 필드를 무조건 덮어씀. 200 성공 + 전-버킷 0 응답이 신선한 tap의 진짜 값(5h 2%/7d 43%)을 0으로 가림.
- `render.py:2101-2111` — `_rl` 집계가 `s.mtime`(transcript mtime) 기준 freshest 세션 1개 pick. tap은 모델-스코프로 분화(Fable 세션 7d 0% vs opus 세션 43%)해 tick마다 요동.
- tap 신선도 증거 부재: `s.mtime`은 transcript mtime이라 rate 필드가 언제 쓰였는지 말해주지 않음. tap 파일 자체의 mtime이 필요.
- tap 스키마 실측: `rate_limits.five_hour = {used_percentage, resets_at}` — `resets_at`이 있으나 `_apply_statusline`이 버리고 있음.

## 변경 (최소 침습)

1. `collectors/claude.py` — tap 읽기 성공 시 ephemeral 증거 2개 부착: `_rl_mtime`(tap 파일 mtime), `_rl_tap_rs`(tap의 5h/7d resets_at). 언더스코어 = `_transcript_path` 선례대로 `--json`(asdict) 표면 불변, `sess.rl_rs`는 건드리지 않아 API 경로 무회귀.
2. `collectors/__init__.py` — 규칙 ①. `_usage_all_zero(au)` ∧ `_fresh_tap_positive(sessions)` 이면 override skip(tap 값 유지). 아니면 기존대로 authoritative + 덮어쓴 행에 `_rl_api = True` 표시. codex/opencode 블록 불변.
3. `render.py` — 규칙 ②. `_rl` freshest-pick 루프는 유지(모든 harness 공통 fallback), 그 뒤 claude 한정으로 `_claude_tap_usage()`(신선 ≤300s tap들의 창구별 max, resets는 max를 준 세션 값) 결과가 있으면 교체. `_rl_api` 행이 있으면(=API authoritative) 교체하지 않음 — 계정 공유값이라 이미 동일.
4. 규칙 ③ — 소스 전무 시 `_rl`/`_live_h` 경로 그대로 → "no usage api" 행 불변. `_claude_tap_usage()`가 None을 반환하면 기존 fallback 행이 그대로 서므로 stale-only(ⓓ)에서 플리커 없음.

## 검증

- 신규 테스트 `tests/test_usage_source.py` — ⓐ~ⓔ 5 케이스, `usage_api.account_usage` monkeypatch + tmp tap fixture(네트워크·실세션·live 쓰기 0).
- 전체 `python3 -m unittest discover -s tools/fleet/tests -t .` (기준선 실측 556 — 지시서 555는 v10 minor #2 착륙분 반영 전 수치).
- 렌더 스모크 `COLUMNS={60,120,168} python3 tools/fleet/fleet.py --once`.
- mirror parity `rsync -a --delete tools/fleet/ adapters/claude/tools/fleet/` → `diff -r` 무출력.
