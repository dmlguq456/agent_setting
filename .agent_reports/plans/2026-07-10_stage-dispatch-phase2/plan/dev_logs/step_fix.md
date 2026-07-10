# Fix cycle — projection/mirror 동기화 (code-test 신규 회귀 2건)

집중 retry. 대상: code-test(Level 3) 가 확정한 신규 회귀 2건만. 이미 구현된 Phase A–J(커밋 5ae8c8a..8224285)는 재작업하지 않음.

## 재현 (수정 전)

```
$ bash tools/check-adaptation-boundary.sh
FAIL: no projection decision for utilities/dispatch-wait.sh (must be classified projected or deferred)
FAIL: no projection decision for utilities/dispatch-wait.test.sh (must be classified projected or deferred)
FAIL: no projection decision for utilities/dispatch-wait.sh (must be classified projected or deferred)
FAIL: no projection decision for utilities/dispatch-wait.test.sh (must be classified projected or deferred)
FAIL: skills/ compatibility refs must stay byte-equivalent to adapters/claude/skills/ except .sync_state.json:
  (10개 파일 differ — autopilot-{code,design,draft,lab,research,spec} SKILL.md/references)
FAIL: adapters/claude/hooks/conductor-stop-gate.sh is missing
FAIL: adapters/claude/hooks/stage-dispatch-reminder.sh is missing
```

## 원인

1. **projection decision 누락**: `tools/check-adaptation-boundary.sh` 의 `check_codex_utility_projection`/`check_opencode_utility_projection` 두 함수 각각 `UTILITY_PROJECTED`/`UTILITY_DEFERRED` 하드코드 목록으로 `utilities/*` 완결성을 검사(P-40 audit derived pair). Phase 2 C4 에서 신규 추가한 `utilities/dispatch-wait.sh`·`.test.sh` 가 이 목록에 없어 "no projection decision" FAIL.
2. **skills 미러 stale**: Phase 2 가 `skills/**` 10파일(SKILL.md·references)을 직접 편집했지만 `adapters/claude/skills/**` 미러(Claude native source)는 갱신 안 됨 — sync-skills 캐논 경로(`--force` 재생성 등)를 안 거쳤기 때문.
3. **hooks 미러 누락**: Phase 2 E1/E2 에서 신규 생성한 `hooks/{conductor-stop-gate.sh,stage-dispatch-reminder.sh}` 가 `adapters/claude/hooks/` 에 대응 심링크가 없음 — 기존 hooks(예: git-state-guard.sh 등)는 전부 `../../../hooks/<name>` 심링크로 collapse 되어 있는데 이 2개만 누락.

## 조사 (정규 동기화 경로 확인)

- `adaptation-exemptions.tsv` 헤더: "여기에 없는 최상위 공유층 파일은 canonical(`../../../<layer>/<name>`)로 collapse(symlink)되어 있어야 한다 — collapse 가 기본, 예외가 증명 부담." → hooks 미러 기본 해법 = 심링크.
- `skills/sync-skills/SKILL.md` §Targets: "Claude Skills: `adapters/claude/skills/*/SKILL.md`" 가 입력(source of truth), "Skill compatibility refs: `skills/*/SKILL.md` (parity/drift check only)". `git diff --stat -- skills/ adapters/claude/skills/` 로 실제 diff 확인한 결과 skills/ 쪽이 Phase 2 편집분(순수 추가, mtime 최신)이고 adapters 쪽이 stale — 충돌 없는 단순 반영이라 판단해 `skills/<f>` → `adapters/claude/skills/<f>` 복사로 byte-equivalent 회복(sync-skills skill 자체를 풀 파이프로 돌리지 않음 — 이 회귀는 10파일 단순 反영이고 sync-skills 는 README/manifest 재생성까지 포함한 더 큰 절차라 범위 초과 판단).
- `utilities/dispatch-liveness.sh`·`.test.sh` 가 이미 두 함수의 `UTILITY_DEFERRED`(Codex/OpenCode 미문서화 보류)에 있음 — 동일 클래스(dispatch 계열, Codex/OpenCode 지원 미문서화)인 `dispatch-wait.sh`·`.test.sh` 를 같은 선례로 `UTILITY_DEFERRED` 에 추가.

## 수정

1. `tools/check-adaptation-boundary.sh`: `check_codex_utility_projection`/`check_opencode_utility_projection` 두 곳의 `UTILITY_DEFERRED` 목록·"must not be projected" 루프에 `dispatch-wait.sh dispatch-wait.test.sh` 추가.
2. `adapters/claude/hooks/conductor-stop-gate.sh` → `../../../hooks/conductor-stop-gate.sh` 심링크 생성.
3. `adapters/claude/hooks/stage-dispatch-reminder.sh` → `../../../hooks/stage-dispatch-reminder.sh` 심링크 생성.
4. `skills/**` 10파일을 `adapters/claude/skills/**` 로 복사(byte-equivalent 회복).
5. `python3 tools/build-manifest.py` 재실행 (미러 변경분 반영, `manifest.json` 재생성).

## 검증 (수정 후)

```
$ bash tools/check-adaptation-boundary.sh
OK: adaptation boundary checks passed

$ python3 tools/build-manifest.py --check
manifest up-to-date; delta baselines bound
```

신규 FAIL 5줄(2 projection + 10 mirror + 2 hook) 전부 해소. baseline 기존 FAIL 10건(code-test Level 3 보고, `8596e25` 에서도 재현)은 본 스크립트 범위 밖(별도 환경 FAIL) — 손대지 않음, 재현 확인은 code-test 산출물 참조.

## 변경 파일
- `tools/check-adaptation-boundary.sh` (2곳 UTILITY_DEFERRED 목록 갱신)
- `adapters/claude/hooks/conductor-stop-gate.sh` (신규 심링크)
- `adapters/claude/hooks/stage-dispatch-reminder.sh` (신규 심링크)
- `adapters/claude/skills/autopilot-code/{SKILL.md,references/dev-pipeline.md}`
- `adapters/claude/skills/autopilot-design/SKILL.md`
- `adapters/claude/skills/autopilot-draft/references/pipeline-steps.md`
- `adapters/claude/skills/autopilot-lab/references/{eval-procedure.md,setup-procedure.md}`
- `adapters/claude/skills/autopilot-research/references/{pipeline-search-analysis.md,report-generation.md}`
- `adapters/claude/skills/autopilot-spec/references/{prd-authoring.md,scaffolding.md}`
- `manifest.json` (재생성)
