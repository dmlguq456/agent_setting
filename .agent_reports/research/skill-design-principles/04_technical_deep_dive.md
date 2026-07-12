# 04 · 4원칙 메커니즘 심층 — Skill Design Principles

> mode: technology · date: 2026-07-13
> 각 원칙을 (a)문제 정의 → (b)메커니즘(왜 context load / 행동유도 정확도에 영향) → (c)key insight 3층으로 전개. analysis_summary §2~§5 기반.

## ① Invocation (트리거)

**(a) 문제 정의.** 스킬에 도달하는 방식의 이분. **Model-Invoked** = description 유지 → 에이전트 자율발화 + 타 스킬 도달 가능, 대가는 **context load**(매 턴 상주). **User-Invoked** = `disable-model-invocation: true` → 사람만 호출, **zero context load** 이나 **cognitive load**(사람이 인덱스). 원문: *"There is no model-only state"* — model-invoked 는 항상 user reach 를 포함.

**(b) 메커니즘 (context load 영향).** description 만 상시 로드(~100 토큰/스킬, Anthropic Level 1). 스킬 수가 늘수록 description 들이 어텐션을 두고 경쟁 → 무분별한 model-invoked 화는 context load 증가로 *다른* 스킬 발화 정확도까지 저하시킨다. 반대로 전부 user-invoked 면 cognitive load 폭증 → **router skill**(`ask-matt`)로 흡수. code_search.md frontmatter 전수 카탈로그가 이를 실증: user-invoked 다수 + 단방향(user→model, user↛user).

**(c) Key insight.** invocation 선택은 "호출 방식"이 아니라 **어떤 load 를 지불하느냐의 경제 문제**다. `grill-me`(user, 1줄 위임) → `grilling`(model, 재사용 규율) 처럼 오케스트레이터(user-invoked)가 규율(model-invoked)을 호출하는 구조가 두 load 를 최적 분배한다. **Caveat**: description 이 정확히 매칭돼도 자동발화가 무시될 수 있고 hook 워크어라운드 뒤에도 신뢰도가 ~50%에 그친다(scottspence) → wording 단독 신뢰 불가이므로 hook 강제 라우팅이 합당한 방향이나, 우리 deterministic hook 의 신뢰도 이득은 측정 미검증이다.

## ② Information Hierarchy (구조)

**(a) 문제 정의.** 콘텐츠를 *즉시성 사다리*로 배치. **3-rung**: **in-skill step**(1차) → **in-skill reference**(2차) → **external reference behind context pointer**(필요시 로드). **Progressive disclosure** = 사다리 아래로 내리는 이동(*"so the top stays legible"*). **Co-location** = 내려간 뒤 *무엇을 옆에 둘지*(정의·규칙·caveat 한 heading). 원문: *"A context pointer's wording, not its target, decides when and how reliably the agent reaches the material."*

**(b) 메커니즘 (부하·정확도 영향).** SKILL.md body 는 트리거 시 통째 로드(Anthropic Level 2, <5k 토큰). 필요 없는 reference 를 인라인하면 sprawl → 어텐션 희석 + *"lost in the middle"*(Sourcegraph). disclosure 는 필요 branch 만 로드해 고신호 유지 = just-in-time retrieval 의 스킬판. 단 must-have 자료가 약한 pointer 뒤에 있으면 **variance bug**(동전 던지기식 로딩).

**(c) Key insight.** target 이 아니라 **pointer 의 wording 이 도달 시점·신뢰도를 결정**한다. ⚠️ 사용자 요약의 "2계층/절차 외 설명 배제"는 부정확 — 실제는 **3-rung**이고, "설명 배제"는 Pruning 소관이다. tdd(all-reference + tests.md/mocking.md 1-depth), code-review(2축 병렬 sub-agent 로 관심사 격리)가 canonical 예시.

## ③ Steering (유도)

