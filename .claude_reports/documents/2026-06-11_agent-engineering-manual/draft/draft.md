---
changelog:
  - version: v3
    date: "2026-06-11T18:30"
    by: autopilot-refine (quick)
    applied: 3
    overridden: 0
    entries:
      - |
        [FACT §4.2 verified autopilot-note/SKILL.md]: secondary_card_ids 보조 카드 복수 제안 (prd v32) 한 문장 추가 — 흐름 2번.
      - |
        [FACT §4.2 verified autopilot-note/SKILL.md Stage D]: backbone manifest 유지 (prd v33 — 빈 본문+노트 3건↑ 초안 자동, confirmed 직접 수정 금지, 계보 사용자 확정) 문단 추가.
      - |
        [FACT §4.2 verified autopilot-note/SKILL.md Stage D.5]: 편집팀 polish batch (light=매일 cron 기본, frontmatter·링크·수치 불변) 문장 추가 — 2.2 P3 cross-ref.
  - version: v2
    date: 2026-06-11
    by: autopilot-refine (doc)
    notes: |
      review memo 8건 반영 (applied 8 / overridden 0).
      [§1.5 verified research/05_deployment.md §1]: 안전장치 4층(permission→classifier→sandbox→hook) 합성 단락 + F3 embed 추가 — 다리 절의 자율성-안전 논거 해소.
      [§3.2 verified ~/.claude/CLAUDE.md §0(B)]: 4트랙별 대표 발화 예시 추가 (lookup 답 확보).
      [§3.5/3.7/3.9 verified plans/·drill/cases/·notes/study/]: 각 절 끝 기대 산출물 위치 한 줄 추가.
      [§2.4/§3.6 verified ~/.claude/loops/oncall.md]: "당직 7호" → "당직(oncall) 항목 8" 교정 (2곳) — oncall.md 디스패치 감시는 항목 8.
      [§1.0 verified cards/osmani-context-engineering.md]: "Karpathy 의 한 줄" → 카드 "One analysis quipped:" 표현에 맞춰 귀속 완화.
      [§1.3 verified cards/anthropic-c-compiler-parallel-claudes.md]: C compiler "Rust 기반" 한 단어 보강.
      [§1.2/§1.4-T4 verified cards/arxiv-code-as-agent-harness.md·arxiv-evaluating-agents-md.md·loops/metrics.csv]: 학술 def verbatim·+20% 수치·g0 39566≈40k 전부 라이브 대조 일치 — memo만 제거.
  - version: v1
    date: 2026-06-11
    by: autopilot-draft (doc pipeline)
    notes: initial draft from autopilot-draft doc pipeline (strategy v2 §4 Section Plan 기반).
---

# 에이전트 엔지니어링 매뉴얼 — `~/.claude/` 세팅의 자기 문서화

> 이 문서는 `~/.claude/` 에이전트 시스템의 README 확장판이다. 업계의 에이전트 엔지니어링 원칙(prompt → context → harness → loop 세대 + 실무 패턴 11종)을 망라하고(1부), 그 원칙들이 우리 세팅 어디에 어떻게 녹아 있나를 라이브 파일 anchor 로 매핑하며(2부), 발화 중심 실전 가이드(3부)와 worklog-board 에이전틱 노트 활용(4부)까지 잇는다.
>
> 위상은 세팅 자체의 자기 문서화 — 외부 독자를 위한 홍보물이 아니라 찾아보는 참조서다. 독자는 시스템 설계자 본인이며, 절 단위 독립성과 표 anchor 로 lookup 을 최적화했다.
>
> **인용 규칙**: 1부의 외부 원칙 주장은 research card `[card-slug]` 로 귀속한다 (단일 출처 = `research/agent-engineering-principles/cards/`). 2~4부의 우리 세팅 주장은 `파일경로 §절번호` anchor 로 귀속하며, 이 anchor 들은 작성 시점(2026-06-11)의 라이브 파일 스냅샷이다 — 파일이 바뀌면 anchor 로 추적해 재확인할 것.

---

# 1부 — 원칙의 세대사 (업계 망라)

## 1.0 들어가며 — 왜 세대사인가

에이전트 엔지니어링은 2024년 말부터 2026년 중반까지 약 18개월 사이에 네 번 이름을 바꿔 달았다 — prompt engineering → context engineering → harness engineering → loop engineering. 매뉴얼이 이 세대사를 1부의 골격으로 삼는 이유는, 우리 세팅의 거의 모든 구성 요소가 이 네 세대 중 하나에서 파생한 패턴의 구현이기 때문이다.

핵심 프레임은 단 하나다 — **세대는 대체가 아니라 누적 layer 다.** loop 는 harness 위에서 돌고, harness 는 context 를 관리하며, context 는 prompt 를 감싼다 (loop ⊃ harness ⊃ context ⊃ prompt). 각 세대는 이전 세대를 폐기하지 않고, 이전 세대가 풀지 못한 미해결분을 다음 세대가 흡수하는 식으로 쌓인다 `[osmani-loop-engineering]` `[greyling-loop-engineering]`. Osmani 가 인용한 한 줄("One analysis quipped:")이 이 누적성을 압축한다 — "Prompt engineering walked so context engineering could run" `[osmani-context-engineering]` (카드는 Karpathy 풍 quip 으로 표기하나 원문은 출처를 한 분석으로만 돌려, 직접 발언 귀속은 단정하지 않는다).

<img src="../assets/figures/f1_generations_timeline.png" width="500">

**그림 1**: prompt → context → harness → loop — 각 세대는 이전 세대의 미해결분을 흡수하며 누적 layer 로 쌓인다 (loop ⊃ harness ⊃ context ⊃ prompt).

세대사를 관통하는 정초 텍스트는 둘이다. Anthropic 의 "Building effective agents" (2024-12) 는 workflow 와 agent 를 구분하고 6개 조합 패턴을 제시해 후속 모든 실무 패턴의 어원이 됐다 — harness 세대의 정초다 `[anthropic-building-effective-agents]`. HumanLayer 의 "12-Factor Agents" 는 "agents... are comprised of mostly just software" 라는 software-discipline 측 manifesto 로, harness·loop 세대의 소프트웨어 규율 관점을 대표한다 `[humanlayer-12-factor-agents]`.

## 1.1 Gen0 → Gen1: prompt → context engineering

이 절은 첫 세대 전환을 다룬다 — 단일 prompt 최적화(Gen0)에서 정보 환경 전체를 설계하는 context engineering(Gen1)으로의 이동.

**Gen0 — prompt engineering** (배경 세대, ~2023–2024). 단일 prompt 의 phrasing 을 최적화하는 작업, "cleverly phrasing a question" `[osmani-context-engineering]`. 한계가 다음 세대의 동력이 됐다 — demo 용 one-off prompt 로는 production 신뢰성을 못 낸다: "a witty one-off prompt might have wowed us in demos, but building reliable, industrial-strength LLM systems demanded something more comprehensive" `[osmani-context-engineering]`. prompt engineering 은 정초 텍스트 없이 회고적으로 명명된 세대다.

**Gen1 — context engineering** (2025). canonical 정의는 "the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference" `[anthropic-effective-context-engineering]`. Addy Osmani 판은 "constructing an entire information environment so the AI can solve the problem reliably" `[osmani-context-engineering]`. **명명 권위는 Anthropic + Addy Osmani 공동**이다 — Anthropic 의 "Effective context engineering for AI agents" (2025-09) 가 prompt → context 세대 전환을 직접 선언했고, Osmani 의 "Context Engineering: Bringing Engineering Discipline to Prompts" (2025-07) 가 동시 canonical 이다.

등장 배경은 agent 가 multi-turn·long-horizon 으로 확장하면서 단일 prompt 최적화로는 부족해진 데 있다. context window 라는 유한 자원을 loop 전체에 걸쳐 관리해야 한다는 문제의식에서 네 핵심 개념이 나왔다 `[anthropic-effective-context-engineering]`:

- **context rot** — token 이 늘수록 recall 이 저하된다 ("this characteristic emerges across all models").
- **attention budget** — transformer 의 n² 구조에서 오는 유한한 주의 자원.
- **compaction** — 누적 context 를 압축.
- **just-in-time retrieval** — 필요할 때만 lightweight identifier 로 끌어옴.

학술 측 정량 정식화로 context collapse 가 있다 — monolithic rewrite 시 context 가 18,282 tokens(66.7%)에서 122 tokens(57.1%)로 붕괴하며, Generator/Reflector/Curator delta update 로 이를 방지한다 `[arxiv-agentic-context-engineering]` (ACE, tier 4 — tier 1 의 context rot 개념을 backing 하는 학술 측정값이다).

<img src="../../../research/agent-engineering-principles/figures/arxiv-agentic-context-engineering_fig2.png" width="500">

**그림 2**: monolithic rewrite 시 context 가 18,282 → 122 tokens 로 붕괴 (ACE context collapse, arXiv 2510.04618 fig2).

## 1.2 Gen2: harness engineering

이 절은 세 번째 세대를 다룬다 — model 을 둘러싼 소프트웨어 layer 를 일급 artifact 로 격상한 harness engineering.

**정의**: "A coding agent is the model plus everything you build around it. Harness engineering treats that scaffolding as a real artifact, and it tightens every time the agent slips" `[osmani-agent-harness-engineering]`. 학술 한 문장 정의는 더 구체적이다 — "the software layer that surrounds an LLM with tools, APIs, sandboxes, memory, validators, permission boundaries, execution loops, and feedback channels, thereby turning a stateless model into a functional agent" `[arxiv-code-as-agent-harness]`.

**명명 권위**: **"harness engineering" 용어는 Viv Trivedy 가 coined 했다** `[osmani-agent-harness-engineering]`. Anthropic 의 "Effective harnesses for long-running agents" (2025-11) 와 Addy Osmani 의 "Agent Harness Engineering" 이 canonical 정초다. **Agent = Model + Harness** 등식은 Harness-Bench 논문 발이다 `[greyling-agent-model-harness]` `[arxiv-harness-bench]`.

등장 배경은 모델 논쟁이 놓친 나머지 절반을 짚은 데 있다 — "We've spent the last two years arguing about models... That conversation is fine as far as it goes, but it's missing the other half of the system" `[osmani-agent-harness-engineering]`. 문제를 모델 한계가 아니라 scaffolding 한계로 재정의한다: "The gap between what today's models can do and what you see them doing is largely a harness gap". harness 가 메우는 이전 세대 미해결분은 context rot, early stopping, poor decomposition, incoherence across context windows 다. thesis 는 "A decent model with a great harness beats a great model with a bad harness" `[osmani-agent-harness-engineering]`.

**self-aware caveat (감쇠론으로 이어지는 핵심 명제)**: harness 의 모든 구성 요소는 "모델이 혼자 못 하는 것"에 대한 가정을 encode 한다 — "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing" `[anthropic-harness-design-long-running-apps]`. 따라서 harness 는 모델이 개선되면 축소되어야 한다 (v1 의 sprint construct 가 v2 에서 제거되는 식). 이 감쇠론은 1.4-T Tension ③ 에서 정량과 함께 균형 서술한다.

**정리·대중화 (tier 2)**: Cobus Greyling 이 harness 를 SDK / Framework / Scaffolding 위 **4번째 architectural layer** 로 정리했다 — Schmid 의 OS analogy, parallel.ai 의 6-component 구조, "framework collapsing into harness" 의 80/20 관찰을 한데 묶었다 `[greyling-rise-of-harness-engineering]`. 단 Greyling 은 명명자가 아니라 정리·대중화자이므로(아래 박스 참조), material claim 인용 시 원 출처로 거슬러 표기한다.

