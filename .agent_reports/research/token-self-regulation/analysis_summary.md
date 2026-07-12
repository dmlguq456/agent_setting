# Analysis Summary — Token Self-Regulation (caveman·ponytail 생태계)

**mode**: technology
**phase flags**: `chaining_available: false`, `code_search_available: true`
**발견물**: 25 sources → 22 cards (일부 카탈로그 mirror·secondary blog 병합). primary 3종(caveman·
ponytail·wilpel)은 실제 clone·소스 열람(Phase C, `code_resources/` + `EXCERPTS.md`).

핵심 대상: **JuliusBrussee/caveman**(출력 산문 압축, output 65% 절감 주장이나 세션 전체 4-21%),
**DietrichGebert/ponytail**(lazy senior dev decision ladder 로 코드 작성량 억제). 보조 생태계:
wilpel/caveman-compression(알고리즘 입력 압축), headroom/RTK·TokenSave·claw-compactor(도구출력·컨텍스트
압축), token-optimizer(self-audit skill). 학술 반증축: CAVEWOMAN·codepointer(실사용 3.7%).

---

## 1. 메커니즘 분류

발견물을 4계층으로 태깅. 핵심 발견: **"토큰 절감"은 단일 현상이 아니라 서로 다른 표면·부호를 가진
4개 레버**이고, 이들을 뭉뚱그리면 axis 2 의 과대평가가 발생한다.

| 계층 | 정의 | 대표 발견물 | 조절 대상 |
|---|---|---|---|
| **A. output-compression** | 모델이 짧게 답하게(문체) | caveman(JuliusBrussee), Hackenberger stack 의 Caveman Mode | 생성 출력 표면 |
| **B. behavior-suppression** | 얼마나 일할지/코드를 쓸지 억제 | ponytail | 작업 범위·산출물량 |
| **C. input-context-reduction** | 입력·컨텍스트·도구출력을 LLM 도달 전 압축 | wilpel/caveman-compression, headroom/RTK, tokensave, claw-compactor | 입력 페이로드 |
| **D. budget-directive-self-monitoring** | 예산·위험 신호로 스스로 조절/감사 | caveman Auto-Clarity, token-optimizer, ContextBudget, Active Context Compression | 정책·자기감사 |

**계층 간 부호 비대칭 (가장 중요)**: CAVEWOMAN(2606.24083)이 A와 C의 부호가 반대임을 실측 —
A(output)는 1.4-2.4x 비용 절감, **C(input)는 strict lose-lose 로 순비용 ~1.15x 상승**. 즉 caveman
브랜드를 공유하는 두 프로젝트(JuliusBrussee=A, wilpel=C)가 정반대 효과를 낸다.

**코드로 확인된 메커니즘 실체**(Phase C):
- caveman = **system-prompt 지시문**(알고리즘 아님). SKILL.md 5KB 가 매 turn 재주입. ultra 모드는
  "invented abbreviation(cfg/impl)은 tokenizer 가 full word 와 동일 분할 → 절감 0" 이라 명시 금지 —
  토큰화 메커니즘에 대한 이례적 정확성.
- ponytail = **7-rung decision ladder**(YAGNI→reuse→stdlib→native→existing-dep→one-liner→minimal).
  safety(validation/security/a11y) 불가침. "the ladder shortens the solution, never the reading."
- wilpel = **결정론/LLM 하이브리드 알고리즘**. SPEC 원리: "LLM 이 결정론적으로 복원 가능한 것(문법·
  connective)만 제거, 사실·숫자·제약은 보존."

대부분 발견물은 복수 계층. caveman 은 A(주)+D(Auto-Clarity). token-optimizer 는 D(주)+C.

---

## 2. 실측 절감과 한계

핵심 결론: **광고 수치(60-90%)와 세션 실절감(3.7-21%) 사이에 큰 gap 이 있고, 이 gap 은 도구 저자
스스로·독립 replay·학술 논문 3중으로 교차 검증된다.** output-only 절감의 세션 희석, skill 재주입
오버헤드, 입력 압축의 순손실이 세 축의 한계다.

### (a) output-only 절감의 세션 전체 희석
- caveman 광고 output 65% → 저자 HONEST-NUMBERS: session-level **14-21%**(output-heavy),
  terse workload **net-negative**. 이유: input(프롬프트·컨텍스트·파일·주입 rule)이 agentic coding
  에서 output 을 압도.
- **codepointer 독립 replay(500 실세션·2,182 세션·614M tok·$926 baseline): rtk+headroom+caveman
  합산 실절감 3.7%.** 3중 gap — ① denominator mismatch(per-payload % vs 세션 전체 청구), ②
  workload mismatch(도구는 synthetic/repetitive 에서만 잘 압축, 실 트래픽 비중 작음), ③ pricing
  structure(압축분은 싼 cache_read 로, 청구는 cache_create 42%·output 29%가 지배 → 도구 미접촉).

