# Analysis Summary — Skill Design Principles (Matt Pocock 'writing-great-skills' 심층)

- **topic**: skill-design-principles · **mode**: technology · **depth**: deep · **date**: 2026-07-13
- **phase flags**: `chaining_available: false`(technology mode — Phase B 비활성) · `code_search_available: true` · `figures: n/a`
- **sources**: 21 cards (full-read 13 / abstract 8) · anchor = mattpocock/skills repo verbatim clone
- **입력 통합**: `cards/*` + `_internal/pocock-verbatim-comparison.md` + `_internal/code_search.md`

---

## 0. 핵심 발견 (executive)

1. **원문의 실제 4축은 Invocation / Information Hierarchy / Steering / Pruning** (GLOSSARY line 5 명시). 사용자 요약(트리거/구조/유도/가지치기)은 커뮤니티(StartupHub)의 Trigger/Structure/Steering/Pruning 을 국문화한 것으로 **개념은 맞다**.
2. **"유도(Guidance)"의 canonical 라벨은 "Steering"** — search stage 가설 CONFIRMED. Steering 은 leading word·completion criterion·미래단계 숨기기·negation 을 묶는 축.
3. **상위 개념 Predictability**(같은 *출력*이 아니라 같은 *과정*)가 4축 전체의 목적 — 사용자 요약에서 누락된 가장 중요한 프레임.
4. 모든 레버는 **두 비용축**으로 환원: **context load**(model-invoked description 상주) vs **cognitive load**(user 가 기억). 대부분의 설계 결정(split/inline/invocation)이 이 둘의 지불 문제.
5. Pocock 원칙의 *메커니즘*은 Anthropic "attention budget / context rot" 로 뒷받침 — 저신호 토큰은 고신호 토큰의 정확도를 깎으므로 pruning·progressive disclosure 가 성능 레버가 된다.

---

## 1. 상위 프레임: Predictability + 두 load

- **(a) 정의**: *"A skill exists to wrangle determinism out of a stochastic system. Predictability — the agent taking the same process every run, not producing the same output — is the root virtue."* (SKILL.md)
- **(b) 메커니즘**: LLM 은 확률적 시스템. 스킬은 *출력*을 고정할 수 없고 *과정*을 고정한다. 두 비용축(context/cognitive load)이 이 과정 고정의 예산 제약.
- **(c) 근거**: GLOSSARY §Predictability(`_Avoid_`: consistency/reliability/output-determinism); README(GSD/BMAD/Spec-Kit 은 process 를 소유해 통제권 상실 → 작고 조합가능한 스킬로 대체).

---

## 2. 원칙 ① Invocation (트리거)

- **(a) 원문 정의**: 스킬 도달 방식의 이분. **Model-Invoked** = description 유지 → 에이전트 자율발화 + 타 스킬 도달 가능, 대가는 **context load**(매 턴 상주). **User-Invoked** = `disable-model-invocation: true` → 사람만 호출, **zero context load** 이나 **cognitive load**(사람이 인덱스). *"There is no model-only state"* — model-invoked 는 항상 user reach 를 포함.
- **(b) 메커니즘 (컨텍스트 부하 영향)**: description 만 상시 로드(~100 토큰/스킬, Anthropic Level 1). 스킬 수가 늘수록 description 들이 어텐션을 두고 경쟁 → 무분별한 model-invoked 화는 context load 증가로 *다른* 스킬 발화 정확도까지 저하. 반대로 전부 user-invoked 면 cognitive load 폭증 → **router skill** 로 흡수.
- **(c) 근거/사례**: frontmatter 전수 카탈로그(`code_search.md`) — user-invoked 다수 + 단방향(user→model). `grill-me`(user, 1줄 위임) → `grilling`(model, 재사용 규율). `ask-matt` = router. **Caveat(scottspence)**: 실전 auto-activation 신뢰도 ~50% → description wording 만으론 부족, hook 강제 보강 필요.

---

## 3. 원칙 ② Information Hierarchy (구조)

- **(a) 원문 정의**: 콘텐츠를 *즉시성 사다리*로 배치. 3-rung: **in-skill step**(1차) → **in-skill reference**(2차) → **external reference behind context pointer**(필요시 로드). **Progressive disclosure** = 사다리 아래로 내리는 이동("so the top stays legible"). **Co-location** = 내려간 뒤 *무엇을 옆에 둘지*(정의·규칙·caveat 한 heading). **Context pointer 의 wording 이 도달 시점·신뢰도를 결정**(target 이 아니라).
- **(b) 메커니즘 (부하·정확도 영향)**: SKILL.md body 는 트리거 시 통째 로드(Anthropic Level 2, <5k 토큰 권장). 필요 없는 reference 를 인라인하면 sprawl → 어텐션 희석 + "lost in the middle"(Sourcegraph). disclosure 는 필요 branch 만 로드해 고신호 유지 = just-in-time retrieval 의 스킬판. 단 must-have 자료가 약한 pointer 뒤에 있으면 **variance bug**(코인플립 로딩).
- **(c) 근거/사례**: Anthropic overview 3-level 테이블(startup/trigger/on-demand); best-practices(<500줄, 참조 1-depth, 깊은 중첩 참조 금지); tdd(all-reference + tests.md/mocking.md 1-depth); code-review(2축 병렬 sub-agent 로 관심사 격리). ⚠️ 사용자 요약의 "2계층/절차 외 설명 배제"는 부정확 — 3-rung 이고, "설명 배제"는 Pruning 소관.

---

