# mattpocock/skills — README (Skills For Real Engineers, full-read verbatim)

- **title**: Skills For Real Engineers (repo README)
- **author**: Matt Pocock
- **url**: https://github.com/mattpocock/skills
- **date**: 2026 (repo main @ 2026-07-13)
- **type**: repo README
- **access**: full-read (`code_resources/repo-README.md`)
- **관련 축**: 원문대조 + 생태계확장

## Verbatim 핵심 인용 (직접 인용)

> "My agent skills that I use every day to do real engineering - not vibe coding."

> "Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve. These skills are designed to be small, easy to adapt, and composable."

> (#2 verbosity fix — CONTEXT.md 용어집 근거) "The Fix for this is a shared language. It's a document that helps agents decode the jargon used in the project." — 예시: **BEFORE** "a lesson inside a section of a course is made 'real'" → **AFTER** "the materialization cascade".

> (Reference 축) "**User-invoked** skills are reachable only when you type them … their job is to orchestrate. **Model-invoked** skills can be invoked by you _or_ reached for automatically … they hold the reusable discipline. A user-invoked skill may invoke model-invoked skills, but never another user-invoked one."

## 핵심 주장 요약

- 4대 실패모드 대응: (#1 misalignment→grill-me/grill-with-docs) (#2 verbosity→CONTEXT.md 공유언어) (#3 broken code→tdd red-green + diagnosing-bugs) (#4 ball of mud→improve-codebase-architecture).
- **"CONTEXT.md 용어집"의 출처는 여기(#2)** — writing-great-skills 의 4원칙이 아니라 별도 `grill-with-docs`/`domain-modeling` 스킬 소관. (사용자 요약이 두 개념을 섞을 위험 지점.)
- Invocation 이분법(user vs model)이 repo 전체를 가르는 실제 조직 축.

## 우리 조사 축과의 관련성

원문대조에서 "CONTEXT.md 용어집" 뉘앙스의 정확한 출처 확정. 생태계확장에서 "process 를 소유하는 프레임워크(GSD/BMAD/Spec-Kit) 대 작고 조합가능한 스킬" 대비 = 우리 autopilot 파이프 설계철학과의 비교점.
