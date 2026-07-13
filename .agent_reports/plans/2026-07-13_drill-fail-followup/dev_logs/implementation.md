# Implementation

- shared drill case + adapter-selected runner/diagnosis/judge로 통합했다.
- dispatch register/watch/harvest의 registry 우선순위를 모든 adapter와 portable utility에 통일했다.
- Fleet drill fixture attribution과 depth-1 owner/depth-2 child grouping을 교정했다.
- code-test/code-report artifact ownership을 core 계약에 맞춰 capability와 Codex projection에 동기화했다.
- stale conformance 기대값·installer/skill projection 검사를 현재 계약에 맞췄다.
- Codex `turn.failed`와 runtime nonzero가 adapter runner에서 성공으로 소거되지 않게 exit status를 보존했다.
