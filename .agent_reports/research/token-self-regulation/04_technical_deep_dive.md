# 04 — Algorithm·Mechanism Deep Dive

> 관련: [03_vendor_comparison.md](03_vendor_comparison.md) · [05_deployment.md](05_deployment.md)
>
> 주요 3종(caveman·ponytail·wilpel)은 실제 clone·소스 열람(`code_resources/EXCERPTS.md`)이 1차 근거. 보조로 ContextBudget·Active Context Compression 의 정책 메커니즘.

---

## 테마 1 — caveman: system-prompt 지시문 (알고리즘 아님)

**핵심**: caveman 은 압축 **알고리즘이 아니라 프롬프트 규율**이다. `skills/caveman/SKILL.md`(약 5KB)가 매 turn 재주입되어 모델에게 "smart caveman 처럼 짧게 써라"를 강제한다. 입력·컨텍스트·thinking 토큰은 건드리지 않고 **출력 표면만** 줄인다(저자 명시).

drop 규칙 (SKILL.md 발췌):
- 관사(a/an/the), filler(just/really/basically), pleasantry, hedging 제거
- fragment 허용, 짧은 동의어, tool-call narration·장식 table·emoji 금지
- **causal arrow(→) 금지** — 자체 토큰이라 절감 없음

**토큰화 정확성 (이례적)**: SKILL.md 는 **invented abbreviation(cfg/impl/req/res/fn)을 명시 금지**한다. 이유 — tokenizer 가 이런 약자를 완전한 단어와 **동일하게 분할**하기 때문에 절감이 0 이고, 오히려 읽는 쪽·모델의 디코딩 비용만 든다. "standard acronym 은 OK, 새 약자 발명은 금지." 이는 대부분의 순진한 압축 도구가 놓치는, tokenizer 동작에 대한 드문 정확성이다.

**intensity 축**: lite / full / ultra / wenyan-{lite,full,ultra}. wenyan = 문언문(classical Chinese) 극단 압축, 80-90% char 감축 주장.

**Auto-Clarity (self-monitoring 레버)** — caveman 이 자동 해제되는 조건:
- Security warnings / irreversible action confirmations
- Multi-step sequences where fragment order risks misread
- Compression itself creates ambiguity (예: "migrate table drop column backup first")
- User asks to clarify

즉 caveman 자체가 **신호(위험·모호)→레버(압축 강도 off)** self-regulation 을 내장한다. 이것이 하네스 설계에 가장 직접적인 참고점이다.

**Takeaway**: caveman 의 가치는 65% 헤드라인이 아니라 (1) tokenizer 정확성(invented abbreviation 금지) (2) Auto-Clarity if-then 패턴이다. 후자는 우리 token-budget 축의 "위험→레버 off" 배선의 직접 모델이다.

---

## 테마 2 — ponytail: 7-rung decision ladder (행동 억제)

**핵심**: 출력 문체가 아니라 **얼마나 코드를 쓸지**를 규율. "lazy senior dev" decision ladder — 첫 번째로 성립하는 rung 에서 멈춘다:

```
1. Does this need to exist at all?   (YAGNI)
2. Already in this codebase?          (reuse)
3. Stdlib does it?
4. Native platform feature covers it?
5. Already-installed dependency solves it?
6. Can it be one line?
7. Only then: minimum code that works.
```

레버: unrequested abstraction 금지, deletion > addition, shortest working diff, `ponytail:` 주석으로 의도적 simplification 표기.

**safety rail (불가침)**: "When NOT to be lazy" 섹션 — input validation / error handling(데이터 손실 방지) / security / accessibility / 명시 요청은 **절대 축소 금지**. 저자의 핵심 문장: *"Never lazy about understanding the problem. The ladder shortens the solution, never the reading."* 억제 레버가 이해·검증을 훼손하지 않게 하는 명시적 경계다.

**신호→레버**: "Complex request? Ship lazy version + question it in same response" — 작업 복잡도(신호)→범위 축소+되묻기(레버).

**Takeaway**: ladder 의 rung1(necessity, "존재해야 하나")은 사실 **중요도(intensity) 판단**이고, "shortest diff"는 **예산(budget) 판단**이다. 한 skill 안에 두 축이 섞여 있다 — 하네스는 이 둘을 분리해야 한다([05](05_deployment.md) 간섭 지점). safety rail 불가침은 두 축 공통 불변식.

---

## 테마 3 — wilpel: 결정론/LLM 하이브리드 입력 압축

**핵심**: JuliusBrussee/caveman 과 브랜딩만 공유, 실체는 완전히 다른 **Python 알고리즘 파이프라인**. 텍스트를 LLM 입력 전에 caveman 스타일로 압축한다. 3모드:
- `caveman_compress.py` — LLM (OpenAI API, ~2s/req), 40-58%
- `_nlp.py` — spaCy rule-based (offline <100ms, 15+ langs), 15-30%
- `_mlm.py` — RoBERTa masked-LM (1-5s), 20-30%

