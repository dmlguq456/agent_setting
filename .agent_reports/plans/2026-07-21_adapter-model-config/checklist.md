# checklist — adapter-model-config

Safety commit: base_head eda11cd4 (worktree adapter-model-config)

## Phase 0 — 포터블 계약
- [x] roles/README.md Adapter Requirements 강화 (config SoT + 결정론 가드)
- [x] core/ADAPTATION.md §3 모델-role 문단 강화

## Phase 1 — codex (참조 구현)
- [x] adapters/codex/config/models.conf 신설 (terra 제거, deep/light/mini + 역할·라이프사이클·프로필)
- [x] model-map.sh → config source (검증)
- [x] role-map.sh → config source (별개 resolver, terra 제거, 검증)
- [x] sync-native-agents.py → PROFILE_CONFIG 제거, config 파싱
- [x] agents/*.toml 재생성 (dev-team terra→sol) — --check idempotent
- [x] distill-worker.sh → config화 (nudge=mini, curate=light) — 검증
- [x] README/ADAPTATION 모델표 → 티어명+config 참조 (가드 통과)

## Phase 2 — claude
- [x] adapters/claude/config/models.conf (deep=fable, light=sonnet, mini=haiku, 캐스케이드)
- [x] model-map.sh → config source (opus→fable, 그룹 보존) — 검증
- [x] mem-distill-worker.sh → config화 (fast-distiller→haiku, deep-curator→sonnet) — 검증
- [x] deep 에이전트 frontmatter opus→fable (plan/design/research/editorial)
- [x] ADAPTATION 모델표 → config 참조
- [x] qa-team·material-team frontmatter opus→sonnet (light) — variable reviewer 기본값=fast/light, codex 정합 (사용자 승인 2026-07-21). opus는 이제 failover 캐스케이드 전용

## Phase 3 — opencode
- [x] adapters/opencode/config/models.conf (glm-5.2 / deepseek-v4-pro / deepseek-v4-flash — 실측)
- [x] role-map.sh → config source (deep/balanced/fast → deep/light/mini) — 검증

## Phase 4 — 가드 + 테스트
- [x] tools/check-model-config.py 신규 (config-외 concrete ID fail-closed) — 통과
- [x] 가드 배선: claude tools 심링크 projection + adaptation-exemptions(TOOL_DEFERRED) + CI(checks.yml)
- [x] capacity test terra→현행 모델 정합 (8/8 통과)
- [x] 재생성 idempotent (sync --check) + 경계 가드 통과
- [x] 회귀: fleet test_dispatch 76 / test_harness_model_merge 17 / build-manifest --check 통과

## 남은 결정 (사용자)
- claude qa-team / material-team 네이티브 에이전트 티어 (현재 opus → light? deep 유지?)
- claude 네이티브 에이전트 frontmatter는 아직 config-파생 아님(가드 exempt) — 완전 결정론 원하면 claude agent 생성기 신설 후속
