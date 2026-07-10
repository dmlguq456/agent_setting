# code-plan

> 본 README 는 Claude adapter skill 요약. 권위 있는 Claude runtime 동작 명세는 같은 폴더의 `SKILL.md`; portable capability 의미는 `<agent-home>/capabilities/`.

## 개요
실제 코드베이스를 기반으로 상세 구현 계획을 작성하는 skill. 기획팀에 위임하여 영어 `plan.md` 생성 + QA 루프 후 한국어 `plan_ko.md` 전체 번역.

## 호출 형식
```
/code-plan <task description> [--autonomy proactive|standard|passive]
```

> **Caller note**: 계획 수립은 `high` / `xhigh` effort에서 이점. 낮은 effort에서는 cross-file 분석에서 호출 지점 누락 가능.

## 언어 규칙
- 사용자 출력은 자연스러운 한국어 (번역체 회피)

## Pre-Check — 기존 plan 상태 게이팅
`--autonomy` 플래그 파싱 후 `<artifact-root>/plans/` 유사 plan 존재 확인:

| 기존 상태 | 처리 |
|---|---|
| `active` (Critical — 항상 질문) | "기존에 진행 중인 plan이 있습니다. 이어서 진행할까요, 새로 만들까요?" 확인 전 진행 금지 |
| `done`/`failed` (Significant) | proactive: 참고용 기록 후 자동 생성. standard/passive: "이전에 완료/실패한 plan이 있습니다. 새로 생성할까요?" |
| `partial` (Significant) | proactive: 자동으로 실패 step만 커버하는 새 plan. standard/passive: 사용자에게 질문 |

## 위임 — 기획팀
```
Plan mode. Create a new implementation plan.

Task: {$ARGUMENTS}
Save English plan to: <artifact-root>/plans/{YYYY-MM-DD}_{short-task-name}/plan/plan.md
Date: {YYYY-MM-DD}
{If done/failed/partial plan exists: "Reference previous plan: [path], status: [status]"}
{If partial: "Failed steps from previous execution: [list]"}
```

기획팀이 plan 파일을 직접 씀. 오케스트레이터는 경로와 요약만 받음.

## Plan-Check Assurance

`code-plan` is used for durable `standard+` code work cycles. `direct` skips it; `quick` uses inline micro-plan plus plan-check-lite. The rigor tier (derived from `--intensity`, per [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)) scales the plan-check budget but does not create the stage graph.

| Rigor tier | 행동 |
|---|---|
| quick | direct invocation only; single fast sanity check, no repeated fix loop |
| light | one focused fast review or self-check |
| standard | one lightweight independent plan review, at most one correction |
| thorough | multi-axis/depth2 review only when intensity selected it |
| adversarial | selected thorough budget plus adversary/failure-mode/security critique when available |

Unresolved findings after the selected budget are recorded in the plan risk/unresolved section and returned to the caller.

## Korean Version Generation
리뷰 루프 종료 후 기획팀 Translate 모드 최종 호출:
```
Translate mode. English plan file: {plan_path}. Save Korean version to: {same dir}/plan_ko.md.
Full Korean translation (NOT a summary). Section titles: 목표, 현황 분석, 변경 계획, 리스크, 검증 방법.
Code identifiers stay in English. Return ONLY the file path.
```

사용자에게 영·한 plan 경로, 요약, QA verdict 보고.

---
*Claude adapter realization: `<agent-home>/adapters/claude/skills/code-plan/SKILL.md`; compatibility reference: `<agent-home>/skills/code-plan/SKILL.md`*
