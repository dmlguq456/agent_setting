# depth-1 표면 용어 혼동 제거 — 수정안 (handoff)

> 작성: 2026-07-20 main 세션. 다른 세션이 이 문서만 읽고 작업할 수 있게 정리한 편집 제안.
> 발단: hub 페이지 quick 사이클에서 acting 세션이 native subagent(팀 위임) 분사를
> "depth-1 one-shot worker"로 명명·실행 → 사용자 교정("depth=1의 원칙은 서브 에이전트가
> 아닌 dispatch 서브 세션"). 2026-07-14 사고(네이티브 제한을 headless 금지로 오독)의
> **대칭 방향 오독**이 실제로 발생한 것.

## 0. 원칙 (규범 신설 금지)

정답 규칙은 **이미 존재**한다 — `core/CONVENTIONS.md:497` (Route, resource, and report invariants):

> "Depth applies only to registered dispatched agents: quick is depth 1, standard+ has a
> depth-1 owner and at most depth-2 workers, … in-session native team subagents are
> internal parallelism inside their session … that adds no depth."

따라서 이 작업은 **새 규범·새 문서를 만들지 않는다**. 문제는 acting 세션이 실제로 로드하는
운영 문장들이 이 규칙을 인용하지 않고 "depth-1 one-shot worker"를 표면 무규정으로 쓰며,
§5.10에서 "Light team delegation" 불릿이 "Quick one-shot" 불릿 바로 옆에 있어 팀 위임이
quick의 실현 표면으로 읽히는 구조라는 것. 수정은 기존 문장 정밀화 + CONVENTIONS 규칙
상호 인용만으로 한다.

## 1. 편집 대상 (파일:라인, 2026-07-20 main 기준)

우선순위순. 한 문서당 한정어 삽입은 1–2회면 충분 — 모든 등장 지점에 반복 부착해 footprint를
불리지 말 것 (`core/ADAPTATION.md §6.1` 예산 준수).

### A. `core/OPERATIONS.md` (핵심)

1. **:86** — before: "`direct` runs inline, `quick` uses one depth-1 one-shot worker, and depth 3 or greater is forbidden."
   → after(제안): "`direct` runs inline, `quick` uses one depth-1 one-shot worker — a registered headless dispatch session, never a runtime-native subagent — and depth 3 or greater is forbidden. Depth numbers count registered dispatch sessions only (CONVENTIONS route invariants)."
2. **:97** "Delegation surfaces are distinct" 문단 끝에 대칭 방향 1문장 추가(기존 2026-07-14 사고 기록과 같은 스타일):
   → "Symmetrically, the depth vocabulary belongs to the registered surface: a native sub-agent is never `depth-1`, and substituting team delegation for the quick one-shot worker beyond small, fast iterations is a recorded surface deviation, not depth-1 dispatch (observed 2026-07-20)."
3. **:103** scale 표 quick 행 — "Depth-1 one-shot worker in an isolated worktree" → "One **registered** depth-1 one-shot worker **session** in an isolated worktree".
4. **:104** standard+ 행 마지막 문장 — "Team delegation and inline micro-stages are limited to `quick` and genuinely microscopic stages." → "**Native** team delegation (**no depth**) and inline micro-stages are limited to `quick`-scale small, fast iterations and genuinely microscopic stages; **neither substitutes for the registered quick one-shot worker.**"
5. **:120–121** 인접 불릿 상호 구분 —
   - Light team delegation 불릿에 괄호 한정: "(runtime-native subagent; outside the depth ladder and the jobs registry)".
   - Quick one-shot 불릿: "open one depth-1 owner" → "open one depth-1 owner **as a registered headless session through the checked adapter wrapper**".

### B. 부트스트랩·워크플로

6. **`adapters/claude/CLAUDE.md`** — "`quick`: one depth-1 one-shot worker with micro-plan, …" 줄에 "(registered headless session)" 한정어 추가. Codex/OpenCode 형제 부트스트랩에 동일 문구가 있는지 grep 후 동형 반영 (portable 의미는 core가 SoT, 어댑터는 실현만).
7. **`core/WORKFLOW.md:336`** — "Quick uses one depth-1 session" → "one **registered** depth-1 session". (:283·:290은 이미 "session"/"one-shot" 대비가 있어 저우선; 손대면 최소로.)

### C. capability·skill 계층

8. **`capabilities/autopilot-code.md`** :113 (Portable Procedure 6번)에 1회 한정: "`quick` runs as a depth-1 one-shot worker **(registered dispatch session)** with an inline micro-plan…". Stage Mapping 표(:72/:74/:77)는 :113 수정으로 충분하면 유지.
9. **공유 intensity 문단** — `capabilities/autopilot-{research,ship,draft,refine,spec,design,note}.md`에 동일 문장("`quick` is a depth-1 one-shot worker with its inline micro-plan…")이 7회 반복. **주의: 이 문단이 생성물인지 먼저 확인**(harness-manifest/`tools/build-manifest.py`가 Contract 블록을 생성 — 이 문단이 generator 소유면 템플릿/원천을 고쳐 `tools/generate.py`로 전파, 수기면 7파일 일괄 수정). 생성물 수기 수정은 CI가 거부하므로 ownership 확인이 선행.
10. **`adapters/claude/skills/autopilot-code/references/context-and-guards.md`** — "direct and quick remain inline at their intended layer" → "direct stays inline in the acting session; quick runs its whole cycle inside its single **registered** depth-1 session (no depth-2 fan-out)". 같은 파일의 "dispatch the whole autopilot-code cycle into a depth-1 headless session"은 이미 명시적이므로 유지. `skills/` 미러는 byte-identical 강제(`check-adaptation-boundary.sh`) — canonical 쪽 수정 후 동기화 경로로 맞출 것.
11. **`adapters/claude/skills/autopilot-code/references/owner-execution.md`** — Stage Graph quick 행 또는 "quick returns its concise report from the depth-1 one-shot worker" 부근 1회 한정어.

## 2. 작업 방식 주의

- 다파일 행동 지침 변경 → **브랜치 + clean worktree** (`<repo>-wt/<slug>` 규약). 가드류는 primary가 아닌 worktree에서 실행 (primary 실행은 live 회전 유발 이력 있음).
- 생성물/미러 경계: 편집 후 `python3 tools/generate.py` → `--check` 통과, `sh tools/check-adaptation-boundary.sh` 통과 확인.
- **행동 지침 변경이므로 drill 대상**: 관련 케이스 또는 `drill/run.sh --sample 2`. worktree에서 돌릴 때 `AGENT_HOME`과 `DRILL_HOME`을 worktree로 명시하지 않으면 조용히 primary를 검증하니 주의.
- 문구는 제안일 뿐 — 각 문서의 기존 어조·밀도에 맞게 다듬되, "registered dispatch session ≠ native subagent, depth는 등록 표면 전용" 의미는 보존.

## 3. 검증 체크리스트

1. grep 스윕: `grep -rn "depth-1 one-shot\|one depth-1\|Team delegation" core/ capabilities/ adapters/ skills/` — 남은 등장 지점마다 문서 내 어딘가에서 표면이 규정되는지 확인 (모든 지점 한정어 반복은 불요).
2. `tools/generate.py --check` + `check-adaptation-boundary.sh` 녹색.
3. context footprint 예산: 추가는 파일당 1–3줄 이내 유지, footprint 가드가 있으면 실행.
4. drill 샘플 통과 (2번 항목 환경변수 주의).

## 4. 비목표

- 새 규범 문서·새 섹션 신설 금지 (기존 문장 정밀화 + 상호 인용만).
- native 팀 위임 금지가 **아님** — "Light team delegation"은 small/fast 반복용으로 존치. 두 표면의 제약 비확장 원칙(§5.10, 양방향)도 그대로.
- dispatch 구현(broker/launch-authority 등) 변경 없음 — 순수 문서 작업.
