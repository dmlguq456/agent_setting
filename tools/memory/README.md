# tools/memory — Unified Memory System (`mem`)

Portable store and retrieval layer. Spec: `<artifact-root>/spec/prd.md` (`.agent_reports` first, legacy `.claude_reports` compatible).

## Boundary

Short-lived post-its, durable learned memory, and the global profile share one
SQLite store. The acting agent decides contextually what to store, retrieve,
promote, merge, or prune. Code owns mechanical integrity, scope isolation,
pending protection, lifecycle execution, bounded telemetry, and recovery.
`memory.db` is the source of truth; `dump.jsonl` is its text mirror.

## 구조
| 층 | 위치 | git | 역할 |
|---|---|---|---|
| **원본(SoT)** | `<agent-home>/memory/memory.db` (SQLite WAL) | **gitignore** (바이너리) | write의 진실원천. `records` 테이블 + FTS5 가상테이블(unicode61 + trigram CJK) 내장 |
| **git mirror** | `<agent-home>/memory/dump.jsonl` (레코드당 1줄, id 정렬) | **tracked** (전용 repo) | DB→deterministic 텍스트 export. 변경 줄만 diff. 복원 source (`mem import`) |
| **하네스 projection** | `<agent-home>/projects/<cwd>/memory/` | gitignore | 보조 — 하네스가 auto-memory 쓰는 자리 → `mem sync` 로 DB durable 흡수. `mem project` 는 보조 projection 생성 |

레코드 = `tier`(working/durable) × `scope`(project/global) × `type` × `delivery_state`(ordinary/pending/consumed). 단기=working(자동 만료/졸업), 장기=durable(영구+consolidate). 새 `type=handoff`와 `--requires-consume` thread는 pending으로 시작해 명시 `consume` 전까지 파괴 경로에서 보호된다. FTS5는 `.index.db` 파생 파일이 아니라 `memory.db` 본체 안에 내장.

