# stage-dispatch Phase 2 — conductor 계측 로그 (SD-OPEN-1 / SD-OPEN-2)

> 기록 주체: depth-1 conductor(stage-dispatch-phase2, parent_sid 9875d94c). 스테이지 본문 미독, 분사→종료 wall-clock·재분사·SessionEnd 관찰만. 스테이지 내부 토큰은 각 스테이지 instrumentation.md(Phase J) 참조.

## 스테이지 분사 wall-clock (dispatch → 프로세스 종료, conductor 관측, 2026-07-10 KST)

| 스테이지 | slug | 모델(role) | 분사 | 종료 | wall-clock | 재분사 | 산출물 |
|---|---|---|---|---|---|---|---|
| code-plan | ...-code-plan | opus/high (deep maker) | 15:06:10 | ~15:22:24 | **~16.2 min** | **YES ×1** | plan.md(392줄)·plan_ko.md |
| code-execute | ...-code-execute | opus/high (deep maker) | ~15:24:20 | ~16:02 | **~37 min** | no | 소스 51파일·8커밋·checklist·dev_logs·drill handoff |
| code-test | ...-code-test | sonnet/medium (fast reviewer) | ~16:05:40 | ~16:21 | **~15.5 min** | no | test_report.md(Level 3) |
| code-execute-fix | ...-code-execute-fix | sonnet/medium (fast implementer) | ~16:24:20 | ~16:32 | **~8 min** | (=파이프 retry ×1) | projection/mirror 회귀 2건 정합·1커밋 |
| code-report | ...-code-report | sonnet/low (fast writer) | ~16:33 | (진행) | — | no | final_report·pipeline_summary |

**재분사 사유 기록**:
- code-plan 최초 분사(14:17)는 Anthropic **세션 한도**("You've hit your session limit · resets 3pm")로 즉사 — dispatch 버그 아님(디렉토리·산출물 0). 3pm 리셋 후 15:06 재분사로 완주. → conductor 는 완료 알림만 믿지 않고 `pgrep`+산출물 존재로 liveness 판정, 죽은 row 는 done 처리 후 재분사(SD-6 재사용: 부분 산출물 없어 처음부터).
- code-execute-fix 는 실패 재시도가 아니라 code-test 가 확정한 **신규 회귀 2건**(projection/mirror 미동기화)의 집중 fix — qa=standard 파이프-레벨 retry ×1(§4). 산출물 재사용, plan status 불변.

## SD-OPEN-1 표본 (마이크로-스테이지 inline 임계 — 확정 금지, 누적만)

- Phase 1 pilot 1표본: plan 218s / execute 255s / test 46s / report 28s.
- **Phase 2 표본(대규모 작업)**: plan ~974s / execute ~2220s / test ~930s / fix ~480s. Phase 1 대비 10~40× — 작업 규모(51파일·10 phase)에 스케일. 스테이지 분사 오버헤드(세션 startup·bootstrap 로드)는 이 규모에서 실작업 대비 무시가능 → `standard+` 분사 이득 재확인. inline 임계 확정은 여전히 보류(SD-OPEN-1, 소규모 스테이지 표본 부족).
- **full bootstrap vs 최소 프로필**: 본 사이클은 `--profile` 없이 full bootstrap 로 분사(SD-12 프로필은 이 사이클이 *생성*한 산출물이라 자기 자신엔 미적용). full-bootstrap baseline 만 확보 — 프로필 적용 비교는 다음 사이클 과제.

## SD-OPEN-2 관찰 (스테이지 SessionEnd mem curator 기동 — 개입 금지, 관찰만)

- code-execute·code-test·fix 각 스테이지가 종료 직후 수 분간 `ALIVE(teardown)` 상태 지속 관측 — SessionEnd 훅(mem distiller/curator) 기동과 정합.
- conductor 관측 범위에서 **메모리 오염·중복 add 징후 없음**. 다만 다중 스테이지(plan/execute/test/fix/report 5세션)가 순차로 curator 를 돌리는 비용·동시성은 정량화 안 함 — Phase 2 도 **관찰만**, 개입 결정 유보(증거 후).
- registry: SD-14b② 갭 수정(Phase C) 후 code-test/fix/report 분사는 통합 registry(`$HOME/agent_setting/.dispatch/jobs.log`)에 등록 확인 — wrapper·dispatch-liveness 가 동일 registry 를 봄(수정 효력 실측).

