# draft-strategy

> 본 README 는 Claude adapter skill 요약. 권위 있는 Claude runtime 동작 명세는 같은 폴더의 `SKILL.md`; portable capability 의미는 `<agent-home>/capabilities/`.

## 개요
분석된 참고 자료를 기반으로 초기 문서 전략(rebuttal/paper/review/report/proposal/presentation)을 생성하는 skill. 연구팀에 위임 + selected review/source-check pass + 한국어 번역.

> autopilot-draft 내부에서 자동 호출. 직접 사용은 거의 없음 (autopilot-draft의 Step 2).
>
> **Paragraph Cohesion Pre-Check (모든 mode, 2026-05-20)**: paste-ready block (LaTeX / markdown / slide / table) 작성 전 target paragraph **전체 narrative flow** 분석 + 4-step self-check — (1) substance 이미 명시 여부 / (2) paragraph axis (motivation→design→formalization 등) 단절 여부 / (3) §-level cross-section redundancy / (4) edit type 선택 (응집성 순 EDIT in-line > REPLACE > INSERT > DROP). Anti-pattern: mechanical "INSERT after sentence X", AFTER가 BEFORE보다 verbose, 같은 substance § 레벨 반복. 상세 — `SKILL.md` ## Paragraph Cohesion Pre-Check 섹션.
>
> **Paper mode camera-ready / major revision 특이 룰** (2026-05-19): reviewer concern → paper-body mutation 변환 시 **natural-integration rule** 적용 (위 Pre-Check 통과 후 추가 gate). Single gating question — *"1-2 sentence inline rewrite로 자연 통합 가능한가?"* YES → M15-style inline rewrite (subsection-head opening + 본론 paragraph touch-up + Figure cascade). NO → drop / Appendix defer (rebuttal-format table·Q&A block은 본문 mutation 금지). 상세 — `SKILL.md` paper mode "Natural-integration rule" 섹션.

## 호출 형식
```
/draft-strategy <mode> --inputs <comma-separated-paths> --output <artifact-dir> <task description>
```

### 인자
- **mode**: 첫 단어 — `rebuttal | paper | review | report | proposal | presentation` (6개)
- **--inputs**: Input Discovery 결과 path list (콤마 구분). autopilot-draft Pre-flight Step 2에서 결정.
- **--output**: artifact 디렉토리 (`<artifact-root>/documents/{date}_{name}/`)
- 남은 텍스트: task description

> survey 모드는 autopilot-research로 분리됨 (`/autopilot-research <주제> --mode academic|technology|market`).
> format spec은 `analysis_project/doc/{matching}/formats/`에서 자동 발견 (`--format-ref` flag 없음).

## Pre-Check
`{output_dir}/analysis/`에 분석 파일 존재 확인:
- `material_index.md` (모든 모드 필수)
- `reviewer_analysis.md` (rebuttal 필수)
- `ref_analysis.md` (paper/review/report/proposal/presentation 필수)

누락 시 에러 — autopilot-draft Step 1이 생성했어야 함.

## 위임 — 연구팀
mode별 전략 템플릿으로 전략 문서 작성. 자동 발견된 format spec이 있으면 venue-specific section/length/tone 추출.

### 모드별 핵심 섹션 (요약)

| 모드 | 핵심 섹션 |
|---|---|
| rebuttal | Meta-Review / Response Priority Matrix / Reviewer별 상세 / Additional Experiments / Paper Revision / Tone / Risk |
| paper | Positioning / Contribution / Outline / Key Arguments / Related Work 전략 / Experiment Design / Risk / Venue |
| review | format spec에서 추출한 섹션 (venue별 다름). 패턴: Summary / Strengths / Weaknesses / Questions / Missing References / Overall / Confidence |
| report | Objective / Key Findings / Analysis Framework / Section Plan / Evidence / Recommendations / Risk |
| proposal | Problem / Prior Art / Approach / Feasibility / Work Plan / Resource / Impact / Risk |
| presentation | Audience / Core Message / Story Arc / Slide Outline / Visuals / Q&A / Time / Delivery Notes |

### 품질 요구
- 모든 reviewer 포인트가 rebuttal 전략에 등장 (누락은 Critical Error)
- Severity 분류 justification 필요
- 모든 citation은 **paper analyses / discovered_inputs의 실재 자료만** (fabricate 금지)
- 전략은 구체적·실행 가능
- academic: venue-specific norms / professional: 업계 best practice

연구팀이 파일 직접 작성. 오케스트레이터는 경로 + 3-5줄 요약만 받음.

## QA Scaling
Quality reviewer + fact-checker는 selected graph/QA budget이 요구할 때만 동작한다.

| Level | 조건 | Quality reviewer | Fact-checker (parallel) |
|---|---|---|---|
| Light | review/presentation 또는 ≤3 inputs | 1× fast reviewer | skip |
| Standard | paper/report/proposal 또는 rebuttal ≤3 reviewers | 1× deep reviewer | 1× fast fact-checker |
| Thorough | rebuttal ≥4 reviewers 또는 ≥10 inputs | 2× deep reviewers 병렬 | 1× fast fact-checker |

**Fact-checker**는 `analysis_project/paper/*.md` verbatim 대조로 venue/year/metric/citation을 narrow하게 검증. quality reviewer는 narrative arc / cohesion / 모든 reviewer point 응답 여부에 집중.

## Selected Post-Strategy Review Pass (최대 2 라운드)
1. **Selected quality/source-check reviewer 호출**
   - Quality prompt → `round_N_quality.md`
   - Fact-check prompt → `round_N_factcheck.md`
2. Verdict:
   - 🔴 없음 (양쪽) → Korean Version Generation
   - 🔴 quality → 연구팀 revise with quality findings
   - 🔴 fact-check → 연구팀 revise with **mandatory ref-grounding** (re-read named paper analyses)
   - 🔴 양쪽 → 연구팀 revise with combined findings
3. 2 라운드 후 🔴 잔여 → `## 미해결 이슈` (`[FACT-RESIDUAL]` 태그)

## Korean Version Generation
연구팀 Translate 모드 최종 호출. 전체 번역 (요약 X). Code identifiers·paper titles·technical terms는 영어.

---
*Claude adapter realization: `<agent-home>/adapters/claude/skills/draft-strategy/SKILL.md`; compatibility reference: `<agent-home>/skills/draft-strategy/SKILL.md`*