## 명령 (`python3 <agent-home>/tools/memory/mem.py <cmd>`)
| 명령 | 동작 |
|---|---|
| `add <tier> <type> "<body>" [--scope] [--tags] [--links] [--source] [--requires-consume]` | 수동 기록 (품질게이트·dedup·injection 통과분 → DB INSERT). `type=handoff` 또는 `--requires-consume`은 pending |
| `note "<body>" [--type] [--requires-consume]` | working tier 단축 기록. 인계 목적 thread는 `--requires-consume`으로 pending 지정 |
| `recall "<q>" [--tier] [--scope] [--all] [--sessions] [--full] [--limit 1..100]` | 명시 회상 (FTS5 bm25 + trigram CJK, LIKE fallback, +raw 세션). 기본 limit 20; `--full`은 같은 ranked ID의 snippet을 body 전문으로 교체 |
| `show <id> [--all]` | visibility fence 안의 단일 레코드 metadata+body 전문. 기본 current project+global; 타 project는 `--all`; injection-flagged/비가시 ID는 generic not-found |
| `consume <id>` | pending handoff/thread를 명시적으로 consumed 전이. 조회·주입은 소비로 간주하지 않음 |
| `restore <id>` | action/canonical 메타가 보존된 graveyard에서 단일 레코드를 복구 |
| `index [--rebuild]` | DB 내장 FTS5 가상테이블 재구축 (`memory.db` 안에서 — 별도 파일 없음) |
| `export [--target dump\|profile] [--apply]` | DB → `dump.jsonl` (git mirror, default) 또는 `user_profile/0X_*.md` (on-demand 사람 열람 캐시, SoT 아님). `--target profile` 은 default dry-run — 실제 write는 `--apply` 필요 |
| `import <dump.jsonl>` | 덤프 → DB **완전 복원** (기존 records 전체 삭제 후 dump replay = exact mirror 재현, additive merge 아님). 복원 후 FTS 재구축 동일 connection 에서 수행 |
| `project [--cwd]` | 보조 projection 생성 (세션 주입은 `inject` 담당) |
| `migrate [--apply]` | auto-memory(전 cwd) + post-it + **구 markdown SoT 파일** → DB (멱등, default dry-run) |
| `lifecycle [--apply]` | working 만료 + durable dup-flag. pending handoff/thread는 `--apply`에서도 보존 |
| `stats` | store 통계 (`records` 테이블 GROUP BY, 스냅샷) |
| `log [--limit 20] [--action] [--tier] [--actor] [--json]` | **(v15 D-38)** write-events 저널 tail 조회 — `stats`(스냅샷)를 보완하는 흐름(시간축). fleet·oncall·사용자 공용 표면 |
| `doctor` | **(v15 D-39, read-only)** store 전수 진단 9항목(integrity·FTS 정합·schema 불변식·working 비대·stale pending·durable soft-ceiling·graveyard 정합·dump 신선도·워커 건강) + exit 0(clean)/1(WARN)/2(FAIL). 수정 0 — 조치는 D-18 세션끝 curator 소유 불변 |
| `inject [--hook]` | SessionStart 주입 — DB(durable+working+profile)→context 직접 주입. 기본 2000자·15개 bullet hard cap 후 초과분은 recall 안내로 대체. `--hook` 시 `additionalContext` JSON 출력 |
| `sync` | SessionEnd 회수 — `projects/<cwd>/memory/` auto-memory → DB durable 흡수 + FTS5 재구축 + `dump.jsonl` 재export |
| `distill <sid> [--advance]` | 세션 jsonl 의 공유 marker 이후 정규화 텍스트 출력(+`--advance` 로 marker 전진). SessionEnd distiller(D-12)·in-session consolidation(D-13) 공용 헬퍼 |
| `curate-snapshot` | **(γ, read-only)** 현 프로젝트 durable/working snapshot + SIGNALS(ceiling/cold-decay/orphan) + destructive `IDS:` 멤버십 줄. pending은 `PROTECTED PENDING`에 보이되 destructive `IDS:`에서는 제외. body 라벨은 구조적 무력화(control/newline strip) |
| `reinforce <id>` | **(γ)** strength++ + last_accessed 갱신 (재출현=중요도, E-1). 화이트리스트 게이트(현 프로젝트만) |
| `merge --canonical <id> <ids…>` | **(γ)** near-dup 병합 — strength 합산을 canonical 에, 나머지는 graveyard 후 삭제. pending 하나라도 포함되면 strength 변경·삭제 없이 전체 원자 취소 |
| `prune <id>` | **(γ)** 삭제 — `deleted-records.jsonl` graveyard 백업 **성공 후에만**(S1 fail-closed). pending은 consume 전 거부 |
| `delete <id> [--force]` | 사용자-개시 단건 삭제. pending은 consume 선행 또는 명시 `--force` 없이는 거부 |
| `graduate <id> [--to durable]` | **(γ)** working→durable 승격 (E-6). 화이트리스트 게이트 |
| `reattribute <id>` | **(γ)** 고아(어떤 live 프로젝트로도 해석 안 되는 cwd_origin) 레코드를 현 프로젝트로 재귀속 (비파괴). 역게이트(live-resolving cwd_origin·git:/id:/root:·self 거부 — 탈취 방지) |
| `register-postit <path>` | **deprecated (legacy-migration-only)** — `.postit-roots` 레지스트리 등록. skills 에서 더 이상 호출 안 함 (post-it 은 DB working 레코드 직접 write). |

> **γ 큐레이터 보안 불변(D-18/D-35)**: 위 5개 변이 서브커맨드(reinforce/merge/prune/graduate/reattribute)는 distiller LLM 이 **직접 실행하지 않는다**. distiller(no-tools)는 action JSON(`{"action":…}`)만 출력하고, `tools/memory/apply-distill-actions.py` 가 파싱·shape 검증·멤버십 게이트 후 이 서브커맨드를 **argv 로** 호출한다. 각 서브커맨드는 자체 화이트리스트 게이트로 현 프로젝트 외(profile·global·타 프로젝트·존재안함) 대상을 거부(비0 exit, 삭제 0). pending은 snapshot 멤버십과 실행시점 DB 이중 가드로 보호하며, prune/merge/delete는 삭제 전 graveyard 백업을 남긴다.

