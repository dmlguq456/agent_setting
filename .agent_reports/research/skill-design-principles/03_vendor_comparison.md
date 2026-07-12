# 03 · 소스별 관점 비교 — Skill Design Principles

> mode: technology · date: 2026-07-13
> vendor 제품 비교 대신, 동일 주제를 다룬 **세 관점(Anthropic 공식 / Matt Pocock 개인 철학 / 커뮤니티 실전)**의 강조점·차이·상충을 비교한다.

## 1. 관점 Matrix

| 관점 | 대표 소스 | 프레이밍 언어 | 강조점 | 약점/공백 |
|---|---|---|---|---|
| **Anthropic 공식** | best-practices, context-engineering, skills-overview, equipping-agents | 측정·규범 ("context window is a **public good**", "attention budget", "degrees of freedom") | 정량 수치(500줄·1-depth·~100토큰), progressive disclosure 를 *core* 원리로, evaluations-first, context rot 메커니즘 | Steering 세부(leading word·negation) 부재, 개별 skill 언어 규율 얕음 |
| **Matt Pocock** | writing-great-skills SKILL/GLOSSARY, tdd, grill-me, README | 개념·언어 ("**Predictability** = root virtue", "_Leitwort_", "context pointer wording") | 4축 명시 정의, leading word 로 최소 토큰 앵커, completion criterion·미래 숨기기, SoT 실천례 | 정량 수치 얇음, eval 규범 없음, degrees-of-freedom 개념 없음 |
| **커뮤니티(실전)** | StartupHub, Remio, scottspence, generativeprogrammer | 실전·caveat ("4원칙 국문화", "5-test", "**don't auto-activate**") | 4원칙 요약 접근성, pruning 5-test, auto-activation 불안정 반례(hook 후에도 ~50%), hook 우회책 | 1차 정의는 Pocock/Anthropic 인용에 의존, 신규 개념 적음 |

**Takeaway**: Anthropic 은 *측정 가능한 규범*, Pocock 은 *개념·언어 정밀도*, 커뮤니티는 *실전 반례*를 담당한다 — 세 관점을 층위별로 조합해야 완전한 그림이 된다.

## 2. Capability Checklist (개념 × 관점)

다룸 ✅ / 암시 △ / 공백 ❌

| 개념 | Anthropic 공식 | Matt Pocock | 커뮤니티 |
|---|---|---|---|
| Predictability (root virtue) | △ | ✅ | ✅ (Remio) |
| Degrees of freedom | ✅ | ❌ | ✅ (generativeprogrammer) |
| Evaluations-first | ✅ | ❌ | △ (generativeprogrammer) |
| Auto-activation caveat | ❌ | ❌ | ✅ (scottspence) |
| Failure-mode taxonomy(6종) | ❌ | ✅ | △ (Remio 5-test) |
| Leading word / _Leitwort_ | △ | ✅ | △ (StartupHub) |
| Context pointer wording | ❌ | ✅ | △ (StartupHub) |
| Progressive disclosure | ✅ | ✅ | ✅ |
| attention budget / context rot | ✅ | △ | ✅ (Sourcegraph) |
| 정량 수치(500줄·1-depth) | ✅ | ❌ | △ (KISDigital) |

**Takeaway**: 세 관점이 모두 ✅ 인 유일한 개념은 **progressive disclosure** — 이 분야의 합의된 핵심 원리다. 반대로 각 관점 고유 강점(Anthropic=degrees-of-freedom·eval, Pocock=failure taxonomy·leading word, 커뮤니티=auto-activation caveat)은 다른 관점에 공백으로 남는다.

## 3. 상충 / 긴장 지점

| 지점 | 관점 A | 관점 B | 상충 성격 | 우리 harness 의 해소 |
|---|---|---|---|---|
| **wording 신뢰도** | Pocock: *"context pointer's wording decides how reliably the agent reaches material"* | scottspence: *"skills just sit there… you have to remember to use them"*, wording 매칭돼도 무시, hook 워크어라운드 후에도 ~50% | 이론(wording 이 신뢰도 결정) vs 실전(wording 만으론 부족) | **hook 강제**(합당한 방향) — `mem-recall-inject`·`workflow-guard-hook` 로 wording 위에 강제 주입 계층 추가. 단 우리 deterministic hook 의 신뢰도 이득은 측정 미검증(scottspence 근거상 hook 도 ~50%) |
| **model-invoked 자율성** | Anthropic: *"If Claude thinks the skill is relevant, it will load…"* (자율 판단 신뢰) | scottspence: auto-activation 불안정 | 공식 문서 낙관 vs 실전 회의 | model-invoked description + hook trigger 이중화 |
| **process 소유** | GSD/BMAD/Spec-Kit: process 를 프레임워크가 소유 | Pocock: *"they take away your control… small, composable skills"* | 통제권 집중 vs 분산 | autopilot-* 는 파이프(process 일부 소유)이나 skill 조합 가능 — 중간 지점 |
| **완결성 규범** | Anthropic: eval-first (사전 시나리오) | Pocock: completion criterion (runtime 판정) | 사전 평가 vs 런타임 판정 | drill 회귀(사후) + completion criterion(런타임) 병행 |

**Takeaway**: 가장 중요한 상충은 **"wording 이 신뢰도를 결정한다"(Pocock) vs "wording 만으론 부족 — hook 후에도 ~50%"(scottspence)**이며, 우리 harness 의 hook 강제 라우팅은 이 긴장에 대한 **합당한 대응 방향**이다 — Pocock 의 wording 규율은 유지하되 hook 이 안전망을 깐다. 다만 scottspence 근거상 hook 을 써도 ~50%에 그쳐 완전한 해소는 아니며, 우리 deterministic UserPromptSubmit 주입의 신뢰도 이득은 측정 미검증이다.

## 4. 우리 harness 설계 시 관점 배분

| 설계 자리 | 채택 관점 | 이유 |
|---|---|---|
| 정량 audit 기준(줄 수·depth·description) | Anthropic 공식 | 측정 가능한 hard 스캔 기준 제공 |
| 4축 라벨·steering wording·failure taxonomy | Matt Pocock | 개념 정의의 SoT |
| invocation 신뢰도 보강(hook) | 커뮤니티(scottspence) | 실전 반례가 hook 강제의 합당성 근거(단, 신뢰도 이득은 측정 미검증) |
| context budget 메커니즘 서술 | Anthropic(attention budget) + Sourcegraph | 벤더 중립 재확인 |

**Takeaway**: 우리 harness 는 세 관점을 배타적으로 고르지 않고 층위별 분업으로 채택한다 — Anthropic(규범)·Pocock(개념)·커뮤니티(caveat/hook).

## Cross-References

- auto-activation caveat 의 배포 대응 → [05_deployment.md](05_deployment.md)
- 4축 개념 정의 상세 → [04_technical_deep_dive.md](04_technical_deep_dive.md)
