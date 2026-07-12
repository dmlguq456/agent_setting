# 원문 대조 — 사용자 4단계 요약 vs Matt Pocock 원문

> **SoT**: `mattpocock/skills@main` 의 `skills/productivity/writing-great-skills/SKILL.md` + `GLOSSARY.md` (2026-07-13 git clone verbatim, `code_resources/` 보존). 커뮤니티 계보: StartupHub "Missing Manual", Remio 해설.

## 0. 결론 한 줄

사용자의 4단계(트리거/구조/유도/가지치기)는 **틀리지 않았고**, 커뮤니티 해설(StartupHub)의 4원칙 **Trigger / Structure / Steering / Pruning** 를 국문화한 것이다. 다만 (1) 3번째 축의 canonical 용어는 **"Steering"**(사용자의 "유도/Guidance"는 정확한 번역이나 원어 라벨 아님), (2) 원문 GLOSSARY 는 이 4개를 **명시적 4-axis**(Invocation / Information Hierarchy / Steering / Pruning)로 정의하며, (3) 사용자 요약엔 없는 상위 개념 **Predictability**·두 비용축(**context load / cognitive load**)·다수 하위 레버가 존재한다.

## 1. 4축 나란히 놓기

| # | 사용자 국문 요약 | 커뮤니티(StartupHub) | **원문 GLOSSARY 축(canonical)** | 판정 |
|---|---|---|---|---|
| 1 | 트리거(Trigger) — 사용자 호출 vs 모델 호출 | Trigger — "How the skill is invoked" | **Invocation** (Model-Invoked / User-Invoked) | ✅ 개념 일치, 원어 라벨은 **Invocation** (Trigger 는 커뮤니티 별칭). 원문에서 "trigger"는 description 안의 발화어를 가리키는 하위어. |
| 2 | 구조(Structure) — 절차 외 설명 배제 + 참고자료 별도 파일(2계층) | Structure — "internal organization" | **Information Hierarchy** (step / in-file reference / external reference behind context pointer) + Progressive Disclosure + Co-location | ⚠️ 부분. "2계층"이 아니라 **3-rung 사다리**. "절차 외 설명 배제"는 실제로 **Pruning**(no-op) 소관인데 사용자가 Structure 로 묶음. |
| 3 | 유도(Guidance) — 강력한 기존 용어로 즉각 행동 유도 + 단계별 미래 숨기기 | **Steering** — "how the skill is guided to perform specific actions" | **Steering** (Leading Word / Completion Criterion / Post-Completion Steps 숨기기 / Premature Completion / Negation) | ✅ **핵심 확인**: canonical = **Steering**. "유도(Guidance)"는 Steering 의 뜻풀이("guided to…")를 옮긴 것으로 의미는 맞음. 하위 레버는 사용자 요약보다 풍부. |
| 4 | 가지치기(Pruning) — 무동작 문장 삭제 테스트 | Pruning — "removing unnecessary/outdated elements" | **Pruning** (Single Source of Truth / Relevance / No-Op) + failure modes(Duplication/Sediment/Sprawl) | ✅ 라벨·개념 일치. "무동작 문장 삭제"는 4개 하위 중 **No-Op 테스트** 1개를 대표로 라벨화. |

## 2. Guidance ↔ Steering 확정 (search stage 가설 검증)

