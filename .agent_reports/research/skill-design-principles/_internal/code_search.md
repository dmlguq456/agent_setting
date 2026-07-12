# Phase C — Code & Model Search (technology mode)

> mattpocock/skills repo 자체가 사실상 code resource. 2026-07-13 `gh repo clone mattpocock/skills` (depth 1, main) → `/tmp/mp-skills`. 원칙을 잘 보여주는 SKILL.md 예시를 `{artifact_dir}/code_resources/` 에 verbatim 보존.

## 수집한 code resources

| 파일(code_resources/) | 원경로 | 예시하는 원칙 |
|---|---|---|
| `writing-great-skills.SKILL.md` | skills/productivity/writing-great-skills/SKILL.md | anchor — 4축 전부, all-reference 스킬 |
| `writing-great-skills.GLOSSARY.md` | 〃/GLOSSARY.md | 4-axis 정의 SoT, `_Avoid_` 로 leading-word 규율 자기적용 |
| `tdd.SKILL.md` | skills/engineering/tdd/SKILL.md | **Steering**(leading words: seam·red→green·vertical slice·tracer bullet), all-reference, 1-depth disclosure(tests.md·mocking.md) |
| `ask-matt.SKILL.md` | skills/engineering/ask-matt/SKILL.md | **Invocation**: router skill(user-invoked), cognitive-load 흡수 |
| `grill-me.SKILL.md` | skills/productivity/grill-me/SKILL.md | **Invocation**: user-invoked + model-invoked(`grilling`) 위임, single-source-of-truth |
| `prototype.SKILL.md` | skills/engineering/prototype/SKILL.md | **Invocation**: model-invoked 전환 예시(리치 "Use when…" 트리거, leading word _prototype_) |
| `code-review.SKILL.md` | skills/engineering/code-review/SKILL.md | **Information Hierarchy**: 2-axis(Standards/Spec) 병렬 sub-agent, Fowler smell 인라인 baseline |
| `repo-README.md` | README.md | Invocation 이분법 조직축, 4대 실패모드, CONTEXT.md 공유언어 |
| `repo-CONTEXT.md` | CONTEXT.md | 공유언어(ubiquitous language) 실물 — Issue tracker/Issue/Triage role + `_Avoid_` |

## Invocation 축 — frontmatter 카탈로그 (repo 전수, 원칙의 정량 증거)

`disable-model-invocation: true` = **user-invoked**(오케스트레이션·짧은 human-facing 설명), 없으면 **model-invoked**(재사용 규율·"Use when…" 트리거 풍부).

**User-invoked** (disable-model-invocation: true): ask-matt, grill-with-docs, implement, improve-codebase-architecture, setup-matt-pocock-skills, to-spec, to-tickets, triage, wayfinder, grill-me, handoff, teach, writing-great-skills, (deprecated) ubiquitous-language, (in-progress) claude-handoff·loop-me·setup-ts-deep-modules·wizard·writing-*.

**Model-invoked** (description 에 "Use when…" 트리거): codebase-design, code-review, diagnosing-bugs, domain-modeling, prototype, research, tdd, grilling, (misc) git-guardrails·migrate-to-shoehorn·scaffold-exercises.

**관찰**: user-invoked 가 수적으로 우세 → README 진술 *"cognitive load is the pressure the whole system is built to manage"* 와 정합. 오케스트레이터(user-invoked)가 규율(model-invoked)을 호출하는 단방향(user→model, user↛user) 구조가 frontmatter 로 확인됨.

## Leading-word 실물 사례 (grep 소견)

- tdd: `seam`, `red → green`, `vertical slice`, `tracer bullet`
- wayfinder: `fog of war`, `frontier`, `the map`, `destination`
- prototype: `prototype`(throwaway code answering a design question)
- code-review: `Standards` / `Spec` 2축, Fowler `smell`
- 각 leading word 는 pretrained prior 소환 → 최소 토큰으로 행동 앵커(GLOSSARY §Leading Word).

## Anthropic 공식 오픈소스 스킬 (참고)

- github.com/anthropics/skills (pptx/xlsx/docx/pdf + claude-api). progressive disclosure·utility-script 실행 패턴의 1급 레퍼런스. (본 조사 범위에선 mattpocock repo 우선, 필요 시 downstream 확장.)

## 재현 명령

```bash
gh repo clone mattpocock/skills /tmp/mp-skills -- --depth 1
find /tmp/mp-skills/skills -name SKILL.md          # 전체 스킬 목록
# frontmatter invocation 카탈로그:
for f in $(find /tmp/mp-skills/skills -name SKILL.md); do \
  awk '/^---/{c++;next} c==1' "$f" | grep -E '^(name|disable-model-invocation):'; done
```
