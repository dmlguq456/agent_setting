# 01 · Technology Landscape — Skill Design Principles

> mode: technology · date: 2026-07-13

## 1. Category Taxonomy

이 분야의 개념 지도는 **상위 프레임 1개 + 4축 + 생태계 보강 개념**의 3층 구조다.

### 상위 프레임 (root)

- **Predictability** — *"the agent taking the same process every run, not producing the same output — is the root virtue; every lever below serves it."* (writing-great-skills SKILL.md). 같은 *출력*이 아니라 같은 *과정*의 재현. GLOSSARY 는 이를 *"The root virtue every other term serves — cost and maintainability are symptoms of it, not rivals."* 로 정의.
- **두 비용축** — 모든 레버가 지불하는 통화: **context load**(model-invoked description 이 *"permanent context load on every turn"*) vs **cognitive load**(user-invoked → *"you are the index"*).

### 4축 (canonical, GLOSSARY line 5)

| 축 | 원어 정의 | 커뮤니티 별칭 |
|---|---|---|
| ① Invocation | *"how a skill is reached"* | Trigger (StartupHub) |
| ② Information Hierarchy | *"how its content is arranged"* | Structure (StartupHub) |
| ③ Steering | *"how the agent's runtime behaviour is shaped"* | Steering (동일) |
| ④ Pruning | *"how it is kept lean"* | Pruning (동일) |

### 생태계 보강 개념 (원문 4축 밖)

- **Degrees of freedom** (Anthropic) — 작업 fragility 에 지시 구체성 매칭: narrow bridge(low freedom, 정확 스크립트) vs open field(high freedom, 방향만). 우리 `--intensity` 와 유사.
- **Evaluations-first** (Anthropic) — *"Create evaluations BEFORE writing extensive documentation."* 3 scenarios + baseline. Pocock 문서에 없는 강한 규범.
- **Skills vs MCP** (Anthropic) — 스킬=절차지식/조직컨텍스트, MCP=외부도구. 상호보완.
- **Auto-activation caveat** (scottspence) — model-invoked 자동발화는 description 이 정확히 매칭돼도 무시될 수 있고, UserPromptSubmit hook 워크어라운드를 적용한 뒤에도 신뢰도가 ~50%에 그친다. 원문 4축의 실전 반례이자, hook 만능론을 오히려 약화하는 근거(hook 을 써도 ~50%).

**Takeaway**: Predictability 를 정점으로, 4축이 레버, 생태계 보강 개념(특히 degrees-of-freedom·eval-first·auto-activation caveat)이 원문 밖에서 실전 정밀도를 더한다.

## 2. 개념 × 소스 Matrix

각 개념이 어느 소스에서 정의/보강되는지.

| 개념 | Pocock GLOSSARY/SKILL | Anthropic docs | 커뮤니티 |
|---|---|---|---|
| Predictability (root) | ★정의 (SKILL/GLOSSARY) | 암시 | Remio 재확인 |
| Invocation (model/user) | ★정의 (GLOSSARY) | Level 1 metadata / disable-model-invocation | KISDigital 보강 |
| context/cognitive load | ★정의 (GLOSSARY/README) | attention budget(공식) | — |
| Information Hierarchy 3-rung | ★정의 (SKILL) | 3-level(startup/trigger/on-demand) | StartupHub |
| Progressive disclosure | ★정의 (SKILL) | ★핵심 설계원리 (equipping-agents) | StartupHub |
| Context pointer wording | ★정의 (GLOSSARY: variance bug) | — | — |
| Steering / leading word | ★정의 (GLOSSARY: _Leitwort_) | 암시 | StartupHub·Remio |
| Completion criterion / premature completion | ★정의 (GLOSSARY) | — | Remio(5-test) |
| Negation→positive | ★정의 (GLOSSARY) | — | — |
| Pruning / no-op / SoT | ★정의 (SKILL) | token cost 정당화(best-practices) | Remio(5-test) |
| Failure modes(6종) | ★정의 (SKILL/GLOSSARY) | — | Remio(5-test) |
| Degrees of freedom | ❌ | ★정의 (best-practices) | generativeprogrammer |
| Evaluations-first | ❌ | ★정의 (best-practices) | generativeprogrammer |
| Skills vs MCP | ❌ | ★정의 (equipping-agents) | — |
| Auto-activation caveat | ❌ | ❌ | ★scottspence |
| 정량 규범(500줄·1-depth·3인칭 "Use when…") | ❌ | ★정의 (best-practices) | KISDigital |

