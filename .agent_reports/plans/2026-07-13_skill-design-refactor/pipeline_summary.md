# skill-design-refactor 파이프라인 요약

## 최종 판정

**RED (source gates green).** 리팩터 자체의 정량·미러·manifest·semantic·drill 검사는 통과했지만, 잔여 계약 검사가 남아 최종 전체 green은 아니다.

- **C1 gate:** (a) **PASS** — `disable-model-invocation: true` 상태에서도 `/draft-strategy` 명시 호출 instruction 생존. (b) **FAIL** — parent Skill-tool dispatch가 runtime에서 거부. (c) **FAIL** — 동일 거부로 실파이프 handoff 미도달.
- **D1 flip:** **0개**. slash-only PASS는 parent/pipeline handoff를 보존하는 안전한 부분집합이 아니므로 13개 모두 model-invoked 유지.
- **autopilot-ship dedupe:** **PASS**. 발화→자리 표와 사용자 직접 배포 명령 경계를 Step 2 단일 authority로 통합했고, Step 4의 env/domain/migration 고유 의미 3/3을 양 트리에서 보존.
- **SD-10 정량:** **PASS** — 양 트리 28/28, `line_ok=N` 0, `ref_depth_ok=N` 0; references 34개가 1-depth.
- **SD-10 의미:** **PASS** — `no-op=0`, `sediment=0`, `premature-completion=0`, `variance-bug=0`.

## 회귀·계약 결과

- **양 트리 grep/scan:** PASS. `skills/`와 `adapters/claude/skills/` scan 출력 동일, stale `keep in sync`·Language Rule·artifact-root snippet·Required Reads/Reference Map 헤더 0.
- **mirror:** PASS. 두 트리는 byte parity이며 허용 차이는 `skills/.sync_state.json`뿐.
- **manifest:** PASS — `python3 tools/build-manifest.py --check` up-to-date.
- **g7:** PASS — `g7_skill_conformance`, Codex 격리 repository drill exit 0, 0 turns/tokens/cost. Codex-native drill executable projection은 `loop-info drill`상 manual-only.

## 잔여·지원 한계

- invocation/runtime conflict: slash invocation은 생존하지만 Skill-tool·실파이프 handoff는 막힘; invocation 계약 재결정 필요.
- `sync-skills --check`: **36개 changed + 1개 new**(`agents/memory-scout`) state drift.
- capability 계약: **14개 `--qa` drift** — live SKILL은 intensity-derived rigor인데 `capabilities/*.md` argument shape에 폐지된 별도 QA 축 잔존.
- Codex depth-2 parity: 격리 worker/file-only handoff는 동작했으나 liveness가 실행 중 worker를 DEAD로 오판했고, workspace-write child의 Git worktree metadata commit은 sandbox 밖 index lock 때문에 실패해 parent 수확·commit이 필요.
- standard QA 정책은 `1x deep reviewer + 2x fast reviewers`를 요구하나 이 stage에서는 독립 reviewer/headless pass를 수행하지 못해 inline evidence review만 보고한다.

## 브랜치·커밋·변경 범위

- branch: `skill-design-c1`; worktree: `/home/Uihyeop/agent_setting-wt/skill-design-c1`; HEAD `9d1abb2` (`refactor(skills): dedupe autopilot ship routing`).
- `9d1abb2` 변경: `adapters/claude/skills/autopilot-ship/SKILL.md`, `skills/autopilot-ship/SKILL.md`.
- 최근 기준 커밋: `a8305be`, `f76c513`, `619f260`, `b4e303a`.
- 현재 비소스 worktree 변경은 보존: checklist/pipeline_state/c1_gate_log/metrics/test_logs 및 `profiles/c1-gate.yaml`. **push/merge/cleanup 수행 안 함.**

## 검증 명령·증거 경로

- `adapters/codex/bin/preflight.sh verification-runner --timeout ...`로 실행한 전체 원문: `.agent_reports/plans/2026-07-13_skill-design-refactor/test_logs/01_runner_contract.log`~`13_git_scope.log`.
- 종합 verdict: `.agent_reports/plans/2026-07-13_skill-design-refactor/test_logs/00_VERDICT.md`.
- C1 증거: `.agent_reports/plans/2026-07-13_skill-design-refactor/_internal/c1_gate_log.md`.
- SD-10 의미 rubric: `.agent_reports/plans/2026-07-13_skill-design-refactor/test_logs/12_semantic_rubric.md`.
- sync/capability 실패 원문: `test_logs/08_sync_skills_check.log`, `test_logs/11_capability_contracts.log`.