> **명명 권위 vs 정리 역할 (인용 시 구분 필수)**. Greyling (tier 2) 은 명명자가 아니라 정리·대중화자다 — 매 글이 외부 1차 권위를 명시 호명한다 (loop = Osmani 명명 / Steinberger·Cherny 슬로건, harness = OpenAI·Anthropic·Fowler·parallel.ai·Schmid, Agent = Model + Harness = Harness-Bench 논문). material claim 인용 시 Greyling 카드를 통해 원 출처로 거슬러 인용한다. 정리하면 — **context = Osmani + Anthropic 공동 / harness = Trivedy coined / loop = Osmani.**

학술 정식화는 세 갈래다 (모두 tier 4, 단독 근거 금지): 정의는 `[arxiv-code-as-agent-harness]` (UIUC/Meta/Stanford, 200+ works survey — §5.2 가 "science of harness engineering 부재"를 open challenge 로 명시한다, 즉 harness 는 아직 정립된 분과가 아니다). 측정은 `[arxiv-inside-the-scaffold]` (13개 OSS coding agent 소스코드 taxonomy, 3 layer × 12 dimension). 벤치는 `[arxiv-harness-bench]`.

<img src="../../../research/agent-engineering-principles/figures/arxiv-inside-the-scaffold_fig1.png" width="500">

**그림 3**: 13개 OSS coding agent 의 3 layer × 12 dimension scaffold taxonomy (arXiv inside-the-scaffold fig1). loop primitive 들이 배타적 타입이 아니라 연속 spectrum 위 조합으로 나타난다는 것이 핵심 관찰이다.

## 1.3 Gen3: loop engineering

이 절은 가장 최근 세대를 다룬다 — agent 에게 prompt 하는 사람 자체를 시스템으로 대체하는 loop engineering.

**정의**: "Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead" `[osmani-loop-engineering]`. harness 와의 차이는 — "The harness but it runs on a timer, it spawns little helpers, and it feeds itself" → harness **위** 계층이다.

**명명 권위**: **Addy Osmani 가 명명자다** ("Loop Engineering", 2026-06). 실무 슬로건은 Peter Steinberger ("You should be designing loops that prompt your agents") 와 Boris Cherny (head of Claude Code @Anthropic: "I don't prompt Claude anymore. I have loops running that prompt Claude... My job is to write loops") 가 제공했다 `[greyling-loop-engineering]`. Greyling 은 이를 6-block 구조로 묶은 정리자이지 명명 권위가 아니다.

등장 배경은 type/read/type 수동 루프의 종말이다 — "For like two years the way you got something out of a coding agent was you wrote a good prompt and shared enough context. You type a thing, you read what came back, you type the next thing" `[osmani-loop-engineering]`. harness engineering 글이 open problem 으로 남겼던 것("agents that run on a timer / self-improving")이 여기서 실현된다.

**6-block 구조** `[greyling-loop-engineering]`: scheduling(heartbeat) / worktrees / skills / connectors / sub-agents(maker-checker) / memory. **runtime tiering** 으로는 Tier A terminal (Claude Code / Grok) / Tier B platform (LangChain durable execution) / Tier C editor 로 나뉜다 `[greyling-loop-engineering-playbook]`.

**실증 정초**: 16개 Claude Opus instance × 약 2,000 세션(약 $20,000)으로 100,000줄 Rust 기반 C compiler 를 자율 구축한 사례 — 무한 bash loop + lock 기반 task 조율 + 거의 완벽한 verifier 조합이다 `[anthropic-c-compiler-parallel-claudes]`. 이 사례는 우리 세팅의 headless 분사(2부 2.4)·loops 계층(2부 2.5)의 외부 실증 근거다.

**경계**: "The loop changes the work, it does not delete you from it" — verification 은 여전히 인간 책임이며, comprehension debt·cognitive surrender 위험이 따른다 `[osmani-loop-engineering]`. loop 가 사람을 일에서 지우지는 않는다.

## 1.4 패턴 카탈로그 (P1~P11)

이 절은 세대사를 가로지르는 실무 패턴 11종을 GoF 식 named pattern 으로 정리한다. 각 패턴은 문제 → 핵심 원칙(verbatim) → 메커니즘 → 반론 구조를 따른다. 패턴이 어느 세대에서 파생했는지는 그림 4 가 보여준다.

<img src="../assets/figures/f2_pattern_generation_matrix.png" width="500">

**그림 4**: 11개 실무 패턴이 어느 세대에서 파생했나 — maker-verifier(P3)는 harness·loop 두 갈래에서 수렴한다.

**표 1.4a — 패턴 11종 1차 카드·서술 강도** (`04_technical_deep_dive.md` Takeaway 기준). 강도 ★ = 단정 서술 가능 / ▲ = caveat 동반:

| 패턴 | 1차 카드 | 강도 |
|---|---|---|
| P1 plan-then-execute | `[anthropic-claude-code-best-practices]` `[owainlewis-spec-driven]` `[osmani-good-spec]` | ★ |
| P2 spec-driven | `[github-spec-kit]` `[owainlewis-spec-driven]` `[osmani-good-spec]` | ★ |
| P3 maker-verifier | `[anthropic-harness-design-long-running-apps]` `[epsilla-gan-style-agent-loop]` `[mindstudio-planner-generator-evaluator]` `[willison-agentic-engineering-patterns]` | ★ |
| P4 서브에이전트 | `[anthropic-multi-agent-research-system]` `[cognition-dont-build-multi-agents]` `[cognition-multi-agents-working]` `[openai-practical-guide-agents]` | ▲ |
| P5 파이프라인 세분화 | `[anthropic-building-effective-agents]` `[github-spec-kit]` | ★ |
| P6 golden set | `[anthropic-demystifying-evals]` `[braintrust-eval-driven-development]` `[anthropic-infrastructure-noise]` `[anthropic-ai-resistant-evals]` `[redhat-eval-driven-development]` | ★ |
| P7 오답노트 승격 | `[osmani-agent-harness-engineering]` `[braintrust-eval-driven-development]` `[arxiv-agentic-context-engineering]` | ▲ |
| **P8 상태 영속성·산출물 소통** | `[osmani-long-running-agents]` `[humanlayer-12-factor-agents]` `[anthropic-effective-harnesses]` `[anthropic-managed-agents]` | ★ (canonical) |
| P9 worktree | `[zylos-git-worktree-isolation]` `[anthropic-c-compiler-parallel-claudes]` `[anthropic-claude-code-sandboxing]` | ▲ |
| P10 headless·cron | `[claude-code-github-actions]` `[anthropic-claude-code-auto-mode]` `[mindstudio-headless-mode]` | ▲ |
| P11 컨텍스트 절약 | `[anthropic-effective-context-engineering]` `[anthropic-agent-skills]` `[anthropic-code-execution-mcp]` `[anthropic-advanced-tool-use]` `[anthropic-think-tool]` | ★ |

### P1. Plan-then-execute (계획·실행 분리)

**문제**: 같은 agent 에게 계획과 실행을 동시에 맡기면 엉뚱한 문제를 풀거나 edge case 를 놓친다.

**핵심 원칙**: "Separate research and planning from implementation to avoid solving the wrong problem" `[anthropic-claude-code-best-practices]`. "don't ask the same agent to plan the work and do the work" — planning(edge-case 분석)과 execution(shipping)은 서로 다른 cognitive mode 다 `[owainlewis-spec-driven]`. "Planning in advance matters even more with an agent - you can iterate on the plan first, then hand it off to the agent" `[osmani-good-spec]`.

**메커니즘**: explore → plan → implement → commit 4단계 + plan mode `[anthropic-claude-code-best-practices]`. agent 가 "plan and operate independently" 한다 `[anthropic-building-effective-agents]`.

**반론**: plan mode 는 그 자체로 overhead 다 — "If you could describe the diff in one sentence, skip the plan" `[anthropic-claude-code-best-practices]`. 작은 작업은 plan 을 건너뛴다. tier-4 backing 으로 P-t-E 가 ReAct 대비 predictability·cost 우위를 보인다 `[arxiv-secure-plan-then-execute]`.

### P2. Spec-driven development (spec-first)

**문제**: 즉흥 prompt 는 agent 가 수십 개의 결정을 추측하게 만들고, 그 추측이 누적된다.

**핵심 원칙**: "We're moving from 'code is the source of truth' to 'intent is the source of truth'" `[github-spec-kit]`. "A plan Claude generates lives in a conversation. A spec lives in your repo" `[owainlewis-spec-driven]`. "Specs become the shared source of truth… living, executable artifacts that evolve with the project" `[osmani-good-spec]`. 결과적으로 "the bottleneck shifts from implementation to specification" `[owainlewis-spec-driven]`.

**메커니즘**: spec-kit 4-phase (Specify → Plan → Tasks → Implement) 에서 Tasks 단계가 spec 을 small isolated chunk 로 분해한다 (TDD 유사) `[github-spec-kit]`. spec 의 4요소는 Context / Scope / Constraints / Tasks 다 `[owainlewis-spec-driven]`.

**정량 (tier 4 보조)**: constitutional spec-driven 에서 보안 defect −73%, velocity 유지 `[arxiv-constitutional-spec-driven]`.

**반론**: 작은 작업에 over-spec 은 overhead 다 — "Don't under-spec a hard problem… but don't over-spec a trivial one" `[osmani-good-spec]`. 거대 spec 통째 주입도 context/attention 한계로 실패하므로 "practical context size 안에서 진화하는 spec" 이 되어야 한다 `[osmani-good-spec]`.

### P3. Maker-verifier 분리 (자기채점 금지)

**문제**: 모델은 자기 산출물을 후하게 평가한다 (모든 출처가 일치하는 가장 강한 합의).

**핵심 원칙**: "When asked to evaluate work they've produced, agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre" / "Separating the agent doing the work from the agent judging it proves to be a strong lever" `[anthropic-harness-design-long-running-apps]`. 모델은 "pathological optimists" 이며 "By engineering conflict, you engineer progress" `[epsilla-gan-style-agent-loop]`. "Models reliably skew positive when they grade their own work" `[osmani-long-running-agents]`.

**메커니즘 (왜 실패하나)**: autocomplete bias — "When the same model that wrote the code reviews it, it tends to overlook its own mistakes" `[mindstudio-planner-generator-evaluator]`. 해법은 adversarial reviewer — "a fresh model try to refute the result, so the agent doing the work isn't the one grading it" / "A reviewer running in a fresh subagent context sees only the diff and the criteria... not the reasoning that produced the change" `[anthropic-claude-code-best-practices]`. 일반화 형태로 brain/hands 분리 `[anthropic-managed-agents]`, CitationAgent 별도 검증 `[anthropic-multi-agent-research-system]`, red/green TDD `[willison-agentic-engineering-patterns]` 가 있다.

**반론 (GAN 비유 caveat)**: "the evaluator isn't adversarial in a competitive sense. It's more like a senior engineer reviewing a pull request" `[mindstudio-planner-generator-evaluator]` — GAN 라벨을 문자 그대로 적용하면 안 된다. adversarial reviewer 도 과신하면 안 된다 — "A reviewer prompted to find gaps will usually report some, even when the work is sound... Chasing every finding leads to over-engineering" `[anthropic-claude-code-best-practices]`.

### P4. 서브에이전트 분업 (orchestrator-worker)

**문제**: 단일 agent 는 context window·path dependency 에 갇히고, 다중 agent 는 깨지기 쉬워질 위험이 있다.

