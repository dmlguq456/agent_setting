# Pipeline Summary

- intensity: standard
- separability: 테스트 기대값, adaptation guard, drill runner/case는 분리 가능하지만 동일 미러와 최종 gate를 공유하므로 한 worktree에서 순차 통합한다.
- implementation: in-session, no subagent
- implementation result: drill case는 공유하고 `DRILL_ADAPTER`가 runner만 선택한다. 모든 harness가 `--jobs > AGENT_DISPATCH_JOBS > <agent-home>/.dispatch/jobs.log` 한 원장을 사용하며 Fleet은 `/tmp/drill-*` fixture 하나로 합친다.
- verification: portable guards 336/0, Fleet 180/180, manifest/skill-conformance/adaptation-boundary, targeted Codex drill 및 g10 postfix replay.
- runtime note: 최종 g10 재실행은 Codex usage limit에서 turn 시작 전에 차단됐다. 직전 Codex 실행은 구현·실제 OpenCode child marker까지 완료했고, false-fail 원인이던 가짜 parent id 기대값은 실제 wrapper-resolved thread id로 교정해 동일 assert replay를 PASS했다.
