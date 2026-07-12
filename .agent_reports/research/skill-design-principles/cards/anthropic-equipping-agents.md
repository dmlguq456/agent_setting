# Anthropic — Equipping agents for the real world with Agent Skills (full-read)

- **title**: Equipping agents for the real world with Agent Skills
- **author**: Anthropic (engineering blog)
- **url**: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- **date**: 2026
- **type**: 공식 blog
- **access**: full-read (WebFetch)
- **관련 축**: 일반화 + 생태계확장

## Verbatim 핵심 인용 (직접 인용)

> "Progressive disclosure is the core design principle that makes Agent Skills flexible and scalable."

> "If Claude thinks the skill is relevant to the current task, it will load the skill by reading its full SKILL.md into context."

> "Skills can complement Model Context Protocol servers by teaching agents more complex workflows that involve external tools and software."

## 핵심 주장 요약

- Progressive disclosure 를 스킬 시스템의 *핵심* 설계원리로 못박음(Pocock 과 동일 강조점).
- 스킬 트리거는 모델 자율 판단("Claude thinks the skill is relevant") — Pocock 의 model-invoked 정의와 일치. (단 실제 자동발화 신뢰도 문제는 scottspence 카드 참조.)
- Skills vs MCP: 스킬=절차지식/조직컨텍스트, MCP=외부도구 통합 — 상호보완. 우리 하네스가 skill+MCP 를 함께 쓰는 구조와 정합.

## 우리 조사 축과의 관련성

일반화(progressive disclosure 의 벤더 공식 위상). 생태계확장(Skills↔MCP 경계 — 우리 harness 의 도구/스킬 분리 설계 비교점).
