# tracked/untracked 모드 전면 퇴역

- 날짜: 2026-07-19 · 강도: standard · 경로: autopilot-code (사용자 승인 완료)
- 결정 근거: 모드 비트 실사용 0(플래그 현존 0, 사용자 실측 "요즘 untracked를 쓴 적도 없는데 지장이 없었어"), 정보량 0(모든 표면 상시 tracked), 안내 과장("gates bypassed"라지만 실제 우회 대상은 guard 2종뿐 — spec-read·core-first·git-state는 플래그를 읽지 않음). 성숙 프로젝트에서 생성순서 게이트는 구조적 불발(research/·spec/*/pipeline_state.yaml 영구 충족).
- 설계 결정: ① artifact-guard의 생성순서 게이트는 모드 없이는 출구 없는 벽이 되므로 함께 삭제, canonical-root 강제·spec_touch route 검사는 존치. ② worktree-path-guard 규약 강제 존치, 탈출구는 `WORKTREE_GUARD_BYPASS=1` env로 교체. ③ route-record `tracked_gate_evidence` 스키마와 git-untracked(git 의미) 어휘, 과거 기록물(research/documents/analysis_project)은 불변.
- 잔여 리스크(승인 시 고지): 매 프롬프트 라우팅 리마인더 소실 → 장기 세션 라우팅 규율 감시, 필요 시 모드 없는 고정 한 줄 리마인더로 복구.

## 체크리스트

### A. 사전 읽기 (worker)
- [ ] core/CORE.md, core/WORKFLOW.md §0·§7, hooks/artifact-guard.sh·worktree-path-guard.sh 현행, utilities/workflow-guard-hook.sh 현행
- [ ] .agent_reports/spec/agent-fleet-dashboard/prd.md 의 게이트 배지 등재부(105행·218행 부근) — **읽기만, spec/ 쓰기 금지(메인이 등재)**

### B. 런타임 코드
- [ ] utilities/workflow-toggle.sh, utilities/workflow-guard-hook.sh 삭제
- [ ] adapters/claude/settings.json: workflow-guard-hook 등록 2건(UserPromptSubmit·SessionStart) 제거
- [ ] adapters/claude/track-toggle.sh, adapters/claude/commands/track.md 삭제
- [ ] hooks/artifact-guard.sh 개편: untracked 플래그 우회(140-143행) 삭제, 생성순서 게이트(145-165행: has_spec/has_research/block, "Bypass: /track" 문구, toggle_label) 삭제, 헤더 주석 갱신. **존치**: linked-worktree canonical 강제, `_internal` 예외, spec_touch route 검사, route_failure 경로
- [ ] hooks/worktree-path-guard.sh: `.untracked` 우회 → `WORKTREE_GUARD_BYPASS=1` env 우회로 교체, deny 메시지의 "Bypass: /track" → env 안내로
- [ ] adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/artifact-guard.sh 미러 동기화
- [ ] adapters/claude/statusline.sh: gate 세그먼트(149-157행 부근 + 조립부) 제거
- [ ] utilities/harness-status.sh: workflow_state/workflow_flag/untracked_flag 블록 제거 (git_untracked 카운트는 git 의미 — 유지)
- [ ] adapters/codex/bin/preflight.sh, adapters/opencode/bin/preflight.sh, adapters/codex/hooks/userprompt-lifecycle.py: 모드 분기·안내 제거
- [ ] tools/fleet/render.py: _gate_info/_gate_word/_gate_tag + 세션 행 dim 태그 + 그룹 헤더 배지 + wide 이름칸 태그 공간 예약(2486행 부근) + 1673행 부근 주석 제거. 빈자리는 침묵(healthy-silent) — 대체 표식 발명 금지
- [ ] tools/fleet/model.py·demo.py: gate 필드/픽스처 제거
- [ ] tools/fleet/tests: gate 관련 단언 전수 개편(test_f26_registry.py 포함, grep으로 확인)
- [ ] tools/install/projector.py, tools/install/runtime_activation.py, tools/install/profile-activation.test.sh, adapters/claude/bin/install-windows.sh: workflow-toggle/track-toggle/workflow-guard-hook 설치 목록 제거
- [ ] manifest.json, tools/check-adaptation-boundary.sh, tools/adaptation-guard.test.sh 목록 갱신
- [ ] .gitignore 의 .untracked 항목 제거
- [ ] utilities/worktree-cleanup.py·worktree-residue.py 등 "untracked" 히트는 git 의미면 유지 (개별 판정)
- [ ] **불변**: capabilities/topologies.json, utilities/capability-route.py, capability_route.test.py, worker_route_guard.test.py 의 tracked_gate_evidence

### C. 테스트·drill
- [ ] hooks/portable-guards.test.sh: 우회·생성순서 케이스 제거, canonical-root·spec_touch 케이스 유지/보강, worktree-path-guard env 우회 케이스 추가
- [ ] loops/drill/cases/g5_artifact_guard·g5b_artifact_guard_agentreports: assert를 새 의미(canonical-root 강제)로 개편, adapters/claude/loops/drill 미러 동일, loops/drill/README.md 갱신. **drill 실행 금지**
- [ ] utilities/worktree-cleanup.test.py·worktree_residue.test.py 등 영향 테스트 확인

### D. 문서
- [ ] core 7종(WORKFLOW·CORE·CONVENTIONS·OPERATIONS·HOOKS·ADAPTATION·ADAPTATION_INVENTORY): 모드 서술 제거, "tracked project" 개념은 "spec-backed project"로 재표현, WORKFLOW §0 Invariants 제목·mechanical-enforcement 절 개정
- [ ] adapters/{claude,codex,opencode}/README.md·ADAPTATION.md, MANUAL.md, INSTALL_LAYOUT.md
- [ ] skills/autopilot-code/references/dev-pipeline.md, skills/autopilot-spec/references/owner-execution.md — adapters/claude/skills/ 동일 파일 + plugin-marketplace 미러까지 3벌 동기화
- [ ] adapters/claude/CLAUDE.md 등 부트스트랩 잔존 언급 확인
- [ ] **쓰기 금지**: .agent_reports/spec/**, .agent_reports/research·documents·analysis_project(과거 기록)

### E. 검증 (worker → 메인 독립 재검증)
- [ ] rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
- [ ] fleet 전체 스위트 + hooks/portable-guards.test.sh + tools/adaptation-guard.test.sh + tools/install/profile-activation.test.sh 통과
- [ ] 전수 grep: 잔존 어휘 0 (허용 예외: git-untracked 의미, tracked_gate_evidence, 과거 기록물)
- [ ] COLUMNS=168 fleet --once 스모크: 게이트 워드 부재 + 레이아웃 정상
- [ ] worktree 브랜치 커밋 + 로그 3줄 계약

### F. 메인 harvest (worker 종료 후)
- [ ] 독립 스위트 재실행 + 라이브 스모크 + core 문서 diff 정독
- [ ] fleet PRD minor #2(게이트 배지 퇴역) + pipeline_summary 등재 — 메인이 직접
- [ ] merge → push, registry row flip(done,note=harvested-pass)
- [ ] 설치본 동기화: ~/.claude/utilities/{workflow-guard-hook,workflow-toggle}.sh·~/.claude/track-toggle.sh·~/.claude/commands/track.md 제거, ~/.claude/settings.json 등록 해제 + artifact-guard 중복 등록 정리, 갱신된 guard·statusline·harness-status 복사