**핵심 원칙 (찬성)**: orchestrator-worker 가 single-agent 대비 내부 eval 90.2% 향상, "Multi-agent systems work mainly because they help spend enough tokens to solve the problem" `[anthropic-multi-agent-research-system]`. clean-context 찬성 — "A clean-context reviewer catches bugs the coder can't see" `[cognition-multi-agents-working]`.

**핵심 원칙 (반대)**: "Running multiple agents in collaboration only results in fragile systems" — "Actions carry implicit decisions, and conflicting decisions carry bad results" `[cognition-dont-build-multi-agents]`.

**메커니즘**: 각 sub-agent 가 별도 context window 에서 병렬 압축, 1,000–2,000 token 요약을 반환 `[anthropic-effective-context-engineering]`. manager pattern(agents as tools) / decentralized(handoff) 구분 `[openai-practical-guide-agents]`.

**정량**: multi-agent 는 chat 대비 약 15배 token, subagent 3–5개 병렬 → research time 최대 90% 단축 `[anthropic-multi-agent-research-system]`. enterprise 사용 약 8x 성장 `[cognition-multi-agents-working]`.

**반론**: coordination 제약 — "shared context 를 요하거나 inter-agent dependency 무거운 domain 엔 부적합" `[anthropic-multi-agent-research-system]`. 두 Cognition 글의 대립은 read/write 축으로 종합된다 (1.4-T Tension ① 참조).

### P5. 파이프라인 세분화

**문제**: 거대한 monolithic 작업은 검증이 불가능하고 context 를 넘친다.

**핵심 원칙**: prompt chaining — "decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one" `[anthropic-building-effective-agents]`. Tasks 단계가 spec 을 "small, review-able, isolated work chunk" 로 쪼갠다 `[github-spec-kit]`.

**메커니즘**: research loop → citation verification → final compilation 순차 phase `[anthropic-multi-agent-research-system]`. feature-by-feature 점진 진행 `[anthropic-effective-harnesses]`.

**반론 (tier 4)**: loop primitive 는 배타적 타입이 아니라 조합 가능하다 — "compositions of loop primitives along continuous spectra" `[arxiv-inside-the-scaffold]`. 세분화 단계 수는 고정 규칙이 아니라 spectrum 이다.

### P6. Golden set · eval 회귀

**문제**: markdown/prompt 변경이 개선인지 측정하지 않고 배포하면 조용히 regress 한다.

**핵심 원칙**: "frozen core(golden set) + growing set" 이분법, "If your eval correctly captures what 'good' means, then optimizing against it is sufficient" / "When every change runs through the same eval suite before shipping, regressions surface in development instead of in production" `[braintrust-eval-driven-development]`. "A markdown edit without a before/after eval is a vibe" `[greyling-configured-not-coded]`.

**메커니즘**: eval anatomy (Task / Trial / Grader / Transcript / Outcome), "what proportion of trials an agent succeeds"(pass@k), eval saturation, 20–50 simple task 로 출발 `[anthropic-demystifying-evals]`. judge calibration, "known bad" set `[redhat-eval-driven-development]`. AI-resistant 설계로 saturation·contamination 에 저항한다 `[anthropic-ai-resistant-evals]`.

**정량 (신뢰성 caveat)**: infrastructure noise — Terminal-Bench 2.0 에서 strict↔uncapped 사이 6%p swing, "A few-point lead might signal a real capability gap—or it might just be a bigger VM" `[anthropic-infrastructure-noise]`. eval 수치의 noise floor 를 인지해야 한다.

**반론 (tier 4)**: Goodhart 위험 — eval 이 "good" 을 부정확하게 포착하면 잘못 최적화된다. generic prompt 개선이 오히려 해친 사례 — Qwen 2.5 RAG 26/30 → 9/30 `[arxiv-eval-driven-iteration]`.

### P7. 오답노트 → 케이스 승격 (failure-driven evolution)

**문제**: 같은 실수를 반복하면 누적 비용이 크다.

**핵심 원칙 (1차 정의)**: "anytime you find an agent makes a mistake, you take the time to engineer a solution such that the agent never makes that mistake again" `[osmani-agent-harness-engineering]`. "failure-driven evolution" — production 실패를 correct reference 와 함께 golden dataset 에 추가해 "permanent regression guards" 로 굳힌다 `[braintrust-eval-driven-development]`. bug tracker·support queue 를 task 소스로 삼는다 `[anthropic-demystifying-evals]`.

**메커니즘 (tier 4)**: Reflector → Curator playbook delta update — Generator(생성)/Reflector(insight 추출)/Curator(통합) `[arxiv-agentic-context-engineering]`. self-edit 로 SWE-bench 17% → 53% `[arxiv-self-improving-coding-agent]`.

**caveat (tier 의존)**: 블로그 1차 출처에는 자동 승격 절차가 없다 — 자동 승격 메커니즘은 tier 4 (ACE / SICA) 에만 있다. 따라서 "자동 승격" 은 단정하지 않는다. system prompt 에 "be careful about X" 만 쌓으면 attention 이 옅어진다 — "silent killer" `[greyling-configured-not-coded]`.

### P8. 상태 파일 · 세션 간 영속성 · 산출물 소통 (canonical site)

> **이 절이 산출물 기반 소통 원칙의 canonical site 다.** 2부 2.3 과 4부 4.4 는 우리 실물 매핑·종착점만 다루고 원칙 자체는 여기로 cross-ref 한다 (원칙 재서술 금지).

**문제**: agent 는 amnesiac 이다 — 매 세션이 교대 근무자처럼 기억이 없다.

**핵심 원칙**: "State lives outside the agent's context… the agent itself is amnesiac, but the filesystem isn't" / "git as the coordination substrate" `[osmani-long-running-agents]`. "each new engineer arrives with no memory of what happened on the previous shift" `[anthropic-effective-harnesses]`. 12-Factor 로는 Factor 5(unify execution + business state), Factor 6(Launch/Pause/Resume), Factor 12(stateless reducer) `[humanlayer-12-factor-agents]`.

**원칙의 핵심**: agent 는 context 를 공유하는 것이 아니라 **파일 산출물로 소통한다.** 두 agent(또는 두 세션)가 직접 메모리를 주고받는 게 아니라, durable filesystem 에 산출물을 남기고 다음 agent 가 그것을 읽는다. amnesiac agent + durable filesystem 의 조합이다. 이것이 우리 세팅에서 `.claude_reports` 통신 버스로 구현된다 (2부 2.3).

**메커니즘**: 세 artifact — `claude-progress.txt`(로그) / `feature_list.json`(immutable acceptance) / git history `[anthropic-effective-harnesses]`. session 은 context window 밖 append-only event log 이고, `getEvents()` slice 로 재구성한다 `[anthropic-managed-agents]`. memory hierarchy 로 L1 working(TTL) / L2 long-term(vector) `[redis-context-compaction]`.

**반론 (tier 4)**: context file 과다는 역효과를 부른다 (1.4-T Tension ④). stateless reducer 는 이상형이며, 실제 LLM 은 완전히 pure 하기 어렵다 `[humanlayer-12-factor-agents]`.

### P9. Worktree 병렬 격리

**문제**: 두 agent 가 같은 tree 에서 동시에 작업하면 file collision·index corruption 이 난다.

**핵심 원칙**: "When two agents operate concurrently in the same tree, the failure modes are severe: File collisions, context contamination, index corruption, and conversation confusion" / "The 'Rebase Before PR' model is the most widely recommended convention" `[zylos-git-worktree-isolation]`. "Each worktree gets a private HEAD, private index, and private working directory" `[augmentcode-git-worktrees]`.

**메커니즘**: 공유 object store + private HEAD/index, container clone-push 격리 + lock 파일 task 조율 — "Merge conflicts are frequent, but Claude is smart enough to figure that out" `[anthropic-c-compiler-parallel-claudes]`. deferred conflict → PR merge 단계 ("visible git conflicts instead of silent runtime overwrites") `[augmentcode-git-worktrees]`.

**정량 (안전 층)**: filesystem + network sandboxing — "sandboxing safely reduces permission prompts by 84%" `[anthropic-claude-code-sandboxing]`.

**caveat (tier 의존)**: 패턴 합의는 강하나(C compiler 실증 `[anthropic-c-compiler-parallel-claudes]`), 정량 비교는 tier 3(zylos / augmentcode)에 머문다. "four or more concurrent sessions" cap 은 환경 의존이며 peer-review 가 없다. worktree 자체 비용(creation / disk / removal)도 존재한다 `[zylos-git-worktree-isolation]`.

### P10. Headless · cron 자동화

**문제**: 사람이 매 turn 붙어 있는 한 자율 운영이 안 된다.

**핵심 원칙**: `@claude` mention → PR 자동 생성, `on: schedule: cron`, Agent SDK 기반 `[claude-code-github-actions]`. `claude -p` CI/pre-commit + fan-out (`for file in ...; do claude -p ... done`) `[anthropic-claude-code-best-practices]`.

**메커니즘 (안전장치)**: auto mode classifier — "Claude Code users approve 93% of permission prompts" (17% false-negative rate) `[anthropic-claude-code-auto-mode]`. `--dangerously-skip-permissions` 는 격리 환경에서만 `[mindstudio-headless-mode]`. cron 3원칙 — full path / env 명시 / output redirect `[mindstudio-headless-mode]`.

**caveat (tier 의존)**: tier 1 은 docs + auto-mode(93% / 17% FN)뿐이고, cron 운영 디테일은 tier 3(`codewithseb-headless-cicd` 는 본문 403 차단, `mindstudio-headless-mode`)이다 — verbatim 정밀도가 약하다.

### P11. 컨텍스트 절약 (고정 오버헤드 / 압축)

**문제**: context 는 유한 자원이고 attention budget 은 token 마다 소진된다.

**핵심 원칙**: "Find the smallest possible set of high-signal tokens that maximize the likelihood of your desired outcome" `[anthropic-effective-context-engineering]`. progressive disclosure — "Skills let Claude load information only as needed" `[anthropic-agent-skills]` (우리 세팅의 skill on-demand 로드 근거 — 2부 2.6 cross-ref). "The right optimization target is not tokens per request. It is tokens per task" `[factory-evaluating-compression]`.

**정량**: code execution MCP 150,000 → 2,000 tokens, 98.7% 절감 `[anthropic-code-execution-mcp]`. Tool Search 85% 절감, programmatic calling 43,588 → 27,297 = 37% 절감 `[anthropic-advanced-tool-use]`. SkillReducer 48% description / 39% body 압축에 quality +2.8% `[arxiv-skillreducer]`. think tool 은 tool chain 도중 reasoning 공간을 준다 `[anthropic-think-tool]`.

**메커니즘**: raw → reversible compaction → lossy summarization 단계 폴백, L1/L2 hierarchy `[redis-context-compaction]`. just-in-time retrieval(lightweight identifier) `[anthropic-effective-context-engineering]`.

**반론**: aggressive 압축은 re-fetch 로 token 을 낭비한다 (tokens-per-task 관점) `[factory-evaluating-compression]`. compaction 의 공통 약점은 artifact trail preservation 으로 모든 방법이 2.19–2.45 에 머문다 `[factory-evaluating-compression]`. overly aggressive compaction 은 "subtle but critical context" 를 손실한다 `[anthropic-effective-context-engineering]`.

## 1.4-T Tensions — 논쟁점 4종 (균형 서술)

패턴 카탈로그가 합의 가능한 원칙을 다뤘다면, 이 절은 출처들이 대립하는 자리를 균형 있게 정리한다. 특히 ①(read/write 축)·④(context file 과다)는 반론을 반드시 동반한다.

### Tension ① — 서브에이전트 분업 찬반 (read/write 축 종합)

