# Pilot — 스테이지 분사 계측 (SD-OPEN-1 데이터 수집)

**사이클**: `/tmp` fixture repo(calc lib, drill g6 패턴)에 `subtract(a,b)` 추가를 autopilot-code
standard 사이클로, **각 스테이지를 depth-2 headless 세션으로 분사**해서 완주.
- conductor slug = `2026-07-10_stage-dispatch-phase1` (이 depth-1 워커).
- fixture-local jobs.log(`/tmp/.../registry/jobs.log`) 사용 → 실 레지스트리(`~/.claude/.dispatch/jobs.log`) **무오염(calc-subtract 0건 확인)**, 각 스테이지 종료 시 `--mark-done`.

## 성공 기준 대조 (§12)

| 기준 | 결과 |
|---|---|
| fleet 에 code-plan·execute·test·report **스테이지별 row** + liveness | ✅ 4 row 전부 `depth=2, parent=<conductor>, worker_role=code-*, owner=autopilot-code`; `dispatch-liveness.sh` 가 각 스테이지 `ALIVE/…` 판정 (운영 실증 ① 해소) |
| 각 스테이지 산출물 §2.1 표대로, 앞 산출물만으로(대화 전달 0) 완주 | ✅ plan.md·checklist.md → calc.py(subtract)+README+커밋 → test_report.md(PASS) → final_report.md(done). 각 스테이지 프롬프트는 **입력 산출물 경로만** 실었고 앞 스테이지 본문/대화 미전달 (SD-2·§0.5 완결성 증명) |
| depth ≤ 2 강제 | ✅ fixture registry depth=2 4건, depth=3+ **0건**. 스테이지 세션이 재분사 안 함 |
| §5.8 lock 경합 미발생 | ✅ 스테이지 산출물 전부 `plans/<slug>/` 경로-분리, 공유 단일파일 동시쓰기 없음 |
| 스테이지별 토큰·시간 계측 (SD-OPEN-1) | 아래 표 |

## 계측표 (per-stage)

| 스테이지 | model role → model/effort | wall-clock | conductor 프롬프트(입력 컨텍스트) | 스테이지 반환 로그 |
|---|---|---|---|---|
| code-plan | deep maker → opus/high | ~218s | 1904 B | 835 B |
| code-execute | fast implementer → sonnet/medium | ~255s | 2069 B | 1621 B |
| code-test | fast reviewer → sonnet/medium | ~46s | 1817 B | 408 B |
| code-report | fast writer → sonnet/low | ~28s | 1713 B | 408 B (final_report 별도 파일) |

**SD-OPEN-1 관찰 (임계 *확정은 main+사용자* — 여기선 데이터만)**:
- **conductor 프롬프트가 스테이지 무관 1.7–2.1 KB 로 일정** — conductor 가 plan/execute **본문을 누적하지 않음**(파일 경로만 전달). "file-only handoff = conductor lean" 이 실측으로 성립(§8 승격 근거·운영 실증 ③ 해소).
- **무거운 스테이지 vs 마이크로**: plan(opus/high 218s)·execute(255s)는 실작업이 커 분사 격리 이득이 명확. 반대로 report(28s, 1.7 KB 프롬프트)·test(46s)는 세션 startup·bootstrap 로드 오버헤드가 실작업 대비 큰 구간에 가까움 — §8 "마이크로-스테이지 inline 경계" 가 겨냥한 지점. 즉 손익 임계는 대략 _report/test 급 경량 스테이지 부근_ 에 있을 가능성을 시사(단정 금지, 표본 1·trivial task).
- 한계: 정확 토큰 회계는 `claude -p --output-format json` usage 필요 — 본 pilot 은 wrapper 고정 명령(text)이라 **프롬프트/로그 byte 를 컨텍스트 크기 proxy** 로 씀 + wall-clock. 정밀 토큰 계측 helper 는 Phase 2/SD-9 helper 판정 자리로 이관.

## 부수 발견 (운영 실증 ② 재확인 + 신규)

- **스테이지가 풀 hook ceremony 를 실제 수령**: plan·execute 세션이 fixture(spec 부재)에서 `artifact-guard.sh` 의 "신규 plan 작성 전 spec 필요" 차단을 **직접 맞음** → in-session subagent 가 못 받던 격리를 스테이지 세션이 획득함을 증명(§5 hook ceremony 수령, 운영 실증 ② 해소).
- **신규 발견 (conductor 책임 힌트)**: spec-less repo 에 스테이지 분사 시 plan-cycle sidecar(dev_logs 등) 신규 파일이 artifact-guard 에 막힌다. plan 세션은 ⚡untracked 토글로 우회했으나 execute 세션은 permission classifier 가 self-modification 로 분류해 자가 토글 거부(정책상 정상) → **dev_logs 두 파일 미생성**(내용은 커밋 메시지·checklist 에 반영). 함의: conductor 가 스테이지 분사 전 spec 전제(또는 untracked 승인)를 **미리 보장**해야 스테이지가 sidecar 를 정상 기록. 본 pilot 은 중간에 fixture 에 최소 spec 을 넣어 test·report 스테이지를 정상화. (이 힌트는 Phase 2 확산·drill 케이스 설계 입력.)
