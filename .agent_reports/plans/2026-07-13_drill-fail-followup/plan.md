# Plan — drill FAIL follow-up

## 목표

- portable guards의 재현된 8개 실패를 canonical 계약에 맞게 제거한다.
- 같은 drill case를 선택한 runtime adapter로 실행하고, Codex가 fixture worktree와 공유 dispatch registry를 쓸 수 있게 한다.
- FAIL 진단과 judge도 선택 adapter를 사용하며 Claude Code를 암묵 호출하지 않는다.

## 구현 순서

1. liveness fixture runtime root와 OpenCode role 기대값을 실제 계약에 맞춘다.
2. 기계화된 `harness install/verify`를 검사하도록 adaptation guard를 갱신한다.
3. `skill-conformance`의 portable/Claude projection 결정을 기록하고 collapse한다.
4. Codex runner writable scope와 adapter-neutral g10/diagnosis 계약을 반영한다.
5. conformance와 대상 Codex drill 3개를 재실행한다.

## 경계

- Claude Code CLI는 실행하지 않는다 (`CLAUDE_BIN=/bin/false`).
- push는 하지 않고, 검증된 worktree commit은 사용자 요청대로 main 세션에서 병합한다.
- root `loops/` 변경은 `adapters/claude/loops/`에 동일 반영한다.