## 4. 원칙 ③ Steering (유도) — canonical 용어

- **(a) 원문 정의**: *"the levers that shape the agent's runtime behaviour toward Predictability."* 하위: **Leading Word**(pretrained prior 소환하는 압축 개념, _Leitwort_), **Completion Criterion**(checkable + exhaustive), **Post-Completion Steps 숨기기**(= "단계별 미래 숨기기"), **Premature Completion**(방어대상), **Negation**(부정 대신 긍정 지시).
- **(b) 메커니즘 (행동유도 정확도 영향)**:
  - *Leading word*: 이미 사전학습된 개념(_seam_, _red_, _tracer bullet_, _fog of war_)을 토큰 하나로 소환 → **최소 토큰으로 행동 앵커** + description 에 쓰면 invocation 도 앵커(prompts/docs/code 에 같은 단어 → 발화 신뢰도↑). "You win twice over: fewer tokens, and a sharper hook." 자작 단어는 prior 미소환 → 정의 토큰 낭비.
  - *미래 단계 숨기기*: 보이는 post-completion steps 는 에이전트를 *끝났다는 상태*로 당겨 **premature completion** 유발 → 순서를 둘로 쪼개 뒤를 컨텍스트에서 제거(단, 실제 context 경계 = subagent/user hand-off 에서만 효과; 인라인 model-invoked 는 안 지워짐). **우선순위**: completion criterion 을 먼저 날카롭게(cheap·local), 관찰된 rush + 환원불가 모호일 때만 숨기기.
  - *Negation*: 금지는 금지대상을 프레임에 끌어와 *더* available("don't think of an elephant") → 긍정 목표로 서술.
- **(c) 근거/사례**: GLOSSARY §Steering 전체; tdd 의 leading-word 밀집; StartupHub("consistent leading words like vertical slice … more predictable"); Remio("expected outcome word first"). ✅ 사용자의 "강력한 기존 용어로 즉각 행동 유도 + 미래 숨기기"는 정확 매핑, 단 completion criterion·negation 누락.

---

## 5. 원칙 ④ Pruning (가지치기)

- **(a) 원문 정의**: 스킬을 lean 하게. **Single Source of Truth**(각 의미는 한 권위 자리 → 한 곳 편집), **Relevance**(줄이 여전히 작업에 관여하나), **No-Op 테스트**(모델이 기본으로 이미 하는가 = default 대비 행동 변화 있나). 문장 단위로 no-op 사냥, 실패 시 *단어 다듬기 말고 문장 통째 삭제*, "Be aggressive." Failure modes: **Duplication / Sediment / Sprawl / No-Op**.
- **(b) 메커니즘 (부하 영향)**: no-op·sediment·duplication·sprawl 은 전부 **attention budget 낭비** — 행동을 안 바꾸는 토큰이 고신호 토큰의 어텐션을 잠식(context rot). duplication 은 유지비 + *의미 서열 과대평가*(사다리에서 실제 rank 넘어 부풀림). leading word 의 정확한 역상(반복으로 의미가 아니라 *주의*를 의도적으로 올림).
- **(c) 근거/사례**: SKILL.md §Pruning + §Failure modes; Anthropic best-practices("context window is a public good", "does this paragraph justify its token cost?", "Claude is already very smart"); Remio(5-test 요약); tdd(refactor 규칙을 code-review 로 이관 = SoT 실천, CHANGELOG). ✅ 사용자의 "무동작 문장 삭제 테스트"는 No-Op 테스트 정확 반영(단 SoT/relevance/sediment/sprawl 누락).

---

## 6. 생태계 보강 개념 (원문 4축 밖, 일반화)

- **Degrees of freedom**(Anthropic): 작업 fragility 에 지시 구체성 매칭(low=정확 스크립트 / high=방향만). 우리 intensity 와 유사.
- **Evaluations-first**(Anthropic): 문서 쓰기 전 평가 시나리오 3개 + baseline. 강한 규범.
- **Skills vs MCP**: 스킬=절차지식, MCP=외부도구. 상호보완.
- **정량 규범**: SKILL.md <500줄, 참조 1-depth, description 3인칭 gerund "Use when…".

---

## 7. 다운스트림 함의 (스킬셋 audit + 개선 spec 입력)

1. **4축 표준 라벨 채택**: Invocation / Information Hierarchy / Steering / Pruning (병기: 트리거·구조·유도·가지치기). "유도"는 "Steering(유도)"로 병기.
2. **감사 체크리스트**(우리 28스킬 전수는 scope 밖·로드맵): 각 스킬에 대해 — Predictability(같은 과정) 명시? / model↔user 선택이 load 로 정당화? / context pointer wording 견고? / leading word 로 재작성 여지? / negation→positive? / no-op·sediment·duplication·sprawl 6종 진단? / SKILL.md <500줄·참조 1-depth?
3. **하네스 특이점 반영**: auto-activation 불안정(scottspence) → 우리 harness 의 hook-강제 라우팅(mem-recall-inject, workflow-guard-hook)은 정당한 대응. router-skill = 우리 autopilot-* 라우팅(CLAUDE.md §0)과 동형.
4. **오해 방지**: "CONTEXT.md 용어집"은 writing-great-skills 4원칙이 아니라 별도 공유언어 축(README #2 / grill-with-docs / domain-modeling). spec 에서 분리 서술.

> **상태**: analyze stage 완료. Phase A(skim)·Phase C(code) 활성 수행, Phase B(chaining) technology mode 비활성. 다음 = report generation(Step 4).
