# tools/memory — 통합 기억 시스템 (`mem`)

Hermes 메모리 벤치마킹의 store/write 층. spec: [`.claude_reports/spec/prd.md`](../../.claude_reports/spec/prd.md) (Unified Memory System).

## 한 줄
흩어진 기억(post-it 단기 · auto-memory 장기 · user_profile 전역)을 **하나의 포터블 store + tier 모델**로 통합. 자동 기록 + FTS 회상.

## 구조
| 층 | 위치 | git | 역할 |
|---|---|---|---|
| 원본(SoT) | `~/.claude/memory/<tier>/<scope>/*.md` | tracked | markdown, 포터블(repo 따라 이동), 사람이 읽고 diff |
| 색인 | `~/.claude/memory/.index.db` | gitignore | SQLite FTS5, rebuildable |
| 주입 projection | `~/.claude/projects/<cwd>/memory/` | gitignore | 세션 시작 하네스 주입용, store에서 생성 |

레코드 = `tier`(working/durable) × `scope`(project/global) × `type`. 단기=working(자동 만료/졸업), 장기=durable(영구+consolidate).

## 명령 (`python3 ~/.claude/tools/memory/mem.py <cmd>`)
| 명령 | 동작 |
|---|---|
| `add <tier> <type> "<body>" [--scope] [--tags]` | 수동 기록 (품질게이트·dedup·injection 통과분) |
| `note "<body>"` | working tier 단축 기록 |
| `recall "<q>" [--tier] [--scope] [--all] [--sessions]` | 회상 (FTS5 or fallback, +raw 세션) |
| `index [--rebuild]` | FTS5 색인 생성 |
| `project [--cwd]` | 주입 projection 생성 |
| `migrate [--apply]` | auto-memory(전 cwd) + 현 cwd post-it → store (멱등, default dry-run) |
| `lifecycle [--apply]` | working 만료 + durable dup-flag |
| `stats` | store 통계 |

env override (테스트): `MEM_STORE` · `MEM_PROJECTS`.

## 자동 write 불변식
기억 저장 = **자동**(사람 승인 게이트 없음 — "결정은 사용자"는 *세팅 변경*용이지 *기억 기록*용 아님). 안전장치는 자동 필터뿐: 품질게이트(promote/skip) · dedup · injection/secret 가드. 세팅·원칙 변경은 본 모듈 영역 아님(여전히 사람 게이트).

## 전환 상태 (2026-06-15)
- ✅ 모듈(store/write/index/recall/migrate/lifecycle/project) 구현·테스트
- ⏳ **live 적용**: `migrate --apply`로 기존 메모 → store (추가형 — 기존 `projects/*/memory/` 안 지움)
- ⏳ **소스 전환**(후속·신중): recall.sh → `mem recall` alias / post-it → `mem` alias / projection 세션-시작 hook(D-4). store 안정 확인 후.

legacy `recall.sh`·`index-check.sh`는 전환 완료까지 기존 위치(`projects/*/memory/`) 대상으로 병행 동작.
