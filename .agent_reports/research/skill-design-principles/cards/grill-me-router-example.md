# mattpocock/skills — grill-me + ask-matt (Invocation·router 예시, full-read verbatim)

- **title**: grill-me/SKILL.md, ask-matt/SKILL.md (code exemplars)
- **author**: Matt Pocock
- **url**: https://github.com/mattpocock/skills/tree/main/skills
- **date**: 2026
- **type**: repo / SKILL.md (예시)
- **access**: full-read (`code_resources/grill-me.SKILL.md`, `code_resources/ask-matt.SKILL.md`)
- **관련 축**: 원문대조 (Invocation 축 구현 예시) — Phase C

## Verbatim 핵심 인용 (직접 인용)

grill-me 전문(4줄):
> `disable-model-invocation: true` / description: "A relentless interview to sharpen a plan or design." / 본문: "Run a `/grilling` session."

ask-matt frontmatter:
> `disable-model-invocation: true` / description: "Ask which skill or flow fits your situation. A router over the skills in this repo."

## 핵심 주장 요약

- **grill-me = user-invoked + delegation 패턴**: 짧은 human-facing description(트리거 리스트 없음), 본문은 model-invoked `grilling` 을 호출만. 재사용 규율(reusable discipline)은 `grilling`(model-invoked)에 두고, `grill-me`는 1줄 포인터 → **single source of truth** 실천.
- **ask-matt = router skill**: cognitive load(사용자가 스킬들을 다 기억)를 하나의 user-invoked 라우터로 흡수. GLOSSARY 의 "router skill" 정의의 실물.
- 대비 근거(frontmatter 카탈로그): user-invoked 다수(`disable-model-invocation: true` + 짧은 설명) vs model-invoked(tdd/prototype/code-review 등, "Use when…" 트리거 풍부).

## 우리 조사 축과의 관련성

Invocation 축(user vs model)과 router 개념의 canonical 예시. 하네스매핑: 우리 autopilot-* 라우팅(CLAUDE.md §0)이 사실상 router-skill 역할 — Pocock 의 cognitive-load 흡수 논리와 대응.