## Retrieval boundary (D-40)
- `show`, explicit recall/full, and SessionStart injection do not consume a handoff. Explicit recall/show update `last_accessed` unless `--no-touch` is supplied. Source upsert/body dedup never lowers an existing pending record to ordinary.
- Prompt-submit hooks do not classify every prompt for recall. The agent chooses when prior context may help, then invokes `recall.sh` or `mem recall`.
- FTS/BM25 ranking, CJK/identifier tokenization, scope fences, and limits organize results for an agent-chosen query. They do not decide whether recall is relevant.
- Retrieval telemetry does not store raw prompts and distinguishes `explicit-recall`, `show`, `session-inject`, and `consume`.
- telemetry 기본 위치는 `$XDG_STATE_HOME/agent-memory/recall-events.jsonl`(미설정 시 `~/.local/state/agent-memory/`)이며 memory git mirror 밖의 local state다. `MEM_RECALL_EVENTS`로 테스트/운영 경로를 바꿀 수 있다.
- The SessionStart 2,000-character/15-bullet cap remains.

env override (테스트용): `MEM_STORE` · `MEM_PROJECTS` · `MEM_PROFILE` · `MEM_INJECT_MAX_CHARS` · `MEM_INJECT_MAX_BULLETS` · `MEM_INJECT_MAX_WORKING` · `MEM_INJECT_MAX_DURABLE` · `MEM_INJECT_CLEANUP_LINES` · `MEM_INJECT_SNIPPET_CHARS` · `MEM_DISTILL` · `MEM_DISTILL_ENABLE` · `MEM_DISTILL_WORKER` · `MEM_DISTILL_MODEL` · `MEM_WRITE_EVENTS` · `MEM_ACTOR` · `MEM_SID`.

## Cluster J 불변식 (v15 D-37/D-38/D-39)
- 전 변이 경로(add/note/consume/reinforce/merge/prune/graduate/reattribute/delete/restore/lifecycle-expire)가 `write-events.jsonl`에 1줄 append — 필드 `ts/action/id/tier/scope/type/actor/sid/snippet(≤80자)`. RECALL_EVENTS와 동일 rotation 패턴(256KB/최근 500줄)의 쓰기측 대칭. dump.jsonl·agent-memory 동기 대상 아님(로컬 관측 데이터).
- 저널 경로 우선순위: `MEM_WRITE_EVENTS` 명시 > **`MEM_STORE` override 시 그 store 옆**(`<store>/write-events.jsonl` — fixture DB 를 쓰는 모든 테스트가 실 XDG 저널을 오염시키지 않는 격리 계약, 2026-07-11 실유출 회귀 고정) > `$XDG_STATE_HOME/agent-memory/write-events.jsonl` 기본.
- **fail-open (graveyard와 반대 방향, 의도적)**: 저널 append 실패는 절대 mutation을 막지 않는다. graveyard(파괴 복구 안전망)=fail-closed 유지, 저널(관측 telemetry)=fail-open — 이중화가 아니라 역할이 다른 두 안전판.
- actor 결정론: `MEM_ACTOR`(명시 override) → `MEM_DISTILL=1`(distiller) → 각 함수 호출 맥락 default(예: `restore`→restore, `lifecycle --apply`→lifecycle) → 최종 fallback `manual`. `apply-distill-actions.py`는 `--mode curate` 실행 시 자식 프로세스 env에 `MEM_ACTOR=curator`를 세팅해 D-18 큐레이터 실행분을 세션 distiller(`MEM_DISTILL=1`)와 구분한다.
- `mem log`는 `stats`(스냅샷)를 보완하는 흐름(시간축) 조회이지 대체가 아니다.
- `mem doctor`는 read-only 진단 전용 — 발견을 스스로 고치지 않는다. 삭제·consolidate·merge·graduate 실행 권한은 세션끝 opus 큐레이터(D-18)에 있고, doctor 발견은 그 입력·oncall 안건으로만 흐른다 (D-25).
- `MEM_STORE` → `memory.db` 경로와 `dump.jsonl` 경로 모두 이 디렉터리 하위로 파생됨.
- `MEM_PROFILE` → `export --target profile` 의 출력 디렉터리. 테스트 시 `/tmp/...` 로 지정해 실 `user_profile/` 보호.
- `MEM_INJECT_MAX_CHARS` / `MEM_INJECT_MAX_BULLETS` → SessionStart memory injection hard cap when an adapter enables automatic or opt-in injection. 기본 2000자·15 bullet. 초과분은 본문 주입 대신 생략 요약과 `mem recall` 안내로 전환해 초기 컨텍스트를 보호.
- `MEM_INJECT_MAX_WORKING` / `MEM_INJECT_MAX_DURABLE` / `MEM_INJECT_CLEANUP_LINES` / `MEM_INJECT_SNIPPET_CHARS` → 위 hard cap 안에서 섹션별 기본 예산을 조정. 기본 working 8, durable 4, cleanup 2줄, snippet 100자.
- `MEM_DISTILL_ENABLE` → **distiller opt-in 게이트**. `1` 일 때만 `mem-distill-dispatch.sh` 가 실제 분사. 미설정이면 hook 은 no-op. 이유: 매 세션 종료·N턴마다 background LLM 자동 실행(비용·동작 인지) + distiller 가 대화 본문(외부 입력일 수 있음)을 LLM 으로 읽는 신뢰경계 면 → 사용자가 검토 후 활성화. Adapter-native settings own whether this is enabled in a runtime. v8 no-tools 재설계로 acceptance(임의명령 차단 실측)·env-상속 재귀가드·ghost-marker·e2e 검증 통과 후 ENABLE 가능. (`--permission-mode` 는 default 유지 — dontAsk/bypass 는 allow-all 이라 금지.)
- `MEM_DISTILL` → `1` keeps distillation lifecycle hooks from recursively launching another worker. `mem-recall-inject.sh` is a deprecated no-op retained only for stale installed projections.
- `MEM_DISTILL_WORKER` → shared dispatcher 가 호출할 adapter-owned executable. Contract: `<worker> <mode> <model> <prompt-file>`; stdout 은 JSON-lines proposal 이고 no-tools/permission contract 는 adapter worker 가 보장한다.
- `MEM_DISTILL_MODEL` → distiller 분사 모델 지정. Concrete defaults belong to adapter-native realization docs.

