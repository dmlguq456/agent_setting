# Code / Ruleset Excerpts (Phase C)

실제 clone 한 소스에서 발췌한 메커니즘 핵심. 전체 clone 은 이 디렉토리 하위:
`JuliusBrussee_caveman/`, `DietrichGebert_ponytail/`, `wilpel_caveman-compression/`.

---

## 1. caveman (JuliusBrussee) — 출력 표면 압축 (system-prompt skill)

**메커니즘**: `skills/caveman/SKILL.md` 는 알고리즘이 아니라 **system-prompt 지시문**. 모델에게
"짧게 써라"를 규율로 강제. 입력·컨텍스트·thinking 토큰은 건드리지 않음(저자 명시).

핵심 규칙 (SKILL.md 발췌):
> Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging.
> Fragments OK. Short synonyms. No tool-call narration, no decorative tables/emoji.
> **Standard acronyms OK; never invent new abbreviations (cfg/impl/req/res/fn) — tokenizer
> split them same as full word: zero token saved, reader still decode.**
> No causal arrows (→) — own token, save nothing.

intensity: lite / full / ultra / wenyan-{lite,full,ultra}. wenyan = 문언문(classical Chinese)
극단 압축, 80-90% char 감축 주장.

**Auto-Clarity (self-monitoring 레버)**: 아래 조건에서 caveman 자동 해제 →
- Security warnings / irreversible action confirmations
- Multi-step sequences where fragment order risks misread
- Compression itself creates ambiguity (예: "migrate table drop column backup first")
- User asks to clarify

즉 caveman 자체가 **신호(위험·모호)→레버(압축 강도 off)** self-regulation 을 내장. 이게 하네스
설계에 가장 직접적인 참고점.

**저자 자기비판** (`docs/HONEST-NUMBERS.md`, 마케팅 아님):
- output reduction 65% avg (22-87%, n=10) — output 토큰 한정
- input reduction 0%, skill 이 **더하는** input 비용 ~1-1.5k tok/turn
- "session-level totals always smaller than output-reduction headline; independent
  session-level measurements land around **14-21% total** on output-heavy workloads,
  **below zero on terse ones**"
- net-negative 조건: terse coding Q&A(#145), per-request 과금 agent(Copilot, #506),
  일부 tool-side counter 역주행(#550, Cursor A/B 4.3M vs 1M)
- rule of thumb: normal reply >1.5-2k output tok → 절감, 그 이하 → 손해

---

## 2. ponytail (DietrichGebert) — 행동 억제 (작업량 축소, coding-task skill)

**메커니즘**: `skills/ponytail/SKILL.md`. 출력 문체가 아니라 **얼마나 코드를 쓸지**를 규율.
"lazy senior dev" decision ladder — 첫 번째로 성립하는 rung 에서 멈춤:

> 1. Does this need to exist at all? (YAGNI)
> 2. Already in this codebase? (reuse)
> 3. Stdlib does it?
> 4. Native platform feature covers it?
> 5. Already-installed dependency solves it?
> 6. Can it be one line?
> 7. Only then: minimum code that works.

레버: unrequested abstraction 금지, deletion>addition, shortest working diff, `ponytail:`
주석으로 의도적 simplification 표기. **safety rail**: input validation / error handling /
security / accessibility 는 절대 축소 금지 ("When NOT to be lazy" 섹션).

**신호→레버**: "Complex request? Ship lazy version + question it in same response" —
작업 복잡도(신호)→범위 축소+되묻기(레버).

**저자 자기검증** (`benchmarks/results/2026-06-17-cost-verification.md`):
- Claude: Haiku 63% / Sonnet 74.5% / Opus 42.3% cheaper (30 reps pooled). latency 3.1-5.8x.
- **OpenAI 에서 역전**: gpt-4.1-mini 39.6% cheaper 지만 **gpt-5.4-mini +26.2%, gpt-5.5 +38.7%
  more expensive** — "reasoning models: always-on ruleset(large input, extra reasoning tokens)
  outweighs shorter code". ← caveman HONEST-NUMBERS 의 재주입 오버헤드 비판을 다른 repo 벤치가 독립 재현.
- correctness 100% 유지 (baseline Sonnet 은 76%로 오히려 over-engineering bug 발생).

**caveman-vs-ponytail** (`benchmarks/results/2026-06-12-caveman-vs-ponytail.md`):
- ponytail 코드 라인 최소(caveman 대비 2.2x, baseline 대비 5.5x 적음)
- v1 은 총 토큰에서 caveman 에 ~4% 뒤짐 — "wrote minimal code, then long 'skipped on purpose'
  essays. Prose ate the code savings." → v2 output cap, v3 SKILL.md 압축으로 개선.
- **floor effect**: 이미 minimal 한 task(csv-sum) 은 두 skill 모두 baseline 대비 ~3k tok
  "skill-read tax" 지불. ← skill 재주입 비용의 직접 증거.

---

## 3. wilpel/caveman-compression — 입력/컨텍스트 알고리즘 압축 (system prompt 아님)

**메커니즘**: 실제 Python 파이프라인 3종 (`caveman_compress.py` LLM, `_nlp.py` spaCy,
`_mlm.py` RoBERTa). 텍스트를 caveman 스타일로 **입력 전 압축**.

`prompts/compression.txt` 발췌 (LLM 모드 rule):
> ALWAYS REMOVE: articles / auxiliary verbs / common prepositions when clear / pronouns when
> clear / pure intensifiers.
> ALWAYS KEEP: nouns / main verbs / meaningful adjectives / numbers+quantifiers / uncertainty
> qualifiers / critical prepositions / negations / technical terms.

`SPEC.md` 핵심 원리:
> "Remove only what LLMs can deterministically reconstruct. LLMs excel at predicting grammar,
> connectives, sentence structure. They cannot reliably predict facts, numbers, constraints.
> We compress the former, preserve the latter." (Sentence Atomicity, 2-5 word limit,
> connective elimination)

수치: LLM 40-58%, NLP 15-30%(offline <100ms, 15+ langs), MLM 20-30%. factual preservation
13/13(100%). **BUT** 이건 입력 압축 — CAVEWOMAN(2606.24083) 이 입력 압축은 net-loss(~1.15x)라
직접 반박하는 대상.
