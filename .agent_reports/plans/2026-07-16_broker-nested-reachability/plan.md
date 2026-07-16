# Broker nested reachability — 생존증거 위계와 sandbox-독립 도달성 (SD-57)

> **상태: 철회 (2026-07-16, 구현 착수 전)** — spec v15(b50e4524) broker 폐기(SD-61~63)와 충돌, SD-57 구현 취소 명시. 근거·존속 가치는 `_internal/withdrawal.md`.

## Route

- Capability: `autopilot-code`
- Mode/intensity: `debug/standard`
- Spec significance: spec-backed — stage-dispatch PRD v14 §13.6.1 SD-57 (spec commit 47512630 선행)
- Governing contracts: SD-51~57, OPERATIONS §5.10, 사용자 진단 2026-07-16 항목 1

## Problem

1. `broker_status()`가 `/proc/<pid>/stat` exact 검증을 단일 하드 게이트로 사용 — PID 네임스페이스가 격리된 중첩 sandbox(depth-1 owner/worker)에서 항상 실패해, heartbeat·socket이 정상인 산 broker를 `broker-unavailable`로 오판한다. socket ping은 게이트 뒤에 있어 실행되지 않는다.
2. `ensure`가 같은 오판 후 flock을 획득하지 못하는 serve를 반복 spawn해 `broker-start-timeout`으로 끝난다(2026-07-16 fleet-depth2 준비 실측, pid 1057841/12701276). `stop`도 status 게이트에서 죽어 fenced shutdown에 도달하지 못한다.
3. socket connect 자체를 거부하는 sandbox(`network-operation-not-permitted` 계열)에서는 ping 기반 검증도 request 제출도 불가능 — 등록형 depth-2 dispatch가 전면 불능.

## Implementation

1. **생존증거 위계** (`utilities/dispatch-broker.py`): `process_evidence()` = live(exact 일치)/dead(ticks 불일치 관측)/unverifiable(`/proc` 부재) 3분류. unverifiable은 `broker.lock` 비블로킹 flock 프로브(획득=사망, 거부=프로세스 생존)로 판별하고, fenced socket ping(instance_id 대조)으로 프로토콜 생존을 확인한다. ping이 sandbox에 의해 거부(EPERM/EACCES)되면 lock 보유+fresh heartbeat(파일 증거)로 판정한다. ticks 불일치=확정 사망과 양성 증거 없는 fail-closed는 불변.
2. **전 클라이언트 경로 공통화**: `status`/`request`/`stop`/`ensure`가 같은 위계를 사용. `ensure`/`stop`의 교체·종료 대기는 `/proc` 대신 meta `state=stopped` 또는 lock 해제 관찰. 검증 불가 PID signal 전송·타 프로세스 lock unlink 금지 유지.
3. **durable file-spool transport**: client는 `requests/inbox/`에 envelope를 원자 publish하고 `requests/replies/`의 동일-이름 reply를 poll(socket 응답과 동일 스키마 — 오류·duplicate 포함). serve loop가 accept tick마다 inbox를 소비해 동일 `process_request`(per-request lease·idempotency·fencing 그대로)로 처리한다. `request --transport auto|socket|spool` — auto는 socket 우선, sandbox-denied 시 spool.
4. **미러 동기화**: `adapters/claude/utilities/{dispatch-broker.py,stage-dispatch-fallback.py}` byte-for-byte.
5. `plans/2026-07-16_fleet-depth2-retry-liveness` 플랜의 broker 복구 항목(구현 §3)은 본 사이클이 흡수 — 잔여 항목(F-25 attempt identity·newest-attempt)은 SD-58 사이클과 연계.

## Verification

- 신규 fixture: ① proc-invisible(살아있는 broker + `process_start_ticks` 비가시 패치)에서 status/request 성공·ensure 무회전·stop fenced shutdown, ② 사망 fixture(lock free + 메타 잔존)는 `broker-unavailable` fail-closed, ③ socket-denied(EPERM 패치)에서 spool 경유 request 성공 + idempotency/terminal 의미 동일, ④ spool 오류 reply(검증 실패)가 socket 오류 응답과 동일 스키마.
- 기존 `dispatch_broker.test.py` 15종 + `stage_dispatch_fallback.test.py` 회귀 0. 미러 parity. Python compile. zsh/bash 양쪽 CLI smoke.
- 실전 acceptance(SD-57 ④): root에서 ensure된 broker를 worker-유사 컨텍스트에서 같은 jobs metadata로 status 조회 + code-plan smoke request가 통과.

## Definition of done

- proc-invisible 컨텍스트에서 status/request/stop이 성공하고 ensure가 산 broker를 회전시키지 않는다.
- socket-denied 컨텍스트에서 spool로 request가 완주한다(authority·fail-closed 의미 불변).
- 사망/오염 fixture는 전부 기존대로 fail-closed. 전체 스위트 회귀 0 + 미러 parity + smoke 통과.
- merge 후 live broker 롤오버(in-flight 0 시점 shutdown→ensure).