정면으로 대립하지만 시점·작업유형으로 종합할 수 있다.

| 출처 | 입장 | 단서 |
|---|---|---|
| Cognition 2025 | "Running multiple agents in collaboration only results in fragile systems" — decision 분산 반대 `[cognition-dont-build-multi-agents]` | "agents today" 시점 한정 명시 |
| Cognition 2026 | 입장 조건부 완화 — read(search/review)·planning 보조는 OK, write/decision 은 single-thread `[cognition-multi-agents-working]` | 모델 약 10개월 발전 |
| Anthropic | orchestrator-worker 90.2% 향상 `[anthropic-multi-agent-research-system]` | "shared context/heavy dependency domain 엔 부적합" |

**종합 규칙**: read 작업(search / review / citation)은 병렬 분업 OK, write/decision 은 single-thread. 두 Cognition 글은 대립이 아니라 보완이다. tier-4 backing — multi-agent violation 은 주로 inter-agent 정보 전달에서 일어난다 `[arxiv-auditing-harness-safety]`. 이 종합이 우리 세팅의 "orchestrator = main 고정, read 병렬 / write 브랜치 single-thread" 정책의 외부 근거다 (2부 2.4).

### Tension ② — GAN 비유의 한계

- 차용: generator-discriminator adversarial loop 가 self-scoring 금지를 잘 설명한다 `[epsilla-gan-style-agent-loop]`.
- 한계: 저자 스스로 "evaluator ≠ pure GAN, more like a senior engineer reviewing a PR" 라고 못박는다 — competitive adversarial 이 아니다 `[mindstudio-planner-generator-evaluator]`. enterprise 에선 evaluator 가 "in a vacuum" 으로 동작한다 (compliance·org state 에 접근하지 못함) `[epsilla-gan-style-agent-loop]`. GAN 라벨을 문자 그대로 적용하면 오해를 부르므로 cooperative review 로 한정해 인용한다.

### Tension ③ — Harness 가치 감쇠론 (inversion)

harness 만능론을 스스로 제한하는 논의다. 1.2 의 self-aware caveat 가 정량으로 확장된 자리다.

- "harness 복잡도는 모델 개선에 따라 줄어야 한다" — v1 sprint construct → v2 제거 `[anthropic-harness-design-long-running-apps]`.
- **정량 (Harness-Bench, Greyling 경유 2차 인용)**: harness 만 바꿔도 23.8pt 이동(동일 task·동일 model pool), NanoBot 76.2 vs OpenClaw 52.4 — 단 cross-harness variance 는 model 이 강해질수록 줄어든다. "Weak models are hostages to their harness… Strong models shrug it off… a crutch whose value decays as the model improves" `[greyling-agent-model-harness]`.
- minimal-loop 우월 — NanoBot 76.2 @ 7.3 turns < Hermes 71.2 @ 22.6 turns / 139.7K tokens; "a small loop that keeps its books beats a large one that loses them" `[greyling-agent-model-harness]`.
- **caveat**: 위 수치(76.2 / 52.4 / 23.8 등)는 Harness-Bench 논문에 귀속되며 Greyling 카드 경유 2차 인용이다 — 정밀 인용 시 arXiv 원문과 대조 권장. 미래 추정("model that is about to outgrow it")은 Greyling 의 수사적 확장이다.

### Tension ④ — Context file 과다의 역효과 (반례 데이터)

- "Bloated CLAUDE.md files cause Claude to ignore your actual instructions!" `[anthropic-claude-code-best-practices]`.
- **정량 반례 (tier 4)**: AGENTS.md 류 context file 이 오히려 task success rate 를 낮추고 inference cost 를 +20% 늘린다 — broader exploration(과한 testing·file traversal)을 유발하기 때문이다. "human-written context file 은 minimal requirement 만" `[arxiv-evaluating-agents-md]`. less-is-more — SkillReducer 48% 압축에 quality +2.8% `[arxiv-skillreducer]`.
- system prompt 를 dumping ground 로 쓰지 말라는 경고 — "attention 이 wall of text 에 옅어진다(silent killer)" `[greyling-configured-not-coded]`.
- **메타-tension (configuration 규율 격차)**: prompt → harness collapse 는 "win"(less infra)이지만, "Configuration is code in a different costume" — markdown edit 에는 diff / predict / rollback / measure / prune 규율이 따라오지 않는다. "The model is rented, the harness is owned" `[greyling-configured-not-coded]`. 이 반례는 우리 세팅의 얇은 CLAUDE.md 부트스트랩(2부 2.6)·지침 회귀 모의훈련(2부 2.5)의 직접 동기다.

## 1.5 1부에서 2부로 — 우리 시스템 매핑 다리

**자율 실행 안전장치 4층 (1부 원칙 → 2부 hard boundary 의 다리 논거)**: 1부의 패턴들은 자율성을 키우는 방향이지만, 자율성이 커질수록 hard boundary 와 intent classifier 를 층층이 쌓아야 한다 `[anthropic-claude-code-auto-mode]` `[anthropic-claude-code-sandboxing]`. 네 층이 서로를 보완한다 — **L1 permission prompt**(per-action 승인, "Claude Code users approve 93% of permission prompts" 라 대부분 마찰만) → **L2 auto-mode classifier**(intent-alignment 판정, 단 17% false-negative) → **L3 sandboxing**(filesystem+network hard boundary, "sandboxing safely reduces permission prompts by 84%") → **L4 hook gate**(deterministic 강제, "Unlike CLAUDE.md instructions which are advisory, hooks are deterministic"). 핵심 종합은 — **자율성이 커질수록 무게가 L1(승인)에서 L3(sandbox)·L4(hook)의 hard boundary 로 옮겨간다.** classifier(L2)는 편의(prompt 감소)를 주지만 17% FN 이 있어 sandbox(L3)의 hard boundary 가 안전의 바닥이다 `[anthropic-claude-code-auto-mode]`. 1부에 흩어진 84%(P9)·93%/17%FN(P10) 수치가 이 4층 위에서 하나의 안전 논리로 묶인다.

<img src="../assets/figures/f3_safety_layers.png" width="500">

**그림 5**: 자율 실행 안전장치 4층 — L1 permission(93% 승인) → L2 classifier(17% FN) → L3 sandbox(84% prompt 감소) → L4 hook gate(advisory 아닌 deterministic). 자율성이 커질수록 무게가 L1 에서 L3/L4 의 hard boundary 로 이동한다.

이 4층 논거가 1부에서 2부로 넘어가는 다리다 — 우리 세팅의 hook 4종(2부 2.5)이 정확히 이 L4(deterministic hard boundary)에 해당하고, sandbox·permission 정책이 L1~L3 에 대응한다. 즉 "원칙은 자율성을 키우고, 안전장치는 그 자율성에 hard boundary 를 덧댄다" 는 전환이 1부 → 2부 매핑의 동기다.

1부는 분야를 망라했다. 2부는 그 원칙들이 우리 세팅 어디에 어떻게 녹아 있나를 매핑한다. 핵심 질문은 하나다 — **"요즘 쏟아지는 에이전트 코딩 원칙들이 우리 세팅 어디에 어떻게 녹아 있나."** 1부 패턴 P1~P11 각각이 2부 매핑 표의 행이 되고, 1부에서 정리한 명명 권위·tier·반론이 2부 anchor 의 근거 강도를 결정한다.

2부 anchor 는 1부 카드와 형식이 다르다 — 2부부터는 `파일경로 §절번호` 형식의 라이브 파일 anchor 를 쓰며, 이는 작성 시점(2026-06-11)에 실제 Read 한 파일의 스냅샷이다. 라이브 파일이 갱신되면 anchor 로 추적해 재확인한다.

---

# 2부 — 우리 세팅 매핑 (라이브 파일 anchor)

## 2.0 매핑의 원리

이 부는 1부의 외부 원칙이 `~/.claude/` 세팅 어디에 구현됐는지를 라이브 파일 anchor 로 매핑한다. 매핑 표(표 2.0a)는 P1~P11 각 패턴을 우리 실물에 연결하고, 이어지는 절(2.1~2.6)이 각 묶음을 해설한다.

표의 anchor 들은 모두 작성 시점(2026-06-11) 라이브 파일에서 직접 Read 한 것이다 — 이 표는 그 시점의 스냅샷이며, CLAUDE.md·CONVENTIONS.md·loops/README.md 가 바뀌면 매뉴얼이 stale 해진다. 그래서 anchor 를 `파일경로 §절번호` 로 명시했다 — drift 가 나면 anchor 로 추적해 재확인하라는 의도다.

**표 2.0a — P1~P11 × 우리 실물 매핑**:

| 패턴 | 우리 실물 | 라이브 anchor | 해설 절 |
|---|---|---|---|
| P1/P2 | 하드 순서 게이트 (research → spec → code), 신규 산출물 생성 순서 기계 강제 | `WORKFLOW.md §0(a)` · `CLAUDE.md §0(0)` · `hooks/artifact-guard.sh` · `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` | 2.1 |
| P3 | 팀 분업 critic·verifier + QA 5단계 + Step 5.5 편집팀 polish | `CONVENTIONS.md §1.1` · `§2` · `autopilot-draft/SKILL.md` Step 5.5 | 2.2 |
| P8 | `.claude_reports` 통신 버스 → 핸드오프 → pipeline_state 재개 → 3-tier → headless 분사 → worklog 2-layer | `CONVENTIONS.md §5` · `§5.4` · `§5.8` · `§5.10` | 2.3 |
| P4/P9 | orchestrator = main 고정, 본작업 브랜치 강제, 중첩 1단 한계, 머지 게이트 | `CONVENTIONS.md §5.10` · `§5.9` · `hooks/git-state-guard.sh` | 2.4 |
| P6/P7/P10 | loops 4종 + hooks 6종, 케이스 승격, 디스패치 등록부 | `loops/README.md` 현역 표 · `CONVENTIONS.md §5.10` · `§3` invariant 6 | 2.5 |
| P11 | 얇은 CLAUDE.md 부트스트랩, on-demand Read, skill progressive disclosure | `CLAUDE.md` 헤더 · `WORKFLOW.md §0` | 2.6 |

## 2.1 파이프 철학 — 하드 순서 게이트 (P1/P2/P5)

이 절은 plan/spec 분리(P1/P2)와 파이프라인 세분화(P5)가 우리 세팅에서 하드 순서 게이트로 구현된 자리다.

**단방향 순서**: 산출물은 한 방향으로만 흐른다 — 앞 단계 산출물 없이 다음 단계 진입이 금지된다. 코드 트랙은 `research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)`, 문서 트랙은 `research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine` (`WORKFLOW.md §0(a)`). 이것이 P2 의 "intent is the source of truth" 를 절차로 박은 것이다 — spec 없이 코드를 쓸 수 없다.

<img src="../assets/figures/f4_four_track_pipeline.png" width="500">

**그림 6**: 4트랙 파이프 — 문서 / 연구·실험 / 앱 / 라이브러리·CLI, 모두 research → spec → code 하드 순서 게이트를 통과한다 (artifact-guard.sh 가 생성 순서를 강제).

**기계 강제의 정확한 범위**: hook 이 강제하는 것은 _신규 산출물 생성 순서_ 뿐이다. `hooks/artifact-guard.sh` (PreToolUse Edit|Write|MultiEdit) 는 신규 spec ← research/analyze, 신규 plan ← spec, 신규 documents ← research/analyze 의 순서를 hard 차단한다 (`CLAUDE.md §0(0)`). 반면 **기존 산출물 편집·소스 코드는 차단하지 않는다** — "소유 스킬로 수정" 은 convention 이지 hook 강제가 아니다 (hook 이 소유 스킬과 직접 편집을 구분하지 못하기 때문). `/track`(⚡untracked)이면 생성 순서까지 전부 우회되며, Claude 는 우회용 untracked 를 자기 판단으로 켜지 않는다.

