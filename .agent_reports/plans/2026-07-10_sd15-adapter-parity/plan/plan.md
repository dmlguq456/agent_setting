---
slug: 2026-07-10_sd15-adapter-parity
capability: autopilot-code
mode: dev
intensity: standard
qa: standard
status: done
spec: .agent_reports/spec/stage-dispatch/prd.md §8.5.7b (SD-15)
---

# SD-15 codex/opencode wrapper 동형 이식 — plan

## 목표

Claude wrapper(`adapters/claude/bin/dispatch-headless.py`)의 SD-15 limit-즉사 감지
(`--early-exit-watch`: launch 직후 조기 exit + 로그 limit/auth 패턴 → jobs.log row
`done,note=dead-<사유>[,reset=<x>]` 자동 마감 + reset 캐시 + stdout 표면화)를
**codex·opencode adapter 의 dispatch 경로에 동형 이식**. 구조 제약으로 미실현인 축은
ADAPTATION 문서에 명시 신고.

## 이식 대상 축 (claude 원본 대비)

1. **DEATH_PATTERNS / scan_death / _RESET_RE** — limit/auth 종료 어휘 (wrapper).
2. **watch_early_death** — launch 후 짧은 워치에서 조기 exit + 로그 패턴 감지 (wrapper).
3. **close_job_row** — 자기 open row 를 `done,note=dead-<reason>[,reset=<x>]` 로 마감 (wrapper).
4. **write_reset_cache** — `.dispatch/usage-reset.<harness>` 캐시 (SD-16 연동, wrapper).
5. **`--early-exit-watch` 인자 + start 경로 배선 + 출력 표면화** (wrapper).
6. **liveness 로그-스캔 DEAD 근거** (SD-15b) — `dispatch-liveness.py` 가 open row 의
   dispatch 로그에서 limit 패턴을 transcript/DB 판정보다 _먼저_ DEAD 로 판정.

## runtime-currentness 조사 결과 (2026-07, 실측 근거)

- **Codex** (`codex exec --json`): limit 시 `"exceeded retry limit, last status: 429
  Too Many Requests"`, `usage_limit_reached`, `429 Too Many Requests` 를 출력하고
  대체로 non-zero exit (issue openai/codex#9148·#12677·#11434). rolling 24h reset.
  → 조기-exit 축 실현 가능(best-effort). JSONL 안 텍스트라도 substring 스캔은 동일 동작.
- **OpenCode** (`opencode run --format json`, anomalyco fork): limit 메시지
  `"Provider Rate Limit exceeded [retrying in 15s attempt #N]"`, `"API rate limited
  (429)"`, `"Rate limited. Quick retry in 1s…"`. **구조 제약(issue #8203)**: `opencode
  run` 은 API 에러 시 exit 하지 않고 **무한 hang** 하는 알려진 버그가 있다.

## ADAPTATION disclosure (구조 제약 명시)

- **OpenCode 조기-exit-watch 축은 부분 미실현**: `watch_early_death` 는 자식이 워치 창
  안에서 _exit_ 해야 발화한다. OpenCode 의 hang-on-limit(#8203) 은 exit 하지 않으므로
  launch-watch 가 놓친다 → row 는 `open` 잔존. 이 경우는 **축 6(liveness 로그-스캔)** 이
  뒤늦게 DEAD 로 잡는다(hang 중에도 로그엔 rate-limit 라인이 남으므로). 즉 OpenCode 는
  "clean-exit-on-limit" 만 launch-watch 로 즉시 마감되고, "hang-on-limit" 은 liveness
  로그-스캔이 담당. codex/claude 는 두 축 모두 실현.
- codex/opencode ADAPTATION.md 의 headless dispatch·liveness 절에 위 비대칭 신고.

## 변경 파일

| 파일 | 변경 |
|---|---|
| `adapters/codex/bin/dispatch-headless.py` | SD-15 블록 이식 (patterns/scan/watch/close/cache + `--early-exit-watch` + start 배선 + 출력) |
| `adapters/opencode/bin/dispatch-headless.py` | 동형 이식 + `jobs_lock` helper 추가(close/append 직렬화) |
| `adapters/codex/bin/dispatch-liveness.py` | 로그-스캔 LIMIT_RE DEAD 근거(축 6) |
| `adapters/opencode/bin/dispatch-liveness.py` | 동형 로그-스캔 |
| `adapters/codex/ADAPTATION.md` | SD-15 이식 + OpenCode 대비 parity 노트 |
| `adapters/opencode/ADAPTATION.md` | SD-15 이식 + hang-on-limit 구조 제약 disclosure |
| `adapters/codex/bin/dispatch-headless.sd15.test.sh` (신규) | claude 판 준하는 conformance |
| `adapters/opencode/bin/dispatch-headless.sd15.test.sh` (신규) | 동형 conformance |

## 검증

- 신규 `dispatch-headless.sd15.test.sh` 2종 PASS (scan_death 패턴 + limit-death row 마감
  + clean-exit row 미변경).
- 기존 claude SD-15 test 회귀 없음.
- `tools/check-adaptation-boundary.sh` 신규 FAIL 0 (잔존 2건 = fleet baseline, 범위 외).

## 제외

- `loops/**` · `tools/fleet/**` (타 세션 소유).
- 재시도 로직 없음 (SD-15 는 감지·마감·표면화만; 재분사는 orchestrator 의미 구간).
