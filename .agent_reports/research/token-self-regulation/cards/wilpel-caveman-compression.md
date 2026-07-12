# wilpel/caveman-compression — 알고리즘적 semantic 입력 압축

**Type**: repo
**URL**: https://github.com/wilpel/caveman-compression
**분류축1 (메커니즘)**: input-context-reduction (알고리즘, system prompt 아님)
**절감 claim**: LLM 모드 40-58%, NLP(spaCy) 15-30%, MLM(RoBERTa) 20-30%. avg 40%. factual 13/13(100%).
**실측/검증**: 저자 자체 benchmark 만(독립 검증 없음). **입력 압축이라는 방향 자체가 CAVEWOMAN
(arXiv 2606.24083)이 net-loss(~1.15x)로 직접 반박** — 저장 토큰은 줄어도 모델이 불명확 입력을 긴
출력으로 보상해 순비용 증가. → claim(절감)과 학술 반증(순손실)이 정면 충돌.
**신호->레버 매핑**: 명시 없음(정적 rule 기반, 동적 신호 없음). 3모드는 비용/지연/오프라인 제약(신호)
에 따라 사용자가 선택.
**하네스 시사점**: 입력/컨텍스트 압축 레버는 caveman 계열 중 가장 위험 — 순손실 가능. 하네스가
token-budget 조절 시 입력 압축은 default off, 명확성 손상 없는 범위에서만.

## Summary
JuliusBrussee/caveman 과 브랜딩만 공유, 실체는 완전히 다른 **알고리즘 파이프라인**. 텍스트를 LLM 입력
전에 caveman 스타일로 압축. 3모드: LLM(OpenAI API, ~2s/req), NLP(spaCy rule-based, offline <100ms,
15+ langs), MLM(RoBERTa masked-LM, 1-5s).

SPEC.md 핵심 원리(직접 열람): "Remove only what LLMs can deterministically reconstruct — grammar,
connectives, structure. Preserve facts, numbers, constraints." Sentence Atomicity(문장당 1 원자),
2-5 word limit, connective elimination. compression.txt 는 제거/보존 목록을 명시(관사·auxiliary·
intensifier 제거 / 명사·main verb·숫자·negation·technical term 보존).

이 repo 는 "입력 압축은 무해하다"는 가정 위에 서 있으나, CAVEWOMAN 이 정확히 그 가정을 실험으로 깼다.
따라서 본 카드는 axis 2 에서 **긍정 claim vs 학술 반증의 대조쌍** 으로 쓰인다.

**Figures**: (none extracted)
