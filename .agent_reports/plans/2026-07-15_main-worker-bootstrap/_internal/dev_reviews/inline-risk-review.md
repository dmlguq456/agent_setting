# Inline risk review

독립 agent review는 이번 세션의 no-subagent 정책 때문에 수행하지 않았으며,
`qa-policy thorough code`의 fallback에 따라 inline review로 기록한다.

- PASS: 모든 worker 판별은 fail-closed OR이며 main/default가 worker 증거를
  덮어쓰지 않는다.
- PASS: distill/SessionEnd/turn-nudge gate가 store, stamp, counter, detached spawn
  이전에 위치한다.
- PASS: OpenCode worker plugin은 lifecycle context만 생략하고 write guard와
  liveness heartbeat를 유지한다.
- PASS: Claude runtime settings 병합은 model, effort, Orca hooks 등 사용자 소유
  필드를 변경하지 않았다.
- PASS: native subagent event는 main SessionStart/UserPromptSubmit/SessionEnd와
  별도 runtime event이며, 등록된 main lifecycle을 재사용하지 않는다.
- 발견/수정: Codex freeform apply_patch payload의 중첩 envelope를 재귀 검색하도록
  보완했고 회귀 테스트를 추가했다.
- 잔여 운영 안전장치: distill 및 Fleet title kill switch는 계속 ON이다.
- 동시 작업 격리: 별도 Claude main이 수정 중인 Orca/Fleet 표시 변경은 이
  구현의 소유 범위와 분리해 커밋 대상으로 취급하지 않는다.