**(a) 문제 정의.** 런타임 행동을 Predictability 로 형성하는 레버들 — GLOSSARY verbatim 은 *"how the agent's runtime behaviour is shaped"*. 하위: **Leading Word**(_Leitwort_), **Completion Criterion**(checkable + exhaustive), **Post-Completion Steps 숨기기**, **Premature Completion**(방어대상), **Negation**(부정 대신 긍정).

**(b) 메커니즘 (행동유도 정확도 영향).**
- *Leading word*: 이미 사전학습된 개념(_seam_, _red→green_, _vertical slice_, _tracer bullet_, _fog of war_)을 토큰 하나로 소환 → 최소 토큰으로 행동 앵커. description 에 쓰면 invocation 도 앵커. 원문: *"You win twice over: fewer tokens, and a sharper hook."* 자작 단어는 prior 미소환 → *"a made-up word recruits no priors — you pay in definition tokens what a pretrained word gives free."*
- *미래 단계 숨기기*: 보이는 post-completion steps 는 에이전트를 *끝났다는 상태*로 당겨 **premature completion** 유발 → 순서를 둘로 쪼개 뒤를 컨텍스트에서 제거. **단, 실제 context 경계(subagent/user hand-off)에서만 효과**; 인라인 model-invoked 는 안 지워짐. **우선순위**: completion criterion 을 먼저 날카롭게(cheap·local), 관찰된 rush + 환원불가 모호일 때만 숨기기.
- *Negation*: 금지는 금지대상을 프레임에 끌어와 *더* available(*"don't think of an elephant"*) → 긍정 목표로 서술.

**(c) Key insight.** leading word 는 **토큰↓ + 앵커↑ 이중 이득**의 핵심 레버다. tdd 의 leading-word 밀집이 실증. ✅ 사용자의 "강력한 기존 용어로 즉각 행동 유도 + 미래 숨기기"는 정확 매핑이나 completion criterion·negation 이 누락됐다.

## ④ Pruning (가지치기)

**(a) 문제 정의.** 스킬을 lean 하게. **Single Source of Truth**(각 의미는 한 권위 자리 → 한 곳 편집), **Relevance**(줄이 여전히 작업에 관여하나), **No-Op 테스트**(모델이 기본으로 이미 하는가 = default 대비 행동 변화 있나). 원문: *"hunt no-ops sentence by sentence… when one fails, delete the whole sentence rather than trim words from it. Be aggressive."* Failure modes: **Duplication / Sediment / Sprawl / No-Op**.

**(b) 메커니즘 (부하 영향).** no-op·sediment·duplication·sprawl 은 전부 **attention budget 낭비** — 행동을 안 바꾸는 토큰이 고신호 토큰의 어텐션을 잠식(context rot). duplication 은 유지비 + *의미 서열 과대평가*(사다리에서 실제 rank 넘어 부풀림) — leading word 의 정확한 역상(반복으로 의미가 아니라 *주의*를 부당하게 올림).

**(c) Key insight.** pruning 은 "간결함"이 아니라 **성능 레버**다 — 저신호 토큰 제거가 고신호 토큰 정확도를 회복시킨다. Anthropic *"context window is a public good"*, *"does this paragraph justify its token cost?"*, *"Claude is already very smart"* 가 동형. tdd 가 refactor 규칙을 code-review 로 이관한 것(SoT 실천, CHANGELOG)이 실증. ✅ 사용자의 "무동작 문장 삭제"는 No-Op 테스트만 대표화(SoT/relevance/sediment/sprawl 누락).

## 메커니즘 근거 표 (MANDATORY)

| 원칙 | 메커니즘 | 뒷받침 근거 | 출처 카드 |
|---|---|---|---|
| Invocation | description 상주가 어텐션 경쟁 유발 | ~100토큰/skill always-loaded → context load | anthropic-skills-overview (Level 1) |
| Information Hierarchy | 인라인 sprawl → 어텐션 희석 | "lost in the middle" + context rot | sourcegraph-context-engineering, anthropic-context-engineering |
| Steering (leading word) | 사전학습 prior 소환으로 최소 토큰 앵커 | attention budget 절약 + 행동 앵커 | anthropic-context-engineering, writing-great-skills-glossary |
| Pruning | 저신호 토큰이 고신호 정확도 잠식 | *"attention budget"*, *"context rot"* — retrieval 정확도 저하 | anthropic-context-engineering, sourcegraph-context-engineering |

