# dispatch-liveness pid 신호 서열 — micro-plan (quick, inline)

> status: done · 2026-07-13 · 브랜치 `dispatch-liveness-fix` · 계기 = harness-installer 사이클 1 conductor 실측 보고(공유-worktree 자식 ALIVE 오탐, 수확 ~50분 지연) → durable fact `fact_fact-dispatch-liveness-dispatch_e3c212`

## 문제
transcript-디렉토리 mtime 판정은 같은 worktree 를 공유하는 depth-2 자식에서 깨진다 — conductor 자신의 활동이 같은 `projects/<enc-wt>/` 를 신선하게 유지해, 이미 종료한 자식이 계속 ALIVE 로 보인다.

## 수정 (core 먼저 → adapter → 소비자 → 테스트)
1. `core/OPERATIONS.md` §5.10 — job 레지스트리 metadata 에 `pid=` 추가 + stealth-death 가드에 신호 서열(① pid ② transcript fallback)과 `EXITED` 상태 명문화.
2. `adapters/claude/bin/dispatch-headless.py` — `annotate_job_row()` 신설, Popen 직후 자기 row 에 `pid=<n>` 기록(flock 은 close_job_row 동일 규율), 출력에 `child_pid=` 추가.
3. `utilities/dispatch-liveness.sh` — pid 1순위 판정: `/proc/<pid>` 실존 + cmdline 'claude' 대조(pid-reuse 가드) → ALIVE(pid) / pid 종료 + row open → `EXITED`(limit 사유 있으면 DEAD 유지) / pid 없는 legacy row → 기존 mtime 판정 그대로. `/proc` 없는 플랫폼은 자동 fallback.
4. `utilities/dispatch-wait.sh` — exit 3 의미에 EXITED 포함(주석·배너).
5. 회귀 테스트 3종 추가(G: live pid = transcript 없이 ALIVE / H: dead pid + 신선 transcript = EXITED — 본 수정의 핵심 회귀 / I: pid-less legacy fallback 불변).

## 검증
- `dispatch-liveness.test.sh` 9/9 PASS (기존 6 + 신규 3) · `dispatch-wait.test.sh` PASS · `dispatch-headless.sd15.test.sh` PASS · `dispatch-concurrency.test.sh` PASS · `bash -n`/`sh -n`/`py_compile` 전부 통과.
- 출력 문구 소비자 grep 전수 — liveness stdout 을 파싱하는 외부 스크립트 없음(dispatch-wait 는 exit code 만, fleet 은 jobs.log 직접) 확인.
