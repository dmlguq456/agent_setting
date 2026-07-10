# SD-15 codex/opencode wrapper 동형 이식 — final report

**SoT**: `.agent_reports/spec/stage-dispatch/prd.md` §8.5.7b (SD-15) · OPERATIONS §5.10 ⑨
**브랜치**: sd15-adapter-parity (worktree 격리, main 머지는 메인 세션)

## 무엇을 했나

Claude wrapper 의 SD-15 limit-즉사 감지(launch 직후 조기 exit + 로그 limit/auth 패턴 →
jobs.log row `done,note=dead-<사유>[,reset=<x>]` 자동 마감 + reset 캐시 + stdout 표면화,
재시도 없음)를 **codex·opencode adapter 에 동형 이식**. 구조 제약 축은 ADAPTATION 명시 신고.

### 이식 축 (claude 원본 대비 6축)

1. `DEATH_PATTERNS`/`scan_death`/`_RESET_RE` — codex/opencode 실측 패턴 추가(429·usage_limit_reached·
   provider rate limit·exceeded retry limit), 공유 목록 동기 주석.
2. `watch_early_death` — launch 후 짧은 워치 조기 exit 감지.
3. `close_job_row` — 자기 open row `done,note=dead-<reason>[,reset=<x>]` 마감(flock 직렬).
4. `write_reset_cache` — `.dispatch/usage-reset.{codex,opencode}` (SD-16 usage-check 연동).
5. `--early-exit-watch` 인자 + start 배선 + `early_death=`/`row_closed=` 출력.
6. liveness 로그-스캔 DEAD 근거(SD-15b) — `dispatch-liveness.py` 가 open row 로그의 limit
   패턴을 transcript/DB mtime 판정보다 _먼저_ DEAD 로 판정.

### ADAPTATION disclosure (구조 제약)

**OpenCode launch-watch 부분 미실현**: `opencode run` 은 API 에러 시 exit 하지 않고 **무한
hang**(anomalyco/opencode#8203). watch 는 exit 를 요구하므로 hang-on-limit 을 놓친다 → 이 케이스는
**축 6(liveness 로그-스캔)** 이 담당(hang 중에도 로그의 rate-limit 라인으로 확정 DEAD). 즉
clean-exit-on-limit → launch watch / hang-on-limit → liveness scan 으로 분담. codex·claude 는
런타임이 exit 하므로 두 축 모두 실현. codex/opencode ADAPTATION.md 에 축별 parity 표로 신고.

## 변경 파일

| 파일 | 변경 |
|---|---|
| `adapters/codex/bin/dispatch-headless.py` | SD-15 6축 이식(패턴/watch/close/cache/arg/배선/출력) |
| `adapters/opencode/bin/dispatch-headless.py` | 동형 이식 + `jobs_lock` flock helper(close/append 직렬화) |
| `adapters/codex/bin/dispatch-liveness.py` | `LIMIT_RE` 로그-스캔 DEAD 근거(축 6) |
| `adapters/opencode/bin/dispatch-liveness.py` | 동형 로그-스캔(hang-on-limit 담당) |
| `adapters/codex/ADAPTATION.md` | SD-15 parity: realized 신고 |
| `adapters/opencode/ADAPTATION.md` | SD-15 parity: partial + hang-on-limit 구조 제약 disclosure |
| `adapters/codex/bin/dispatch-headless.sd15.test.sh` (신규) | conformance(scan/close/clean/축6) |
| `adapters/opencode/bin/dispatch-headless.sd15.test.sh` (신규) | conformance + hang 케이스 + 축6 |

## 검증 커맨드·결과

```
bash adapters/codex/bin/dispatch-headless.sd15.test.sh      → PASS (5 ok)
bash adapters/opencode/bin/dispatch-headless.sd15.test.sh   → PASS (6 ok, hang 케이스 포함)
bash adapters/claude/bin/dispatch-headless.sd15.test.sh     → PASS (회귀 없음)
python3 -m py_compile <4 wrapper/liveness>                  → COMPILE_OK
python3 adapters/{codex,opencode}/bin/dispatch-headless.py --dry-run …  → early_death=- 정상
bash tools/check-adaptation-boundary.sh                     → FAIL 2 (둘 다 fleet baseline
   test_f15_rows.py·test_f14_title.py missing = 범위 외), **신규 FAIL 0** (baseline diff NO_DIFF)
```

- core 수정 없음 — SD-15 는 이미 확정된 core 계약(OPERATIONS §5.10 ⑨, codex/opencode liveness
  까지 명시). 순수 adapter parity 이식.
- `loops/**`·`tools/fleet/**` 미접촉(타 세션 소유). `__pycache__` 잔여 정리(boundary 통과).

## 산출물 경로

- plan: `.agent_reports/plans/2026-07-10_sd15-adapter-parity/plan/plan.md`
- metrics: `.agent_reports/plans/2026-07-10_sd15-adapter-parity/_internal/metrics.md`
- report: 본 파일
