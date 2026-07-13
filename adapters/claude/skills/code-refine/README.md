# code-refine

> 본 README 는 Claude adapter skill 요약. 권위 있는 Claude runtime 동작 명세는 같은 폴더의 `SKILL.md`; portable capability 의미는 `<agent-home>/capabilities/`.

## 개요
사용자 메모/코멘트를 plan에 반영해 업데이트하는 skill (**구현 금지**). 한국어 `plan_ko.md`에 삽입된 메모를 감지하고 영·한 양쪽을 동기화.

## 호출 형식
```
/code-refine <plan name or path>
```

## Plan Resolution
> `$ARGUMENTS`→plan 경로 해석 단일 authority = [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md). 단, code-refine 은 `plan.md` 와 `plan_ko.md` 를 _둘 다_ resolve (path swap; refine 고유).

## 위임 — 기획팀
```
Refine mode. Update an existing plan based on user memos.

Korean plan file: {$ARGUMENTS}
English plan file: {with plan_ko.md replaced by plan.md}

Read the Korean plan and find all user memos. Formats:
- <!-- memo: ... --> (standard)
- <!-- ... --> (any HTML comment)
- // ... (inline)
- [memo] ... (bracketed)
- (**...**) (parenthetical)
Do NOT treat the plan's original author-written prose as a memo.

Re-read source files if needed, update Korean plan in-place, sync changes to English.
Remove memo comments after incorporating them.
Return which steps were changed and a brief summary.
```

## Rigor Scaling
검증 rigor tier 는 plan frontmatter 의 `qa_level` (intensity 에서 파생된 값, [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)) 에서 온다. `--autonomy`는 strip만 (code-refine은 autonomy gating 없음).

| Level | 조건 | 행동 |
|---|---|---|
| Light | ≤3 steps 변경, 기계적 | 1× fast reviewer |
| Standard | 4-10 steps 변경, 로직 변경 | 1× deep reviewer |
| Thorough | >10 steps 변경, 아키텍처 | 2× 병렬 (A correctness / B completeness) |
| Adversarial | Cross-variant + external adversary 가용 | Thorough + 1× external adversary |

### Thorough — 병렬 2팀
- Agent A: **correctness** — 수정된 step이 올바른 파일/함수 참조? 의존성 업데이트?
- Agent B: **completeness** — 변경의 downstream 영향 반영? 누락 step?
각자 별도 리뷰 파일에 쓰기. ANY 🔴 처리 필수.

## Selected Post-Refine Review Pass (caller-selected budget)
`mkdir -p {log_dir}/plan_reviews` 후:
- Light/Standard: 1 agent — "Review changed steps. Plan: [path], Changed: [list]. Write to: refine_round_{N}.md"
- Thorough: 2 agents 병렬 (A/B), 다른 focus + 다른 파일

**verdict 체크**:
- 🔴 없음 → 종료, 사용자에게 보고
- 🔴 있음 → 기획팀 재호출 → QA 재호출. 🔴 없거나 최대 라운드까지
- 3 라운드 후 🔴 잔여 → `## 미해결 이슈`에 추가, 사용자에게 변경 step / 해결·미해결 이슈 보고

---
*Claude adapter realization: `<agent-home>/adapters/claude/skills/code-refine/SKILL.md`; compatibility reference: `<agent-home>/skills/code-refine/SKILL.md`*
