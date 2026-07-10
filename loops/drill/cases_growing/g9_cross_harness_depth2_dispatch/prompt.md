실제 headless 런타임은 실행하지 말고, 이 fixture repo 안의 `.dispatch/jobs.log`에 cross-harness depth-2 분사 registry 예시를 작성해줘.

요구사항:
- 표준 6필드 TSV jobs.log 형식이어야 함: `<ISO>	<status>	<repo>	<worktree>	<slug>	<pipe metadata>`.
- `status`는 fleet collector가 live row로 읽는 `open`을 사용. `registered` 같은 임의 상태 금지.
- 6번째 `pipe metadata`는 쉼표로 구분된 `key=value` 목록이어야 함. 예: `capability=autopilot-code,mode=dev,qa=standard,...`. 공백 구분 metadata 금지.
- depth 1 owner row 1개: slug `xh-depth2-owner`, `capability=autopilot-code`, `mode=dev`, `qa=standard`, `intensity=thorough`, `depth=1`, `harness=codex`, `parent_sid=drill-parent-session`, `parent_cwd=<현재 repo 경로>`, `worker_role=capability-owner`, `owner=autopilot-code`.
- depth 2 worker row 2개 이상: 모두 `parent=xh-depth2-owner`, `depth=2`, `parent_sid=drill-parent-session`, `parent_cwd=<현재 repo 경로>`를 포함.
- depth 2 worker들은 서로 다른 하네스를 써야 하며, 최소 `harness=claude`와 `harness=opencode`가 하나씩 있어야 함.
- 실제 `codex`, `claude`, `opencode` 명령을 실행하지 말 것. registry 모델링만 수행.
