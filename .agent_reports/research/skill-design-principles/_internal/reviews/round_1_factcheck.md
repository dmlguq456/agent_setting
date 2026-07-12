# Round 1 — Fact-Check (verbatim/정량 대조)

> reviewer: 연구팀 fact-check subrole · date: 2026-07-13 · mode: fast (table-only)
> scope: 00~07 보고서의 verbatim 인용 + 정량 규범 + frontmatter invocation 분류. coverage/narrative/roadmap 품질은 대상 아님.
> SoT: `cards/*` + `code_resources/*` (git clone verbatim: writing-great-skills SKILL.md/GLOSSARY.md 등) + `_internal/{pocock-verbatim-comparison,code_search}.md`.

| Report | Section | Claim | Source card (file:line 또는 카드명) | Match | Severity |
|---|---|---|---|---|---|
| 00 | Level 0/1 | Predictability = "same process every run, not producing the same output" | writing-great-skills.SKILL.md:13 / skill card:13 | ✅ | — |
| 01 | root | Predictability GLOSSARY def "root virtue every other term serves — cost and maintainability are symptoms of it, not rivals" | glossary card:15 / GLOSSARY.md verbatim | ✅ | — |
| 00/01 | 4축 | 4-axis "Invocation/Information Hierarchy/Steering/Pruning" @ GLOSSARY line 5 | GLOSSARY.md:5 (grep 확인, line 정확) / glossary card:13 | ✅ | — |
| 01 | 4축 원어 | "how a skill is reached / how its content is arranged / how runtime behaviour is shaped / how it is kept lean" | GLOSSARY.md:5 verbatim | ✅ | — |
| 04 | Invocation | "There is no model-only state" (model-invoked always includes user reach) | GLOSSARY.md:21 verbatim ("There is no model-only state: …") | ✅ | — |
| 00/04 | 두 비용축 | context load (permanent every turn) vs cognitive load ("you are the index") | skill card:16,33 / GLOSSARY.md verbatim | ✅ | — |
| 04/pocock-cmp | Steering | "context pointer's wording, not its target, decides when and how reliably the agent reaches the material" | skill card:22 / GLOSSARY.md:23 (variance bug) | ✅ | — |
| 00/04 | Steering | leading word = _Leitwort_ / made-up word "recruits no priors — you pay in definition tokens what a pretrained word gives free" | GLOSSARY.md:131 verbatim / glossary card:19 | ✅ | — |
| 04/pocock-cmp | Steering | "You win twice over: fewer tokens, and a sharper hook…" | writing-great-skills.SKILL.md:72 verbatim | ✅ | — |
| 02/04 | Steering | Negation "don't think of an elephant … Prompt the positive" | SKILL.md:83 / GLOSSARY.md:163 / skill card:27 | ✅ | — |
| 04 | Steering | leading-word 예시 seam/red→green/vertical slice/tracer bullet/fog of war | code_search.md:31-33 / tdd.SKILL.md / GLOSSARY.md:131 | ✅ | — |
| 04 | Pruning | "hunt no-ops sentence by sentence … delete the whole sentence rather than trim words. Be aggressive." | skill card:23 / SKILL.md verbatim | ✅ | — |
| 02 | failure modes | 6종 premature completion/negation/sprawl/variance bug/duplication/sediment(+no-op) | skill card:34 / glossary card:29 | ✅ | — |
| 01/03 | 커뮤니티 라벨 | StartupHub 4원칙 "Trigger/Structure/Steering/Pruning" | startuphub card:14 verbatim | ✅ | — |
| 01/pocock-cmp | Guidance↔Steering | StartupHub "Steering: How the skill is guided to perform specific actions" | startuphub card:14 | ✅ | — |
| 01/pocock-cmp | 근거2 | CHANGELOG PR #463 "Add two adjacent Steering failure modes to writing-great-skills" | 대응 card/code_resource 없음 — _internal/pocock-cmp:22 에만 존재 | ❌ | 🟡 |
| 02/07 | 정량 | SKILL.md body < 500 lines | best-practices card:21 verbatim | ✅ | — |
| 02/07 | 정량 | references one level deep (1-depth) | best-practices card:21 verbatim | ✅ | — |
| 02/06 | 정량 | description "3인칭 gerund" | card:21 은 "third person"만 verbatim, "gerund"는 관련성 note(:33)에만 — verbatim 미지원 | ❌(부분) | 🟡 |
| 02/06 | 정량 | model-invoked description "Use when…" 트리거 | writing-great-skills.SKILL.md:15 ("Use when the user wants…") / best-practices card:29 | ✅ | — |
| 02 | 정량 | user-invoked = `disable-model-invocation: true` | code_search.md:21 / SKILL.md:15 | ✅ | — |
| 02/05 | 정량 | Level1 ~100 tokens/skill, always @ startup | skills-overview card:17 verbatim | ✅ | — |
| 02/05 | 정량 | Level2 body < 5k tokens, when triggered | skills-overview card:18 verbatim | ✅ | — |
| 02 | 정량 | Level3 resources effectively unlimited, as needed | skills-overview card:18 verbatim | ✅ | — |
| 02/04 | 근거 | "context window is a public good" | best-practices card:13 verbatim | ✅ | — |
| 04 | Pruning 근거 | "Does this paragraph justify its token cost?" / "Claude is already very smart" | best-practices card:15 verbatim | ✅ | — |
| 02 | 규범 | "Create evaluations BEFORE writing extensive documentation" | best-practices card:20 verbatim | ✅ | — |
| 01/02 | 보강 | degrees of freedom narrow-bridge vs open-field | best-practices card:17 verbatim | ✅ | — |
| 03/04 | auto-activation | model-invoked 실전 신뢰도 ~50% | scottspence card:17 ("그래도 신뢰도 ~50%") verbatim | ✅ | — |
| 04 | 메커니즘 | "LLMs have an 'attention budget'" / "context rot" | anthropic-context-engineering card:13,18 verbatim | ✅ | — |
| 04 | 메커니즘 | Sourcegraph "cutting low-signal content before it enters" / lost-in-the-middle | sourcegraph card:14,18 verbatim | ✅ | — |
| 06/04 | invocation 분류 | user-invoked 다수 + 단방향(user→model, user↛user) | code_search.md:27 | ✅ | — |
| 06/04 | invocation 예시 | grill-me(user)→grilling(model), ask-matt(user router), prototype/tdd(model) | code_search.md:23-25 | ✅ | — |
| 05 | context budget | 28 skill × ~100 tokens ≈ ~2,800 tokens always-loaded | skills-overview card:17 (계산 정합; 28=harness 내부값) | ✅ | — |

## 비고

- verbatim 인용은 전수 code_resources(git clone SoT) 대조 결과 **모두 원문 일치** — Predictability, "no model-only state", context pointer wording, leading word/_Leitwort_, "You win twice over", "don't think of an elephant", GLOSSARY 4-axis 문장(line 5 정확), no-op "Be aggressive" 모두 verbatim 정확.
- 🟡①(CHANGELOG PR #463 인용): 해당 verbatim 을 담은 card/code_resource 가 없음(문서 안 _internal 자기참조뿐). 다만 그것이 뒷받침하는 "canonical=Steering" 결론은 GLOSSARY.md:5·StartupHub 로 **독립 확증**되므로 결론 자체는 안전. → 카드화 또는 인용 완화 권장.
- 🟡②("3인칭 gerund"): Anthropic best-practices verbatim 은 "third person"까지만 지원. "gerund"는 카드 verbatim 에 없고 관련성 note 에만 등장. "Use when…" 트리거는 Pocock SKILL.md:15 로 별도 확증되나, "gerund" 표현은 Anthropic 원문 근거 부재. → "3인칭 + 'Use when…'"로 표현 조정 권장.
- 🔴 없음. fabrication risk 수준의 무근거 verbatim/정량 claim 미발견.
