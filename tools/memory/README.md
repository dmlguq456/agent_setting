# tools/memory — 통합 기억 시스템 (`mem`)

Hermes 메모리 벤치마킹의 store/write 층. spec: [`.claude_reports/spec/prd.md`](../../.claude_reports/spec/prd.md) (Unified Memory System).

## 한 줄
흩어진 기억(post-it 단기 · auto-memory 장기 · user_profile 전역)을 **하나의 SQLite store + tier 모델**로 통합. 자동 기록 + FTS 회상. 진실원천은 `memory.db`(DB-SoT), git은 텍스트 덤프(`dump.jsonl`)를 mirror.

## 구조
| 층 | 위치 | git | 역할 |
|---|---|---|---|
| **원본(SoT)** | `~/.claude/memory/memory.db` (SQLite WAL) | **gitignore** (바이너리) | write의 진실원천. `records` 테이블 + FTS5 가상테이블(unicode61 + trigram CJK) 내장 |
| **git mirror** | `~/.claude/memory/dump.jsonl` (레코드당 1줄, id 정렬) | **tracked** (전용 repo) | DB→deterministic 텍스트 export. 변경 줄만 diff. 복원 source (`mem import`) |
| **하네스 projection** | `~/.claude/projects/<cwd>/memory/` | gitignore | 보조 — 하네스가 auto-memory 쓰는 자리 → `mem sync` 로 DB durable 흡수. `mem project` 는 보조 projection 생성 |

레코드 = `tier`(working/durable) × `scope`(project/global) × `type`. 단기=working(자동 만료/졸업), 장기=durable(영구+consolidate). FTS5는 `.index.db` 파생 파일이 아니라 `memory.db` 본체 안에 내장.

## 명령 (`python3 ~/.claude/tools/memory/mem.py <cmd>`)
| 명령 | 동작 |
|---|---|
| `add <tier> <type> "<body>" [--scope] [--tags] [--links] [--source]` | 수동 기록 (품질게이트·dedup·injection 통과분 → DB INSERT) |
| `note "<body>"` | working tier 단축 기록 |
| `recall "<q>" [--tier] [--scope] [--all] [--sessions]` | 회상 (FTS5 bm25 + trigram CJK, LIKE fallback, +raw 세션) |
| `index [--rebuild]` | DB 내장 FTS5 가상테이블 재구축 (`memory.db` 안에서 — 별도 파일 없음) |
| `export [--target dump\|profile] [--apply]` | DB → `dump.jsonl` (git mirror, default) 또는 `user_profile/0X_*.md` (on-demand 사람 열람 캐시, SoT 아님). `--target profile` 은 default dry-run — 실제 write는 `--apply` 필요 |
| `import <dump.jsonl>` | 덤프 → DB **완전 복원** (기존 records 전체 삭제 후 dump replay = exact mirror 재현, additive merge 아님). 복원 후 FTS 재구축 동일 connection 에서 수행 |
| `project [--cwd]` | 보조 projection 생성 (세션 주입은 `inject` 담당) |
| `migrate [--apply]` | auto-memory(전 cwd) + post-it + **구 markdown SoT 파일** → DB (멱등, default dry-run) |
| `lifecycle [--apply]` | working 만료 + durable dup-flag (비가역 삭제는 플래그만, 자동 삭제 없음) |
| `stats` | store 통계 (`records` 테이블 GROUP BY) |
| `inject [--hook]` | SessionStart 주입 — DB(durable+working+profile)→context 직접 주입. `--hook` 시 `additionalContext` JSON 출력 |
| `sync` | SessionEnd 회수 — `projects/<cwd>/memory/` auto-memory → DB durable 흡수 + FTS5 재구축 + `dump.jsonl` 재export |
| `register-postit <path>` | **deprecated (legacy-migration-only)** — `.postit-roots` 레지스트리 등록. skills 에서 더 이상 호출 안 함 (post-it 은 DB working 레코드 직접 write). |

env override (테스트용): `MEM_STORE` · `MEM_PROJECTS` · `MEM_PROFILE`.
- `MEM_STORE` → `memory.db` 경로와 `dump.jsonl` 경로 모두 이 디렉터리 하위로 파생됨.
- `MEM_PROFILE` → `export --target profile` 의 출력 디렉터리. 테스트 시 `/tmp/...` 로 지정해 실 `user_profile/` 보호.

## 자동 write 불변식
기억 저장 = **자동**(사람 승인 게이트 없음 — "결정은 사용자"는 *세팅 변경*용이지 *기억 기록*용 아님). 안전장치는 자동 필터뿐: 품질게이트(promote/skip) · dedup · injection/secret 가드. 세팅·원칙 변경은 본 모듈 영역 아님(여전히 사람 게이트).

## 운영 현황 (2026-06-15)
- **저장 구조**: `memory.db` (SQLite WAL) — `records` 테이블 12컬럼(id, tier, scope, type, cwd_origin, created, updated, expires, source, tags, links, body) + FTS5 unicode61 가상테이블(`records_fts`) + trigram CJK 보조 테이블(`records_trig`). `.index.db` 파생 파일 폐기(DB 내장으로 통합).
- **git mirror**: `dump.jsonl` — id 정렬, `sort_keys=True`, 레코드당 1줄, NULL은 JSON `null`로 표기(키 누락·빈문자열 금지). 복원: `mem import dump.jsonl`.
- **하네스 wired**: SessionStart `mem inject --hook` (settings.json, timeout 20) + SessionEnd `mem sync` (timeout 120) 연결 완료. `sync`는 흡수 + FTS 재구축 + `dump.jsonl` 재export 3단계 수행.
- **recall.sh**: `mem recall` thin wrapper (store FTS5 bm25 + trigram CJK + LIKE fallback). 파일 불변.
- **register-postit deprecated**: legacy-migration-only. 현 post-it 경로는 DB working 레코드 직접 write (`mem note`/`mem add`) — `.postit-roots` 레지스트리·`migrate` post-it 소스는 구 markdown 이관 전용.
- ✅ **live 적용 완료**: `migrate --apply` 로 기존 markdown SoT + auto-memory + post-it → DB 이관 완료. DB-as-SoT 전환 끝 (구 `projects/*/memory/` 는 보존, 추가형).

`index-check.sh` 는 *legacy `projects/*/memory/` 의 MEMORY.md 텍스트 인덱스 점검 전용*으로 잔존 — store FTS5 색인은 `mem index` 가 관할(`memory.db` 내장)하므로 별개 대상.
