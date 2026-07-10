# stage-dispatch Phase 3 — 사이클 계측 (SD-OPEN-1 / SD-OPEN-2 / 오케스트레이션 방식)

> 기록 주체: depth-1 conductor(stage-dispatch-phase3, parent_sid 9875d94c). Phase 2 표본(`../../2026-07-10_stage-dispatch-phase2/_internal/metrics.md`)과 비교 가능하게 기록.

## 오케스트레이션 방식 — 이 사이클의 conductor 결정 (계약 대비 명시)

**계약(depth contract)**: depth-1 conductor 는 `standard+` 파이프의 각 스테이지(plan/execute/test/report)를 depth-2 headless 로 분사해야 한다.

**이 사이클 실제**: **inline 실행**(스테이지 분사 안 함) + SD-16(d) 검증만 실제 depth-2 병렬 분사. 이유(커밋 전 사전 노출 성격의 conductor 판단 기록):
1. **메타-리스크**: 이번 작업 대상이 _분사 인프라 자체_(`dispatch-headless.py`·`dispatch-wait`·`dispatch-liveness`)다. 그 코드를 편집하는 스테이지를 그 코드로 분사하면, 편집 중 버그가 자기 분사를 깨는 순환 노출. 특히 고치려는 버그(SD-15 limit-즉사)에 스테이지가 그대로 노출된다.
2. **응집·소규모**: SD-15/16 은 wrapper+shell+core 문구가 한 몸으로 맞물린 응집 변경(총 소스 ~5파일·문서 2곳)이라 한 컨텍스트에 담긴다 — Phase 2 가 노린 "owner 컨텍스트 비대" 이득이 이 규모에선 미미.
3. **검증이 곧 도그푸딩**: SD-16(d) 동시성 fixture 가 _실제_ depth-2 병렬 분사(3워커)를 돌려 계약을 실측 — 분사 기계를 이 사이클에서도 행사한다.

⇒ 계약과의 drift 를 _은폐하지 않고_ 여기 명시. 순수 인프라-자기수정 사이클의 예외적 판단이며, 다음 일반 코드 사이클은 스테이지 분사 기본으로 복귀.

## 스테이지 wall-clock (inline, conductor 자기 관측, 2026-07-10 KST)

| 스테이지 | 방식 | 대략 wall-clock | 산출물 |
|---|---|---|---|
| research(runtime-currentness) | inline + WebSearch ×2 | ~2 min | usage 표면 조사(§ 아래) |
| code-plan | inline | ~5 min | plan/plan.md |
| code-execute | inline | ~25 min | 소스 5파일·문서 2곳·테스트 3파일 |
| code-test | inline + fixture 분사 | ~10 min | test_logs/*, boundary check |
| code-report | inline | ~5 min | final_report·metrics |

Phase 2(대규모 51파일 분사: plan 974s/execute 2220s/test 930s)와 달리 이 사이클은 소규모 인프라 증분이라 스테이지별 실작업이 짧다 — SD-OPEN-1 의 **소규모 스테이지 표본**에 해당(inline 이 분사보다 유리한 구간의 데이터점). 분사 오버헤드(세션 startup~수십초)가 스테이지 실작업(수 분) 대비 무시 못 할 비중이 되는 경계 근처.

## 프로필 사용 여부 (SD-12)

- 이 사이클은 inline 이라 `--profile` 미사용. SD-16(d) fixture 의 분사는 fake `claude`(계측 대상 아님)라 프로필 A/B 계측 없음.
- **full-bootstrap vs 최소 프로필 A/B 는 여전히 미확보** — Phase 2 와 동일하게 다음 실-분사 사이클 과제로 이월(SD-OPEN-1 데이터).

## SD-16 runtime-currentness 조사 결과 (2026-07, 사용량 조회 표면)

- **Claude Code**: `/usage` = 대화형 슬래시 커맨드뿐. 스크립트 가능한 headless 사용량 CLI/API 부재.
- **Codex CLI**: `/status` = 대화형. 프로그래밍 노출은 open feature request(openai/codex#15281). `codex /reset` 도 대화형.
- ⇒ **공식 스크립트 표면 부재** 확정 → `usage-check.sh` 는 spec §8.5.7c 지시대로 **보수 구현**(jobs.log `dead-*limit*` 마커 + reset 캐시). `ok`=알려진 차단 없음(가용 보장 아님)·`limited(reset)`=활성 마커·`unknown`=판정 불가. 한계를 헬퍼 헤더·OPERATIONS §5.10 ⑧·dev-pipeline 에 명시.

## SD-OPEN-2 관찰 (스테이지 SessionEnd mem curator)

- inline 사이클이라 다중 스테이지 세션 curator 순차 기동 없음 — 이 사이클은 관찰 표본 아님. Phase 2 관찰(오염 징후 없음) 유지, 개입 없음.

## SD-16(c) fleet 연속성 실측

- SD-15 fake-death 테스트·SD-16(d) fixture 의 jobs.log row 전부 `harness=claude`·`owner_harness=claude`·`parent_sid=…`·`parent=…`·`worker_role=…` 를 담아 append 됨(append_job 기존 계약 불변) → cross-harness row 연속성 유지 확인. row 마감(SD-15) 후에도 pipe 의 continuity 키는 보존(status 만 open→done, note/reset 추가).
