# qa-intensity-unify — Spec Pipeline Summary

- **Date**: 2026-07-10
- **Mode**: library (하네스 계약 문서 — 파이프 옵션 축 개정)
- **Status**: spec done (v1) · dev pending (다음 사이클 — sd15-adapter-parity 수확 후)
- **Placement**: 독립 컴포넌트 `spec/qa-intensity-unify/` — `spec/stage-dispatch/`(분사 토폴로지)·`spec/harness-layer-sync/` 무수정.

## 배경

사용자 결정(2026-07-10): "qa 가 따로 있어야 하나 — intensity 에 자연스럽게 따라가는 게 맞다." 선행 결정(decision_74ca88)이 이미 qa 를 "verify rigor override" 로 반쯤 접었고 CONVENTIONS §1:71 이 intensity→rigor 파생을 명문화한 상태 — 본 spec 은 잔존 명시-override 표면까지 접는 마무리. 검증 프로세스 유지 원칙 불변. adversarial 이 qa/intensity 양쪽 tier 에 있는 이중 정의도 해소.

## 채택 결정 (locked)
- **QA-1**: --qa 축 폐지·완전 파생 — §1:71 테이블 SoT 승격. 검증 프로세스 제거 없음.
- **QA-2**: high-stakes 자동 상향 = intensity 상향 재매핑. external adversary 요구(검증가능성 게이트 포함)를 intensity=adversarial 로 이전.
- **QA-3**: 표면 정리 — SKILL hint 46파일(+projection sync)·CONVENTIONS §1·WORKFLOW §1.1·wrapper 3종(--qa optional/derived, jobs.log qa= 필드는 하위호환 파생값 유지)·bootstrap 3종·drill fixture. fleet check:<qa> 라벨은 타 세션 소유 — handoff 통지만.

## 미결 (open)
- **QA-OPEN-1**: shape 독립 rigor override 실존 반례 — 구현 사이클 census 판정 (있으면 내부 전용 잔존, 없으면 완전 폐지).

## Next
구현 = autopilot-code 다음 사이클 (sd15-adapter-parity 수확 후 — wrapper·adapter 문서 파일 겹침 회피). core-first 순서: CONVENTIONS §1 → WORKFLOW §1.1 → bootstrap → skills → wrapper → census/drill/sync.

## Version History
- v1 (2026-07-10): 초기 PRD — 사용자 결정 + decision_74ca88 계승 + census 실측. QA-1~3 + QA-OPEN-1.
