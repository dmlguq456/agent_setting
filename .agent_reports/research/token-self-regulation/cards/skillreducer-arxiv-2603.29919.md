# SkillReducer — LLM agent skill 을 token 효율로 압축 (arXiv 2603.29919)

**Type**: paper
**URL**: https://arxiv.org/abs/2603.29919
**분류축1 (메커니즘)**: input-context-reduction (skill 정의 압축 = 정적 컨텍스트 절감)
**절감 claim**: skill description 48% mean 압축, body 39% 압축. compressed skill 이 원본 대비 기능
품질 +2.8%.
**실측/검증**: 논문 실험 — 600 skills + SkillsBench. transferability 0.965 retention(5 model, 4 family).
**신호->레버 매핑**: 명시적 동적 신호 없음(설계-시 정적 압축). "less is more" — 비필수 내용이 context
window 를 distract 하므로 제거하면 품질↑.
**하네스 시사점**: caveman/ponytail SKILL.md 의 **재주입 오버헤드 문제를 근본에서 줄이는 방향** — skill
정의 자체를 압축하면 매 turn input 비용이 준다. progressive disclosure(essential rule vs on-demand
supplement 분리)는 하네스 skill 설계에 직접 적용 가능.

## Summary
token-saving 을 "출력/입력 압축"이 아니라 **skill 정의 자체의 다이어트** 로 접근한 학술 방법. caveman
HONEST-NUMBERS 가 지적한 "skill 이 매 turn ~1-1.5k input 추가" 문제의 정면 해법.

방법: (1) routing 최적화 — verbose description 압축 + adversarial delta debugging 으로 누락 description
생성, (2) body restructuring — taxonomy 분류 + **progressive disclosure**(essential rule 은 상시,
supplement 는 on-demand 로딩), faithfulness check + self-correcting loop.

핵심 반직관 결과("less is more"): description 48%·body 39% 압축했는데 기능 품질이 **오히려 +2.8%** —
비필수 내용이 context window 를 distract 하기 때문. 즉 압축이 비용만 아니라 품질도 개선. 하네스가 자체
skill catalog(28개)를 다이어트할 근거이자, ponytail 이 SKILL.md 를 v3 에서 압축한 것과 같은 방향의
학술적 뒷받침.

**Figures**: (none extracted)
