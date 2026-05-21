# §doc — Word / HWP / markdown prose

> autopilot-draft `--mode doc` 의 본문 구조 + 강제 룰. `common.md` (§Common) 의 룰도 모두 적용.
>
> doc mode 의 본문 구조는 _자연어 task description 의 genre 의도_ 에 따라 분기. 다음 sub-section 은 _의도별 권장 본문 구조_. mode argument 가 `doc` 인 한 모두 본 절 적용.
>
> 공통 — audience-driven 톤 / 시제 (한국 기관·위원회·산학협력단 → 한국어, international → 영문, 시제는 genre 따라 — 보고 = 과거, 제안 = 미래, rebuttal-response = 시제 혼합). 절 구조 가변. 정량 metric 있으면 표. §Common 의 paragraph cohesion / anchor 정책 / 약자 정책 적용.

## doc — 기술 보고서 / mid-report / post-mortem / quarterly 의도

- Frontmatter: type, status: draft, date
- Executive Summary
- Introduction / Background
- Methodology / Approach
- Findings / Analysis (with data tables, charts description)
- Discussion
- Recommendations (prioritized, actionable)
- Appendices (if needed)
- _시간 흐름 자산_ 의 정적 snapshot 위험 — "당시 snapshot YYYY-MM-DD" 명시 (DSC mid-report 같은 _재학습 / 추가 보고_ cycle).
- _post-mortem_ 의 경우 — 시간순 사건 / root cause / fix / preventive measure 구조.

## doc — grant proposal / 사업 제안서 의도

- Frontmatter: type, status: draft, date
- Executive Summary
- Problem Statement / Motivation
- Proposed Approach / Technical Plan
- Preliminary Results / Feasibility Evidence
- Timeline & Milestones
- Resource Requirements / Budget (if applicable)
- Expected Outcomes / Impact
- Risk Assessment
- NRF / NSF / Horizon / 산학협력단 별 변형 — `analysis_project/doc/{matching}/formats/` 에서 venue-specific section 강제.

## doc — rebuttal-response 의도 (OpenReview 응답 form)

- Frontmatter: type, venue, status: draft, date
- Per-reviewer response sections following the strategy's priority matrix
- Each response: acknowledgment → core argument → evidence → conclusion
- Tone calibrated per the strategy's tone guidelines
- Additional experiments section with preliminary descriptions
- Revision summary table
- _camera-ready 본문 통합_ 은 본 sub 가 아니라 `paper.md` 의 _camera-ready / major-revision specific Natural-integration rule_ 으로 — rebuttal 응답과 본문 통합은 _다른 장르_.

## doc — peer review 작성 의도

Adapt the section structure to the auto-discovered format spec at `{format_ref}` (read it first). No built-in presets — extract the venue's required sections / rating axes / length limits from the format spec file.

**Frontmatter** (always): type, venue, paper_title, status: draft, date, format_ref (path to auto-discovered format spec)

**Procedure**:

1. Read the format spec at `{format_ref}` first. Extract: required sections, rating axes (with score scales 1-N and meanings), length limits, tone/style guidelines, submission portal layout.
2. If the format spec is a venue's reviewer guidelines PDF/doc, prefer its exact section names verbatim. If it's a sample review, infer the structure.
3. Layer any additional reviewer guidelines from siblings in `analysis_project/doc/{matching}/formats/` on top.
4. Produce a draft that satisfies every required section from the format spec.

**Common patterns** (reference only — the actual structure must come from the format spec, not from these):

- _OpenReview-family_ (NeurIPS, ICML, ICLR, AAAI variants): Summary / Strengths / Weaknesses / numeric ratings (Soundness, Presentation, Significance, Originality on 1-4 or 1-5) / Questions / Limitations / Overall Recommendation + Confidence
- _ACL ARR_: Paper Summary / Strengths / Weaknesses / Comments+Typos / Soundness, Excitement, Reproducibility (1-5) / Ethical Concerns
- _IEEE conference_ (ICASSP, INTERSPEECH): Brief Summary / Strengths / Weaknesses / Detailed Comments / Recommendation (Accept/Reject scale) / Confidence
- _Journal_ (T-ASLP, JASA, TPAMI, etc.): Significance / Technical Quality / Clarity / Recommendation (Accept/Minor Revision/Major Revision/Reject) / Per-section comments

These are starting hints only. Always follow the format spec file's actual specification — venue templates change year-to-year.
