# 02 — Contracts and Standards

## 유지할 현재 계약

- portable 의미론은 `core/`가 소유하고 adapter는 투영한다.
- standard+ route는 depth-1 owner와 필요한 depth-2 stage worker를 사용하며 depth 3은 금지한다.
- `jobs.log` exact attempt, completion marker, liveness/harvest가 실행 결과의 권위다.
- worktree·artifact root·write preflight·cleanup gate를 유지한다.
- native subagent와 registered headless worker는 서로 다른 delegation surface다.

근거: `core/OPERATIONS.md` §5.10, 특히 delegation surface와 fallback/attempt 계약.

## Herdr 연동 계약

1. **Probe before use**: 설치 binary의 `herdr api schema`와 protocol을 확인하고 알려지지 않은 필드는 관대하게 처리한다. Herdr 공식 문서도 protocol 확인을 요구한다. [Socket API](https://herdr.dev/docs/socket-api/)
2. **Authority separation**:
   - job 완료/실패/재시도: 하네스 권위
   - pane 화면·attach·agent-visible state: Herdr 권위
   - 상충 시 Herdr가 exact attempt 완료를 덮어쓰지 않는다.
3. **Explicit binding**: Herdr-hosted worker만 `(session, workspace, tab, pane/terminal)`에 명시 결합한다.
4. **No ambient inheritance**: 일반 headless worker는 부모 pane의 `HERDR_*`를 상속하지 않는다.
5. **User control**: attach/input/kill/worktree mutation은 자동 관찰과 분리하고 명시적인 사용자 동작으로 둔다.
6. **Discussion envelope**: `discussion_id`, `round`, `sender_role`, `recipient_role`, `claim`, `evidence_refs`, `deadline`, `reply_to`를 하네스 artifact에 기록한다.

## 상태 정규화

Herdr의 `idle/working/blocked/done`은 UI·wait에 활용하되 `blocked` 탐지는 알려진 화면 패턴에 엄격하게 의존한다. 새 승인 UI는 idle fallback일 수 있다. [Agents status authority](https://herdr.dev/docs/agents/)
