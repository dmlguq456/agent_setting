# ContextBudget — Budget-Aware Context Management (arXiv 2604.01664)

**Type**: paper
**URL**: https://arxiv.org/abs/2604.01664
**분류축1 (메커니즘)**: budget-directive-self-monitoring (+ input-context-reduction 을 정책으로 조절)
**절감 claim**: high-complexity 세팅에서 강 baseline 대비 >1.6x 성능 gain (budget 축소 시 우위 유지)
**실측/검증**: 논문 자체 실험 (BACM-RL, curriculum RL). budget 이 줄수록 경쟁 방법은 성능 급락, 본 방법은 우위 유지.
**신호->레버 매핑**: **명시적** — 신호=잔여 context budget, 레버=언제/얼마나 interaction history 를
압축할지. "assess available budget before incorporating new observations." RL 로 정책 학습.
**하네스 시사점**: token self-regulation 을 **정적 rule(caveman/ponytail)이 아니라 예산-제약 sequential
decision** 으로 formalize 한 핵심 참고. 하네스의 "잔여 budget → 레버 조절" 축을 정책 문제로 볼 근거.

## Summary
context-window 관리를 **budget-constrained sequential decision problem** 으로 정식화. caveman/
ponytail 의 정적 prompt-rule 접근과 대비되는, self-regulation 의 정책적(policy) 틀.

핵심: 에이전트가 새 관찰을 넣기 전에 **잔여 budget 을 평가**하고, 그에 맞춰 history 압축의 시점·정도를
동적으로 결정. curriculum 기반 RL(BACM-RL)로 다양한 budget 제약에서 압축 정책을 학습. budget 이 빡빡할수록
baseline 대비 우위가 커진다(>1.6x, high-complexity).

axis 3(self-regulation 일반화)의 신호→레버 매핑을 가장 깨끗하게 제공: **신호 = 잔여 context 용량,
레버 = history 압축 강도**. 하네스가 token-budget 축을 설계할 때, 고정 임계값이 아니라 잔여 예산에
적응하는 정책으로 볼 수 있음을 시사.

**Figures**: (none extracted)
