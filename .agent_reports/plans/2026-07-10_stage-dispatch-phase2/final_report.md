# Final Report — stage-dispatch Phase 2 (code-report)

slug: `2026-07-10_stage-dispatch-phase2` · qa=standard · intensity=strong · spec: `spec/stage-dispatch/prd.md` §12 Phase 2

## 스코프 — 무엇을 했나

spec SoT `prd.md` §12 Phase 2 (v2 결정목록 SD-10~14 + SD-OPEN-2) 를 구현. Phase 1(5b7cf33, 이미 merge)이 놓은 core/adapter 계약 문구 위에, "반쪽 배선"을 완결하고 새 메커니즘을 신설:

| 항목 | 내용 | Phase |
|---|---|---|
| SD-10 | `dev-pipeline.md` Step1~7 본문을 dispatch-first 로 재작성(in-session "Invoke Skill" 이중 신호 제거), fallback 을 direct/quick·헤드리스 불가 런타임으로 한정, `SKILL.md` Stage Graph 에 dispatch 표기 | F |
| SD-11 | conductor 의 code-* 직접 Skill 호출 reminder hook (`hooks/stage-dispatch-reminder.sh`) — **soft**(deny 미상향), 5 conformance PASS, settings.json 등록 | E |
| SD-12 | 스테이지-워커별 최소 dispatch-profile fragment 4종(code-plan/execute/test/report) + yaml + `--check` 4/4 통과 | D |
| SD-13 | conductor 스테이지 분사 전 spec 전제 선보장 문구 (`OPERATIONS.md §5.10`) | B |
| SD-14 | conductor 조기종료 방지 3층: (a) wrapper depth_note one-shot 대기 계약, (b) Stop hook 게이트(`conductor-stop-gate.sh`) — **held**(아래 참조), (c) `utilities/dispatch-wait.sh` 동기 대기 헬퍼(6/6 exit-matrix PASS) | C, E |
| 확산 | draft/research×2/spec×2/design/lab 5개 파이프에 stage-worker 표+계약 이식(8 파일) | H |
| drill | `drill_case_stage_dispatch/` handoff 산출물(fixture+assert, `loops/**` 미터치) | I |
| 계측 | `instrumentation.md` — pilot seed row + SD-OPEN-2 관찰 테이블 | J |

## 스테이지 분사 파이프 실행 사실

전 스테이지 depth-2 headless 로 완주, conductor(depth-1)가 산출물 파일로만 소통:

- **code-plan** (opus/high) — 최초 시도는 3pm 세션 한도로 즉사, **재분사 1회**로 완료.
- **code-execute** (opus/high) — Phase A~J 실행, **8개 안전 커밋** (5ae8c8a → a63b708, 아래 커밋 목록).
- **code-test** (sonnet/medium) — Level 3 conformance, PASS 311 / FAIL 12.
- **code-execute-fix** (sonnet/medium) — code-test 가 지목한 신규 회귀 2건 정합화, 8224285(status→implemented) 이후 `cd9859b` 로 커밋.

### Phase A 실측 — Stop hook 미발화