원문 인용: *"LLMs have an 'attention budget'…"* / *"context rot — retrieval 정확도가 저하"* (anthropic-context-engineering). *"Token budget management is the discipline of cutting low-signal content before it enters the context window, not after."* / *"The model's ability to attend to any single piece degrades as input data grows."* (sourcegraph).

**Takeaway**: 4원칙은 모두 동일한 물리적 근거(유한한 attention budget + context rot)로 환원되며, pruning·progressive disclosure·leading word 는 전부 "고신호 토큰 밀도를 지키는" 서로 다른 레버다.

## Performance Trade-off

- **context load ↔ cognitive load**: model-invoked 를 늘리면 자동 도달성↑이나 매 턴 어텐션 경쟁↑. user-invoked 를 늘리면 context 절약이나 사람 기억 부담↑. router skill 이 이 곡선의 최적점.
- **high-signal 토큰 밀도 ↔ coverage**: pruning 을 aggressive 하게 하면 밀도↑이나 edge-case 커버리지↓ 위험. Anthropic *"minimal ≠ sparse — 충분한 정보는 남겨야"* 가 하한.
- **leading word 압축 ↔ 자작 용어 정의비**: pretrained 단어는 무료 앵커, 자작 단어는 정의 토큰 지불. 압축 이득은 prior 존재 여부에 달림.

**Takeaway**: 모든 trade-off 는 "어텐션 예산을 어디에 쓸까"의 배분 문제이며, 정답은 작업 fragility(degrees of freedom)에 따라 달라진다.

## 미해결 과제 / 긴장

| 과제 | difficulty | impact |
|---|---|---|
| **auto-activation 신뢰도** — model-invoked 자동발화 실전 불안정, wording 개선의 상한 불명, hook 워크어라운드 후에도 ~50% 잔존(scottspence) | high | high (hook 보강도 ~50% 잔존 — 신뢰도 이득 측정 미검증) |
| **pointer wording 견고성 측정 불가** — "얼마나 강한 pointer 인가"의 정량 지표 부재 | high | high (variance bug 사전 탐지 어려움) |
| **no-op 판정의 주관성** — "모델이 기본으로 하는가"는 모델·버전 의존, 재현 어려움 | medium | medium (audit 판정 흔들림) |
| **미래 단계 숨기기의 조건부 효과** — 실제 context 경계에서만 작동, 인라인은 무효 | medium | medium (오적용 시 무효 노력) |
| **degrees of freedom 매핑 규칙 부재** — 작업 fragility→지시 구체성 매핑이 정성적 | medium | medium (intensity 자동화 한계) |
| **completion criterion exhaustiveness 검증** — "빠짐없음"을 어떻게 보장하나 | high | medium (premature completion 재발) |
| **leading word prior 존재 확인 불가** — 특정 단어가 모델 prior 를 소환하는지 사전 확인 불가 | medium | low (경험적 선택에 의존) |

**Takeaway**: 가장 큰 미해결 긴장은 **정량화 불가능성** — auto-activation 신뢰도·pointer wording 견고성·no-op 판정이 모두 측정 지표를 결여해, 우리 harness 는 hook 강제·drill 회귀 같은 *공학적 안전망*으로 이를 우회한다. 단 hook 강제 자체의 신뢰도 이득도 측정 미검증(scottspence 근거상 hook 후에도 ~50%)이라, 안전망은 "합당한 방향"이지 검증된 해결이 아니다.

## Cross-References

- 정량 규범·failure 진단 → [02_standards.md](02_standards.md)
- 관점별 상충(wording vs hook) → [03_vendor_comparison.md](03_vendor_comparison.md)
- 배포 시 mitigation → [05_deployment.md](05_deployment.md)
