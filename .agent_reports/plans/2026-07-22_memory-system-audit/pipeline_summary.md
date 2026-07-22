# Pipeline Summary — Memory System Audit

## Goal
(1) 에이전트 지침에 화석화된 도메인/사용자 지식 전수 스윕, (2) 메모리 체계 자체의 매우 강한 감사(이관 전제 = 안정적 회수), (3) OSS 지형 → 개선.

## Artifacts
- `audit-verdict.md` — 통합 판정(지도·이관 정책·개선 12·OSS 채택 6·사용자 결정 9) **PRIMARY**
- `_internal/{legacy-content-sweep, memory-architecture, recall-reliability, oss-landscape}.md`

## Status
| 항목 | 상태 |
|---|---|
| 4-stream 병렬 감사 (5 agents, 0 err, 581k tok) | ✅ |
| 판정: 프로필 이설=조건부 GO(P1·P2·P3 선행) / durable-recall 의존 이설=VETO | ✅ 확정 |
| **P1 미러 복구** | ✅ 고아 lock(7/14) 제거 → 8일 공백 백필 → 분기 merge(원격 이력 보존) → **유실 1건 복원**(onedrive 피드백, DB 1,379) → sync 재작동 → agent-memory push |
| **P2 빈-스토어 가드** | ✅ `a7b87408` — 파생 경로 거부+해석 출력, MEM_STORE/MEM_INIT 허용, 4케이스 테스트, 기존 스위트 회귀 0 |
| 선재 확인 | distill.test red = HEAD 동일 = **turn-nudge 사망(7/15~)을 스위트가 이미 감지** (개선 #7 근거) |
| 사용자 결정 | ✅ 3답 확정: spectrogram 값 확정(256/512/1024)·DB remap 승인·나머지 추천안 일괄 |
| 실행 라운드 2 (3-agent 병렬) | ⏳ A=mem.py 3종(주소 remap v6·CJK bigram·plain-commit) / B=모순 교정·프로필 포인터화·P3 소비 라인·footgun 승격 / C=윈도우값 검증도구 승격·retrieval eval 하네스 |
| 저장 정비 (main 직접) | ✅ inner git gc 408→153MB · 고아 distill-state 16,961개 삭제 (memory/ 602→286MB) |
| 보류 | 표 강조 정본(②) 미정 → data-script→프로필04 병합만 이연 · turn-nudge 수리(#7)는 라이브 세션 프로브 필요 |

## User decisions (요약)
1. spectrogram 윈도우 값(8k=256/16k=512/48k=1024) 확정 + 거처(검증도구 승격 vs 프로필 04)
2. 표 강조 정본(논문 bold-only vs data-script vs 슬라이드 방식)
3. 베뉴 4-tier 사다리 거처 4. fact-check 충돌쌍 사전 거처
5. 활성 모순 2건: 실값 교정 vs genericize (+실프로젝트명 예시 ~12곳 일괄 여부)
6. dump 미러 설계: amend-rolling+주기 gc vs plain+주기 squash (406MB 근본원인)
7. 한국어 회수: SQLite 3.34+ 번들 vs CJK bigram 자체 구현
8. legacy cwd 키 118+ v6 remap 승인 (라이브 DB 일회성 마이그레이션, 고가치 24건 가시화)
9. upsert footgun 문서 거처: core/MEMORY.md vs tools/memory
