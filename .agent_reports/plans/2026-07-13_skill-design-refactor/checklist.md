# Checklist — skill-design-refactor (cycle 1)

> plan.md 의 checkable step 1:1. 미체크 상태로 초기화. 순서 = CORE → C2 → C3 → C1 → 회귀.
>
> **⚠️ BLOCKED (2026-07-13, SD-6 게이트 실행 중 발견)**: `_internal/BLOCKING_FINDING.md` — root `skills/`
> 는 Claude 런타임 live source 가 아니다(`adapters/claude/skills/` 가 진짜 SoT, manifest.json 도 거기만
> glob). CORE+Cluster 2 는 계획대로 완료·커밋(`cd48b25`)했으나 **live 런타임엔 미반영**. Cluster 3·1 은
> 같은 오류 반복 방지를 위해 **중단** — spec back-jump 필요(대상 트리 재확정 후 재개).

## CORE — 설계 계약 core-first (SD-3·SD-4)
- [x] CORE-1 `core/CONVENTIONS.md` §5.6a Skill-Design 정량 규범 표 추가 (줄 수/depth/frontmatter + DESIGN_PRINCIPLES 상호 포인터)
- [x] CORE-2 `core/DESIGN_PRINCIPLES.md` §10 4축+Predictability tenet 추가 (CONVENTIONS §5.6a 1줄 포인터, 정량 수치 미포함)
- [x] CORE-2 `core/DESIGN_PRINCIPLES.md` 부록 이력 1줄
- [x] CORE-3 `roles/modes/design/_design_rules.md` §시각 자가검증 루프 = SoT 지정 + 4-scope(ui/webapp·slide·icon·diagram) 렌더 표 1회 흡수
- [x] CORE-4 scan.sh → `tools/skill-conformance/scan.sh` stable 위치 이전 (git mv, executable 유지)
- [x] CORE-4 `sync-skills` `--check` 에 scan.sh 정량 규범 lint 스텝 편입 (finalize-and-hooks.md Step 6c + SKILL.md Step 표)
- [x] CORE-4 drill `loops/drill/cases/g7_skill_conformance/{config,fixture.sh,assert.sh}` 신규 (AXIS=static, run.sh static-branch, README 등재, PASS 검증)
- [x] CORE 완료: mirror 적용(cd48b25 diff → adapters 트리 patch 적용) + `python3 tools/build-manifest.py --check`(up-to-date) + `diff -rq skills/ adapters/claude/skills/`(.sync_state.json만 차이) + scan.sh 양 트리 출력 일치 확인 (2026-07-13 재개)

## Cluster 2 — SoT 통합 (P2+P5, SD-2)
- [x] C2-1 authority `autopilot-code/references/arguments-and-decisions.md` Plan Resolution 헤더 "keep in sync" 제거 (single SoT authority 표기)
- [x] C2-1 `code-execute/SKILL.md` Plan Resolution 블록 → 1줄 pointer
- [x] C2-1 `code-test/SKILL.md` Plan Resolution 블록 → pointer (no-match 직접-테스트 fallback 고유 보존)
- [x] C2-1 `code-report/SKILL.md` Plan Resolution 블록 → pointer (+"resolved via Plan Resolution" 문구 조정)
- [x] C2-1 `code-refine/SKILL.md` Plan Resolution 블록 → pointer (plan.md+plan_ko.md 이중 해석 고유 보존)
- [x] C2-1 README 미러 4개(code-execute/test/report/refine README.md) → pointer (고유 semantics 보존)
- [x] C2-1 완료: `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` = 0
- [x] C2-2 authority `arguments-and-decisions.md:1` Language Rule SoT 텍스트 richer wording 흡수
- [x] C2-2 code-execute/refine/report/test SKILL.md + code-plan/SKILL.md Language Rule 블록(5개) → pointer
- [x] C2-2 완료: `grep -rln "## Language Rule" skills/code-*/SKILL.md` = 0
- [x] C2-3 `design-components/SKILL.md` 공통 루프+scope 표 → `_design_rules.md` pointer (invariant 잔류)
- [x] C2-3 `design-review/SKILL.md` render flow+scope 표 → pointer (critic 고유 유지)
- [x] C2-3 `design-tokens/SKILL.md` 공통 루프 → pointer (specimen-consume gate 유지)
- [x] C2-3 `autopilot-design/SKILL.md` 시각 검증 인라인 → pointer 축약
- [x] C2-4 `<artifact-root>` 해석 스니펫 6개(analyze-project·audit·autopilot-research·autopilot-draft·autopilot-spec·autopilot-refine) → CONVENTIONS §5.1 pointer
- [x] C2-4 완료: `grep -rln "REPORTS_DIR=.agent_reports; \[ -d .claude_reports \]" skills/*/SKILL.md` = 0
- [x] C2-5 `core/CONVENTIONS.md §5.6` 단일 Reference Index 컨벤션 1줄 추가
- [x] C2-5 13 라우터 Required Reads+Reference Map → 단일 Reference Index 표 병합 (파일+시점+의무 3요소 유지)
- [x] C2-5 완료: 13 스킬 각 `Required Reads`/`Reference Map` 헤더 0, Reference Index 1
- [x] C2 완료: 양 트리 grep 완료기준 재확인(keep in sync/Language Rule/artifact-root snippet/Required Reads·Reference Map 헤더 = 0 양 트리) + manifest --check 통과 (2026-07-13 재개, mirror 적용 후)