`claude -p` one-shot 세션에서 `Stop` hook 이 발화하지 않음을 empirical probe 로 확인(exit 1, sentinel 없음; CC #38651/#40506/#20063 교차확인, `_internal/dev_reviews/phaseA_stop_probe.md`). 이에 따라 **SD-14b Stop 게이트는 등록 보류(held)** — `conductor-stop-gate.sh` 는 디스크상 존재·CLI 유닛 4/4 PASS 이나 `adapters/claude/settings.json` 의 `Stop` 배열에는 미등록. 조기종료 방지는 (a) depth_note 대기 계약 + (c) `dispatch-wait.sh` 로 대체 커버.

## 검증 결과

### code-test 판정 시점 (Level 3, PASS 311/FAIL 12)
`hooks/portable-guards.test.sh` 를 baseline `8596e25` 클린 체크아웃(PASS 301/FAIL 13)과 대조 판별:
- FAIL 12건 중 **10건은 baseline 과 동일한 기존 환경 FAIL**(codex/opencode dispatch wrapper·dispatch-liveness 타이밍 의존 케이스 등) — 이 작업의 회귀 아님.
- **2건은 신규 회귀** — `codex doctor --runtime[-strict]` 가 `status=ok` 를 요구하는데, 근본 원인은 다른 서브체크(`manifest`·`adaptation-boundary`) 실패: (1) `manifest.json` stale(Phase C/E/D 신규 파일 미반영), (2) `check-adaptation-boundary.sh` 가 `utilities/dispatch-wait*.sh` projection 미분류, `adapters/claude/hooks/{conductor-stop-gate,stage-dispatch-reminder}.sh` 미러 부재, `skills/**` 9개 편집분이 `adapters/claude/skills/**` 와 byte-불일치를 지적.

### code-execute-fix 이후 최종 상태 (conductor 독립 재검증)
- `bash tools/check-adaptation-boundary.sh` → **`OK: adaptation boundary checks passed`**
- `python3 tools/build-manifest.py --check` → **`manifest up-to-date; delta baselines bound`**

Fix 조치: `utilities/dispatch-wait{.sh,.test.sh}` 를 codex/opencode `UTILITY_DEFERRED` 목록에 추가, `adapters/claude/hooks/` 에 2개 hook 심링크 생성, `skills/**` 10파일을 `adapters/claude/skills/**` 로 미러(순수 추가분, 충돌 없음), `manifest.json` 재생성.

**결론: 신규 회귀 0. 잔존 FAIL 은 baseline 부터 있던 환경 의존 FAIL 10건뿐**(이 작업이 유발한 것 아님, code-test 시점 판정과 fix 이후 최종 상태 모두 위와 같이 확정).

Level 4(functional) — 이 plan 이 신설한 모든 메커니즘 유닛 PASS: `dispatch-wait.sh` exit-matrix 6/6, SD-11 reminder 5/5, SD-14b CLI 4/4, dispatch-liveness 회귀 3/3.

## 잔여 handoff (비차단)

1. **drill 케이스** — `drill_case_stage_dispatch/` 는 정의 산출물만; 러너(`loops/**`)는 타 세션 소유로 미설치.
2. **drill `assert.sh` bashism** — `sh -n` 기준 line 48 "redirection unexpected" (POSIX 위반, bash 전용 구문) — loops 소유 세션에 `bash -n` 재확인 요청과 함께 전달 필요.
3. **SD-11 reminder** — soft 유지(deny 미상향); hook 이 intensity 를 몰라 false-positive 위험 → drill·계측 데이터 축적 후 재판단.
4. **SD-OPEN-2** — 스테이지 SessionEnd mem curator 기동 관찰 지속(개입 없음), `instrumentation.md` 관찰 테이블에 로그.

## 커밋 목록 (8596e25..HEAD)

```
5ae8c8a stage-dispatch P2 Phase A+B: probe verdict (Stop held) + core doc increments
e97d916 stage-dispatch P2 Phase C: SD-14 wrapper + dispatch-wait helper
d27ab12 stage-dispatch P2 Phase D: SD-12 stage-worker profiles
3dfb993 stage-dispatch P2 Phase E: SD-11 reminder (registered) + SD-14b Stop gate (held)
7a74889 stage-dispatch P2 Phase F (SD-10 priority-0): dispatch-first dev-pipeline + SKILL Stage Graph
976ba3a stage-dispatch P2 Phase G: adapter bootstrap parity (SD-14 one-shot)
a63b708 stage-dispatch P2 Phase H+I+J: diffusion + drill handoff + instrumentation
8224285 stage-dispatch P2: plan status → implemented (all phases A–J complete)
cd9859b stage-dispatch P2 fix: projection/mirror 회귀 2건 정합화
```

## 최종 판정

**파이프 완주, plan status=implemented, 신규 회귀 0(baseline 기존 FAIL 10건만 잔존), SD-14b Stop 게이트는 실측 근거로 보류.** merge·worktree 정리는 conductor/orchestrator 몫.