**"인용 ≠ 읽기" 검증 게이트**: spec-backed cwd 에서 사후 수정 요청이 들어오면, prd.md 를 _실제로 Read_ 했는지를 검증한다. `hooks/spec-skill-gate.sh` (PreToolUse Skill) 는 autopilot-code / autopilot-spec / autopilot-note 호출 시, 이번 세션에 prd.md 를 실제 Read 한 마커가 없거나 Read 이후 prd.md 가 갱신됐으면(역방향 drift) DENY 한다. 마커는 `hooks/spec-read-marker.sh` (PostToolUse Read) 가 prd.md Read 순간에만 생성한다. 즉 코드 주석이나 기억 속 `§N` 인용은 무효이며(인용 ≠ 읽기), self-report 가 아니라 검증되는 하드 게이트다.

## 2.2 팀 분업 · QA 5단계 (P3)

이 절은 maker-verifier 분리(P3)가 우리 세팅에서 팀 분업 + QA 5단계로 구현된 자리다. "산출 agent ≠ 채점 agent" 라는 P3 의 핵심이 maker 팀(기획·개발)과 verifier 팀(품질관리·연구·편집·디자인·codex)의 분리로 박혀 있다.

<img src="../assets/figures/f5_team_matrix.png" width="500">

**그림 7**: 팀 × 역할 — maker(기획팀·개발팀) vs verifier(품질관리·연구·편집·디자인·자료·codex-review) 분리.

**QA 5단계** (`CONVENTIONS.md §1.1`): quick / light / standard / thorough / adversarial 로 올라가며, reviewer 수와 max round 가 증가한다. quick 은 1× sonnet 단일 1라운드 강제, thorough(default)는 2× opus + 2× sonnet 에 max 2 round, adversarial 은 thorough 위에 외부 Codex review 가 얹힌다. 다중 reviewer 는 _다른 axes_ 를 분담한다 — opus 행은 domain expertise / methodology / completeness / safety 같은 깊이 axis, sonnet 행은 coverage / typo / 표기 일관성 / structure 같은 surface scan axis.

**adversarial 의 정확한 정의** (`CONVENTIONS.md §1.1`, `§3` invariant 2): adversarial = thorough + 1× codex-review-team. research / doc 트랙은 여기에 1× 연구팀 claim-verify(적대적 외부 진위 — N-vote default-refute, WebSearch 모순 탐색)가 추가된다. code 트랙은 외부 claim 이 없어 claim-verify 가 미적용이다. 자주 잘못 적히는 패턴이 "standard + Codex" 인데, base 는 thorough 다. codex-review-team 의 실제 review 는 Codex CLI(GPT-5)가 수행하고 sub-agent 본체(opus)는 호출·한국어 재정리만 담당한다 (`CONVENTIONS.md §2`).

**Step 5.5 편집팀 polish (2026-06-11 신설)**: autopilot-draft 의 draft-refine 이 끝난 뒤, qa standard 이상이면 편집팀이 모드 B(Editorial polish)로 wording 을 다듬는다 (`autopilot-draft/SKILL.md` Step 5.5). maker 가 만든 산출물을 별도 verifier 가 손보는 P3 의 또 다른 적용 자리다. qa < standard 면 skip 된다.

**팀별 model** (`CONVENTIONS.md §2`): 기획팀·연구팀·자료팀·디자인팀·편집팀·품질관리팀은 opus 기반(품질관리팀·연구팀은 가변 — 모드에 따라 sonnet/opus), 개발팀은 sonnet 단일이다. maker 인 개발팀이 sonnet 인 것은 비용 효율이고, 깊은 판단이 필요한 verifier·기획 자리가 opus 인 것이 P3 의 비대칭(채점이 더 비싸다)을 반영한다.

## 2.3 산출물 통신 버스 (P8 — 비중 최대)

> 이 절은 1부 P8 의 산출물 기반 소통 원칙이 우리 세팅에서 구현된 자리만 다룬다. 원칙 자체(amnesiac agent + durable filesystem, "git as the coordination substrate")는 1부 P8 canonical site 를 참조한다 — 여기서 재서술하지 않는다.

1부 P8 의 원칙("agent 는 context 를 공유하는 게 아니라 파일 산출물로 소통한다")이 우리 세팅에선 `.claude_reports` 통신 버스 한 줄기로 내려온다. 이 한 줄기가 1부 P8 → 2부 → 4부 를 관통하며, 매뉴얼에서 비중이 가장 크다.

**한 줄기 — `.claude_reports` 통신 버스**:

1. **3-tier 산출물 구조** (`CONVENTIONS.md §5`, 정의 §5.2): 모든 산출물이 사용자 가시성 기준으로 T1(Primary — 항상 봄) / T2(Secondary — 필요 시) / T3(`_internal/` — 거의 안 봄)으로 나뉜다. T1 은 사용자 인터페이스, T3 은 기계용 — 같은 파일 트리가 사람과 agent 양쪽에 서비스한다. 이것이 P8 의 "filesystem 이 통신 substrate" 를 tier 로 조직한 것이다.

2. **skill별 폴더 매핑** (`CONVENTIONS.md §5.4`): research → `research/{topic}/`, draft → `documents/{date}_{name}/`, code → `spec/`(청사진) + `plans/{date}_{slug}/`(작업), lab → `experiments/`. 각 skill 산출물이 정해진 자리에 떨어지므로 다음 skill 이 그 자리를 약속처럼 읽어 간다 — 이것이 P8 의 핸드오프다 (한 skill 의 출력이 다음 skill 의 입력, context 공유 없이 파일 경유).

3. **pipeline_state.yaml 재개**: 각 파이프 폴더의 `pipeline_state.yaml` 이 `--from <stage>` 재개용 stage state 를 담는다. 세션이 죽어도 state 파일이 남아 다음 세션이 이어받는다 — P8 Factor 6(Launch/Pause/Resume)의 구현이다.

4. **headless 분사가 가능한 이유**: 위 세 가지가 갖춰지면 프로세스 경계를 산출물이 넘을 수 있다. headless 로 분사한 `claude -p` 프로세스가 같은 `.claude_reports` 트리에 산출물을 남기고, main 이 그것을 수확한다 (2.4 에서 상술). agent 가 amnesiac 이고 통신이 filesystem 경유이기 때문에, 프로세스가 분리돼도 통신이 끊기지 않는다.

5. **공유 트리 가드** (`CONVENTIONS.md §5.8`): 여러 worktree 가 하나의 canonical `.claude_reports` 를 symlink 공유할 때, spec 공유 단일파일(`prd.md`·`pipeline_state.yaml`·`pipeline_summary.md`) 동시 쓰기는 `.pipeline-lock` 으로 가드한다 (30분 stale override). `plans/<cycle>/` 는 사이클별 폴더라 경로 분리 → 비경합이다. 통신 버스가 동시성에서도 깨지지 않게 하는 층이다.

6. **종착 — worklog 2-layer** (4부): 이 통신 버스에 쏟아진 산출물 md 들을 사람이 하나하나 안 읽고도 따라가고 다시 찾기 위한 자리가 worklog-board 의 Layer 2 다. P8 줄기의 종착점이며 4부에서 다룬다.

## 2.4 worktree · 병렬 디스패치 (P4/P9)

이 절은 서브에이전트 분업(P4)과 worktree 격리(P9)가 우리 세팅에서 구현된 자리다. 1부 Tension ① 의 "read 병렬 OK / write single-thread" 종합과 P9 의 worktree 격리가 §5.10 작업 격리 정책으로 합쳐진다.

**중첩 1단 한계 (확정 제약)**: 서브에이전트에는 Agent 툴이 노출되지 않는다 — 중첩 1단 한계다 (`CONVENTIONS.md §5.10`, 스모크 테스트 2026-06-11). 따라서 오케스트레이션은 항상 main 전담이고, 팀 에이전트는 prompt 에 명시된 worktree 경로에서만 일한다 (Skill·Bash·Edit 는 서브에이전트에서 정상). 이것이 P4 의 orchestrator-worker 를 우리 환경의 툴 계층 제약에 맞춰 구현한 형태다 — orchestrator = main 고정.

**규모 분기** (`CONVENTIONS.md §5.10`): 자잘한 단발(typo·1줄·quick 급)은 main 워킹트리에서 바로, 본작업(qa standard 이상·plan 추적 대상)은 worktree + 작업 브랜치, 병렬 요청(작업 중 새 독립 요청)은 즉시 새 worktree 로 분사한다. 기능 추가·모듈 신설·다파일 변경은 규모 판단 없이 무조건 브랜치다.

**디스패치 2모드** (`CONVENTIONS.md §5.10`): worktree 생성 후 두 모드가 있다 —

> **헤드리스 디스패치 사례 — Agent 툴 중첩 1단 vs `claude -p` 프로세스 분사 (2026-06-11 실증)**
>
> - **경량 (팀 위임)**: 팀 에이전트를 `run_in_background` 로 분사하고 prompt 에 작업 루트를 명시한다. 검증도 main 이 같은 경로로 QA 팀을 spawn 한다. 작은 단위·빠른 회전용. 단 이 경로는 중첩 1단 한계에 묶인다 — 분사된 팀 에이전트는 또 다른 Agent 를 부르지 못한다.
> - **풀 ceremony (headless 분사)**: worktree 안에서 `claude -p "/autopilot-code --qa quick ..."` 를 background 로 띄운다. headless 는 _완전한 메인_ 이라 Agent 툴을 보유한다 → 팀 분업·hook·plan 산출물까지 파이프 전부가 정상 작동한다. **핵심**: Agent 툴의 중첩 1단 제한은 _툴 계층_ 한정이고, 프로세스 분사는 무관하다 (2026-06-11 실증). 즉 Agent 툴로는 못 넘는 1단 벽을, 프로세스를 새로 띄우면 우회한다.
> - **주의**: ① `--allowedTools` 사전 개방(중간 질문 불가) ② 비용 = 세팅 세금 약 40k/대 (drill g0 실측) ③ 분사는 main 전용·깊이 1 — headless 가 또 headless 분사 금지(폭주 방지) ④ 동시 분사 기본 상한 3대.

**job 레지스트리** (`CONVENTIONS.md §5.10`): 분사 직전 `~/.claude/.dispatch/jobs.log` 에 한 줄 append 한다 — `<ISO시각>\topen\t<repo>\t<worktree경로>\t<slug>\t<파이프>`. 수확·정리 시 `open` 을 `done` 으로 바꾼다. 세션이 죽어도 등록부가 남아, 당직(oncall) 항목 8(디스패치 job 현황)이 고아 job(open 인데 24h+ 경과 또는 worktree 소멸·유휴)을 감시한다. 이것 역시 P8 의 filesystem-as-communication 이다 — 디스패치 상태를 메모리가 아니라 파일에 남긴다.

**git 상태 preflight** (`CONVENTIONS.md §5.9`): 코드 편집 전 1회 + 매 commit 직전, git working-state 를 점검한다. STOP(merge/rebase/cherry-pick 진행 중 · detached HEAD) 이면 편집·commit 을 멈추고 사용자에게 보고한다. WARN(다른 worktree 동일 브랜치 · upstream 앞섬 · dirty)은 한 줄 알림. DONE-BRANCH(base 에 ahead 0 인 끝난 브랜치)면 base 최신에서 새 브랜치를 판다. **하드 강제**: merge/rebase/cherry-pick 중 편집은 `hooks/git-state-guard.sh` (PreToolUse Edit|Write|MultiEdit|NotebookEdit)가 hard deny 한다 — ceremony 비경유 직접 편집 경로까지 커버하며, 모의훈련(drill) g2 가 잡은 구멍이다 (2026-06-11). 탈출구 `$GITDIR/CLAUDE_MERGE_EDIT_OK` 는 사용자가 충돌 해결을 명시 요청한 경우만이며 Claude 자가 판단 생성은 금지다.