## Cluster 3 — Sprawl 추출 (P3+P6, SD-8)
- [x] C3-1 `autopilot-design/references/{pipeline-execution,harness,paper-figure-policy}.md` 신설 (adapters 정본 편집 후 root 미러) — 312→196줄
- [x] C3-1 완료: `wc -l` < 200 (196), references/ 1-depth (scan.sh ref_depth_ok=Y)
- [x] C3-2 `draft-refine/references/{delegate-prompt,changelog-example}.md` 추출 — 278→129줄 (worked example 은 delegate-prompt.md 내 유지, changelog-example.md 는 별도 문서화 사본으로 분리해 프롬프트 무결성 보존; plan 의 정확한 2-분할과 소폭 다름 — 이유는 dev_logs 참조)
- [x] C3-3 `autopilot-ship/references/examples.md` 추출 — 241→212줄 (발화→자리/deploy=user 3중은 이번 사이클 미착수 — 잔여 항목)
- [x] C3-4 `design-tokens/references/{tokens-exemplar,templates}.md` 추출 — 212→99줄
- [x] C3-5 `autopilot-apply` 3중 제외 목록(Override/Scope NOT-for) → `## When NOT to use` 단일 authority pointer — 191→185줄 (references/ 신설 없음, plan 그대로)
- [x] C3 완료: `bash tools/skill-conformance/scan.sh skills`(=adapters, 양 트리 diff 0) — 5개 타깃 전부 body_lines 감소, ref_depth_ok 전부 Y(N행 0)
- [x] C3 완료: `python3 tools/build-manifest.py --check` 통과 (2026-07-13 재개)

## Cluster 1 — Invocation 재분류 (P1+P4+P7, SD-5) — 게이트 후
- [ ] C1-GATE (a) draft-strategy trial-flip → `claude -p "/draft-strategy"` slash 생존 관측 (FAIL→revert)
- [ ] C1-GATE (b) code-test trial-flip → autopilot-code depth-2 Skill-dispatch 생존 관측 (FAIL→revert)
- [ ] C1-GATE (c) (a)+(b) PASS 시 autopilot-code standard 파이프 1회 통과 (plan→execute→test→report)
- [ ] C1-GATE 산출: `_internal/c1_gate_log.md` 3절차 PASS/FAIL + 증거
- [ ] C1-FLIP 게이트 통과분 13(또는 폴백 부분집합) frontmatter `disable-model-invocation: true` 추가
- [ ] C1-FLIP 완료: scan.sh 통과분 disable_model=true + frontmatter diff 로그
- [ ] C1-P7 `post-it/SKILL.md:14` wording 완화 (model-invoked+proactive-nudge 계약과 정합, flip 아님)
- [ ] C1-P4 entry-router 12(autopilot-*·analyze-*·audit) description 첫 문장 영문 "Use when…" 병기 (한국어 blurb 유지)
- [ ] C1-P4 완료: scan.sh 12 entry-router use_when=Y, desc_has_hangul=Y 유지
- [ ] C1 완료: `sync-skills` → manifest invocation/adapter 미러 + doctor(28/28/9) 통과

## 최종 회귀 (SD-10)
- [ ] variance-bug=0 재검 (pointer/Reference Index 3요소 유지)
- [ ] premature-completion=0 재검 (completion criterion checkable, gate 문장 SKILL.md 잔류)
- [ ] no-op=0 · sediment=0 재검 (옛 블록 완전 제거 grep)
- [ ] Predictability 골격 무손상 (스킬 diff 리뷰)
- [ ] drill `g7_skill_conformance` PASS + audit rubric 재적용
