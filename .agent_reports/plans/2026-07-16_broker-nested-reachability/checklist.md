# Checklist

- [x] 지배 계약 read (CORE·WORKFLOW·OPERATIONS §5.10·stage-dispatch PRD v13→v14).
- [x] 근본 원인 코드 수준 확정 (`broker_status()` /proc 단일 게이트 + ensure spawn 루프).
- [x] stage-dispatch spec v14 등재 (SD-57~60, commit 47512630).
- [x] ~~SD-57 구현~~ — **철회**: spec v15(b50e4524) broker 폐기와 충돌 (`_internal/withdrawal.md`).
- [x] 철회 기록·워크트리 제거·후속 라우팅 정리.
