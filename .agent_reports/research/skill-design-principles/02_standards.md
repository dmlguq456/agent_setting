# 02 · 정량 규범 / 컨벤션 인벤토리 — Skill Design Principles

> mode: technology · date: 2026-07-13
> 3GPP/IEEE 류 표준화 기구가 없는 주제이므로, 이 장은 표준 대신 **커뮤니티/공식 컨벤션 인벤토리**로 대체한다.

## 1. 정량 규범 표

| 규범 | 출처 | 값/기준 | 근거 |
|---|---|---|---|
| SKILL.md body 길이 | Anthropic best-practices | **< 500 lines** | *"Keep SKILL.md body under 500 lines."* — 트리거 시 body 통째 로드(Level 2) 되므로 상한 필요 |
| 참조 depth | Anthropic best-practices | **1-depth** (SKILL.md 기준 한 단계) | *"Keep references one level deep from SKILL.md."* 깊은 중첩 참조 금지 |
| description 인칭·형태 | Anthropic best-practices | **3인칭 + "Use when…" 트리거 형태** | *"Always write [description] in third person."* — Anthropic verbatim 은 "third person"·"Use when…"까지 지원(gerund 은 원문에 없음, 우리 컨벤션상 선호) |
| description 상주 비용 | Anthropic skills-overview (Level 1) | **~100 tokens/skill, always at startup** | name+description 만 상시 로드 → Pocock "context load" 정의와 일치 |
| SKILL.md body 로드 비용 | Anthropic skills-overview (Level 2) | **< 5k tokens, when triggered** | 트리거 시에만 로드 |
| Resources(Level 3+) | Anthropic skills-overview | **effectively unlimited, as needed** | 번들 파일은 bash 로 실행, 코드 자체는 context 미로드 |
| model-invoked 요건 | mattpocock frontmatter / Anthropic | description 에 **"Use when…" 트리거 필수** | code_search.md 카탈로그: model-invoked 는 "Use when…" 풍부 |
| user-invoked 지정 | mattpocock frontmatter / Anthropic | **`disable-model-invocation: true`** | zero context load, 사람만 호출 |
| token cost 정당화 테스트 | Anthropic best-practices | 문단마다 *"Does this paragraph justify its token cost?"* | no-op 테스트와 동형 |
| Evaluations-first | Anthropic best-practices | 문서 작성 전 **3 scenarios + baseline** | *"Create evaluations BEFORE writing extensive documentation."* |

**Takeaway**: 정량 규범의 SoT 는 Anthropic best-practices/skills-overview 이며, `<500줄 / 1-depth / 3인칭 + "Use when…"` 는 우리 28스킬 audit 에 즉시 적용 가능한 기계적 스캔 기준이다(gerund 형태는 우리 컨벤션 선호이지 Anthropic verbatim 규범은 아님).

## 2. Failure-Mode 진단 규범 표

canonical failure mode 는 **6종**(pocock-verbatim-comparison §3 기준: premature completion / duplication / sediment / sprawl / no-op / negation). GLOSSARY 는 각 failure 를 치료하는 lever 옆에 배치한다. **variance bug** 는 이 6종에 포함되지 않는 **Information Hierarchy 축의 별도 failure**(약한 context pointer 뒤의 must-have)로, 아래 표에서는 canonical 6종 뒤에 구분해 싣는다.

| mode | 소속 축 | canonical? | 진단 질문 | 치료 |
|---|---|---|---|---|
| **premature completion** | Steering | ✅ 6종 | 에이전트가 작업을 조기 종료하는가? | completion criterion 을 checkable+exhaustive 하게 + post-completion steps 숨기기(실제 context 경계에서만) |
| **negation** | Steering | ✅ 6종 | 금지("don't…")로 서술했는가? | 긍정 목표로 재작성 — *"don't think of an elephant"* 는 elephant 를 더 available 하게 함 |
| **sprawl** | Information Hierarchy | ✅ 6종 | 필요 없는 reference 가 인라인되어 본문이 비대한가? | progressive disclosure — 필요 branch 만 로드 |
| **duplication** | Pruning | ✅ 6종 | 같은 의미가 여러 곳에 있는가? | Single Source of Truth — 한 권위 자리로 통합 |
| **sediment** | Pruning | ✅ 6종 | 낡은·비활성 문장이 쌓였는가? | relevance 테스트 — 줄이 여전히 작업에 관여하나? |
| **no-op** | Pruning | ✅ 6종 | 모델이 기본으로 이미 하는가? | 문장 단위 no-op 테스트 → 실패 시 *"delete the whole sentence rather than trim words. Be aggressive."* |
| **variance bug** | Information Hierarchy | ⚠️ 별도(6종 외) | must-have 자료가 약한 pointer 뒤에 있는가? | context pointer wording 강화(*"wording, not target, decides reliability"*) |

**Takeaway**: canonical failure mode 는 **6종**이고 variance bug 는 IH 축의 별도 failure 로 분리 집계한다. 실무 audit 에서는 6종을 한 체크리스트로 묶어 문장 단위로 스캔하는 것이 효율적이다. (Remio 의 "5-test"는 premature completion/duplication/sediment/sprawl/no-op 로, negation 을 제외한 6종의 부분집합이다.)

## 3. Production vs 원문 권장 — 강제 수위

우리 harness(production) 에 적용할 때 어디까지 hard 강제할지의 판단.

| 규범 | 원문/Anthropic 권장 | 우리 harness 적용 수위(제안) |
|---|---|---|
| SKILL.md <500줄 | 권장 | **hard 스캔** (라우터 SKILL.md 는 이미 lean, 초과 시 references/ 분리) |
| 1-depth 참조 | 권장 | **hard 스캔** (autopilot-research 는 references/ 1-depth 준수) |
| description 3인칭 + "Use when…" | 권장 | **soft** (한국어 blurb 혼용 — 트리거 신뢰도 우선; gerund 은 우리 컨벤션 선호) |
| model-invoked "Use when…" | 필수(model-invoked 시) | **hook 보강 전제로 soft** — hook 워크어라운드 후에도 auto-activation ~50%(scottspence)이므로 wording 단독 신뢰 X |
| Evaluations-first | 강한 규범 | **N/A→drill 로 대체** — 우리는 drill 회귀 테스트가 eval 역할 |
| no-op/SoT/failure 6종 | 권장 | **audit 체크리스트로 정형화** (06_implementation Step 3) |

**Takeaway**: 정량 규범(줄 수·depth)은 hard 스캔으로 강제하되, description wording 규범은 wording 단독으로는 자동발화가 불안정(hook 후에도 ~50%, scottspence)하다는 근거에서 **hook 강제 라우팅으로 보강**하는 것이 합당한 방향이다 — wording 만 믿는 원문 권장을 그대로 hard 강제하지 않는다. 단 우리의 deterministic UserPromptSubmit 주입은 scottspence 의 조건부 키워드-hook 과 성격이 다를 수 있고, hook 이 신뢰도를 회복한다는 강한 주장은 측정 미검증이다.

## Cross-References

- auto-activation 불안정의 상세 근거 → [03_vendor_comparison.md](03_vendor_comparison.md) 상충 지점
- failure-mode 메커니즘(왜 성능에 영향) → [04_technical_deep_dive.md](04_technical_deep_dive.md)
- audit 체크리스트 단계화 → [06_implementation.md](06_implementation.md)
