# Anthropic — Effective context engineering for AI agents (attention budget, full-read)

- **title**: Effective context engineering for AI agents
- **author**: Anthropic (engineering blog)
- **url**: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **date**: 2026
- **type**: 공식 blog
- **access**: full-read (WebFetch)
- **관련 축**: 일반화 (메커니즘 근거)

## Verbatim 핵심 인용 (직접 인용)

> "LLMs have an 'attention budget' that they draw on when parsing large volumes of context."

> 목표는 "the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." (minimal ≠ sparse — 충분한 정보는 남겨야 함)

> "context rot" — context 가 길어질수록 retrieval 정확도가 저하(capability 는 보존되나).

> just-in-time: 에이전트는 "lightweight identifiers (file paths, stored queries, web links, etc.)" 를 유지하고 런타임에 동적 retrieve.

## 핵심 주장 요약

- **이것이 "왜 pruning·progressive disclosure 가 효과 있나"의 메커니즘 근거**: 어텐션은 유한 예산이고, 컨텍스트가 길수록 성능이 저하("context rot", n² 어텐션 제약). 따라서 저신호 토큰을 넣는 것 자체가 고신호 토큰의 정확도를 깎는다.
- Pocock 의 no-op/sprawl/sediment 는 이 예산을 낭비하는 행위로 환원됨 — leading word 는 예산을 아끼면서 행동을 앵커.
- context pointer/progressive disclosure = just-in-time retrieval 의 스킬판.

## 우리 조사 축과의 관련성

일반화 — 4원칙 각각의 *메커니즘 절*(왜 컨텍스트 부하/행동유도 정확도에 영향 주는지)을 뒷받침하는 1차 근거. analysis_summary 의 (b) 메커니즘 파트 핵심 인용원.
