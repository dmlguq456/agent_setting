# Sourcegraph — Context Engineering: A Practical Guide for AI Agents (full-read)

- **title**: Context Engineering: A Practical Guide for AI Agents (2026)
- **author**: Sourcegraph
- **url**: https://sourcegraph.com/blog/context-engineering
- **date**: 2026
- **type**: blog (vendor, 실무 가이드)
- **access**: full-read (WebFetch)
- **관련 축**: 일반화 (메커니즘 보강)

## Verbatim 핵심 인용 (직접 인용)

> "Token budget management is the discipline of cutting low-signal content _before_ it enters the context window, not after."

> "The model's ability to attend to any single piece degrades as input data grows."

> 실패 유형: **Context distraction**(무관 자료가 중요 사실 밀어냄) · **Context confusion**(상충 신호) · **Lost in the Middle**(긴 컨텍스트 중간의 정보가 저성능).

## 핵심 주장 요약

- Anthropic attention-budget 논지의 vendor-중립 재확인. 핵심: 저신호 컨텐츠는 *들어오기 전에* 잘라야(사후 무시에 의존 X) — Pocock pruning 의 "왜"에 대한 실무적 근거.
- "Lost in the Middle" → 스킬 본문 배치·co-location 이 성능에 영향한다는 근거.
- just-in-time retrieval(lightweight identifier) 재강조.

## 우리 조사 축과의 관련성

일반화: pruning/progressive disclosure 가 단일 벤더 주장이 아니라 업계 공통 원리임을 보강. analysis_summary 메커니즘 절의 보조 인용원.