### (b) 재주입 오버헤드 (skill 자체 input 비용)
- caveman: skill 이 매 turn **~1-1.5k input tok 추가**. normal reply <1.5-2k output tok 이면
  net-negative(#145 사용자 실측).
- **ponytail 저자 자체 벤치가 이를 독립 재현**: Claude 는 42-75% cheaper 지만 **OpenAI reasoning
  model 에서 역전 — gpt-5.4-mini +26%, gpt-5.5 +39% more expensive**. always-on ruleset(큰 input
  + 추가 reasoning token)이 짧아진 코드보다 큼.
- caveman-vs-ponytail 벤치: minimal task(csv-sum)는 두 skill 모두 baseline 대비 **~3k "skill-read
  tax"**. ponytail v1 은 "skipped on purpose" 산문이 코드 절감을 먹어 caveman 에 4% 뒤짐 → 억제
  레버가 다른 표면에서 비용을 되돌릴 수 있음(풍선 효과).
- 해법 방향: **SkillReducer(2603.29919)** — skill 정의 자체를 압축(desc 48%·body 39%)하면 재주입
  비용↓, 게다가 기능 품질 +2.8%("less is more", 비필수 내용이 context 를 distract). progressive
  disclosure 로 essential/supplement 분리.

### (c) 품질 회귀 / adversarial safety 주장 검증
- wilpel/caveman-compression: factual 13/13(100%) 보존 주장. **그러나 CAVEWOMAN 반증** — 입력 압축
  생성의 ~절반만 technically correct, 나머지는 baseline 과 의미 divergence(length-control 후에도
  잔존). "without losing meaning"(Peltomäki Medium 제목)의 반례.
- ponytail: correctness 100% 유지(오히려 baseline Sonnet 이 76%로 over-engineering bug) — **행동
  억제(B)는 품질 안전, 입력 압축(C)은 품질 위험** 이라는 계층별 차이.
- 지표 혼동 경계: "54% less code"(pasqualepillitteri)는 코드 라인, "42-75% cheaper"(repo)는 비용,
  "65%"(caveman)는 output 토큰 — 서로 다른 지표를 headline 이 뭉갠다.

**검증 신뢰도 계층**: 저자 자기비판(caveman HONEST-NUMBERS, ponytail cost-verification) > 독립 replay
(codepointer) > 학술(CAVEWOMAN, SkillReducer) 모두 **같은 방향**(세션 효과는 광고보다 훨씬 작고, 입력
압축은 순손실 가능)으로 수렴 → 결론의 강건성 높음. 미검증: headroom 58.7k star, ponytail 74k star,
claw-compactor 97%, tokensave 60-80% — 모두 self-reported/secondary.

---

## 3. Self-Regulation 일반화

발견물에서 **신호 → 레버** 매핑을 추출. self-regulation 을 "어떤 신호로 어떤 레버를 조절하는가"의
2차원 공간으로 일반화하면, 기존 도구들은 이 공간의 부분집합만 커버한다.

### 신호 축 (무엇을 감지하는가)
- **위험/모호** (caveman Auto-Clarity): security warning·irreversible action·multi-step 순서 모호
- **작업 가치/필요성** (ponytail rung1 YAGNI): speculative need 인가
- **잔여 context budget** (ContextBudget): 새 관찰 넣기 전 예산 평가
- **컨텍스트 압박/누적** (Active Context Compression): history 가 쌓임
- **소비자 유형** (caveman-skillsllm blog): 사람 vs 에이전트가 출력을 읽는가
- **낭비 신호** (token-optimizer): bloated config·stale memory·model misrouting

### 레버 축 (무엇을 조절하는가)
- **출력 스타일** (caveman intensity lite/full/ultra/wenyan)
- **작업 범위** (ponytail ladder rung 선택, 되묻기)
- **도구 호출/탐색 방식** (tokensave 심볼 질의, headroom 도구출력 압축)
- **입력/컨텍스트 압축 강도** (wilpel 3모드, ContextBudget history 압축률)
- **자기 감사·정리** (token-optimizer audit, Active Context Compression prune)

### 추출된 신호→레버 매핑 (발견물별)
| 발견물 | 신호 | 레버 | 정책화 수준 |
|---|---|---|---|
| caveman Auto-Clarity | 위험·모호 | 출력 압축 강도 off | 정적 rule(if-then) |
| ponytail | 작업 필요성·복잡도 | 작업 범위 축소·되묻기 | 정적 ladder(reflex) |
| Active Context Compression | 컨텍스트 누적(prompt-driven) | history prune + Knowledge block | 자율(prompt 유도) |
| **ContextBudget** | **잔여 budget** | **history 압축 시점·정도** | **RL 정책(가장 정식화)** |
| token-optimizer | 낭비 audit 신호 | config/memory/routing 정리 | audit rule |

**스펙트럼**: 정적 rule(caveman·ponytail) → prompt-driven 자율(Active Context Compression) → RL 정책
(ContextBudget). caveman/ponytail 은 신호 감지가 얕고(문맥 heuristic) 레버가 고정. ContextBudget 은
잔여 예산을 명시 신호로 삼아 레버를 동적 최적화 → **하네스가 지향할 정식화 방향**.

**핵심 일반화**: 기존 skill 들은 대부분 "신호=암묵적 문맥 판단, 레버=단일 표면(출력 or 코드), 항상 on"
이다. 진짜 self-regulation 은 **잔여 budget·작업 가치를 명시 신호로 측정 → 여러 레버(출력·범위·도구·
압축) 중 상황에 맞는 것을 선택적으로** 조절하는 것. 이 축이 report stage 의 설계 제안 골격.

---

## 4. 하네스 시사점 (초안)

우리 하네스의 **intensity 축**(난이도·중요도 파생 — CONVENTIONS §1.1)과 독립인 **token-budget
자기조절 축**을 설계할 때의 입력.

### (a) 두 축의 직교성
- **intensity 축** = "이 작업이 얼마나 어렵고 중요한가" → 검증 rigor·모델 tier·분사 깊이를 **올리는**
  방향. 신호=난이도·stakes.
- **token-budget 축** = "지금 얼마나 아껴야 하는가" → 출력·범위·도구·압축을 **줄이는** 방향.
  신호=잔여 예산·컨텍스트 압박·세션 누적 비용.
- 두 축은 **원칙적으로 직교**: 어렵고 중요한 작업(high intensity)을 예산이 빠듯한 상황(tight budget)
  에서 수행할 수 있다. intensity 를 낮춰 예산을 아끼는 건 축의 혼동(품질 희생).

### (b) 간섭 지점 (직교가 깨지는 자리) — ponytail 이 코드로 예시
1. **ladder rung1(necessity)은 사실 intensity 판단**: "이 작업이 필요한가"는 중요도 축에 가깝다.
   token-budget 레버로 오해하면 중요한 작업을 예산 이유로 skip 하는 오류.
2. **"shortest diff"는 token-budget 판단**: 같은 작업을 더 적은 토큰으로. 이건 순수 예산 축.
   → 하나의 skill(ponytail) 안에 두 축이 섞여 있음. 하네스는 이 둘을 **분리**해야 함.
3. **safety rail 은 어느 축에서도 불가침**: caveman(security warning 시 압축 off)·ponytail
   (validation/security/a11y 축소 금지) 모두 명시. **token-budget 이 아무리 tight 해도 검증·안전은
   레버 대상 아님** — 이걸 불변식으로.

### (c) 설계 원칙 (발견물에서 도출)
- **레버 우선순위**: output-compression(A, 안전·세션효과 작음) 우선, input-context-reduction(C,
  순손실 위험)은 default off. CAVEWOMAN 의 부호 비대칭을 불변식으로.
- **신호는 세션 전체 기준**: codepointer 교훈 — per-payload % 가 아니라 세션 청구액/잔여 예산을 신호로.
  압축 레버의 목표를 세션 denominator 로 환산해 평가.
- **재주입 오버헤드 회계**: skill/규율을 추가하면 그 자체가 input 비용(caveman ~1.5k/turn). token-budget
  축은 자기 자신의 비용도 계상(SkillReducer 로 규율 정의를 다이어트, progressive disclosure).
- **정적 rule 보다 예산-적응 정책**: ContextBudget 처럼 잔여 예산을 명시 신호로 삼아 레버를 동적 조절.
  단 RL 까지 안 가도, caveman Auto-Clarity 식 if-then(위험→off)을 예산 축으로 확장(예산 tight→출력
  간결·탐색 심볼질의·분사 억제)하는 게 현실적 1단계.
- **자기 감사 레버 포함**: token-optimizer 처럼 config·memory·라우팅의 정적 낭비를 audit(우리 audit
  skill·mem consolidation 과 연결). 런타임 압축만이 아니라 구조적 최적화도 token-budget 축의 일부.

### (d) report stage 로 넘길 열린 질문
- token-budget 축의 신호를 어떻게 측정·노출할 것인가(잔여 컨텍스트 %? 세션 누적 비용? 둘 다?).
- intensity 와 token-budget 이 충돌할 때(high intensity + tight budget) 우선순위 규칙.
- caveman Auto-Clarity 의 if-then 을 우리 skill 계층에 어떻게 이식할 것인가(레버는 있으나 신호 배선 필요).