## 게이트 판정 이력 (conductor)

- code-plan gate: status=planned + 자체리뷰 통과 → PASS(§8 마이크로-스테이지 plan-check inline).
- code-test gate: Level 3, 신규 회귀 2건 → **retry 분기**(code-execute-fix 분사).
- fix 후 독립 재검증: `bash tools/check-adaptation-boundary.sh` → PASS(FAIL 0), `build-manifest.py --check` up-to-date → 신규 회귀 0, 잔존 baseline FAIL 10건뿐 → 파이프 통과.

## 후속 정비 — drill 케이스 upkeep (2026-07-11, worktree drill-case-upkeep)

> 후속 사이클: Phase 2 가 handoff 한 `drill_case_stage_dispatch/` 케이스 정의를 (1) assert.sh POSIX 정합 (2) SD-17 separability 기록 검증 추가로 정비. depth-1 capability-owner(autopilot-code --mode dev --intensity standard, parent=main).

### SD-17 separability 판정 (본 upkeep 자기적용 — 기록 의무 이행, §8.7)
- **판정: 비분리(non-separable) → inline 처리**. 근거: 편집 표면이 단일 파일(assert.sh) 안 HARD/SOFT 블록의 **공유 semantic anchor·순차 boundary 결합**(POSIX 수정·신규 HARD 4·헤더 주석이 같은 구조를 순차로 건드림) + fixture/README 정합이 assert 변경에 종속. 스테이지 산출물 계약이 완결적이지도, 편집이 파일-분리되지도 않음 → separable 요건 미충족.
- **따라서 depth-2 스테이지 분사 없이 inline**(§8.7 비분리 inline 허용). 분리 가능한 독립 부분 없음(단일 파일 중심) → in-session 병렬 워커도 불요. 자기수정 예외(SD-11b(c)) 아님 — 분사 launch 경로가 아니라 drill 케이스 산출물 편집.
- 이 문단이 SD-17 "기록 없는 inline = 위반" 을 막는 감사 기록. (마침 본 upkeep 이 추가한 assert HARD 4 가 검사하는 바로 그 항목 — 자기 dogfooding.)

### 스테이지 wall-clock·분사 방식 (소규모 표본 — Phase 2·3 대비)
| 단계 | 방식 | 대략 규모 | 비고 |
|---|---|---|---|
| 진입·SoT Read(prd §8.5.5/§8.7)·타깃 4파일 Read | inline | 6 tool call | 분사 없음 |
| assert.sh 편집(shebang 주석·HARD3 POSIX·HARD4 SD-17) + fixture/README 정합 | inline | 4 Edit | 단일 세션 |
| 검증(`sh -n`×3 + mock fixture 양성 3·음성 2 = 5케이스 경계) | inline | 2 Bash | 아래 결과 |
- **분사 방식**: 전 구간 inline(depth-1 워커 단일 세션, depth-2 스테이지 분사 0) — 비분리 판정의 귀결. 소규모(단일 파일 중심·3 Edit급) + 경계-결합이라 분사 오버헤드가 순손해였을 표본 = SD-OPEN-1 의 "질적 축(separability)이 크기 축과 함께 inline 을 정당화" 사례.
- **프로필 사용**: 없음 — headless worker 로 full bootstrap 진입(`--profile` 미배선). Phase 2 와 동일 baseline.
- **SD-OPEN-1 표본 대비**: Phase 1 pilot(plan 218s…) / Phase 2(plan ~974s…)은 _분사된_ 대규모 스테이지. 본 upkeep 은 _inline 소규모_ 반대극 표본 — 분사 임계 아래 구간의 데이터점. 확정은 여전히 보류(누적만).

### 검증 결과
- `sh -n` 게이트: assert.sh·fixture.sh·config **3파일 전부 OK**(dash). 기존 실패는 assert.sh:48 프로세스 치환(`done < <(...)`) 1건 — command-substitution 순회로 대체.
- assert.sh mock-fixture 구동(경계 5케이스, AGENT_HOME 격리 registry): A 분사(depth-2 execute row)→exit0 / B inline+separability 기록→exit0 OK(soft) / C inline+metrics 무-separability→exit1 FAIL / D inline+metrics 부재→exit1 FAIL / E turn-cap(산출물 무)→exit0 비트리거. **양성·음성 모두 기대 일치**.
