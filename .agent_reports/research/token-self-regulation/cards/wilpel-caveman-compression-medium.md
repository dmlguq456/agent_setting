# Caveman Compression: Shrinking Contexts Without Losing Meaning (Medium, Peltomäki)

**Type**: blog
**URL**: https://medium.com/@peltomakiw/caveman-compression-shrinking-llm-contexts-without-losing-meaning-927335fd6853
**분류축1 (메커니즘)**: input-context-reduction
**절감 claim**: avg ~40% (repo 재인용), "without losing meaning"
**실측/검증**: 저자 본인 writeup(1차 저자 관점). "meaning 보존" 주장은 CAVEWOMAN(2606.24083)의 입력
압축 순손실·의미 divergence 발견과 충돌.
**신호->레버 매핑**: 명시 없음(정적 rule)
**하네스 시사점**: "meaning 을 잃지 않고 컨텍스트 압축" 이라는 핵심 마케팅 명제 자체가 학술 반증 대상 —
하네스는 입력 압축을 "무손실"로 가정하지 말 것.

## Summary
wilpel/caveman-compression 저자(William Peltomäki)의 방법론·동기 writeup. "의미를 잃지 않고 컨텍스트를
줄인다"는 제목 명제가 이 도구군의 핵심 세일즈 포인트. 그러나 CAVEWOMAN 이 정확히 입력 압축에서 의미
divergence(length-control 후에도 잔존)와 순비용 상승을 실측 → 제목 명제의 반례. axis 2 에서 repo 카드·
CAVEWOMAN 카드와 삼각 대조.

**Figures**: (none extracted)
