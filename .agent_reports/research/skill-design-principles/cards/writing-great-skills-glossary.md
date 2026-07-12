# writing-great-skills — GLOSSARY.md (ANCHOR, 4-axis SoT, full-read verbatim)

- **title**: Glossary — Building Great Skills
- **author**: Matt Pocock
- **url**: https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/GLOSSARY.md
- **date**: 2026 (repo main @ 2026-07-13)
- **type**: repo / disclosed reference file
- **access**: full-read (git clone verbatim — `code_resources/writing-great-skills.GLOSSARY.md`)
- **관련 축**: 원문대조 (★ 4-axis 정의의 단일 출처)

## Verbatim 핵심 인용 (직접 인용)

> "The terms are grouped by axis: **Invocation** (how a skill is reached), **Information Hierarchy** (how its content is arranged), **Steering** (how the agent's runtime behaviour is shaped), and **Pruning** (how it is kept lean). Each **failure mode** lives beside the lever that cures it, tagged _failure mode_."

> (Predictability) "The degree to which a skill makes the agent behave the same _way_ on every run — the same process, not the same output … The root virtue every other term serves — cost and maintainability are symptoms of it, not rivals."

> (Steering axis 소속 용어) Branch · **Leading Word** · **Completion Criterion** · **Legwork** · **Post-Completion Steps** · **Premature Completion** · **Negation**.

> (Leading Word) "a compact concept — also called a _Leitwort_ — already living in the model's pretraining … Coining your own works if you define it clearly, but a made-up word recruits no priors — you pay in definition tokens what a pretrained word gives free."

> (Post-Completion Steps) "Visible, they pull the agent forward into **premature completion** … the defence is to hide them by splitting the sequence of steps into two."

> (Context Pointer) "Its wording, not the target, decides _when_ the agent reaches — and _how reliably_. A must-have target behind a weakly worded pointer is a variance bug."

## 핵심 주장 요약

- **★ 결정적 발견**: 원문의 네 축은 명시적으로 **Invocation / Information Hierarchy / Steering / Pruning**. 사용자 요약의 "유도(Guidance)"에 대응하는 canonical 용어는 **Steering** 이다.
- "Steering" 축이 커버하는 것 = leading word(강력한 기존 용어), completion criterion(checkable+exhaustive), post-completion steps 숨기기(=단계별 미래 숨기기), premature completion, negation(부정 대신 긍정 지시).
- 각 축에 failure mode 가 붙어 있음(치료제 옆에 배치): Steering→premature completion·negation, Information Hierarchy→sprawl, Pruning→duplication·sediment·no-op.
- 용어마다 `_Avoid_:` 리스트로 금지 동의어 지정 — leading word 규율 자체를 스킬에 적용한 메타 사례.

## 우리 조사 축과의 관련성

원문대조의 **4축 골격 확정 근거**. Guidance↔Steering 논쟁을 종결짓는 문서. 하네스 매핑 단계에서 우리 28개 스킬을 이 4축으로 감사할 때의 축 정의로 사용.
