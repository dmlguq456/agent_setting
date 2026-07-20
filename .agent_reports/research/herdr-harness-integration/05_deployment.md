# 05 — Deployment Considerations

## 단계적 배포

| 단계 | 배포 단위 | 실패 시 영향 | rollback |
|---|---|---|---|
| P0 probe/guard | preflight + hook composition + env scrub | 상태 오염 방지 | Herdr bridge만 비활성 |
| P1 observe | Fleet optional collector | 보조 UI만 degraded | collector off |
| P2 discuss | discussion driver + artifacts | 해당 discussion transport fallback | native/file handoff |
| P3 host | selected job `herdr-pty` transport | 해당 job만 headless fallback | 기존 dispatcher |
| P4 remote | SSH/direct attach/plugin | remote 기능만 비활성 | local-only |

## 운영 주의

- 현 0.6.6을 stable 0.7.4로 올릴 때 server restart와 live process 보존을 별도로 계획한다. detach는 프로세스를 유지하지만 full restart는 그렇지 않다. [Session state](https://herdr.dev/docs/session-state/)
- Claude v4/Codex v4 integration은 최신 native restore 최소 버전(각 6/5)보다 낮다. upgrade 뒤 integration 재설치와 실제 session reference 보고를 검증한다.
- pane screen history는 기본 off이며 secret/token/prompt가 포함될 수 있다. 자동 활성화하지 않는다.
- plugin은 일반 사용자 권한으로 실행되는 신뢰 코드다. 출처 검토와 allowlist가 필요하다. [Plugins](https://herdr.dev/docs/plugins/)
- Herdr의 worktree create/remove는 초기 통합에서 사용하지 않는다. 현재 하네스의 branch/artifact/cleanup authority를 유지한다.
- Herdr가 server/process를 살려도 종료된 Codex root turn을 자동으로 재개시킨다는 뜻은 아니다. `runtime-watch`의 scheduled follow-up/current-turn wait/fallback 계약은 그대로다.
