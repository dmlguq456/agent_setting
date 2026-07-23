# 등록형 dispatch completion join — 최종 변경 보고서

## 결과

Codex/Claude의 적극적인 registered-headless 분사와 Fleet 가시성은 그대로
유지하면서, 자식 작업이 끝날 때까지 부모 LLM이 반복적으로 깨어나
`wait`·로그 읽기·git/source 검사를 수행하던 경로를 runtime-owned completion
join으로 교체했다. 정상 경로에서는 부모 모델이 자식 등록 후 즉시 turn을
양보하고, 비모델 supervisor가 정확한 자식 batch를 기다린 다음 동일한 Codex
thread 또는 Claude session을 batch당 한 번만 재개한다.

## 근본 원인과 수정

기존 SD-14는 Claude `-p` 환경의 same-turn polling 우회책을 portable 기본
계약처럼 사용했다. Codex에는 완료 이벤트를 부모 turn으로 전달하는 bridge가
없었기 때문에, 대기 시간도 모델 turn으로 소비됐고 비정상 종료 시 등록 row와
실제 프로세스가 분리되어 orphan이 남을 수 있었다.

수정된 소유권은 다음과 같다.

| 상태 | 부모 모델에 허용되는 동작 | 대기 소유자 |
|---|---|---|
| open 자식 없음 | 정상 route 작업 | 부모 모델 |
| undelivered open batch | 같은 부모의 정확한 sibling `dispatch-node --action start`만 | runtime supervisor |
| delivered open batch | 전달된 attempt의 정확한 harvest만 | runtime supervisor |
| state 누락/손상 | recovery용 정확한 harvest만 | fail-closed guard |

첫 번째 자식이 열렸다는 이유로 두 번째 sibling 분사를 막지 않으며, batch가
전달된 뒤에는 wait, source/git 검사, raw 로그 읽기, foreign dispatch를 모두
차단한다. 이 구분이 strong 경로에서 depth-2 자식 두 개가 동시에 Fleet에
나타나지 않았던 직접 원인도 함께 해결한다.

## 구현 내용

- `dispatch_completion_join.py`: `parent_attempt_id`에 정확히 귀속된 모든 direct
  child를 snapshot/join하고 raw 출력 없이 bounded typed receipt만 만든다.
- `codex-app-server-supervisor.py`: 하나의 App Server thread에서 초기 turn과
  batch별 continuation을 관리하며 최종 handoff terminal 한 건만 기록한다.
- `claude-session-supervisor.py`: `--session-id`/`--resume`로 동일 세션을 이어가고
  command-scoped `--settings` hook을 주입한다. 사용자 Claude 설정은 변경하지 않는다.
- Codex native PreToolUse와 Claude command-scoped PreToolUse가 동일한 two-phase
  state machine을 적용한다.
- Codex/Claude dispatch wrapper는 `standard+` owner에서 runtime probe가 통과하면
  supervised delivery를 선택하고, 불가하면 checked poll fallback임을 명시한다.
- owner watcher와 orphan reconcile이 attempt-scoped supervisor state까지 정확히
  제거한다. 정상 supervisor 종료도 `finally`에서 동일 state를 제거한다.
- terminal 진단은 마지막 supervised turn에만 한정하고 Codex의 중복 final
  `agent_message`를 제거했다.

## 검증

- completion join/supervisor/phase guard/orphan/terminal/wrapper/conformance 묶음:
  90/90 PASS, parent capture 34건 확인.
- portable guard 전체: `PASS=356 FAIL=0`.
- adaptation boundary와 `git diff --check`: PASS.
- Codex App Server live same-thread two-turn smoke: PASS.
- Claude Code live same-session resume 및 command-scoped wildcard PreToolUse 차단:
  PASS; 사용자 설정 변경 0.
- 독립 registered-headless Claude round-3 감사: high/medium 0, 보고서 PASS.

독립 감사 worker는 보고서를 정상 작성했지만 마지막 응답에 부가 문장을 넣어
strict 3-line terminal envelope가 거부됐다. 해당 Fleet row는 명시적으로 닫았고,
보고서 내용만 감사 증거로 사용했다. terminal PASS를 허위로 주장하지 않는다.
세부 검증은 `test_logs/verification.md`, 감사 내용은
`_internal/dev_reviews/round_3.md`에 있다.

## 최종 운영 상태

- open headless job: 0
- orphaned conductor job: 0
- current-session suspect/dead open row: 0
- 남은 supervisor state file: 0

## 통합 상태

- source main commit: `9c0ecae6`
- canonical spec/report commit: `d00a91b3`
- integration merge: `1145976d`
- push: `origin/main` 반영 완료
- guarded worktree cleanup: `status=removed`, stale registry row 0
