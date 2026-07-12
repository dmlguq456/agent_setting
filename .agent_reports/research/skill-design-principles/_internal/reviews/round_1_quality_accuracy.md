# Round 1 — Quality/Accuracy Review (Deep Reviewer #2)

- **scope**: NO-FABRICATION / DISCLOSURE / INTERNAL-CONSISTENCY (세부 카드 verbatim 대조는 fact-checker 별도)
- **target**: 00~07 보고서 vs `analysis_summary.md` + `_internal/pocock-verbatim-comparison.md` + `cards/`
- **tier**: non-adversarial → confidence 표기·검증탈락 섹션 생략. 미검증 단정만 flag.
- **date**: 2026-07-13
- **verdict**: 🔴 1건 · 🟡 4건. fabrication 위험이 가장 큰 06 하네스 매핑은 실제 skill 파일과 대조해 **정확함을 확인**(아래 Positive). 유일한 🔴 는 새 수치 날조가 아니라 인용 수치의 *의미 재배치*(왜곡).

---

## 🔴 Findings

### 🔴-1. `~50%` auto-activation 수치의 의미가 소스와 어긋나게 재배치됨 (왜곡 + 하네스 정당화 과대)

- **소스**(`cards/scottspence-auto-activate.md` line 17): *"워크어라운드: UserPromptSubmit hook 으로 트리거 키워드 감지 → 강제 주입. **그래도 신뢰도 ~50%.**"* → `~50%` 는 **hook 워크어라운드를 적용한 뒤에도 남는** 신뢰도다. bare auto-activation 은 그보다 나쁘고, **hook 을 깔아도 ~50%** 라는 것이 소스의 핵심.
- **보고서**: 01(`model-invoked 자동발화 실전 신뢰도 ~50%`), 02(`auto-activation ~50% 이므로 wording 만 신뢰 X`), 03(`wording 매칭돼도 무시, ~50%`), 04 미해결과제(`auto-activation ~50% 실전 불안정 … hook 보강 없이는 신뢰 불가`), 05(`wording 만으론 ~50% 인 신뢰도를 끌어올리는 정당한 지출`) — 모두 `~50%` 를 **hook 없는 bare 신뢰도**로 프레이밍하고, hook(우리 harness 의 `mem-recall-inject`·`workflow-guard`)을 그 문제를 **해소**하는 레버로 제시한다(03 Takeaway: *"hook 강제 라우팅이 이 긴장의 정당한 해소책"*).
- **왜 문제인가**: (a) 소스 수치의 측정 대상(*hook 적용 후*)을 *hook 이전*으로 바꿔 인용 — 왜곡. (b) 소스는 오히려 *"hook 을 써도 ~50%"* 라 harness 의 hook 정당화를 **약화**시키는데, 보고서는 이를 정반대(hook 이 신뢰도를 회복)로 사용. (c) 우리 harness 의 hook 이 scottspence 의 키워드-hook 보다 신뢰도가 높다는 주장은 어디에도 측정 근거가 없는 **미검증 단정**.
- **권고**: `~50%` 는 *"hook 워크어라운드 적용 후에도 ~50%"* 로 정확히 귀속하고, "우리 deterministic UserPromptSubmit 주입은 scottspence 의 조건부 키워드-hook 과 성격이 달라 더 강할 *수 있으나 측정 미검증*" 으로 hedge. 하네스 정당화를 소스가 실제로 지지하는 선(=wording 단독은 불충분하다는 방향)까지만 축소.

---

## 🟡 Findings

### 🟡-2. `post-it` 을 "user-invoked 명확"으로 단정 — frontmatter 기준 미충족 (invocation 판정 일관성)

- 06 §2 는 `post-it` 을 *"user-invoked 명확 — sub-action CLI 형태, ceremony 불필요"* 로 분류하고 "4축 정합의 모범"으로 세움.
- 그러나 실제 `~/.claude/skills/post-it/SKILL.md` frontmatter 에는 `disable-model-invocation: true` 가 **없다**. 보고서가 채택한 원문 기준(user-invoked = `disable-model-invocation: true` = zero context load, 02_standards 표)대로면 post-it 은 flag 부재 → **default model-invoked**(description 상주 = context load 지불)이며, 같은 §2 표가 `autopilot-research` 에 대해선 바로 이 기준으로 *"frontmatter invocation 분류 불명"* gap 을 매겼다. 동일 기준의 비대칭 적용.
- 기능적으로 `/post-it` 슬래시 호출로만 변경된다는 점은 방어 가능하나, "명확"이라는 단정은 frontmatter 로 뒷받침되지 않음. → *"invocation 은 실사용상 user-driven 이나 frontmatter 에 disable flag 부재 — 원문 기준상 model-invoked default"* 로 정정 권고.

### 🟡-3. failure-mode "종 수"가 파일 간 불일치 (4 / 5 / 6 / 7 드리프트)

