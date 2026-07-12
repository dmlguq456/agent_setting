# Anthropic — Agent Skills overview (three-level progressive disclosure, full-read)

- **title**: Agent Skills — overview
- **author**: Anthropic
- **url**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- **date**: 2026
- **type**: 공식 문서
- **access**: full-read (WebFetch)
- **관련 축**: 원문대조(교차검증) + 일반화

## Verbatim 핵심 인용 (직접 인용)

> "This filesystem-based architecture enables progressive disclosure: Claude loads information in stages as needed, rather than consuming context upfront."

3-레벨 로딩 테이블 (직접 인용):
> Level 1 Metadata — Always (at startup) — ~100 tokens/Skill — name+description.
> Level 2 Instructions — When triggered — under 5k tokens — SKILL.md body.
> Level 3+ Resources — As needed — effectively unlimited — bundled files executed via bash without loading contents.

> "When a Skill is triggered, Claude uses bash to read SKILL.md … If those instructions reference other files … Claude reads those files too … When instructions mention executable scripts, Claude runs them via bash and receives only the output (the script code itself never enters context)."

## 핵심 주장 요약

- Pocock 의 "information hierarchy" 3-rung(step/in-file reference/external reference)과 Anthropic 의 3-level(metadata/SKILL.md/resources)은 **다른 층위지만 같은 원리**: 필요할 때만 로드. Anthropic 은 *로딩 시점*(startup/trigger/on-demand) 기준, Pocock 은 *즉시성 사다리* 기준.
- 핵심 메커니즘 확증: description(~100토큰)만 상시 상주 → Pocock 의 "context load" 정의와 일치.
- 스크립트 실행은 코드가 컨텍스트에 안 들어옴 → deterministic 연산을 토큰 0으로.

## 우리 조사 축과의 관련성

일반화: "progressive disclosure = 로딩 시점을 필요시점까지 미룸"은 벤더 중립 원리. 원문대조 교차검증(Pocock 개념이 공식 아키텍처와 정합).