**머지 시점 게이트** (`CONVENTIONS.md §5.10`): merge 는 Claude 선별 책임이되(2026-06-11 사용자 위임), 머지 시점은 (a) 사용자 머지 신호 또는 (b) 병렬 디스패치 job 수확 자리로 한정된다. 자기 turn 의 본작업 브랜치를 같은 turn 에 self-merge 하는 것은 금지다 — 브랜치 + 한 줄 보고로 turn 을 끝내고 main ref 는 불변으로 둔다. 머지 절차는 `git diff main...<branch>` 로 실내용 확인 → 회귀·중복이면 머지 안 함 → 충돌은 양쪽 의도 해석 → 애매하면 멈추고 질문 → 빌드 검증 후 커밋이다. "전부 합쳐" = 전량 머지가 아니라 선별 머지다.

## 2.5 loops 4종 + hooks 6종 (P6/P7/P10)

이 절은 golden set(P6)·오답노트 승격(P7)·headless cron(P10)이 우리 세팅에서 loops + hooks 로 구현된 자리다.

**loop 계층 — "loop engineering" 은 4개 층의 통칭** (`loops/README.md` 계층 표): 같은 모양(행동 → 검증 → 조정)이 네 박자로 돈다 — 초(도구) → 분(QA) → 일(작업) → 주(세팅). L1 에이전트 루프(초·Claude Code 자체 — 소비만), L2 과제 루프(분·skills/agents 의 maker/verifier QA 라운드), L3 작업 루프(일·세션 밖 cron+headless — 본 폴더), L4 메타 루프(주·시스템 자체 시험·개선 — 본 폴더). 핵심 불변식 — autopilot = 동사(일하기), loop = 부사(언제·얼마나·끝났는지). 어떤 루프도 라우팅·파이프 순서·산출물 컨벤션을 바꾸지 않는다.

<img src="../assets/figures/f6_loop_layers.png" width="500">

**그림 8**: L1 에이전트(초) → L2 과제(분) → L3 작업(일·당직(oncall)/일지(note)) → L4 메타(주·모의훈련(drill)/연수(study)).

**현역 루프 4종** (`loops/README.md` 현역 표 — 파일명은 ASCII, 표기는 병기. anchor 인용 시점에 실물 재확인 권장 — 과거 rename 이력이 있다):

| 루프 | 형 | 트리거 | 하는 일 | 산출 |
|---|---|---|---|---|
| 당직(oncall) | 시간 | cron 05:37 | 야간 순찰 — 작업장 이상 발견·보고만 | `notes/oncall/<date>.md` |
| 일지(note) | 시간 | cron 05:03 | 전날 산출물 worklog-board L2 노트화·라우팅 (idempotent) | `notes/_layer2/notes/` + digest |
| 모의훈련(drill) | 사건 | 지침 수정 후 `drill/run.sh` | fixture 가상 상황 headless 시험·채점 | `drill/results/<일시>/` |
| 연수(study) | 시간 | cron 일요일 06:17 | 외부 동향 × 현 세팅 → 개선 제안서만 (+ g0 세금 추세) | `notes/study/<date>.md` |

새벽 시간표는 05:03 일지(note) → 05:37 당직(oncall) 으로 충돌 방지 간격을 둔다.

**P6 — golden set ↔ 모의훈련(drill)**: 모의훈련은 지침 회귀 테스트다 (`CLAUDE.md` 도메인 트리거 — 지침 파일 수정 후 `drill/run.sh`). 1부 P6 의 "frozen core(golden set)" 가 우리 세팅에선 fixture 가상 상황의 채점 케이스로 구현된다. 단 업계 용어 'golden set' 과 우리 루프 호칭 모의훈련(drill)은 별개 — 'golden set' 은 P6 의 eval 개념, 모의훈련은 그 개념을 지침 회귀에 적용한 우리 루프다. 비용 측면에서 풀 ceremony headless 분사가 대당 약 40k(g0 세팅 세금)를 쓰므로, 연수(study)가 이 g0 세금 추세를 추적 보고한다.

**P7 — 오답노트 승격 ↔ 케이스 승격 + feedback 메모리** (`loops/README.md` "케이스 승격" 절, `CONVENTIONS.md §3` invariant 6): 실사고가 나면 그 상황을 fixture 로 재현해 `drill/cases/` 에 추가한다 (트리거 발화 "이거 drill 케이스로 박아"). 또한 post-it sweep·졸업, feedback 메모리 → 지침 승격, 당직(oncall) 발견 → triage 가 같은 P7 의 적용이다. 의도 동반 원칙(invariant 6)에 따라 지침·규칙·hook 신설에는 _왜(계기 사건 + 날짜)_ 를 남기며 — "의도의 최상위 보존 형태는 drill 케이스(실행 가능한 의도)" 다. 1부 caveat 그대로 — 자동 승격은 단정하지 않는다 (우리 세팅에서도 승격 결정은 사용자, 루프는 제안까지).

**P10 — headless·cron ↔ loops + `claude -p` 디스패치**: 위 4종 루프가 cron(시간형)·사건형으로 돌고, 2.4 의 headless 분사가 `claude -p` fan-out 이다. 1부 P10 의 cron 3원칙(full path / env 명시 / output redirect)이 그대로 적용된다. 모든 루프의 출구는 보고·제안까지이며(브랜치 merge 만 Claude 선별 책임), 결정(삭제·지침 적용)은 사용자다.

**hooks 6종** (`ls ~/.claude/hooks/` + 헤더 확인):

| hook | trigger | 역할 | 매핑 |
|---|---|---|---|
| `artifact-guard.sh` | PreToolUse(Edit/Write/MultiEdit) | `.claude_reports` 산출물 _생성 순서_ 강제 (📌tracked / ⚡untracked 우회) | P1/P2 |
| `spec-skill-gate.sh` | PreToolUse(Skill) | spec-backed cwd 에서 prd.md 실제 Read 마커 없으면 autopilot-code/spec/note DENY | P1/P2 |
| `spec-read-marker.sh` | PostToolUse(Read) | prd.md Read 시 세션 마커 생성 (gate 통과 증거) | P1/P2 |
| `git-state-guard.sh` | PreToolUse(Edit/Write/MultiEdit/NotebookEdit) | merge/rebase/cherry-pick 중 편집 hard deny (drill g2, 2026-06-11) | P9 |
| `design-postwrite.sh` | PostToolUse(Edit/Write/MultiEdit) | DESIGN HTML 저장 시 headless 렌더 + console error alert | (디자인 트랙) |
| `herdr-agent-state.sh` | (herdr 설치) | 외부 integration 관리 | (외부) |

hooks 는 세션 _안_ 의 부품(툴 호출 순간 강제)이고 loops 는 세션 _무관_ 실행이라는 점에서 역할이 갈린다 (`loops/README.md` 모두 첫 줄). hook 4종(artifact-guard·spec-skill-gate·spec-read-marker·git-state-guard)이 P1/P2/P9 의 하드 강제 층을 이룬다.

## 2.6 컨텍스트 절약 규율 (P11)

이 절은 컨텍스트 절약(P11)이 우리 세팅에서 얇은 부트스트랩·on-demand Read·progressive disclosure 로 구현된 자리다. 1부 Tension ④ 의 "bloated CLAUDE.md" 반례가 직접 동기다.

**얇은 CLAUDE.md 부트스트랩** (`CLAUDE.md` 헤더): CLAUDE.md 는 _얇은 부트스트랩_ 으로, 운영 라우팅의 단일 출처는 §0 이고 상세는 별도 파일에 둔다. 헤더가 직접 명시한다 — "라우팅 결정 시 `~/.claude/WORKFLOW.md` 를 Read 한다 (on-demand)", "eager 세션 전체 로드 X". 이것이 P11 의 "smallest possible set of high-signal tokens" 를 부트스트랩에 적용한 것이다. Tension ④ 의 "Configuration is code in a different costume" 경고에 대응해, CLAUDE.md 확장을 금지하고 skill 변경은 README(자동 동기화)에 반영하도록 운영 정책에 박았다.

**on-demand Read** (`WORKFLOW.md §0`): WORKFLOW.md 는 지침 기반 on-demand 로 적재된다 — 매 프롬프트 `workflow-guard-hook` 모드 신호(📌tracked 따름 / ⚡untracked 면제)가 anchor 이고, tracked 라우팅이 필요한 자리에서만 Read 한다 (hook 주입·eager 로드 아님). user_profile 도 같은 lazy·이식 가능 패턴으로, 해당 자리에서만 Read 하고 default 를 따른다. P11 의 just-in-time retrieval 을 지침 로드에 적용한 형태다.

**skill progressive disclosure**: skill 카탈로그·description 은 매 세션 자동 주입되지만 SKILL.md 본문은 invoke 시에만 로드된다. 1부 P11 의 progressive disclosure ("Skills let Claude load information only as needed" `[anthropic-agent-skills]`)가 우리 skill 시스템의 동작 그대로다 — 카탈로그는 항상, 본문은 필요할 때만.

## 2.7 통합 기억 시스템 (P10 — store + 자체 하네스)

이 절은 _장기·단기 기억_ 이 우리 세팅에서 **하나의 포터블 store + 자체 메모리 하네스** 로 구현된 자리다. Hermes Agent 의 메모리 설계(SQLite cross-session recall · agent-curated write · learning loop)를 벤치마킹해(2026-06-15) 우리 식으로 이식했다. 단 "에이전트가 런타임에 자율로 자기를 고친다"는 Hermes 의 자율성 대신, _우리 거버넌스 불변식_("기억 저장은 자동, 세팅 변경은 사람 게이트")을 지킨다.

**왜 통합인가 (Tension — 흩어진 기억).** 이전엔 기억이 셋으로 흩어져 있었다 — post-it(`.claude_reports/post-it.md`, 프로젝트 단기) · auto-memory(`projects/<cwd>/memory/`, 프로젝트 장기) · user_profile(cross-project 프로필). 각자 별도 메커니즘·별도 위치라 (1) 한 검색면이 없고 (2) auto-memory 는 `.gitignore` 라 _들고 다닐 수 없었다_. → **하나의 store 로 통합**.

**store = 단일소스·포터블** (`~/.claude/memory/`): git추적 markdown 원본이 진실(SoT), `.index.db`(SQLite FTS5)는 파생·재생성 가능. 레코드는 `tier`(working 단기 / durable 장기) × `scope`(project / global) × `type` 세 축으로 구분된다. user_profile 처럼 _repo 따라 GitHub 로 이동_ 하는 포터블 기억이 됐다.

**3 면 → store mirror** (각 면은 live 역할 유지, store 가 canonical 가시 소스): post-it.md = 사람 편집 단기 면 / `projects/<cwd>/memory/` = 하네스 auto-write inbox / user_profile = 프로필 source. 셋 다 `mem sync` 로 store 에 mirror 된다 — 면을 없애지 않고 _store 를 단일 가시 소스_ 로 둔 것.

