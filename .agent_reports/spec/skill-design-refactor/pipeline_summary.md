# Skill-Design Refactor — Pipeline Summary

## 2026-07-15 · v3 back-jump

사용자 진단에 따라 v2의 완료 판정을 재개방했다. Pocock 원칙의 portable tenet와 Claude realization은 완료됐지만, Codex/OpenCode 활성 표면과 초기 컨텍스트 비용이 같은 기준으로 닫히지 않았으므로 전체 상태를 `GREEN`에서 `PARTIAL / dev in_progress`로 변경했다.

v3는 `core/`·`capabilities/`·`roles/`를 유일한 의미 정본으로 두고 Claude·Codex·OpenCode를 동급 sibling adapter로 정의한다. 구현 cycle은 세 adapter의 semantic outcome, runtime fallback/discoverability, bootstrap·skill metadata·hook injection budget을 함께 검증한다. 정적 footprint 감소는 즉시 보고하되, 실제 토큰/비용 절감률은 production paired sessions `n≥30` 전에는 주장하지 않는다.
