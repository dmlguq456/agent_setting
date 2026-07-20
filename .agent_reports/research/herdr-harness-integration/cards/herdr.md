# Card — Herdr

- 종류: agent-aware persistent terminal multiplexer
- 확인 버전: stable v0.7.4; local v0.6.6/protocol 12
- 강점: real PTY, workspace/tab/pane, detach/attach, SSH, status rollup, read/send/wait/events, direct agent attach
- 상태 권위: Claude/Codex는 integration이 session identity를 보고하고 lifecycle state는 screen manifest가 담당
- 제한: 새 approval UI는 idle fallback 가능; server restart는 live process를 보존하지 않음; screen history는 secret 위험
- 토론 판정: coordinator가 조합 가능하지만 built-in debate/consensus protocol 아님
- 보안: plugin/terminal input/worktree mutation을 신뢰·권한 경계로 취급
- 라이선스: AGPL-3.0-or-later 및 commercial dual-license 표기 확인 필요
- 채택 역할: optional PTY/session transport + secondary observer

## Sources

[Agents](https://herdr.dev/docs/agents/) · [Socket API](https://herdr.dev/docs/socket-api/) · [Session restore](https://herdr.dev/docs/session-state/) · [Persistence](https://herdr.dev/docs/persistence-remote/) · [Plugins](https://herdr.dev/docs/plugins/) · [GitHub](https://github.com/ogulcancelik/herdr)