**자체 하네스 — store 가 세션 주입의 source** (`settings.json` hooks, P7 harness). Claude Code 기본은 `projects/<cwd>/memory/` 에서 주입하지만, 우리는 _우리 hook_ 으로 그 위를 덮는다. **SessionStart hook** `mem inject --hook` 이 store 의 현 cwd working+durable + global profile 을 `additionalContext` 로 주입 — store 가 세션 시작 기억의 source. **SessionEnd hook** `mem sync` 가 그 세션이 쓴 기억을 store 로 회수 + 색인. 이로써 `store → (주입) → 작업 → (회수) → store` 학습 루프가 우리 hook 으로 닫힌다 (Hermes learning-loop 의 우리식 구현 — P10 메모리 × P7 하네스).

**회상** (`recall.sh` = `mem recall`): 과거 메모리(store FTS5) + raw 세션 대화(`--sessions`) + 전 scope(`--all`) 를 한 명령으로 검색한다. CLAUDE.md 도메인 트리거가 "과거 결정·교정 회상 필요" 자리에서 Claude 가 자동 실행하게 박혀 있다 — _사용자가 직접 쉘 칠 일 없다_.

**불변식 (거버넌스 — Hermes 와의 분기점).** 기억 _저장_ 은 자동이다 (품질 필터·dedup·injection 가드만 거치고 사람 승인 게이트 없음) — "결정은 사용자"는 _세팅·행동 변경_ 용이지 _기억 기록_ 용이 아니기 때문. 반대로 _삭제(gc)·세팅 변경_ 은 여전히 사람 게이트. 이 분기가 Hermes(런타임 자율 self-edit)와 우리(기억은 자동·세팅은 사람)의 핵심 차이다.

> 라이브 앵커: `tools/memory/mem.py`(구현·CLI `mem {add,note,recall,index,sync,inject,migrate,lifecycle,...}`) · `settings.json`(SessionStart/End hooks) · `CONVENTIONS.md §7`(canonical 규칙) · `.claude_reports/spec/prd.md`(청사진).

---

# 3부 — 입문·실전 가이드 (발화 중심)

## 3.0 들어가며

이 부는 "이 상황엔 이 발화" 형식의 실전 가이드다. 외부 원칙 인용은 최소화하고 실전 절차를 주로 다룬다 — 근거는 `CLAUDE.md` 도메인 트리거 표 + `WORKFLOW.md §7` + `loops/README.md` 발화 규약이다. 3.1 은 하루 일과를 시간순 서사로 보여주고, 3.2~3.9 는 개별 발화 시나리오를 lookup 빈도순(가장 자주 찾는 것 앞)으로 정리한다.

**표 3.0a — 발화 시나리오** (빈도순):

| 상황 | 발화 | 무슨 일 | 라이브 anchor |
|---|---|---|---|
| 새 작업 라우팅 | 트랙별 첫 발화 (자연어 한 줄) | WORKFLOW 작업-본질 매핑 → 옵션 자동 구성 → 한 번 컨펌 → invoke | `CLAUDE.md §0(B)` · `WORKFLOW.md §2` |
| post-it handoff | context ~50%+ / wind-down / 작업 완료 | `/post-it handoff` 제안 (sweep 자동 포함) → 요약 보여주고 저장 여부 confirm | `CLAUDE.md §2` |
| 아침 당직 처리 | `당직 처리` / `당직 보고` | 최신 당직(oncall) 보고 Read → 발견별 triage 제안 → 승인분 실행 | `CLAUDE.md` 도메인 트리거 · `notes/oncall/<date>.md` |
| 사후 수정 (spec-backed) | 기존 프로젝트 수정·기능 요청 | prd.md 실제 Read → spec-drift 체크 → autopilot-spec update → autopilot-code --qa quick | `WORKFLOW.md §7` · `CLAUDE.md`(프로젝트) 트리거 |
| 병렬 디스패치 | 작업 중 새 독립 요청 | 파일 겹침 triage → 새 worktree background 분사 (겹치면 큐잉) | `CONVENTIONS.md §5.10` |
| 케이스 승격 | `이거 drill 케이스로 박아` | 실사고 상황을 fixture 로 재현 → drill/cases/ 추가 | `loops/README.md` "케이스 승격" 절 |
| 모의훈련 발사 | 지침 수정 후 / `drill/run.sh` | fixture 가상 상황 headless 시험·채점, FAIL 시 수정안 | `loops/README.md` 현역 · `CLAUDE.md` 트리거 |
| 연수 | (cron 자동) 일요일 06:17 / 제안 채택 | 외부 동향 조사 → 세팅 대조 → 개선 제안서 → 채택 서명 → 적용 → 모의훈련 | `loops/README.md` 현역 |

## 3.1 하루 일과 흐름 (시간순)

이 절은 발화 시나리오들이 하루 안에서 어떻게 이어지는지 시간순 서사로 보여준다 (개별 lookup 은 3.2~3.9).

<img src="../assets/figures/f7_daily_flow.png" width="500">

**그림 9**: 새벽 cron (일지(note) 05:03 · 당직(oncall) 05:37) → 아침 처리 → 작업 디스패치 → 지침 수정 후 모의훈련(drill) → 일요일 연수(study).

새벽에 cron 루프 두 개가 먼저 돈다 — 05:03 일지(note)가 전날 산출물을 worklog-board L2 로 노트화하고, 05:37 당직(oncall)이 작업장을 순찰해 이상을 보고한다 (`loops/README.md` 새벽 시간표). 아침에 사용자가 출근하면 첫 발화는 보통 "당직 처리" 다 (3.4) — 밤사이 당직 보고를 함께 triage 한다. 이어 본 작업이 디스패치되고(3.2 라우팅, 3.6 병렬 디스패치), 작업 중 지침을 수정했으면 그 세션 마무리에 모의훈련(drill)을 한 번 발사한다 (3.8). 일요일 06:17 에는 연수(study)가 외부 동향을 조사해 개선 제안서를 올린다 (3.9). 하루~한 주의 리듬이 L3(일)·L4(주) 루프 박자와 맞물린다.

## 3.2 새 작업 라우팅 (가장 빈번)

새 작업은 트랙별 첫 발화를 자연어 한 줄로 던지면 된다. 메인 Claude 가 WORKFLOW 작업-본질 매핑(`WORKFLOW.md §2`)으로 skill 을 고르고, 컨텍스트(cwd / `.claude_reports/` / 발화)를 보고 옵션을 자동 구성한 뒤 한 번 컨펌하고 invoke 한다 (`CLAUDE.md §0(B)`).

**트랙별 대표 발화 예시** (자연어 한 줄 — 어느 skill 로 라우팅되는지):

| 발화 (예) | 라우팅 | 트랙 |
|---|---|---|
| "이 논문들 좀 정리해줘" / "이 도메인 survey 떠줘" | autopilot-research → `research/` | 연구 |
| "이 내용으로 매뉴얼/문서 한 편 써줘" | autopilot-draft → `documents/` | 문서 |
| "X 기능 붙여줘" / "이 모듈 새로 만들어줘" | (spec 없으면) autopilot-spec → autopilot-code, 하드 순서 게이트 통과 | 앱/라이브러리 |
| "이 실험 돌려서 결과 정리해줘" | autopilot-lab → `experiments/` | 연구·실험 |
| "이 프로젝트 구조 좀 파악해줘" | analyze-project (작은 작업 — 즉시 invoke) | 공통 |

slash 직접 입력도 된다 — `/autopilot-code --qa quick ...` 처럼 치면 컨펌을 skip 하고 바로 invoke 한다. 즉 평소엔 자연어 한 줄(컨펌 1회), 옵션을 이미 정했으면 slash 직접 (컨펌 skip) 두 길이다.

발화 분류 — ceremony 큰 작업(autopilot-* 전체 + analyze-user)은 컨펌 흐름, 작은 작업(audit / post-it / analyze-project)은 즉시 invoke, sub-skill 자연어는 `--from <stage>` 재개, 매칭 없음은 직접 처리다. `/autopilot-code <args>` 처럼 slash 로 직접 입력하면 컨펌을 skip 한다. 신중히 / camera-ready / submission·PR open 직전 같은 high-stakes 신호가 있으면 qa 가 adversarial 로 자동 상향된다.

## 3.3 post-it handoff

context 가 약 50%+ 차거나, wind-down 발화가 나오거나, 작업 한 덩어리가 끝나면 `/post-it handoff` 를 먼저 제안한다 (`CLAUDE.md §2`). handoff 는 sweep 을 자동 포함한다 — 확실한 졸업·stale 만 자동 prune(애매하면 keep)하고 한 줄 보고한다. 사용자는 post-it 을 읽지 않으므로 줄 단위 검토를 강요하지 않고, 짧은 요약을 보여준 뒤 저장 여부만 confirm 한다. post-it 의 목적은 세션 단절 방지 — Claude 가 사용자 흐름을 이어가고, 사용자가 놓친 것을 상기하는 것이다.

## 3.4 아침 당직 처리

아침 첫 발화로 자주 쓰이는 "당직 처리" / "당직 보고" (alias 동일)다. 최신 당직(oncall) 보고(`notes/oncall/<date>.md`)를 Read 해 발견별 triage 를 제안하고, 승인된 것만 실행한다 (`CLAUDE.md` 도메인 트리거). 기계적 정리(worktree remove 등)는 확인 후 즉시, 파괴 급은 별도 confirm 이다. 처리한 발견은 보고 파일에 ✅ 로 표시한다. 당직은 발견·보고만 하고(2.5), 실제 처리 결정은 이 아침 발화에서 사용자와 함께 내린다.

## 3.5 사후 수정 (spec-backed cwd)

기존 프로젝트의 수정·기능 요청(특히 새 세션)은 ad-hoc 직접 Edit 으로 끝내지 않는다 (`WORKFLOW.md §7`). 순서는 — (0) 기존 산출물 파악: `spec/prd.md` 를 Read 도구로 _실제로_ 읽는다 (코드 주석·기억 속 `§N` 인용은 무효 — 인용 ≠ 읽기) → (1) spec-drift 사전 체크: route / schema / UI-flow / 외부 연동 / 마이그레이션 같은 spec-significant 변경이면 autopilot-spec update(+ versioning), within-spec 이면 "spec 영향 없음" 확인 → (2) autopilot-code --qa quick 경유(`plans/` 에 기록). 순수 typo·1줄만 직접 Edit 이다.

이 순서가 self-report 가 아니라 검증되는 게 핵심이다 — `hooks/spec-skill-gate.sh` 가 prd.md 실제 Read 마커를 검사해, 마커가 없거나 Read 이후 prd.md 가 갱신됐으면 autopilot-code/spec/note 호출을 DENY 한다 (2.1).

기대 산출물 — 수정 작업 기록은 `.claude_reports/plans/{date}_{slug}/` 에 떨어진다 (dev_logs·plan).

## 3.6 병렬 디스패치

작업 진행 중 새 독립 요청이 들어오면, 파일 겹침을 triage 한 뒤 새 worktree 로 background 분사한다 (겹치면 그 job 뒤에 큐잉) (`CONVENTIONS.md §5.10`). 앞 job 완료를 기다리지 않는다. 디스패치 모드(경량 팀 위임 / 풀 ceremony headless 분사)와 중첩 1단 한계·머지 게이트는 2부 2.4 에서 상술했다. 분사 직전 `.dispatch/jobs.log` 에 등록부 한 줄을 남기는 것을 잊지 않는다 — 세션이 죽어도 당직(oncall) 항목 8 이 고아 job 을 감시한다.

## 3.7 케이스 승격