- **가설**(search stage): "Guidance 가 아니라 Steering 일 가능성" → **확정 CONFIRMED**.
- 근거 1(원문, GLOSSARY line 5, 직접 인용): *"The terms are grouped by axis: Invocation …, Information Hierarchy …, **Steering** (how the agent's runtime behaviour is shaped), and Pruning …"*
- 근거 2(원문, CHANGELOG PR #463): *"Add two adjacent **Steering** failure modes to writing-great-skills"* — Negation·Negative Space 를 "Steering failure modes"로 분류. → "Steering"은 repo 의 1급 도메인 용어.
- 근거 3(커뮤니티, StartupHub 직접 인용): 4원칙 3번을 *"Steering: How the skill is guided to perform specific actions"* 로 명명.
- 즉 사용자의 "유도(Guidance)"는 **의미상 정확**(Steering 정의가 "guided")하나, 문헌 표준 라벨은 **Steering**. 다운스트림 문서는 "Steering(유도)"로 병기 권장.

## 3. 원문에만 있고 사용자 요약엔 없는 뉘앙스

| 뉘앙스 | 원문 위치·직접 인용 | 사용자 요약 반영 여부 |
|---|---|---|
| **Predictability = 최상위 root virtue** | SKILL.md: *"Predictability — the agent taking the same _process_ every run, not producing the same output — is the root virtue; every lever below serves it."* | ❌ 누락. 4축이 *무엇을 위한* 것인지의 상위 목적. |
| **두 비용축: context load vs cognitive load** | GLOSSARY: model-invoked=*"permanent context load on every turn"*; user-invoked=*"you are the index"*(cognitive load). | △ 트리거 "사용자 vs 모델"로 *메커니즘*만 반영, *왜*(load trade-off)는 누락. |
| **3-rung 정보 사다리 + context pointer wording** | SKILL.md: step / in-file reference / external reference; *"A context pointer's wording, not its target, decides when and how reliably the agent reaches the material."* | △ "2계층"으로 축약. pointer wording=신뢰도 결정 누락. |
| **"위층/아래층 분리" = progressive disclosure** | SKILL.md: *"Progressive disclosure is the move down the ladder — out of SKILL.md into a linked file — so the top stays legible."* | ✅ "참고자료 별도 파일 분리"로 반영됨(축약). |
| **"단계별 미래 숨기기"의 정확한 기제** | GLOSSARY(Post-Completion Steps): *"Visible, they pull the agent forward into premature completion … hide them by splitting the sequence of steps into two."* | ✅ 반영("단계별 미래 숨기기"), 단 이것이 **premature completion 방어**임은 누락. + 선행 방어는 *completion criterion 날카롭게*(우선), 숨기기는 차선. |
| **"더 적게 적고 더 강력하게 유도" = Leading Word 이득** | SKILL.md: *"You win twice over: fewer tokens, and a sharper hook for the agent to hang its thinking on."* / GLOSSARY: *"encodes a behavioural principle in the fewest possible tokens by invoking priors the model already holds."* | ✅ "강력한 기존 용어로 즉각 행동 유도"로 반영. 원문의 트윈-이득(토큰↓ + 앵커↑) 명시가 근거. |
| **CONTEXT.md 용어집(shared language)** | **출처는 writing-great-skills 4원칙이 아니라 README #2 verbosity 대응** + grill-with-docs/domain-modeling 스킬. 예: *"materialization cascade"*. | ⚠️ 사용자가 이를 4원칙 안으로 오해할 위험. 별개 축(공유언어)임을 명시 필요. |
| **Negation(부정 대신 긍정)** | GLOSSARY: *"don't think of an elephant … Prompt the positive."* | ❌ 누락. Steering 축의 실전 규율. |
| **Failure modes 진단표** | premature completion / duplication / sediment / sprawl / no-op / negation | △ 사용자는 no-op(무동작) 하나만 언급. |
| **Degrees of freedom**(Anthropic) | best-practices: narrow-bridge vs open-field. | ❌ 사용자·Pocock 원문 모두 없음 — 생태계 보강 개념. |

## 4. 사용자 요약의 미세 부정확 (교정 포인트)

1. **"구조: 절차 외 설명 배제"** → "설명 배제"는 Structure 가 아니라 **Pruning(no-op/relevance)** 축. Structure(Information Hierarchy)는 *배치·계층*이 본질이지 *삭제*가 아님.
2. **"2계층"** → 실제 **3-rung**(in-skill step → in-skill reference → external reference). "2계층"은 SKILL.md/참조파일 이분만 포착.
3. **"유도(Guidance)"** → canonical **Steering**. 병기 권장.
4. **트리거를 "호출 방식"으로만** → 원문은 그 선택이 **어떤 load 를 지불하느냐**(context vs cognitive)의 경제 문제로 프레이밍. 이게 split/inline/invocation 결정 전체를 관통.

## 5. 다운스트림(스킬셋 audit+개선 spec) 반영 지침

- 4축 라벨은 **Invocation / Information Hierarchy / Steering / Pruning** 로 표준화(사용자 친화 병기: 트리거·구조·유도·가지치기).
- 감사 기준에 원문 누락분 추가: Predictability(같은 과정) 목표, context/cognitive load 정당화, context pointer wording 점검, leading-word 재작성 여지, negation→positive, failure-mode 6종 진단.
- Anthropic 정량 규범 접목: SKILL.md <500줄, 참조 1-depth, description 3인칭 "Use when…", eval-first.
