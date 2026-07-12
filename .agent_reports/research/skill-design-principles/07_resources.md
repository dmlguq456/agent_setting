# 07 · 소스 · 레퍼런스 리소스 — Skill Design Principles

> mode: technology · date: 2026-07-13
> Tier 기반 리소스 인벤토리. Tier 1 = 직접 사용(1차 SoT) / Tier 2 = 참조(교차검증·보강) / Tier 3 = 보조(맥락).

## Tier 1 — 직접 사용 (1차 SoT)

| 리소스 | 저자 | url | 예시하는 원칙 | notes | Quick verify command |
|---|---|---|---|---|---|
| writing-great-skills SKILL.md | Matt Pocock | github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md | anchor — 4축 전부, Predictability | full-read verbatim, all-reference 스킬 | `gh repo clone mattpocock/skills /tmp/mp-skills -- --depth 1 && find /tmp/mp-skills/skills -name SKILL.md` |
| writing-great-skills GLOSSARY.md | Matt Pocock | 〃/GLOSSARY.md | ★4-axis 정의 SoT, `_Avoid_` 자기적용 | full-read verbatim, Guidance↔Steering 확정 근거 | `cat /tmp/mp-skills/skills/productivity/writing-great-skills/GLOSSARY.md` |
| tdd SKILL.md | Matt Pocock | 〃/skills/engineering/tdd/SKILL.md | Steering(leading words), IH(all-reference+1-depth), Pruning(SoT) | seam·red→green·vertical slice·tracer bullet | `cat /tmp/mp-skills/skills/engineering/tdd/SKILL.md` |
| ask-matt SKILL.md | Matt Pocock | 〃/skills/engineering/ask-matt/SKILL.md | Invocation: router skill(user-invoked) | cognitive-load 흡수 | `cat /tmp/mp-skills/skills/engineering/ask-matt/SKILL.md` |
| grill-me SKILL.md | Matt Pocock | 〃/skills/productivity/grill-me/SKILL.md | Invocation: user→model 위임, SoT | 4줄 전문, grilling 위임 | `cat /tmp/mp-skills/skills/productivity/grill-me/SKILL.md` |
| prototype / code-review SKILL.md | Matt Pocock | 〃/skills/engineering/{prototype,code-review}/SKILL.md | Invocation(model 전환) / IH(2축 병렬 sub-agent) | leading word _prototype_, Fowler smell | `find /tmp/mp-skills -path '*engineering*' -name SKILL.md` |
| Anthropic skill authoring best-practices | Anthropic | platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | 정량 규범(500줄·1-depth·3인칭 "Use when…"), degrees-of-freedom, eval-first | context window=public good | WebFetch (인증 불필요) |
| Anthropic context-engineering | Anthropic | anthropic.com/engineering/effective-context-engineering-for-ai-agents | 메커니즘 근거(attention budget, context rot) | pruning/disclosure 의 "왜" | WebFetch |

**Takeaway**: Tier 1 의 앵커는 `mattpocock/skills` repo(git clone 으로 verbatim 재현 가능) + Anthropic 공식 2문서이며, 개념 정의는 GLOSSARY, 정량·메커니즘은 Anthropic 이 SoT 다.

## Tier 2 — 참조 (교차검증 · 보강)

