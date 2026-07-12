# Anthropic — Skill authoring best practices (full-read)

- **title**: Skill authoring best practices
- **author**: Anthropic
- **url**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **date**: 2026
- **type**: 공식 문서
- **access**: full-read (WebFetch)
- **관련 축**: 원문대조(교차검증) + 하네스매핑

## Verbatim 핵심 인용 (직접 인용)

> "The context window is a public good. Your Skill shares the context window with everything else Claude needs to know."

> "Default assumption: Claude is already very smart. Only add context Claude doesn't already have." — 검증 질문: "Does this paragraph justify its token cost?"

> "Set appropriate degrees of freedom" — narrow bridge(low freedom, 정확한 스크립트) vs open field(high freedom, 방향만).

> "Create evaluations BEFORE writing extensive documentation." (evaluation-driven development, 3 scenarios, baseline 측정)

> "Keep SKILL.md body under 500 lines." · "Keep references one level deep from SKILL.md." · "Always write [description] in third person."

## 핵심 주장 요약

- Pocock 의 no-op 테스트와 동형: "Claude 가 이미 아는 건 넣지 마라"(token cost 정당화). Anthropic 은 이를 규범적 체크리스트로 제공.
- **Degrees of freedom** = Pocock 에 없는 축. 작업의 fragility 에 따라 지시 구체성을 조정(low/medium/high). 우리 파이프의 intensity 개념과 유사.
- **Progressive disclosure** 는 Pocock 과 완전 동일 개념 — SKILL.md=목차, 상세는 링크 파일, 스크립트는 실행(내용 미로드).
- **Evaluations-first** = Pocock 문서에 없는 강한 규범(먼저 평가 시나리오 3개 → baseline → 최소 지시 작성).
- 실무 수치 규범: SKILL.md <500줄, 참조 1-depth, description 3인칭 "Use when…".

## 우리 조사 축과의 관련성

원문대조 교차검증(progressive disclosure·no-op 은 벤더 문서로도 확증). 하네스매핑: 500줄/1-depth/gerund 명명/eval-first 는 우리 28스킬 audit 시 즉시 적용가능한 정량 체크리스트.