**Takeaway**: 개념적 정의의 SoT 는 **Pocock GLOSSARY**, 메커니즘 근거와 정량 규범의 SoT 는 **Anthropic docs**, 실전 caveat 의 SoT 는 **커뮤니티**(특히 scottspence). 세 소스는 경쟁이 아니라 층위가 다르다.

## 3. Lineage Diagram (계보)

사용자 4단계 요약이 어디서 왔는지의 계보:

```
[원문 SoT]                    [커뮤니티 브리지]              [사용자 국문 요약]
mattpocock/skills                StartupHub                   사용자 4단계
GLOSSARY 4-axis        ──►    "Missing Manual"        ──►    체크리스트
                              4원칙 국문화 소스

Invocation             ──►    Trigger                 ──►    트리거
  (how reached)                "How invoked"                  (호출 방식)

Information Hierarchy   ──►    Structure               ──►    구조
  (how arranged)               "internal organization"        (절차 외 설명 배제 ⚠)

Steering ◄════확정════        Steering                ──►    유도 (Guidance)
  (runtime behaviour)          "how guided to                 └ canonical=Steering
                                perform actions"                 (Guidance 는 번역)

Pruning                ──►    Pruning                 ──►    가지치기
  (kept lean)                  "removing unnecessary"          (무동작 문장 삭제)
                                                               └ no-op 1개만 대표화

[누락 — 사용자 요약에 없음]
Predictability (root virtue) · context/cognitive load · 3-rung(2계층 아님) ·
completion criterion · negation · failure modes 6종
```

**Guidance ↔ Steering 확정** (search stage 가설 CONFIRMED):

| 근거 | 출처 | 인용 |
|---|---|---|
| 근거 1 (앵커) | GLOSSARY line 5 | *"…Steering (how the agent's runtime behaviour is shaped)…"* |
| 근거 2 | StartupHub | *"Steering: How the skill is guided to perform specific actions"* |
| 근거 3 (부차) | repo CHANGELOG 관찰(PR #463, 별도 카드화 안 됨) | *"Add two adjacent Steering failure modes…"* — Negation/Negative Space 를 Steering failure 로 분류. 대응 카드/code_resource 없음(문서 내부 자기참조뿐)이라 부차 근거로만 취급 |

→ 결론(canonical = **Steering**)은 **GLOSSARY line 5** 에 앵커한다. 사용자의 "유도(Guidance)"는 의미상 정확(Steering 정의가 "guided")하나 문헌 표준 라벨은 **Steering**. 다운스트림은 **"Steering(유도)"** 병기 권장.

**Takeaway**: 사용자 요약은 StartupHub 국문화를 경유한 정확한 계보를 가지며, 3번째 축의 원어 라벨만 Steering 으로 확정 병기하면 원문과 정합한다.

## 4. Adoption Stage

| 개념 | stage | 근거 |
|---|---|---|
| Predictability | 원문 root (established in repo) | SKILL/GLOSSARY 정점 개념 |
| Invocation 이분(model/user) | established | GLOSSARY 정의 + Anthropic frontmatter 공식 지원 |
| Progressive disclosure | mainstream/established | Anthropic *"core design principle"* + Pocock 동일 강조 |
| Steering / leading word | emerging→mainstream | Pocock 고유 프레이밍, 커뮤니티 확산 중 |
| Pruning / failure modes | emerging→mainstream | Pocock 정의 + Remio 5-test 로 커뮤니티 정착 |
| Degrees of freedom | Anthropic 보강 (mainstream) | 공식 best-practices |
| Evaluations-first | Anthropic 보강 (emerging) | 강한 규범이나 실무 채택 초기 |
| Auto-activation caveat | emerging (실전 반례) | scottspence 단일 소스 + KISDigital 정합 |

**Takeaway**: 원문 4축은 established, degrees-of-freedom·eval-first 는 Anthropic 발 보강, auto-activation caveat 는 아직 emerging 한 실전 반례로 "wording 단독으로는 자동발화가 불안정 → hook 강제 라우팅이 합당한 방향"까지를 뒷받침한다 — 단 hook 이 신뢰도를 회복한다는 강한 주장은 측정 미검증(소스는 hook 후에도 ~50%).

## Cross-References

- 각 축의 메커니즘 심층 → [04_technical_deep_dive.md](04_technical_deep_dive.md)
- 세 소스 관점 비교 → [03_vendor_comparison.md](03_vendor_comparison.md)
- 정량 규범 인벤토리 → [02_standards.md](02_standards.md)
