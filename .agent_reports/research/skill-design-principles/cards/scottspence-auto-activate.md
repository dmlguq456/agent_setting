# Scott Spence — Claude Code Skills Don't Auto-Activate (full-read)

- **title**: Claude Code Skills Don't Auto-Activate (a workaround)
- **author**: Scott Spence
- **url**: https://scottspence.com/posts/claude-code-skills-dont-auto-activate
- **date**: 2026
- **type**: blog (안티패턴/실무 caveat)
- **access**: full-read (WebFetch)
- **관련 축**: 생태계확장 + 하네스매핑 (반례/caveat)

## Verbatim 핵심 인용 (직접 인용)

> "Claude Code skills just sit there. You have to remember to use them." (community member)

> 문서상 model-invoked·"autonomously decides when to use them" 이지만 실제 동작과 불일치 — description 이 정확히 매칭돼도 무시되는 경우.

> 워크어라운드: UserPromptSubmit hook 으로 트리거 키워드 감지 → "INSTRUCTION: Use Skill(skill-name)" 강제 주입. 그래도 신뢰도 ~50%. 저자 권고: 중요 작업은 명시적 `Skill(skill-name)` 수동 호출.

## 핵심 주장 요약

- **중요 반례**: model-invoked 자동발화는 이론만큼 신뢰성 있지 않다. description trigger 를 잘 써도 실전 auto-activation 은 불안정.
- 실무 대응 = hook 기반 강제 주입 + 명시적 호출. → 우리 harness 가 이미 `mem-recall-inject`·`workflow-guard-hook` 등 hook 로 스킬 라우팅을 강제하는 설계와 정확히 같은 문제의식.
- Pocock 의 "context pointer wording 이 신뢰도를 결정" 주장에 대한 실전 압박: wording 만으론 부족, hook 보강 필요.

## 우리 조사 축과의 관련성

생태계확장(auto-activation 신뢰도 한계). 하네스매핑: 우리 harness 의 hook-강제 라우팅이 이 취약점의 정당한 대응임을 뒷받침 — "description 만 믿지 말고 hook 로 강제" 근거.
