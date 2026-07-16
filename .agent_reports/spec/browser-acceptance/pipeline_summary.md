# browser-acceptance — Spec Pipeline Summary

- **Date**: 2026-07-16
- **Mode**: library (브라우저 acceptance 공통 primitive)
- **Status**: v1 registered — BA-1~6; 구현 사이클 착수 (fake-page 단위 테스트 게이트, 실브라우저 통합은 BA-OPEN-1 이월)
- **Placement**: 독립 컴포넌트 `spec/browser-acceptance/` — `spec/prd.md`(Unified Memory System)·`spec/stage-dispatch/`·`spec/agent-fleet-dashboard/` 무수정.

## 배경

2026-07-16 운영 진단 항목 6: v94-reading-face D3 브라우저 검증에서 제품 결함 2건과 별개로, worker가 즉석 작성한 검증 스크립트의 도구-급 실수 4계열(CJS top-level await, 미개방 disclosure 검사, whole-page selector read-only 판정, URL 변경 후 mount 미대기)이 검증 시간을 소모했다. 공통 harness primitive가 있었다면 4건 모두 회피 가능했다는 사용자 진단에 따라, 주입식 0-dependency CJS 라이브러리로 계약을 고정한다. 기존 `tools/design-mcp`(로컬 HTML console hook)와 용도가 분리되며 playwright 해석 fallback만 재사용한다.

## Process Log
| Step | Action | Result |
|---|---|---|
| 입력 확인 | 사용자 진단 항목 6 수용 기준 + 현행 도구 census(design-mcp 중복 없음, playwright 재사용 지점 식별) | — |
| spec | PRD v1 작성 (lean) | BA-1~6 채택, BA-OPEN-1(실브라우저 통합 회수) open |
