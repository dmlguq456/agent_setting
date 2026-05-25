# code-report

> 본 README는 Notion 페이지 [📊 code-report](https://www.notion.so/34987c2bb75381a99e7bd9fb53ac04fb)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
plan + dev logs로부터 상세 변경 보고서를 생성하는 skill. **핵심 변경, 원리, 인사이트**에 초점. 향후 참고를 위한 문서.

## 호출 형식
```
/code-report <plan name or path>
```

## Plan Resolution (canonical)
1. `.md` → 그대로
2. 디렉토리 → `/plan/plan.md`
3. 퍼지 검색 → `_audit`/`_fix_` 없는 폴더 우선

## Model & QA Policy
**Writer: 항상 sonnet**. 최종 보고서는 이전 파이프라인 단계(plan reviews, code reviews, test reviews)에서 이미 검증된 아티팩트의 합성. 보고서 자체에 QA/리뷰 패스는 불필요 — 부정확성(라인 번호 drift, 낡은 follow-up)은 사용자가 읽으면서 교정 가능하며 커밋된 코드에 영향 없음.

| Level | 조건 | 행동 |
|---|---|---|
| 전체 | 모든 level | 1× 품질관리팀 (`model: "sonnet"`)이 보고서 작성 |

`qa_level`은 **프롬프트 컨텍스트용**으로만 사용, 모델/리뷰에 영향 없음. Codex review 없음. 병렬 writer 없음. 리뷰 루프 없음.

## 위임 — 품질관리팀 (sonnet)
인풋: plan + log directory (plan/, dev_logs/, dev_reviews/, plan_reviews/, test_logs/, test_reviews/) + Korean plan.

절차:
1. plan으로 goal, current state, change plan 파악
2. checklist에서 성공/실패/skip step 식별
3. dev_logs/step_*.md 모두 읽어 every code change (old→new) + Decision 추출
4. dev_reviews/phase_*.md에서 이슈와 해결 추출
5. **Documentation Update**: 성공 step만 docs 갱신. mapping에 따라 `analysis_project/code/` 파일 + Interface Reference 테이블 갱신. **검증**: 모든 class/function 라인 번호는 **post-edit** 소스와 대조
6. **doc 변경 실존 확인**: `git diff --stat` — 비었으면 re-do
7. pipeline_summary.md 읽고 Decision Points 테이블 추출
8. 합성 — 단순 나열 아닌 reasoning 설명 + bigger picture 연결

## Report Structure
```
# 변경 보고서: {task name}
- 일시 / 플랜 / 상태: ✅/⚠️/❌

## 1. 변경 개요 — 무엇을 왜 (3-5 문장)
## 2. 핵심 변경 사항 — 논리 카테고리별 그룹핑
   ### 2.N {category} — {file/module}
   - 변경 내용 / 이유 / 핵심 원리 / 영향 범위
## 3. 설계 인사이트 — 향후 작업용 takeaway
## 4. QA 리뷰 요약 — 이슈/해결/미해결
## 4.5 자율 판단 기록 — Decision Points 서사적 요약
## 5. 실패/스킵된 단계 — 이유 또는 "전체 단계 성공 ✅"
## 6. 향후 참고사항 — watch-outs, follow-up
```

## Quality Guidelines
- 단순 summary 아닌 **insight 추출**. "why"와 "기억할 것" 중심
- 구체적 영향 (callers, tensor shapes, config keys)
- 프로젝트 설계와 연결
- 한국어 작성. 식별자·경로·기술 용어는 영어
- 1-3 페이지. 변경 규모에 비례 (≤5 steps: 1p, >20 steps: 3p)

## Post-Report — Memory × Report Reconciliation
품질관리팀 반환 후:
1. **final_report.md 한 번 읽기** (짧음, ≲1500 tokens)
2. **오케스트레이션 메모리와 대조**:
   - 숫자 (step 카운트, 🔴 해결 라운드, test pass/fail, commit hash, 파일 수)
   - 라인 번호 (drift 잦음)
   - follow-up 상태 (보고서 "pending"인데 메모리 "resolved")
   - 편차 (서브에이전트가 flag한 deviation을 보고서가 놓쳤는지)
3. **간결한 한국어 브리핑** (2-3 문단):
   - 최종 상태 (done/partial/failed) + final commit hash
   - 3-5개 구체 deliverable
   - 메모리-보고서 불일치 명시
   - 명백한 next step
4. **보고서에 추가 QA 실행 금지**. reconciliation이 경량 safety net.

---
*원본: `~/.claude/skills/code-report/SKILL.md`*
