# CAVEWOMAN — LLM under linguistic input/output compression (arXiv 2606.24083)

**Type**: paper
**URL**: https://arxiv.org/abs/2606.24083
**분류축1 (메커니즘)**: output-compression vs input-context-reduction (둘을 학술적으로 대조 검증)
**절감 claim**: (검증 논문) — output 압축 1.4-2.4x(최대 3x) 절감 / input 압축 net-loss ~1.15x(최악 1.8x)
**실측/검증**: **본 연구 axis 2 의 학술 1차 근거**. 5-benchmark. output 압축은 대부분 API 모델에서
비용 절감(1.4-2.4x). **input 압축은 strict lose-lose — 순비용 ~1.15x 상승, 최악 데이터셋 1.8x.**
비추론 모델에서 input 압축 생성의 ~절반이 correct 하나 baseline 과 의미 divergence(length-control 후에도).
**신호->레버 매핑**: 압축 방향(input vs output)이 결과 부호를 가르는 핵심 변수 — 레버 선택 자체가 신호.
**하네스 시사점**: token-budget 축은 **output 압축 레버만 안전**, input/context 압축 레버는 순손실 위험.
caveman/wilpel 계열의 input 압축 주장에 대한 결정적 반례 — 하네스는 이 비대칭을 설계 불변식으로.

## Summary
"caveman style" 압축을 학명으로 직접 명명·연구한 논문(2026-06-23 제출). caveman/wilpel 생태계 주장에
대한 가장 강한 독립 학술 반증.

핵심 발견: **output 과 input 압축의 부호가 반대**. output 압축(모델이 짧게 답하게)은 realized cost 를
1.4-2.4x(최대 3x) 낮춘다 — caveman(JuliusBrussee)의 output-only 절감 주장과 방향 일치. 그러나 input
압축(프롬프트를 caveman 화)은 **strict lose-lose**: 순비용을 오히려 ~1.15x(최악 1.8x) 올린다.

메커니즘: 모델이 불명확·압축된 입력을 **더 긴 응답으로 보상**하면서 정확도는 떨어진다. 즉 입력에서 아낀
토큰을 출력에서 더 쓰고 품질까지 잃는 이중 손실. wilpel/caveman-compression 이 서 있는 "입력 압축은
무해" 가정을 정면 반박.

품질: 비추론 모델에서 input-압축 생성의 ~절반만 technically correct, 나머지는 baseline 과 의미
divergence 가 length-control 후에도 잔존 → adversarial safety 주장("의미 보존")에 대한 반증 근거.

**Figures**: (none extracted)
