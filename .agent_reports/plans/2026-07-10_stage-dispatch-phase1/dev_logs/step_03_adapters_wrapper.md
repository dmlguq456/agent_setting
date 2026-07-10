# Step 3 — 어댑터 bootstrap + wrapper 증분 (surfaces 10-12)

core-first 게이트: 어댑터 편집 시도 시 hook 이 "마지막 core Read 이후 core 갱신" 을 잡아 DENY → 편집한 `core/OPERATIONS.md §5.10` 재-Read 후 어댑터 편집 진행 (게이트 정상 동작 확인).

| Surface | 파일 | 변경 |
|---|---|---|
| 10 | `adapters/claude/CLAUDE.md §0(C)` | "분사는 main 전용·깊이 1" → main 은 depth-1 conductor 분사, conductor 가 `standard+` 스테이지를 depth-2 headless 로 분사(산출물 파일 소통, verdict만), in-session 격리 한계가 스테이지 분사 정당화, direct/quick·마이크로 inline·depth 3+ 금지. |
| 11 | `adapters/codex/AGENTS.md` · `adapters/opencode/AGENTS.md` | dispatch 문단의 "depth 2 by depth-1 owner under standard+" 뒤에 depth-2 두 용법(리뷰 sub-worker / 스테이지-워커=standard+ 기본, `--worker-role code-*`, file-only handoff, code-execute 단독 소스 mutation, depth 3+ 금지) 병기. 3어댑터 동형 문구. |
| 12 | `adapters/claude/bin/dispatch-headless.py` | **재작성 X** (SD-9). `depth_note` 를 depth/worker_role-aware 3분기로: depth-2+`code-*` = 스테이지-워커 계약(입력=산출물 파일·write 클래스·no re-dispatch·verdict 반환), depth-2 기타 = 리뷰 sub-worker(read-only 기본), depth-1 = conductor(스테이지 분사 안내). 기존 depth/parent/worker_role/owner/role_map/게이트는 그대로. |

## Wrapper 검증
- `python3 -m py_compile adapters/claude/bin/dispatch-headless.py` → OK
- `dispatch_prompt` 3분기 실측 (함수 직접 호출):
  - depth2 code-execute → "depth-2 pipeline stage-worker ('code-execute')" ✅
  - depth2 verifier → "depth-2 review sub-worker" ✅
  - depth1 → "depth 1 is a capability-owner worker ... thin conductor" ✅
- `--dry-run` 정상, `job_registry` 는 `<AGENT_HOME|worktree>/.dispatch/jobs.log` 기본이며 `--jobs <path>` 로 fixture-local 레지스트리 지정 가능 (pilot 오염 방지 경로 확인).

Decision: stage-dispatch helper 신설 보류 (SD-9 — pilot 후 판정). wrapper 는 depth=2/parent/worker_role 로 이미 스테이지 분사 가능, 유일 갭이던 depth-1 고정 프롬프트만 depth-aware 로 보강.
