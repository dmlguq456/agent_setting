# harness-layer-sync Phase 2 — 구현 plan

> spec: `.agent_reports/spec/harness-layer-sync/prd.md` §3.2·§3.3·§5·§6 / §10 Phase 2 항목 6~8 / §11 HLS-3·4·7·8·9
> 선행: Phase 1 (main 머지, 커밋 `29f714f`) — collapse 27 + 예외 concrete 4 (wrapper 2 / delta 2), 가드 `assert_shared_adapter_class` 3-class 계약, dispatch-liveness runtime-root 정정.
> mode: dev / intensity: strong / branch: `layer-sync-phase2`

## 0. GSD 실코드 정독 evidence (§3.2 gate — 카드 서술 이식 금지, 실코드 재확인)

정독 대상: `open-gsd/gsd-core` (branch `next`) — `bin/install.js` (11,528줄), `gsd-core/bin/lib/state-transition.cjs` (1,603줄). `/tmp/gsd-core-read` 로 clone 후 line 단위 정독.

### manifest 스키마 (`bin/install.js` L7714–7969)
- 상수: `MANIFEST_NAME = 'gsd-file-manifest.json'`, `PATCHES_DIR_NAME = 'gsd-local-patches'`.
- `fileHash(path)` (L7718) = `crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex')` — **raw byte sha256, 정규화 없음**. line-diff 아님.
- `generateManifest(dir, baseDir)` (L7728) = 재귀 walk, 파일별 `{POSIX-relpath: sha256}` map. 디렉터리는 재귀 병합.
- `writeManifest()` (L7780) 산출 = `{version, timestamp, mode, files:{relpath:hash}}`. **`USER_OWNED_ARTIFACTS` 는 hash 에서 제외**(L7810 근처) — 안 그러면 매 refresh 가 그 파일을 "local patch" 로 오탐(bug #2771). ⇒ 소유 경계 = 해시 대상에서의 명시 제외 목록.

### 감지 알고리즘 (`saveLocalPatches()` L8057–8233)
- 저장된 manifest 를 읽어 각 `{relPath, originalHash}` 에 대해 `currentHash = fileHash(live)` 계산 → **`currentHash !== originalHash` 면 로컬 수정 감지** → `gsd-local-patches/` 로 백업.
- `resolveInstallRelativePath` (L7761) = path-safety(절대경로·`..`·심링크 traversal 거부, root 밖 이탈 거부). 우리 repo-relative 신뢰 경로엔 과할 수 있으나 개념 차용.
- 3-way merge baseline = `gsd-pristine/` (originalHash 로 검증된 "수정 안 됐다면 install 이 썼을 내용"). pristine vs user vs new-release.

### 소유 경계 (`state-transition.cjs` FIELD_CLASSIFICATION L49–74)
- **단일 테이블이 "frontmatter↔body 충돌 시 어느 필드가 이기나"를 선언** — `preserve-when-unchanged`/`preserve-always`/`derive`/`preserve-if-placeholder`. "필드 추가 = 이 테이블에 한 행, 9개 transition 편집 아님." null-prototype freeze 로 prototype-pollution 차단.

### 우리에 이식할 것 / 버릴 것
- **이식**: (1) baseline = **canonical raw-byte sha256** 을 선언 파일에 기록, drift = live 재계산 후 불일치 red (GSD manifest 모델 그대로). (2) 선언은 **단일 declaration 파일**(`adaptation-exemptions.tsv` — FIELD_CLASSIFICATION/ USER_OWNED_ARTIFACTS 처럼 "한 행 = 한 결정"). (3) 소유 경계 = 명시 목록(collapse 기본, 예외가 증명 부담 — 이미 Phase 1).
- **버림**: `gsd-local-patches/`·`--reapply` 3-way merge·`gsd-pristine/` 재생성. 우리 delta 예외는 **2개뿐**이고 upstream 소비가 아니라 우리가 소유한 내부 sync 라, 자동 patch reapply 는 과잉. 대신 **baseline drift → 가드 red → 사람이 재파생** (§0.7 의미판단 구간). GSD 도 자동 재적용은 `/gsd-update --reapply` 사용자 명령이지 무인 아님.

⇒ 결론: HLS-3 hash-manifest = "delta 예외의 `delta_baseline` 필드에 canonical raw-byte sha256 을 바인딩, 가드가 live canonical 재해시 후 불일치 시 red". S-1(fix 가 canonical 한쪽만) 을 delta 파일에도 닫는다 — canonical 이 바뀌면 hash 가 뒤집혀 가드가 즉시 재파생을 강제.

## 1. 항목별 구현

### 항목 6 — hash-manifest (HLS-3)
- `tools/adaptation-exemptions.tsv`: delta 2행의 4번째 필드(`delta_baseline`) `-` → canonical raw-byte sha256.
  - `hooks/mem-distill-dispatch.sh` = `0eacc8fa…`
  - `utilities/agent-worklog-state.sh` = `d42789a2…`
- `tools/build-manifest.py` (증분, HLS-4): `delta_baselines()` builder + CLI:
  - `--sync-baselines`: exemptions.tsv delta 행의 baseline 을 live canonical sha256 으로 재기록(생성기 절반).
  - `--check` 확장: manifest.json drift + delta baseline drift 를 함께 검증(검증 절반, drill/CI 단일 진입점).
- `tools/check-adaptation-boundary.sh` `assert_shared_adapter_class` delta 분기: 4번째 필드가 64-hex sha256 이고 `== sha256(canonical)` 인지 assert. `-`/불일치 → red.

### 항목 7 — INVENTORY 파생 (HLS-7)
- `tools/build-manifest.py`: `--adaptation-surface` 프린터 — 파일시스템 파생 집합 출력.
  - `codex-hooks`: `adapters/codex/hooks/*.py` (native hook bridge 집합).
  - `shared-canonical`: `hooks/` `utilities/` `tools/`(top-level) canonical 파일 + exemptions 클래스.
- `tools/check-adaptation-boundary.sh`:
  - L868 하드코딩 7-file codex native hook 열거 → `--adaptation-surface codex-hooks` iterate 로 교체.
  - `core/ADAPTATION_INVENTORY.md` line 33 (Codex native hook surface 행)이 파생 집합의 모든 파일을 참조하는지 대조 — drift red. (ledger 파일목록 = 파생 대조, prose = 사유만.)

### 항목 8a — parity-loss explicit warning (HLS-8, §6.1)
- `tools/check-adaptation-boundary.sh` `check_parity_loss_explicit_warnings` 신설: one-runtime-only 기능(hook 실행 격리·loop auto-run·claude headless/allowedTools/settings-mcp)이 codex/opencode 표면에 **명시 `unsupported`/`fallback` 로 신고**돼 있는지 존재 검증. 누락 = silent skip → red. research 결론(hook 실행 격리는 없는 런타임서 재현 불가)을 정직 반영.

### 항목 8b — bootstrap byte-budget (HLS-9, §6.2)
- `tools/check-adaptation-boundary.sh` `check_bootstrap_byte_budget` 신설: adapter bootstrap byte 상한.
  - `adapters/claude/CLAUDE.md` ≤ 28672 (현재 22850, ~25% 여유; "비확장" 운영정책과 정합).
  - `adapters/codex/AGENTS.md` ≤ 32768 (현재 19136; **Codex `project_doc_max_bytes` 기본 truncation cliff = 32768** 을 상한으로 앵커 — 넘으면 조용히 잘림).
  - `adapters/opencode/AGENTS.md` ≤ 24576 (현재 11750, 여유).
  - 상한 근거를 주석·보고에 명시. GSD `tests/workflow-size-budget.test.cjs` (byte 상한, Codex 정렬) 차용.

### 옵션 — build-manifest REPO_ROOT realpath
- `REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))` (abspath→realpath). 어댑터 심링크(`adapters/claude/tools/build-manifest.py` → canonical) 직접 실행 시 이중경로 소거. 회귀 테스트 포함.

## 2. 검증
- `tools/check-adaptation-boundary.sh` green.
- 음성테스트 `tools/adaptation-guard.test.sh`: delta baseline 어긋남 red / byte-budget 초과 red / 파생집합 대비 ledger drift red / realpath 이중경로.
- `python3 tools/build-manifest.py --check` up-to-date (manifest + baseline).
- `bash -n` 전 변경 스크립트.
- background 금지 — 전부 foreground. drill 은 merge 후 main 실행(사유 보고).

## 3. 경계
- b2(HLS-OPEN-1) 미착수. 지침 파일 문구 변경은 core-first 순서 — ADAPTATION_INVENTORY 는 core 라 최소 diff 로 직접 진행(§5 "core 가 먼저").
- 커밋 누적, push/merge 금지.