| 리소스 | 저자 | url | 예시하는 원칙 | notes | Quick verify command |
|---|---|---|---|---|---|
| Agent Skills overview | Anthropic | platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | 3-level progressive disclosure(~100토큰/5k/unlimited) | Level 정의 SoT | WebFetch |
| Equipping agents (blog) | Anthropic | anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | progressive disclosure=core, Skills vs MCP | 벤더 공식 위상 | WebFetch |
| repo README | Matt Pocock | github.com/mattpocock/skills | Invocation 이분, 4대 failure mode, CONTEXT.md 공유언어 | GSD/BMAD/Spec-Kit 대비 | `cat /tmp/mp-skills/README.md` |
| StartupHub "Missing Manual" | StartupHub.ai | startuphub.ai/…/building-better-ai-agent-skills-the-missing-manual | 4원칙 국문화 계보(Trigger/Structure/Steering/Pruning) | 사용자 요약의 브리지 | WebFetch |
| Remio writing-great-skills | Remio.ai | remio.ai/post/matt-pocock-shares-writing-great-skills-guide-for-predictable-ai-agents | Pruning 5-test, description=trigger | no-op 특정 근거 | WebFetch |
| scottspence auto-activate | Scott Spence | scottspence.com/posts/claude-code-skills-dont-auto-activate | ★auto-activation 반례 — hook 워크어라운드 후에도 ~50% + hook 우회책 | hook 강제의 합당성 근거(신뢰도 이득 미검증) | WebFetch |
| Sourcegraph context-engineering | Sourcegraph | sourcegraph.com/blog/context-engineering | attention budget 벤더중립 재확인, lost-in-the-middle | pruning 근거 보강 | WebFetch |

**Takeaway**: Tier 2 는 Tier 1 을 교차검증(Anthropic overview/blog·Sourcegraph)하거나 실전 caveat(scottspence)·계보(StartupHub)를 보강하며, 특히 scottspence 는 우리 hook 설계의 핵심 근거다.

## Tier 3 — 보조 (맥락)

| 리소스 | 저자 | url | notes |
|---|---|---|---|
| generativeprogrammer patterns | Generative Programmer | generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics | degrees-of-freedom·eval-first 실전 패턴, 신규 개념 없음 |
| KISDigital effective skills | KISDigital | kisdigital.com/posts/2026/04/writing-effective-claude-skills | Invocation 실무 팁, auto-activation 정합 |
| Claude Code skills docs | Anthropic | code.claude.com/docs/en/skills | model/user invocation 공식 문서 |
| talksintel Pocock talk | Matt Pocock | talksintel.ai/…/full-walkthrough-workflow-for-ai-coding-matt-pocock | AIE EU 2026 워크스루, transcript 미확보 |
| Hatchworks / ExplainX / DeepWiki / DJClaw / aihero | 각 | (search_results.json) | 맥락·해설, 1차 아님 |

**Takeaway**: Tier 3 는 신규 개념 없이 Tier 1-2 를 재정리·해설하며, transcript 미확보 소스(talksintel)는 downstream 확장 시 추출 후보다.

## Reproducibility / 접근성 Matrix

| 소스 | full-read/abstract | 접근 방식 | 신뢰도 |
|---|---|---|---|
| mattpocock/skills repo (SKILL/GLOSSARY/tdd/…) | full-read | `gh repo clone` (verbatim) | ★★★ 1차 소스, git 재현 |
| Anthropic best-practices/context-eng/overview/blog | full-read | WebFetch (공개, 인증 불필요) | ★★★ 공식 문서 |
| StartupHub / Remio / scottspence / Sourcegraph | full-read | WebFetch | ★★ 커뮤니티, 인용 명시 |
| generativeprogrammer / KISDigital | abstract | WebFetch | ★★ 해설, 1차 아님 |
| talksintel (talk) | abstract | WebFetch (transcript 미확보) | ★ metadata only |

**Takeaway**: 1차 소스(mattpocock repo)는 `gh repo clone` 으로 완전 재현 가능하고 Anthropic 공식 문서는 WebFetch 로 접근 가능해, 본 보고서의 핵심 주장은 모두 재현 가능한 소스에 근거한다.

## 재현 명령 (code_search.md 재사용)

```bash
gh repo clone mattpocock/skills /tmp/mp-skills -- --depth 1
find /tmp/mp-skills/skills -name SKILL.md          # 전체 스킬 목록
# frontmatter invocation 카탈로그:
for f in $(find /tmp/mp-skills/skills -name SKILL.md); do \
  awk '/^---/{c++;next} c==1' "$f" | grep -E '^(name|disable-model-invocation):'; done
```

## Cross-References

- 소스별 관점 비교 → [03_vendor_comparison.md](03_vendor_comparison.md)
- 개념×소스 matrix → [01_landscape.md](01_landscape.md)
