# card 02 — Axis 2·3(parity·single-source) · Axis 4·5(dead-ref·doc↔code)

> inspector(축 2+3, 축 4+5) 종합. OVERCLAIM 0 — 전부 UNDERCLAIM/stale.

## Axis 2 — parity 신고 정확성
- **[2-1] P1** — `ADAPTATION_INVENTORY.md:33` Codex hook location 이 2파일만 명시, 실제 `hooks.json` 7-스크립트 wired + 가드 `check-adaptation-boundary.sh:788` 7개 강제. ledger 과소열거.
- **[2-2] P2** — `codex/ADAPTATION.md:50`(요약표 3) / `:397`(매핑행 5, sessionstart·userprompt 누락) / prose(6) 3자 불일치.
- **[2-3] P2** — `ADAPTATION_INVENTORY.md:30` Codex agent 생성경로가 EXTRA_AGENTS(memory-scout, `sync-native-agents.py:29`) 누락 — OpenCode 행(`:41`)과 비대칭.
- 검증(정상): `codex-review-team`↔`external-adversary` name-map 은 `roles/README.md:22`+가드 `:2829` 로 정확 문서화.

## Axis 3 — single-source
- **[3-1] P2** — Codex 모델 튜플(gpt-5.4-mini/gpt-5.5) `codex/ADAPTATION.md:184-185·418-419·428-432` 3회 + 생성기 `sync-native-agents.py:25` 중복.
- **[3-2] P2** — `DESIGN_PRINCIPLES.md:97` 에이전트 로스터가 `roles/README.md:15-22`(단일출처)와 divergence(memory-scout 누락).
- *(최상위 구조 위반은 card 00 / §S-3.)*

## Axis 4 — 죽은 참조
- **[4-1] P1** — `report-generation.md:290` 죽은 앵커 `CONVENTIONS §1.4`(실제 §1.1 뿐) + 폐기된 "default thorough 통일" 인용(↔ `CONVENTIONS.md:71` intensity-derived).
- **[4-2] P2** — `CLAUDE.md:54` `CONVENTIONS.md §5.10` 오인용(실 내용 `OPERATIONS.md:46,78`; `CONVENTIONS.md:366` 리다이렉트 스텁). 같은 파일 `:62` 는 정상 → 자기모순.
- **[4-3] P2** — `loops/study.md:14` `CONVENTIONS §3.6`(§3 은 평 리스트, 의도는 항목 8 `:141`).
- 오탐(dead 아님): `loops/drill/metrics.csv`(런타임 생성 `run.sh:185`), `loops/note.sh`(문서가 "제거된 파일 예시" 로 의도 언급).

## Axis 5 — 문서↔코드
- 안전 hook 11종 문서=실동작 일치, **P0 없음**(artifact-guard 신규생성만 차단·builtin-memory hard-deny·git-state merge/rebase deny+탈출구·mem-recall PAT 3자 일치·build-manifest --check up-to-date).
- **[5-1] P2** — recall 신호어 `CLAUDE.md:99` 6개 vs `mem-recall-inject.sh:98`/`MEMORY.md:78` 8개(예시 "류" 라 엄격 dead 아님).
- 교차: §S-1 은 "동작 일치" 가 **공유 복사본 기준일 때만** 참 — Claude 실행본은 stale(card 00).