실사고가 났을 때 "이거 drill 케이스로 박아" 라고 발화하면, 그 상황을 fixture 로 재현해 `drill/cases/` 에 추가한다 (`loops/README.md` "케이스 승격" 절). 1부 P7(오답노트 승격)의 적용으로, 같은 실수를 다시 안 하도록 실행 가능한 의도(drill 케이스)로 굳히는 자리다. 의도의 최상위 보존 형태가 drill 케이스라는 점(2.5)에서, 이 발화는 P7 의 가장 강한 형태다.

기대 산출물 — 재현된 fixture 케이스는 `~/.claude/loops/drill/cases/` 에 추가된다 (이후 `drill/run.sh` 가 함께 채점).

## 3.8 모의훈련 발사

지침 파일(CLAUDE.md / CONVENTIONS / WORKFLOW / SKILL.md / agents / hooks)을 수정한 뒤에는, 편집 세션 마무리에 `drill/run.sh` 를 1회 발사한다 (커밋마다 X) (`loops/README.md` 현역 · `CLAUDE.md` 도메인 트리거). fixture 가상 상황을 headless 로 시험·채점해, FAIL 이면 수정안을 제시한다. 미실행 시 당직(oncall)이 다음날 아침 보고한다. 사건형 루프라 cron 이 아니라 지침 수정이라는 _사건_ 이 트리거다.

## 3.9 연수

연수(study)는 일요일 06:17 cron 으로 자동 실행된다 (`loops/README.md` 현역). 외부 동향(agent engineering 신간·Claude Code 변경)을 조사해 현 세팅과 대조하고 개선 제안서만 올린다(+ g0 세금 추세). 제안 채택은 사용자 서명 → 적용 → 모의훈련(drill) 순서다. 1부 P7 의 failure-driven evolution 을 _외부 동향 driven_ 으로 확장한 자리로, 루프 출구가 제안까지인 공통 규약(2.5)을 따른다.

기대 산출물 — 개선 제안서는 `notes/study/<date>.md` 에 떨어진다 (제안만 — 적용·채택은 사용자 서명 후).

---

# 4부 — worklog-board 활용 (에이전틱 노트)

## 4.0 왜 에이전틱 노트인가

이 부는 산출물 기반 소통(1부 P8)의 종착점인 worklog-board 에이전틱 노트를 다룬다. 2부 2.3 의 `.claude_reports` 통신 버스에 산출물 md 가 쏟아지면, 사람이 그것을 하나하나 읽기 어렵다. worklog-board 의 제품 비전(v18)이 정확히 이 문제를 겨눈다 — "쏟아지는 산출물 md 를 하나하나 안 읽고도 따라가고 다시 찾는 것" (`worklog-board/.claude_reports/spec/prd.md §2`).

즉 P8 줄기(1부 P8 → 2부 2.3 → 4부)의 끝점이 여기다. 통신 버스가 산출물을 _쌓는_ 층이라면, worklog-board 의 Layer 2 는 그 산출물을 _읽기 좋게 정돈해 다시 찾을 수 있게_ 하는 층이다. 원칙 자체(amnesiac agent + durable filesystem)는 1부 P8 canonical 을 참조한다 — 여기서 재서술하지 않는다.

## 4.1 2-Layer 아키텍처

worklog-board 는 소유 주체·생성 경로가 다른 두 레이어로 나뉜다 (`worklog-board/.claude_reports/spec/prd.md §2`).

**표 4.1a — 2-layer 실물**:

| layer | 위치 | 주인 | 단위 |
|---|---|---|---|
| Layer 1 | `notes/cards/` (82 cards 실재) | 사용자 (보드 직접 생성) | `kind: task` · `kind: project` 카드 |
| Layer 2 | `notes/_layer2/` (backbones·tasks·papers·notes 4 디렉터리 실재) | 에이전트 (autopilot-note 정리) | 산출물 노트화 row + 카탈로그 |
| 연결 다리 | `_layer2/notes/<id>.md` row | — | `card_id`(→L1) + `backbone_ids`·`task_ids`·`paper_id`(→L2) |

Layer 1 은 사용자가 보드에서 직접 만드는 프로젝트 관리·로깅 층(`kind: task` 단기 commitment / `kind: project` 납품·논문 출간 단위)이고 (`prd.md §2.1`·`§2.2`), Layer 2 는 에이전트가 `.claude_reports` 산출물을 정리한 산출물 맵이다 (`prd.md §2`).

**연결 고리 = `_layer2/notes/<id>.md` row** (`prd.md §2`): 한 노트가 `card_id`(→Layer 1 카드) + `backbone_ids`·`task_ids`(→Layer 2 축) + `paper_id`(→papers)를 동시에 들고 양 레이어를 잇는다 (M:N). 경계 규칙이 핵심이다 — 경계를 넘는 유일한 다리가 `notes.card_id`(soft ref, nullable, hard FK 없음)이며, 이는 _에이전트가 L1 을 직접 못 건드리는 소유권 불변식_ 을 제약으로 강제한 것이다 (`prd.md §2.5`). 에이전트는 L1 에 _제안만_ 한다.

> 주의: prd.md 는 v2~v33 누적이며 진행 중 vision 이 섞여 있다 (DB 전환 v21·홈 콕핏 v22 등). 매뉴얼은 _현재 실재하는 실물_(notes/ 파일 구조 + prd 확정 결정)만 anchor 하고, 미구현 vision(DB 마이그레이션 등)은 "진행 중" 으로 표시하며 단정하지 않는다.

## 4.2 실물 구조 · autopilot-note 흐름

이 절은 notes/ 트리의 실물 구조와 autopilot-note 가 산출물을 노트화하는 흐름을 다룬다.

**실물 구조** (`ls /home/nas/user/Uihyeop/notes/`, `notes/README.md`): `notes/cards/`(L1 카드 82장) · `notes/_layer2/`(backbones·tasks·papers·notes) · `notes/digests/`(다이제스트) · `notes/oncall/`(당직 보고) · `notes/_triage/`(triage 제안 큐). notes/ 는 Obsidian 호환 vault 로도 열 수 있으며, 본문 `[[wikilink]]` 가 그래프 edge 로 잡힌다 (`notes/README.md`).

**autopilot-note 흐름** (`worklog-board/.claude_reports/spec/prd.md §4.3`): 산출물이 들어오면 —

1. **Layer 2 note row 생성** — `_layer2/notes/<id>.md` (frontmatter card_id/backbone_ids/task_ids/paper_id/intent/work_status). 모든 trackable 산출물에 자동.
2. **note `card_id` → Layer 1 카드 연결** — 산출물 context·키워드가 기존 project/task 카드와 매칭(≥0.7)되면 자동. 연결의 1급 대상은 **task 카드**이고 project 직접 연결은 task 부재 시 보조다 (`prd.md` v43 — 프로젝트는 보통 task 의 `project` 필드에서 파생). 여러 카드에 걸치는 산출물은 최고 confidence 매칭이 주(`card_id`)가 되고 나머지는 `secondary_card_ids` 보조 제안으로 함께 실린다 — 보고·다이제스트의 단일 기준은 여전히 주 카드다 (`prd.md` v32).
3. **note `backbone_ids`/`task_ids` → Layer 2 카탈로그 연결** — 없으면 backbone/task 카탈로그가 새로 생겨난다. 자동.
4. **신규 Layer 1 카드 _제안_** — 매칭 카드가 없고 새 과제·작업 단위로 보이면 triage 제안(자동생성 X — L1 사용자 소유). 제안 기본 단위는 **task 카드**이며 source 노트를 함께 실어 승인 1번에 카드 생성+노트 연결이 끝난다 (`prd.md` v41). project 는 사용자 소유 생성 단위라 보조(세트 제안)다.
5. **매핑 모호 → `card_id: null` ambient note** — 어디에도 확신 없으면 ambient 로 두고 사후 승격한다.

규칙 — Layer 2 적재·연결은 자동, Layer 1 신설만 triage, 애매하면 ambient, 산출물 원본 불변 + idempotent(같은 source 두 번 들어와도 중복 X) (`prd.md §4.3`). 단 무인 cron 자동확정에는 드리프트 정정이 있다 — v22 계약은 무인 밤 실행을 confidence 무관 `inbox`(staging)로 두고 `confirmed` 승격은 오직 사용자 컨펌으로 한다 (아침 리뷰 큐가 비지 않도록) (`prd.md §4.3` v22 정정). 이는 진행 중 결정이므로 단정하지 않는다.

backbone 카탈로그에는 manifest 유지가 붙는다 — 본문이 빈 backbone 에 노트가 3건 이상 쌓이면 run 마다 정의·쓰임새 초안을 자동 작성하고(`manifest_status: draft`), 사용자가 확정한 본문은 직접 수정하지 않고 검토함 제안으로만 갱신하며, 계보(파생 사슬)는 항상 사용자 확정 영역이다 (`autopilot-note/SKILL.md` Stage D, prd v33).

노트 본문과 다이제스트는 사용자가 직접 읽는 산출물이라, light(매일 cron 기본) 이상에선 편집팀이 batch 1회 다듬는다 (`autopilot-note/SKILL.md` Stage D.5, 2026-06-11 신설) — 2.2 의 P3 편집팀 polish 와 같은 적용 자리며, frontmatter·링크·수치는 불변이다.

## 4.3 진행 줄 마커 · triage 운영

Layer 1 카드 본문의 `## 진행` 줄과 Layer 2 노트는 진행 줄 마커로 보고 가능 여부를 표시한다 (`worklog-board/.claude_reports/spec/prd.md §2.1`):

- `✓` = 보고 가능
- `-` = 내부 (보고 X)
- `×` = private (보고 절대 X)

마커는 autopilot-note 가 default 로 박고, 사용자가 _아침 triage_ 에서 한 글자 조정한다 (`prd.md §2.1`). 마크다운 그대로 사람이 읽을 수 있다. triage 운영은 `/triage` 의 daily review 에서 라우팅 제안(`routing_status: inbox`)을 승인/고치기/폐기로 보정해 `confirmed` 로 올리는 2단 구조다 — "에이전트 판단 + 사람 daily 보정" (`prd.md §4.3` v19). 신규 L1 카드 제안도 같은 `/triage` 에서 사용자 confirm 후 생성된다.

## 4.4 산출물 소통의 닫힘

worklog-board 의 2-layer 가 P8 산출물 소통 줄기의 종착점이다. 1부 P8 에서 원칙(amnesiac agent + durable filesystem)이 정의되고, 2부 2.3 에서 `.claude_reports` 통신 버스로 우리 세팅에 내려왔으며, 여기 4부에서 그 통신 버스에 쌓인 산출물을 사람이 다시 찾을 수 있게 정돈하는 worklog 2-layer 로 닫힌다.

줄기 전체의 갈무리는 cross-ref 로만 한다 — 원칙은 1부 P8, 우리 실물 매핑은 2부 2.3, 종착 정돈은 본 4부다. agent 가 amnesiac 이라는 P8 의 전제가 있는 한, filesystem 산출물은 단지 쌓이는 데 그치지 않고 _다시 읽힐 수 있게 정돈되어야_ 비로소 통신이 완성된다 — worklog-board 의 Layer 2 가 그 "다시 읽힘" 을 담당하는 마지막 층이다.

---

> **작성 메모**: 이 매뉴얼의 2~4부 anchor 는 2026-06-11 라이브 파일 스냅샷이다. `analysis_project/paper/`·`analysis_project/code/` 는 본 프로젝트에 없으며(research-only 도메인 — 정상), 2~4부는 라이브 파일 직접 Read 로 근거를 댔다. 1부 외부 원칙은 모두 `research/agent-engineering-principles/cards/` card 귀속이다. Harness-Bench 수치(76.2 / 52.4 / 23.8)는 Greyling 경유 2차 인용이므로 정밀 인용 시 arXiv 원문 대조를 권장한다.
