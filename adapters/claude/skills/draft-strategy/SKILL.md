---
name: draft-strategy
description: "문서 전략 초안 작성 — 6 모드(rebuttal·paper·review·report·proposal·presentation) sub-skill"
argument-hint: "<mode> --inputs <comma-separated-paths> --output <artifact-dir> <task description>"
metadata:
  group: sub
  fam: sub
  modes: [rebuttal, paper, review, report, proposal, presentation]
  blurb: "문서 전략 초안 작성 — 6 모드(rebuttal·paper·review·report·proposal·presentation) sub-skill"
---

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Argument Parsing
Parse `$ARGUMENTS`:
- **mode**: first word — `rebuttal | paper | review | report | proposal | presentation`
- **--inputs <comma-separated-paths>**: comma-joined list of pre-discovered input paths (from autopilot-draft Pre-flight Step 2 Input Discovery — typically `analysis_project/{paper,doc}/...` and/or `research/{topic}/`). Each path is an artifact directory containing pre-analyzed materials.
- **--output <dir>**: artifact output directory (`<artifact-root>/documents/{date}_{name}/`)
- **검증 rigor tier**: `quick | light | standard | thorough | adversarial` — `--intensity` 에서 파생 (autopilot-draft 가 전파). 단일 source: [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)
- Remaining text: task description / context

## Pre-Check
- Verify analysis files exist in `{output_dir}/analysis/`:
  - `material_index.md` (required for all modes)
  - `reviewer_analysis.md` (required for rebuttal mode)
  - `ref_analysis.md` (required for paper/review/report/proposal/presentation modes)
- If missing, report error — autopilot-draft Step 1 should have created these.

## Mode Routing

첫 인자 mode 로 6종 strategy template 중 하나를 선택한다. autopilot-draft 의 form-first 3-mode(paper·presentation·doc) 는 Pre-flight 에서 6-mode 라벨로 변환돼 전달된다 (doc → rebuttal/review/report/proposal, task keyword 매칭; 모호 시 report). 직접 `/draft-strategy` 호출 시는 사용자가 첫 인자로 6-mode 중 하나를 명시.

- **rebuttal** — reviewer 대응 전략 (meta-review → priority matrix → reviewer-by-reviewer)
- **paper** — 논문 작성 전략 (positioning → contribution → outline → evidence)
- **review** — peer review 의견서
- **report** — 보고서 전략 (objective → findings → section plan)
- **proposal** — 제안서 전략 (problem → approach → work plan → impact)
- **presentation** — 발표 전략 (audience → core message → slide outline; slide 산출 직접 가이드)

mode↔autopilot-draft 매핑 표·6종 template 전문·Paragraph Cohesion Pre-Check·Tone Auto-Detection·Slide Format Conventions·Quality Requirements 는 모두 `references/delegate-prompt.md` 에 verbatim 보존.

## Delegation & Flow

1. Argument Parsing → Pre-Check (`{output_dir}/analysis/` 파일 존재 검증).
2. **Delegate**: `references/delegate-prompt.md` 의 전체 프롬프트로 연구팀(research-team) 을 subagent 호출 — agent 가 strategy 파일을 직접 쓰고 경로 + 3-5줄 한국어 요약만 반환. orchestrator 는 내용이 아닌 경로·요약만 수신.
3. **QA**: `references/qa-review.md` 의 QA Scaling(레벨 auto-detect) + Selected Post-Strategy Review Pass(quality reviewer + fact-checker 병렬, max 2 rounds) 수행.
4. **Mirror** (conditional, default skip): strategy primary language ≠ 사용자 작업 언어일 때만 `references/mirror.md` 의 편집팀 모드 A 호출.
5. 사용자 보고: strategy path(s) + summary + QA verdict.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/delegate-prompt.md` | 연구팀 delegate 프롬프트 구성 시 (필수) | `## Delegate to 연구팀` 전체 — 연구팀 프롬프트(Inputs / Paragraph Cohesion Pre-Check / Mode mapping / Mode-Specific Instructions 6종 template: rebuttal·paper·review·report·proposal·presentation / Tone Auto-Detection / Slide Format Conventions / Quality Requirements) + orchestrator 반환 계약 |
| `references/qa-review.md` | QA 레벨 스케일링·리뷰 패스 시 | `## QA Scaling`(레벨 표·fast fact-checker 근거) + `## Selected Post-Strategy Review Pass`(reviewer/fact-checker 프롬프트, verdict 분기, max 2 rounds) |
| `references/mirror.md` | Mirror 생성 시 | `## Mirror Generation`(편집팀 모드 A 조건부 호출, primary-language 판정, 최종 사용자 보고 라인) |

## Task
$ARGUMENTS
