# Hackenberger — Ultimate Token-Saving Stack (RTK+Caveman+TokenSave)

**Type**: blog
**URL**: https://paul-hackenberger.medium.com/the-ultimate-token-saving-stack-rtk-caveman-and-tokensave-163badadd9ec
**분류축1 (메커니즘)**: 3계층 조합 — input-context-reduction(RTK/Headroom, TokenSave) + output-compression(Caveman)
**절감 claim**: RTK/Headroom up to 90%(CLI output), TokenSave 60-80%(structural discovery),
Caveman 40-70%(chat prose)
**실측/검증**: **홍보글 — 실사용 gap 무비판**. 정확히 이 stack 을 codepointer 가 replay 해 합산 3.7%
로 반박. 세 도구의 per-payload 수치를 나열하나 세션 합산 효과는 언급 안 함.
**신호->레버 매핑**: 명시 없음(도구 조합 레시피).
**하네스 시사점**: "여러 압축 레버를 쌓으면 절감이 합쳐진다"는 순진한 가정의 대표 사례 — codepointer 반증과
쌍으로 axis 2 에서 인용. 레버 stacking 은 denominator 를 공유하므로 단순 합산 안 됨.

## Summary
세 도구를 계층별로 조합하는 홍보성 레시피: RTK/Headroom(stdout/stderr 압축, CLI output 90%),
TokenSave(AST code query MCP, 구조 discovery 60-80%), Caveman(chat prose 40-70%). 각 도구가 서로 다른
표면(도구출력·코드탐색·산문)을 담당한다는 점에서 메커니즘 3분류를 한 글에 모아 보여주는 유용한 지도.

그러나 실사용 gap 비판이 전무 — codepointer 가 정확히 이 rtk+headroom+caveman 조합을 500 세션 replay
해 합산 3.7% 로 반박했다. axis 2 에서 이 글(주장)과 codepointer(반증)를 대조쌍으로 사용. 교훈: 레버를
쌓아도 각 per-payload % 는 공통 세션 denominator 를 나눠 갖기에 단순 덧셈이 성립하지 않는다.

**Figures**: (none extracted)
