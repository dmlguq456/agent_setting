# 01 — Landscape

## 분류

Herdr와 현재 하네스는 같은 층의 제품이 아니다.

```text
portable semantics       capabilities / roles / QA / memory / artifacts
          ↓
harness control plane    route / attempts / jobs.log / worktree / liveness / harvest
          ↓
runtime adapters         Codex / Claude / OpenCode / native or headless
          ↓ optional
Herdr PTY/session plane  persistent pane / attach / read-send-wait / state / events
          ↘
Fleet observer           exact job evidence + optional Herdr session evidence
```

Herdr는 terminal multiplexer와 agent-aware automation surface의 결합이다. 현재 하네스는 portable execution semantics와 assurance control plane이다. Herdr를 기존 runtime adapter의 대체재로 넣으면 역할이 뒤섞이고, 선택적 PTY host로 넣으면 서로의 빈칸을 채운다.

## “토론” 기능의 실제 위치

| 기능 | Herdr | native Codex subagent | 현 headless |
|---|---|---|---|
| 병렬 실행 | 강함 | 강함 | 강함 |
| 메시지 전달 | terminal input | sibling message | 주로 parent/file |
| 응답 대기 | state/output wait | parent wait | dispatch wait/harvest |
| 토론 라운드 | 외부 구현 필요 | coordinator 구현 필요 | coordinator 구현 필요 |
| 합의·반대 기록 | 없음 | 외부 artifact 필요 | artifact에 적합 |
| 세션 지속/직접 attach | 강함 | thread 수명 종속 | process/log 중심 |

따라서 목표 기능은 “Herdr 토론 엔진 채택”이 아니라 **하네스 토론 driver + 복수 transport**다.
