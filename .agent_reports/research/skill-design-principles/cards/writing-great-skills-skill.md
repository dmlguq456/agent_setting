# writing-great-skills — SKILL.md (ANCHOR, full-read verbatim)

- **title**: writing-great-skills SKILL.md
- **author**: Matt Pocock
- **url**: https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md
- **date**: 2026 (repo main @ clone 2026-07-13)
- **type**: repo / SKILL.md (anchor 원문)
- **access**: full-read (git clone verbatim — `code_resources/writing-great-skills.SKILL.md`)
- **관련 축**: 원문대조 (primary anchor)

## Verbatim 핵심 인용 (직접 인용)

> "A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same _process_ every run, not producing the same output — is the root virtue; every lever below serves it."

> (Invocation) "A **model-invoked** skill keeps a **description** … It contributes to **context load** … A **user-invoked** skill strips the description … Zero context load, but it spends **cognitive load**: _you_ are the index that must remember it exists."

> (Information hierarchy) "1. **In-skill step** … 2. **In-skill reference** … 3. **External reference** — reference pushed out of `SKILL.md` into a separate file, reached by a **context pointer**, loaded only when the pointer fires."

> "**Progressive disclosure** is the move down the ladder — out of `SKILL.md` into a linked file — so the top stays legible."

> "A **context pointer**'s _wording_, not its target, decides when and how reliably the agent reaches the material."

> (Pruning) "hunt **no-ops** sentence by sentence, not just line by line: run the no-op test on each sentence in isolation, and when one fails, delete the whole sentence rather than trim words from it. Be aggressive."

> (Leading words) "A **leading word** is a compact concept already living in the model's pretraining … Repeated throughout the text … it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens."

> (Negation failure mode) "_don't think of an elephant_ names the elephant and makes it more available, not less. Prompt the **positive**."

## 핵심 주장 요약

- SKILL.md 실제 섹션 구조: **Invocation → Writing the description → Information hierarchy → When to split → Pruning → Leading words → Failure modes**. (사용자 요약의 4단어 라벨과 1:1 대응하지 않음 — 더 세분화·풍부.)
- 최상위 개념 = **Predictability**(같은 *과정*, 같은 *출력*이 아님). 나머지 모든 레버는 이걸 위한 것.
- 두 비용축: **context load**(model-invoked description 이 매 턴 상주) vs **cognitive load**(user-invoked 를 사람이 기억해야 함). 대부분의 설계 결정은 이 둘 중 하나를 쓰는 문제로 환원.
- Failure modes(진단용): premature completion / duplication / sediment / sprawl / no-op / negation.

## 우리 조사 축과의 관련성

원문대조의 **1차 기준점**. 사용자 4단계 체크리스트가 이 문서의 어느 부분을 축약/재명명했는지 판정하는 근거. `_internal/pocock-verbatim-comparison.md` 의 SoT.