`prompts/compression.txt` (LLM 모드 rule):
- **ALWAYS REMOVE**: articles / auxiliary verbs / common prepositions when clear / pronouns when clear / pure intensifiers
- **ALWAYS KEEP**: nouns / main verbs / meaningful adjectives / numbers+quantifiers / uncertainty qualifiers / critical prepositions / negations / technical terms

`SPEC.md` 핵심 원리:
> "Remove only what LLMs can deterministically reconstruct. LLMs excel at predicting grammar, connectives, sentence structure. They cannot reliably predict facts, numbers, constraints. We compress the former, preserve the latter."

Sentence Atomicity(문장당 1 원자), 2-5 word limit, connective elimination.

**반증 (균형 서술)**: 저자는 factual preservation 13/13(100%)와 "without losing meaning"(Peltomäki Medium 제목)을 주장한다. 그러나 이 방향(입력 압축)은 **CAVEWOMAN(2606.24083)이 정면 반박**한다 — 입력 압축은 strict lose-lose 로 순비용 ~1.15x(최악 1.8x) 상승, 비추론 모델에서 생성물의 ~절반만 정확하고, 나머지는 length-control 후에도 의미 괴리. 메커니즘: 모델이 불명확·압축된 입력을 **더 긴 응답으로 보상**하면서 정확도까지 잃는 이중 손실. "LLM 이 결정론적 복원 가능한 것만 제거한다"는 전제 자체가 실험적으로 깨진 것.

**Takeaway**: wilpel 의 설계 원리는 정교하지만("복원 가능한 것만 제거"), 그 전제가 CAVEWOMAN 에 의해 반증됐다. 입력 압축은 저장 토큰을 줄여도 세션 순비용을 올릴 수 있다 — 하네스는 입력 압축을 "무손실"로 가정하지 않는다.

---

## 테마 4 — 정책적 self-regulation: ContextBudget & Active Context Compression

**ContextBudget (2604.01664)** — context-window 관리를 **budget-constrained sequential decision problem** 으로 정식화. 에이전트가 새 관찰을 넣기 전에 잔여 budget 을 평가하고("assess available budget before incorporating new observations"), 그에 맞춰 history 압축의 시점·정도를 동적으로 결정. curriculum RL(BACM-RL)로 다양한 budget 제약에서 압축 정책을 학습. budget 이 빡빡할수록 baseline 대비 우위가 커진다(>1.6x, high-complexity). **신호=잔여 budget, 레버=history 압축 강도**를 가장 깨끗하게 제공.

**Active Context Compression (2601.07190, "Focus")** — 외부 도구가 강제하는 압축이 아니라, capable 모델이 압축 도구+적절한 prompting 을 받으면 **스스로** 컨텍스트를 self-regulate. Knowledge block 으로 핵심 통합 + raw history 능동 prune. task 당 평균 6.0회 자율 압축, 전체 22.7%(14.9M→11.5M), 정확도 유지. 단 압축 trigger 신호는 명시적 임계값보다 "aggressive prompting" 기반 — 정량 정책은 불명확.

**Takeaway**: self-regulation 의 정식화는 **정적 rule(caveman·ponytail) → prompt-driven 자율(Active Context Compression) → RL 정책(ContextBudget)** 스펙트럼. 하네스는 RL 까지 안 가도, 잔여 budget 을 명시 신호로 삼는 방향(ContextBudget)을 지향하되 1단계로는 caveman Auto-Clarity 식 if-then 을 예산축으로 확장하는 게 현실적이다.

---

## 성능 Trade-off 종합

| trade-off | 메커니즘 | 근거 |
|---|---|---|
| **세션 희석** | output-only 절감이 input(프롬프트·컨텍스트·파일·주입 rule)에 압도됨 | caveman 65%→14-21% (HONEST-NUMBERS) |
| **재주입 오버헤드** | skill 자체가 매 turn input 추가; reasoning model 에서 역전 | caveman ~1.5k/turn; ponytail OpenAI +26~39% |
| **skill-read tax** | 이미 minimal 한 task(csv-sum)는 두 skill 모두 baseline 대비 ~3k tok | caveman-vs-ponytail 벤치 (floor effect) |
| **풍선 효과** | ponytail v1 "skipped on purpose" 산문이 코드 절감을 먹어 caveman 에 4% 뒤짐 | 억제 레버가 다른 표면에서 비용 되돌림 |
| **부호 반전** | 입력 압축이 출력 보상·품질 손실로 순손실 | CAVEWOMAN input ~1.15x |

**Takeaway**: 모든 레버는 자기 비용(재주입·skill-read tax)을 가지며, 한 표면에서 아낀 토큰이 다른 표면(출력 보상·산문)에서 되돌아올 수 있다(풍선 효과). token-budget 축은 반드시 **자기 자신의 비용도 회계**에 넣어야 한다 — 이것이 SkillReducer(skill 정의 다이어트)가 필요한 이유이자, [05](05_deployment.md)·[06](06_implementation.md) 설계의 핵심 제약이다.
