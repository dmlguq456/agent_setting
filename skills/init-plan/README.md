# init-plan

> 본 README는 Notion 페이지 [📝 init-plan](https://www.notion.so/34987c2bb75381efba0fe6f1ca33ade0)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
실제 코드베이스를 기반으로 상세 구현 계획을 작성하는 skill. 기획팀에 위임하여 영어 `plan.md` 생성 + QA 루프 후 한국어 `plan_ko.md` 전체 번역.

## 호출 형식
```
/init-plan <task description> [--qa light|standard|thorough|adversarial] [--autonomy proactive|standard|passive]
```

> **Caller note**: 계획 수립은 `high` / `xhigh` effort에서 이점. 낮은 effort에서는 cross-file 분석에서 호출 지점 누락 가능.

## 언어 규칙
- 내부 추론 영어, 사용자 출력 한국어

## Pre-Check — 기존 plan 상태 게이팅
`--autonomy` 플래그 파싱 후 `.claude_reports/plans/` 유사 plan 존재 확인:

| 기존 상태 | 처리 |
|---|---|
| `active` (Critical — 항상 질문) | "기존에 진행 중인 plan이 있습니다. 이어서 진행할까요, 새로 만들까요?" 확인 전 진행 금지 |
| `done`/`failed` (Significant) | proactive: 참고용 기록 후 자동 생성. standard/passive: "이전에 완료/실패한 plan이 있습니다. 새로 생성할까요?" |
| `partial` (Significant) | proactive: 자동으로 실패 step만 커버하는 새 plan. standard/passive: 사용자에게 질문 |

## 위임 — 기획팀
```
Plan mode. Create a new implementation plan.

Task: {$ARGUMENTS}
Save English plan to: .claude_reports/plans/{YYYY-MM-DD}_{short-task-name}/plan/plan.md
Date: {YYYY-MM-DD}
{If done/failed/partial plan exists: "Reference previous plan: [path], status: [status]"}
{If partial: "Failed steps from previous execution: [list]"}
```

기획팀이 plan 파일을 직접 씀. 오케스트레이터는 경로와 요약만 받음.

## QA Scaling

| Level | 조건 | 행동 |
|---|---|---|
| Light | ≤3 steps, 기계적, 단일 variant | 1× 품질관리팀 (sonnet) |
| Standard | 4-10 steps, 로직 변경, 단일 모듈 | 1× 품질관리팀 (opus, 기본) |
| Thorough | >10 steps, cross-module/variant, 아키텍처 | 2-3× 품질관리팀 병렬 (opus): A 정합성 / B 완전성 / C 리스크 |
| Adversarial | Cross-variant + Codex 가용 | Thorough + 1× codex-review-team 병렬 |

**Codex 가용성 체크**: Adversarial 선택 전 `codex --version` 실행. 실패 시 Thorough로 silent fallback (`--qa adversarial` 명시는 fail loudly).

## Post-Plan Review Loop (최대 3 리비전 라운드)
로그 디렉토리 = task root (plan/의 부모). `mkdir -p {log_dir}/plan_reviews` 먼저.

**라운드 카운팅**: `round = 0`. 한 라운드 = 기획팀 수정 → QA 리뷰. Thorough 병렬 에이전트도 한 라운드. QA 재호출 시 `round` 증가.

**QA level lock**: 루프 시작 시 확정, 상향만 허용. `--qa` 미지정 시 라운드 2부터 🔴 ≥3이면 한 번 상향 허용 (라운드 리셋 없음).

절차:
1. QA level 평가
2. 품질관리팀 호출 (Light: sonnet / Thorough: 2-3 병렬 + 다른 focus)
3. verdict 확인:
   - 🔴 없음 → Korean Version Generation
   - 🔴 있음 → 기획팀 refine → QA 재호출. `round >= 3`까지 반복
4. **3 라운드 후 🔴 잔여**:
   - proactive: 자동 진행 — 기획팀이 남은 🔴을 `## 미해결 이슈`에 추가
   - standard/passive: "QA 3라운드 후에도 🔴 N개. 리스크 섹션 추가할까요?"

## Korean Version Generation
리뷰 루프 종료 후 기획팀 Translate 모드 최종 호출:
```
Translate mode. English plan file: {plan_path}. Save Korean version to: {same dir}/plan_ko.md.
Full Korean translation (NOT a summary). Section titles: 목표, 현황 분석, 변경 계획, 리스크, 검증 방법.
Code identifiers stay in English. Return ONLY the file path.
```

사용자에게 영·한 plan 경로, 요약, QA verdict 보고.

---
*원본: `~/.claude/skills/init-plan/SKILL.md`*
