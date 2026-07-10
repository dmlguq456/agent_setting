# metrics — stage-dispatch v4 정련 (SD-15b·SD-16e·SD-11b)

> 사이클: `2026-07-10_sd-v4-refine` · 브랜치 `sd-v4-refine` · 시작 2026-07-10 18:48 (+0900)

## 실행 방식 — inline opt-out (orchestrator 명시 부여)

이 사이클은 분사 launch 경로 자체(`dispatch-headless.py`·`dispatch-liveness`·reminder hook)를 편집하는 **자기수정 사이클**이다.
main orchestrator 가 분사 프롬프트에서 **inline 실행 opt-out 을 명시 부여**했다 (SD-11b(c) — 자기수정 예외를 conductor
재량이 아니라 orchestrator 명시로 이동한 그 경로). 따라서 스테이지(code-plan·execute·test·report)를 depth-2 로
분사하지 않고 conductor(이 depth-1 세션) 안에서 in-session 순차 실행한다.

- 부여 근거(프롬프트 원문 요지): "이 사이클은 분사 launch 경로 자체를 편집하는 자기수정 사이클이다. main orchestrator 가
  inline 실행 opt-out 을 명시 부여한다 — 스테이지 분사 대신 in-session 실행 허용. 단 metrics.md 에 opt-out 부여 사실과
  함께 기록할 것."
- 대응 env 신호: `STAGE_DISPATCH_INLINE_OK=1` (SD-11b(c) 로 이번에 신설하는 opt-out env 와 동일 의미 — orchestrator 가
  분사 시 명시 부여한 경우만 deny 대신 soft reminder). 이 사이클은 그 opt-out 이 부여된 첫 실전.

## 스테이지별 wall-clock

| 스테이지 | 실행 방식 | 시작 | 종료 | wall-clock |
|---|---|---|---|---|
| code-plan | inline (opt-out) | 18:48 | 18:51 | ~3m |
| code-execute | inline (opt-out) | 18:51 | 19:05 | ~14m (SD-15b 3어댑터·core + SD-16e + SD-11b + 테스트) |
| code-test | inline (opt-out) | 19:05 | 19:12 | ~7m (스위트 실행 + baseline 대조 stash/pop) |
| code-report | inline (opt-out) | 19:12 | 19:13 | ~1m |

## 테스트 결과 (code-test)

- `utilities/dispatch-liveness.test.sh` — PASS (기존 3 + SD-15b 신규 3: fresh-transcript 배제·terse-line DEAD·prose 앵커링 미매치).
- `utilities/usage-check.test.sh` — PASS (기존 + SD-16e 신규 4: reset未경과 limited·reset경과 ok(expired)·unknown-reset·창밖 downgrade).
- `hooks/portable-guards.test.sh` — **PASS=313 FAIL=12**. baseline(HEAD) = **PASS=311 FAIL=12** (stash 대조). 즉 **신규 FAIL 0**,
  SD-11b 테스트 +2 통과 순증. SDR 7/7 통과(deny·opt-out·intensity불명 3분기). 잔존 12 FAIL 은 전부 baseline —
  (a) dispatch-liveness.sh state-transition 4건: 테스트가 transcript 를 `$AGENT_HOME/projects/` 에 두는데 .sh 는
  runtime-root(`$HOME/.claude/projects`)를 보므로 DEAD — HEAD 와 바이트 동일 출력(회귀 아님, 테스트 환경 전제 문제)
  (b) codex/opencode dispatch/harvest/doctor 8건: 런타임 프로젝션 미설치 환경 의존. 둘 다 이번 변경과 무관.
- `tools/check-adaptation-boundary.sh` — FAIL=2 (둘 다 fleet 소유 baseline: test_f15_rows.py·test_f14_title.py, 범위 외).
- adapter .py `py_compile` OK. 테스트가 남긴 `__pycache__` 커밋 전 정리 완료.

> inline 이라 스테이지별 headless startup·프로필 토큰 비용은 발생하지 않음(분사 오버헤드 0). 계측 목적은 opt-out 부여
> 사실의 감사 기록이 1차 — SD-OPEN-1 손익 임계 표본에는 inline 사이클이라 미기여(분사 표본 아님).
