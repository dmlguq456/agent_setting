# Skill-Design Refactor — Pipeline Summary

## 2026-07-15 · v3 GREEN

portable source를 상위 의미 계층으로 복원하고 Claude·Codex·OpenCode를 동급 sibling adapter로 닫았다. 세 런타임은 모두 같은 `builder` 프로필(14 capabilities, 7 portable roles, 26 modes)로 활성화됐고 freshness는 `fresh`, duplicate discovery는 0이다. Codex의 구형 전체 투영 진단도 프로필 인식형으로 전환해 Claude 전체 트리를 암묵적 기준으로 삼지 않는다.

always-loaded bootstrap 합계는 동일 UTF-8 byte 기준 55,163에서 18,323으로 36,840 bytes(66.8%) 줄었다. 일반/unknown/repeated 훅 주입은 0 bytes이고 활성 Codex native Skill metadata는 정규화 기준 1,946 chars이다. 이는 정적 context footprint 결과이며 토큰·cache·청구액 절감률 주장이 아니다. 실제 절감 채택 판단은 세 런타임별 production paired sessions `n>=30`과 품질 비열화 확인 뒤에만 가능하다.

## 2026-07-15 · v3 back-jump

사용자 진단에 따라 v2의 완료 판정을 재개방했다. Pocock 원칙의 portable tenet와 Claude realization은 완료됐지만, Codex/OpenCode 활성 표면과 초기 컨텍스트 비용이 같은 기준으로 닫히지 않았으므로 전체 상태를 `GREEN`에서 `PARTIAL / dev in_progress`로 변경했다.

v3는 `core/`·`capabilities/`·`roles/`를 유일한 의미 정본으로 두고 Claude·Codex·OpenCode를 동급 sibling adapter로 정의한다. 구현 cycle은 세 adapter의 semantic outcome, runtime fallback/discoverability, bootstrap·skill metadata·hook injection budget을 함께 검증한다. 정적 footprint 감소는 즉시 보고하되, 실제 토큰/비용 절감률은 production paired sessions `n≥30` 전에는 주장하지 않는다.
