# mattpocock/skills — tdd/SKILL.md (Steering·leading-word 예시, full-read verbatim)

- **title**: tdd SKILL.md (code exemplar)
- **author**: Matt Pocock
- **url**: https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md
- **date**: 2026
- **type**: repo / SKILL.md (예시)
- **access**: full-read (`code_resources/tdd.SKILL.md`)
- **관련 축**: 원문대조 (원칙의 살아있는 구현 예시) — Phase C

## Verbatim 핵심 인용 (직접 인용)

> "A **seam** is the public boundary you test at … Tests live at seams, never against internals."

> "Work in **vertical slices** instead — one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you."

> "Red before green. Write the failing test first … Refactoring is not part of the loop. It belongs to the review stage."

> 진입부: "When exploring the codebase, read `CONTEXT.md` (if it exists) so test names and interface vocabulary match the project's domain language."

## 핵심 주장 요약

- **all-reference 스킬 예시**(steps 없음) — GLOSSARY 가 말한 "flat peer-set" 형태. 그럼에도 completion criterion("every section applies on every cycle")이 legwork 를 강제.
- **Leading word 밀집 사례**: `seam`, `red → green`, `vertical slice`, `tracer bullet` — 각각 pretrained prior 를 소환해 최소 토큰으로 행동 앵커.
- **Progressive disclosure**: 상세는 `tests.md`·`mocking.md` 로 분리(1-depth).
- **Single source of truth**: CHANGELOG 상 refactor 규칙은 code-review 로 이동(중복 제거) — pruning 실천례.

## 우리 조사 축과의 관련성

Steering(leading word)·Information hierarchy(all-reference+disclosure)·Pruning(SoT)이 한 파일에 동시 구현된 canonical 예시. 하네스매핑 시 "우리 스킬도 leading word 로 재작성 가능한가" 벤치마크.
