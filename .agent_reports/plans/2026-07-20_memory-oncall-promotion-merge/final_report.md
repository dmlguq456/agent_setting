# Memory on-call proposal promotion 병합 보고서

## 결과

검토 대상 브랜치를 그대로 병합하지 않고 커밋별로 분리 심사했다.
`8ceb3cbd`의 유효한 on-call → improvement proposal bridge만 현재 계약에
맞게 보강·이식했고, 위험한 `35a0c75d`는 전부 제외했다.

- 구현 커밋: `5ab3c9037fd923446f453f64c745a39c9d97617b`
- `main` 병합 커밋: `eaaa89225d19fa9e4a8691a2abba65625cd1fc42`
- 원격 결과: `origin/main`에 `eaaa8922` 푸시 및 포함 확인. 이후 동시
  dispatch 작업 `d04ee778`이 그 위에 추가돼 현재 원격 선두가 됐다.
- handoff:
  `handoff_handoff-oncall-proposal-promotion_c634cc`를 푸시 후
  `pending → consumed`

## 엄격 검토 결론

### 선택 이식: `8ceb3cbd`

- 하나의 bounded single-line `incident_key`로 exact-key create/append
- lookup과 mutation을 동일 inbox lock 안에서 처리
- duplicate key ambiguity는 fail-closed
- recurrence evidence/history를 128개로 제한하고 state·base·human
  provenance 보존
- named collector는 `reproduced` 또는 `proposed`까지만 전이
- human-owned state가 한 번이라도 있었으면 자동 collector 전이 금지
- on-call은 memory log를 후보 신호로만 사용하고 full-body 확인과 현재
  로컬 증거 corroboration 후 제안만 기록
- 기존 manual actor와 worklog parser 호환성 유지

### 전부 제외: `35a0c75d`

이 커밋은 current D-42의 main-session-only memory lifecycle을 훼손하고,
worker 수 상한 위반, 최대 200개 repo full sync 증폭, cursor/journal 유실
가능성, 비트랜잭션 mutation, 사용자별 hard-coded 경로와 Claude 결합을
포함한다. `daily-curator` 계열 파일이나 동작은 하나도 병합하지 않았다.

## 계약·스펙

- root memory PRD: v19 → v20, 신규 D-43
- self-improvement-governance PRD: v1 → v2
- 기존 D-40~42 의미와 번호 유지
- 이전 PRD는 byte-exact snapshot으로 보존
- Codex/OpenCode는 local manual `loop-info` metadata만 갱신했으며 native
  executable loop 지원을 새로 주장하지 않았다.

## 검증

- 병합 후 focused 기능·회귀: `24/24 PASS`
- generated projection verifier: `29/29 PASS`
- portable guards: `355/355 PASS`
- manifest/generation/adaptation boundary/Skill conformance/runtime
  activation/extension lifecycle/managed release: 모두 `PASS`
- 상세 증적:
  `test_logs/test_report.md`

## 보존·정리

- 병합 당시 별도 작업 중이던
  `adapters/{claude,codex}/bin/dispatch-headless.py` 수정과 drill case
  2개는 건드리거나 병합 커밋에 포함하지 않았다. 해당 변경은 이후 동시
  workflow에서 독립 커밋 `d04ee778`로 완료됐다.
- cleanup 안전 검사는 `eligible`; linked worktree는 `removed`.
- `memory-oncall-promotion-merge` 브랜치는 rollback point로 유지했다.
- 실제 on-call/drill 활성화와 runtime-owned config·credential·session·DB
  직접 수정은 수행하지 않았다.

최종 판정: `PASS`, 원격 `main` 통합 완료.