## Agent-owned semantic judgment

There is no deterministic promote/skip classifier. Main agents, distillers, and
curators make semantic choices from context. Scripts validate structured
actions and enforce storage safety; keyword lists, fixed phrases, content
categories, and confidence thresholds do not substitute for an agent.

## 운영 계약 (2026-07-10)
- **저장 구조**: `memory.db` (SQLite WAL) — schema v5 `records` 테이블 16컬럼(기존 v4 15컬럼 + `delivery_state`) + FTS5 unicode61 가상테이블(`records_fts`) + trigram CJK 보조 테이블(`records_trig`). `.index.db` 파생 파일 폐기(DB 내장으로 통합).
- **git mirror**: `dump.jsonl` — id 정렬, `sort_keys=True`, 레코드당 1줄, NULL은 JSON `null`로 표기(키 누락·빈문자열 금지). 복원: `mem import dump.jsonl`.
- **하네스 wired**: SessionStart `mem inject --hook` can be a runtime hook/preflight realization, but adapters may keep it opt-in to avoid repeated startup/resume/compact context injection; SessionEnd `mem sync`, and optional SessionEnd `mem-distill-dispatch.sh` are runtime hook/preflight realizations. `sync`는 흡수 + FTS 재구축 + `dump.jsonl` 재export 3단계 수행. `mem-distill-dispatch.sh` 는 빈-delta 조기 exit + detached spawn 으로 SessionEnd 블로킹 없음. **단 distiller 는 `MEM_DISTILL_ENABLE=1` opt-in 전엔 no-op**(기본 비활성 — 비용·신뢰경계 검토 후 사용자가 켬).
- **recall.sh**: `mem recall` thin wrapper (store FTS5 bm25 + trigram CJK + LIKE fallback + full/limit options).
- **register-postit deprecated**: legacy-migration-only. 현 post-it 경로는 DB working 레코드 직접 write (`mem note`/`mem add`) — `.postit-roots` 레지스트리·`migrate` post-it 소스는 구 markdown 이관 전용.
- ✅ **live 적용 완료**: `migrate --apply` 로 기존 markdown SoT + auto-memory + post-it → DB 이관 완료. DB-as-SoT 전환 끝 (구 `projects/*/memory/` 는 보존, 추가형).

`index-check.sh` 는 *legacy `projects/*/memory/` 의 MEMORY.md 텍스트 인덱스 점검 전용*으로 잔존 — store FTS5 색인은 `mem index` 가 관할(`memory.db` 내장)하므로 별개 대상.