- `pocock-verbatim-comparison.md` §3: 6개 열거(premature completion / duplication / sediment / sprawl / no-op / **negation**, variance bug 제외).
- `02_standards.md` §2 표: **7행**(premature·negation·sprawl·**variance bug**·duplication·sediment·no-op) 인데 같은 절 Takeaway 는 *"6종을 한 체크리스트로"*.
- `analysis_summary.md` §7.2: *"no-op·sediment·duplication·sprawl 6종 진단?"* — 이름은 **4개**만 나열하며 "6종" 이라 표기.
- Remio "5-test"(premature/duplication/sediment/sprawl/no-op = 5)도 병기.
- 모두 실재하는 mode 라 날조는 아니나, **variance bug 를 셈에 넣는지**가 파일마다 갈리고 "6종" 라벨과 열거 개수가 어긋난다. → membership 을 한 곳(예: verbatim-comparison 의 6)으로 고정하고 나머지를 그에 맞추거나, "축별 분산 배치 · Remio 5-test 요약" 관계를 명시.

### 🟡-4. 00 의 "유도(Guidance)=StartupHub 라벨 국문화" 문구가 계보를 뭉갬

- 00 Level 0/1: *"사용자 요약의 '유도(Guidance)'는 커뮤니티(StartupHub) 라벨을 국문화한 것으로 canonical 용어는 Steering"*.
- 그러나 StartupHub 의 3번째 축 **라벨은 "Steering"**(verbatim-comparison §2 근거 3: *"Steering: How the skill is guided…"*). "유도/Guidance" 는 StartupHub 의 *라벨* 이 아니라 그 *정의문("guided to…")* 을 옮긴 것 — 이 뉘앙스는 01·verbatim 이 정확히 서술한다. 00 의 압축 표현은 "StartupHub 가 라벨을 Guidance 로 불렀다"는 오해를 유발할 수 있음. → *"4-set(트리거/구조/유도/가지치기)이 StartupHub 국문화 계보이고, '유도' 는 Steering 정의문의 번역"* 으로 소폭 정정.

### 🟡-5. (fact-checker 인계) 인용부호 안 문구·예시어의 소스 귀속 확인 필요

- Steering 정의가 04 ③(a)·analysis_summary §4(a) 에서 *"the levers that shape the agent's runtime behaviour toward Predictability."* 로 **인용부호**와 함께 제시되나, GLOSSARY verbatim 은 *"how the agent's runtime behaviour is shaped"* (`cards/writing-great-skills-glossary.md`). 전자는 paraphrase 를 quote 로 감싼 형태 — 인용부호 제거 또는 원문 verbatim 으로 교체 권고.
- leading-word 예시어 **"fog of war"**(analysis_summary §4b·00·04)가 내가 확인한 glossary/tdd 카드엔 없음. 다른 카드(prototype/code-review 등)에 실재하는지, 아니면 삽입된 예시인지 verbatim 확인 필요. (card-level 대조는 fact-checker 소관 — 여기선 미검증 인용으로만 표시.)

---

## Positive (확인된 강점 — 유지)

- **06 하네스 매핑 = 날조 아님 (핵심 우려 해소).** 실제 skill 파일 대조 결과: `autopilot-research` 는 `## Required Reads`·`## Reference Map` 존재 + `references/` **정확히 4파일**(invocation-and-modes / pipeline-search-analysis / report-generation / summary-and-briefing) 1-depth — 06 §1·05 §1 서술과 일치. `post-it` 인용(*"본 SKILL.md 는 라우터"*, *"fire-and-forget"*, *"사용자는 들여다보지 않는다"*, *"영구 진실은 산출물"*) 전부 SKILL.md verbatim 과 부합. `autopilot-code` 도 실재. 06 §2 의 우리-스킬 판정은 대부분 `?` 로 hedge 되어 있어 단정 회피(예외 = 🟡-2 post-it).
- **가공 예시 disclosure 규율 양호.** 06 §3 intro 가 *"예시는 원칙 설명용 가공 예시"* 를 선언하고, 모든 Before/After 에 `(가공)` 라벨. tdd 실물 차용분은 *"(tdd 실물 leading word 차용, 출처: tdd-skill-example)"* 로 출처 표기.
- **Guidance↔Steering 라벨 왜곡 없음.** canonical=Steering 확정, 병기 *"Steering(유도)"* 일관, "유도는 Steering 뜻풀이" 뉘앙스가 01·verbatim 에 정확. (00 만 소폭 압축 — 🟡-4.)
- **사용자 요약 오해 재생산 없음.** 3-rung(≠2계층), "설명 배제"=Pruning 소관, CONTEXT.md 용어집=4원칙 밖 — 세 교정이 00/01/04 에 반영되고 오해를 되풀이하지 않음.
- **개념 정의 cross-file 상충 없음** (수치 이슈 제외). "post-completion steps 숨기기 = 실제 context 경계(subagent/user hand-off)에서만 효과, 인라인 model-invoked 는 무효" 단서가 analysis_summary §4·02 §2·04 ③·05 §4 에 일관 유지. 4축 라벨(Invocation/Information Hierarchy/Steering/Pruning)도 전 파일 일치.
