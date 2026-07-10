# b2 행동 규율 roles/ 승격 — 구현 plan (HLS-OPEN-1 해소)

> spec: `.agent_reports/spec/harness-layer-sync/prd.md` §7 (b2)·§11 HLS-OPEN-1 / 감사 `analysis_project/harness-alignment/findings.md` 6-1·6-2
> 결정: 사용자 확정 2026-07-10 = **옵션 B (roles/ 승격)** + 6-1/6-2 분리 처리
> mode: dev / new-lib / intensity: standard / branch: `b2-response-policy`

## 0. 결정 배경

감사 6-1·6-2: 행동 규율이 Claude bootstrap 에만 풍부, Codex/OpenCode 는 Response Policy 4줄 → 런타임 전환 시 계약이 조용히 빈약. spec §7 은 옵션 A(현행)/B(roles)/C(core) + 6-1(무조건 브랜치)/6-2(응답 메타) 분리 결정 가능성을 열어 두고 사용자 논의에 부쳤다(HLS-OPEN-1). 사용자 결정 = **B**:

- **6-2 (응답 메타 원칙)** → 최소 포터블 계약을 `roles/response-policy.md` 신설, 3 어댑터 참조. 어댑터별 상세(한국어 어미·해요체 등 Claude 고유 톤)는 각 bootstrap 잔류.
- **6-1 ("무조건 브랜치" 휴리스틱)** → 운영 안전 규칙이라 `core/OPERATIONS.md §5.10` 규모 분기표 승격 (위임 경계 논쟁 밖, 승격 자명).

## 1. 작업 항목 (core-first 순서)

| # | 파일 | 변경 | 층 |
|---|---|---|---|
| 1 | `core/OPERATIONS.md` §5.10 | 규모 분기표 "본작업" 행에 "기능 추가·모듈 신설·다파일 변경 = 무조건 브랜치, 애매해도 브랜치 (drill g3)" 명문화 (6-1 승격) | core |
| 2 | `roles/response-policy.md` | 신설 — runtime-neutral 최소 행동 계약, 각 원칙 = 한 줄 정의 + 위반 신호 | roles |
| 3 | `roles/README.md` | behavior contract 섹션 추가 (역할 카탈로그와 별개) | roles |
| 4 | `core/DESIGN_PRINCIPLES.md` §196·§7 | 위임을 "adapter single source" → 2층 (포터블 최소 = roles/response-policy, 런타임 구체화 = adapter bootstrap) 으로 정정 | core |
| 5 | `adapters/claude/CLAUDE.md` §1 상단 | "포터블 계약 = roles/response-policy.md, 본 §1~§3 은 그 Claude-구체화" 계보 한 줄 | adapter |
| 6 | `adapters/codex/AGENTS.md` Response Policy | response-policy 참조 + pause/autonomy/auto-followthrough 보강 (byte-budget 32768 준수) | adapter |
| 7 | `adapters/opencode/AGENTS.md` Response Policy | 동형 | adapter |
| 8 | spec `prd.md` §7·§11 + pipeline_state/summary + `_internal/versions/` snapshot | HLS-OPEN-1 닫기 (결정=B, 사용자 2026-07-10) | spec |

## 2. roles/response-policy.md 추출 원칙 (runtime-neutral 만)

소스 = `adapters/claude/CLAUDE.md` §1~§3. **제외**: 말투(한국어 어미·해요체·판교체 회피 = Claude 언어 고유) → bootstrap 잔류 명시.

- §1 → Concise / Promise–action match / Evidence-grounded (verify-before-assert) / Convention adherence
- §2 → Pause is not automatic / Autonomous on no answer / Don't ask the self-evident / Sync-then-execute
- §3 → Auto-continue in-flow follow-ups / Corresponding sync is part of the change

## 3. 검증

- `tools/check-adaptation-boundary.sh` green (특히 codex/opencode bootstrap "must contain" 그대로 유지 + byte-budget: codex 32768 상한 내).
- 참조 앵커 실존 grep (`roles/response-policy.md` 가 3 어댑터·DESIGN_PRINCIPLES 에서 실제 참조됨).
- 편집 후 bootstrap byte 크기 재확인 (codex < 32768).

## 4. 주의 / 경계

- background 금지 (foreground only). 파일 겹침 금지: `adapters/claude/{hooks,tools,utilities}`·`tools/fleet/**`·`loops/**` (타 세션) 미접촉.
- `core/OPERATIONS.md` 는 main 트리에서 타 세션이 미커밋 편집 중 — 이 브랜치 편집은 무방, 수확 시 충돌 가능성 보고에 명시.
- 지침 편집 core-first: OPERATIONS·DESIGN_PRINCIPLES·roles 먼저 → adapter 참조.
- spec 쓰기는 §5.8 pipeline lock acquire/release 경유.
