# Active Context Compression — 자율 memory 관리 "Focus" (arXiv 2601.07190)

**Type**: paper
**URL**: https://arxiv.org/abs/2601.07190
**분류축1 (메커니즘)**: budget-directive-self-monitoring (자율 self-regulation) + input-context-reduction
**절감 claim**: 22.7% overall(14.9M→11.5M), 개별 인스턴스 최대 57%, task 당 평균 6.0회 자율 압축
**실측/검증**: 논문 실험. 정확도 유지(3/5=60% 양쪽 동일). 단, 압축 trigger 신호는 abstract 상 명시적
임계값보다 "aggressive prompting" 기반 — 정량 임계 정책은 불명확.
**신호->레버 매핑**: 부분적 — capable model 은 compression 도구+prompting 주어지면 **스스로** 압축
시점을 결정(task 당 6회). 명시 신호(용량 임계)보다 prompt-driven. 레버=Knowledge block 통합 + raw
history prune.
**하네스 시사점**: 외부 도구가 강제하는 압축(caveman/ponytail/headroom) 대신, **모델 자율 self-regulation**
이 가능함을 보임 — 하네스가 레버를 노출하고 유도 prompt 만 주면 모델이 스스로 조절. axis 3·4 의 "self"
쪽 근거.

## Summary
"Focus" 시스템. 외부 도구가 강제하는 압축이 아니라, **capable 모델이 압축 도구+적절한 prompting 을
받으면 스스로 컨텍스트를 self-regulate** 함을 보인 학술 프레이밍. caveman/ponytail(외부 규율) vs
자율 조절의 대비축.

메커니즘: 핵심 학습을 persistent "Knowledge" block 으로 통합하고 raw interaction history 를 능동적으로
prune(withdraw). task 당 평균 6.0회 자율 압축, 개별 인스턴스 최대 57% 절감, 전체 22.7%, 정확도 유지.

한계(WebFetch 확인): 압축을 촉발하는 정확한 신호(용량 임계인지 오류 누적인지)는 논문이 명시하지 않고
"frequent compression 을 장려하는 aggressive prompting" 기반 — 즉 신호→레버가 정책화됐다기보다
prompt-driven. ContextBudget(2604.01664)가 이를 RL 정책으로 정식화한 것과 대비. axis 3 에서 이 둘을
"prompt-driven 자율 vs RL 정책" 스펙트럼으로 배치.

**Figures**: (none extracted)
