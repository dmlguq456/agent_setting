---
name: autopilot-apply
description: "Autopilot family — the document-side _apply + verify_ arm. Takes a draft-produced cheatsheet (a mutation/edit plan) and applies it to a real working source file _outside_ `.claude_reports/` (e.g. the user's `main.tex`), under git, with a build/compile verify gate. This is the missing counterpart to autopilot-draft: draft _produces_ the cheatsheet (plan), autopilot-apply _executes_ it on the canonical source and _verifies_ it compiles — mirroring code-execute + code-test on the code side. Default target `latex` (latexmk compile gate + latexdiff rendered-diff review). Never touches the canonical source directly: applies on a git branch (or worktree), each mutation = one commit, hands back via `git merge`. Cheatsheet auto-discovered from `.claude_reports/documents/*/draft/`. NOT for `.claude_reports/` markdown artifacts (use autopilot-refine) or codebases (use autopilot-code)."
argument-hint: "\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]"
metadata:
  group: entry
  fam: doc
  modes: []
  blurb: "cheatsheet 초안을 canonical main.tex 에 paste·반영하는 적용 entry"
---

> **산출물 폴더 컨벤션**: 본 skill 은 _.claude_reports/ 밖의 실제 작업 파일_ 을 편집한다 (예외적). 자기 로그·스냅샷은 cheatsheet artifact 의 `_internal/apply/` 하위에 둔다 ([CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) T3).

## Position in autopilot family

family 를 _계획·생성_ vs _실제 대상에 적용+검증_ 으로 나누면, 코드 쪽은 `autopilot-code` 한 스킬에 plan→execute→test 가 다 들었지만 문서 쪽은 `autopilot-draft` 가 **계획(cheatsheet)까지만** 만들고 멈춘다. 그 뒤 사용자가 손으로 main.tex 에 paste 하던 단계가 곧 _문서 쪽 execute+verify_ 였고, autopilot-apply 가 그 빠진 팔이다.

| | 계획·생성 | 실제 대상에 적용 + 검증 |
|---|---|---|
| **코드** | autopilot-spec / code-plan | autopilot-code (execute + test) |
| **문서** | autopilot-draft → cheatsheet | **autopilot-apply** (apply + compile) |

- cheatsheet = plan. autopilot-apply 는 plan 을 새로 만들지 않는다 — _기존 cheatsheet 를 읽어 적용만_ 한다.
- 검증기 = build/compile (latexmk) + latexdiff. run-test 가 코드의 verify 이듯, compile gate 가 문서의 verify.
- 같은 `--target` 추상화로 latex 외 build-검증 대상도 나중에 재사용 (지금은 latex 만 구현).

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §0 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상 (ceremony 큰 갈래 — 실제 사용자 source 파일을 건드리므로). 메인 Claude 가 아래 trigger 를 인지하면 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)
- "cheatsheet 를 main.tex 에 적용해줘" / "mutation 직접 붙여줘" / "paste 대신 클로드가 적용해"
- "이 변경들 논문 소스에 반영하고 컴파일 확인해줘"
- "{문서 artifact} 의 cheatsheet 를 실제 LaTeX 에 적용"

### Default 옵션 권장값 (컨펌 시 제안)
- `--target`: `latex` (현재 유일 구현)
- `--isolation`: `branch` (default — git 분기. 대규모/위험하면 `worktree` 제안)
- `--source`: cheatsheet 의 verification 섹션에서 자동 추론, 못 찾으면 컨펌 자리에서 질문
- cheatsheet: prompt 키워드로 `.claude_reports/documents/*` fuzzy match (autopilot-refine 와 동일 방식)

### Override 1순위 — autopilot 우회
- cheatsheet 자체를 _고치는_ 일 (적용 아님) → `/autopilot-refine` 또는 `/autopilot-draft --from draft`
- `.claude_reports/` 안 markdown 산출물 수정 → `/autopilot-refine`
- 코드베이스 변경 → `/autopilot-code`
- `/autopilot-apply <args>` slash 직접 입력 → 컨펌 skip, 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `~/.claude/README.md` 운영 룰로 자동 반영.

## Scope

- **Targets**: `.claude_reports/` _밖_ 의 실제 작업 source (현재 `--target latex` → `*.tex`). git 으로 추적되는 프로젝트 전제.
- **Source of changes**: `.claude_reports/documents/*/draft/draft*.md` 의 cheatsheet (autopilot-draft paper mode 산출물). 새 plan 을 만들지 않는다.
- **NOT for**:
  - `.claude_reports/{research,documents}/*` markdown 산출물 → `/autopilot-refine`
  - `.claude_reports/plans/*` / 코드베이스 → `/autopilot-code`
  - cheatsheet 가 아직 없을 때 → 먼저 `/autopilot-draft --mode paper`

## Preconditions (Stage A 에서 강제 — 하나라도 실패 시 abort)

1. **git 추적**: `--source` 가 가리키는 파일이 git repo 안에 있어야 한다. 아니면 abort: "autopilot-apply 는 git 추적 전제 — `git init` + 첫 commit 후 재시도."
2. **git working-state** ([OPERATIONS.md §5.9](../../OPERATIONS.md#59-git-working-state-preflight-worktreemerge-가드-canonical)): source 파일에 커밋 안 된 사용자 편집(dirty)이 있거나, **merge/rebase/cherry-pick 진행 중·detached HEAD** 면 abort + "먼저 commit/stash 하거나 진행 중 머지를 해결하세요." (진행 중 작업·반쯤 머지된 트리 클로버 방지)
3. **cheatsheet 존재**: fuzzy match 로 1건 식별. 다수면 list, 0건이면 안내.
4. **build 도구 가용** (`--target latex`): `latexmk` 또는 `pdflatex` 존재 확인. latexdiff 는 _권장_ (없으면 git diff fallback, abort 아님).

전제 실패 시 branch 생성·편집·commit 어느 것도 하지 않고 즉시 종료한다.

## --target <type> (default: latex)

검증기·diff 도구를 고른다. mode 가 아니라 target 추상화.

| target | build/compile gate | rendered-diff review | source glob |
|---|---|---|---|
| `latex` (구현) | `latexmk -pdf -interaction=nonstopmode -outdir="$BUILD_OUT"` (없으면 `pdflatex` 2-pass + bibtex/biber, 동일 `-output-directory`) | `latexdiff <base> <head>` → 컴파일 (실패 시 `git diff` 텍스트 fallback) | `*.tex` |

> 전체 프로젝트로 컴파일한다 — `\input` / 별도 `.sty` / `.bib` 포함. main.tex 단독 컴파일은 false fail 위험. latexmk 가 다중 패스(bibtex/biber) 자동 처리하므로 우선.
>
> **빌드 출력은 로컬 temp 로 (`$BUILD_OUT`)** — Preflight 에서 run 당 한 번 `BUILD_OUT=$(mktemp -d /tmp/lw-apply.XXXXXX)` 생성하고, 이 skill 의 _모든_ 컴파일(baseline / compile gate / latexdiff)에 `-outdir="$BUILD_OUT"` 를 동일하게 넘긴다. 이유: ① source 가 NAS/네트워크 마운트일 때 빌드 I/O 를 로컬 디스크로 빼 속도 회복 ② 사용자 repo 폴더에 `main.aux`/`.pdf` 등 빌드 산출물을 흩뿌리지 않음(repo 비오염). baseline 과 gate 가 _같은_ outdir 을 써야 에러 증가분 비교가 유효하다. 컴파일 에러 판정은 stdout/log 로 하므로 outdir 위치와 무관. latexdiff 결과 PDF 만 `$BUILD_OUT` 에서 `_internal/apply/latexdiff.pdf` 로 복사.

## Language Rule
사용자 향 출력 (chat 요약, diff 안내, report) 은 자연스러운 **한국어** (번역체 회피 — 영어 초안을 옮기지 말고 처음부터 한국어로).

---

## Pipeline

### Stage A — Preflight (적용 전 ceremony)

1. **Cheatsheet 식별**: prompt 키워드로 `ls -d .claude_reports/documents/*<kw>*` fuzzy match → cheatsheet 파일 (`draft/draft.md` 또는 `draft/draft_ko.md`). 다수/0건 처리는 autopilot-refine Artifact Resolution 과 동일.
2. **Source 식별**: `--source` 명시값 우선. 없으면 cheatsheet 의 _최종 verification 체크리스트_ / WHERE anchor 에서 `*.tex` 경로 grep 추론. 못 찾으면 사용자에게 질문 (글로벌 §2 적용 — ScheduleWakeup 10분, 답 없으면 가장 그럴듯한 단일 `main.tex` 로 진행).
3. **Precondition gate** (위 Preconditions 1-4) 강제. 실패 시 abort.
4. **Mutation 파싱**: cheatsheet 에서 M-label 단위로 추출 — 각 mutation = `(M-id, where_anchor, classification, old_or_locator, new_block, reason)`. classification 은 cheatsheet 의 Tier (🔴/🟡/🟢) 또는 MECH/SEM/STRUCT 로 매핑.
5. **Isolation 진입**:
   - **base 선정 ([§5.9](../../OPERATIONS.md#59-git-working-state-preflight-worktreemerge-가드-canonical) DONE-BRANCH)**: 현재 브랜치가 base 에 이미 머지된 끝난 브랜치(ahead 0)거나 upstream 이 앞서면, apply 브랜치를 _현재 HEAD_ 가 아니라 _base 최신_ 에서 딴다 — `git fetch origin && git switch -c apply/{cheatsheet-short-name} origin/<base>`. (죽은/stale 브랜치 base 위에 cheatsheet 적용 방지.) 현재 브랜치가 최신 base 면 아래 default 그대로.
   - `--isolation branch` (default): `git checkout -b apply/{cheatsheet-short-name}`. base commit hash 기록.
   - `--isolation worktree`: 별도 worktree 생성 (canonical 체크아웃 물리적 불가침). 대규모·위험 시 권장.
6. **Baseline compile** (핵심 — 안 하면 compile gate 무의미): 먼저 run 당 로컬 빌드 출력 디렉토리를 한 번 생성 — `BUILD_OUT=$(mktemp -d /tmp/lw-apply.XXXXXX)` (이후 모든 컴파일이 `-outdir="$BUILD_OUT"` 공유). 그 다음 편집 _전_ build 1회. 기존 에러/경고/`undefined reference` 수를 `_internal/apply/baseline.log` 에 기록. _내가 낸 에러_ vs _원래 깨져 있던 것_ 구분의 기준선. (VS Code 의 인터랙티브 빌드와는 _별도_ 의 격리된 출력 — 서로의 aux 를 안 건드린다.)

### Stage B — Apply (mutation = commit)

mutation 을 cheatsheet 순서대로 적용. **각 mutation 하나당 git commit 하나**, commit message = `apply: {M-id} {1-line reason}`. → 사후 특정 mutation 만 `git revert <commit>` 로 외과적 되돌림 가능.

- **MECH / SEM mutation** → 자동 적용 + commit.
- **STRUCT mutation** (단락 통째 재작성 / section 이동 / 5+ 위치 동시 변경) → _자동 적용 안 함_. halt + 사용자에게 알림: "M{id} 는 구조적 변경 — 직접 검토 후 적용 권장." 나머지 MECH/SEM 은 계속 진행하고 STRUCT 만 skip-list 에 남긴다.
- Edit 은 exact-string match. anchor (section/subsection 기준 + 보조 line number) 로 위치 확정. `replace_all` 금지.
- 적용 중 mutation 이 cheatsheet 설명과 실제 source 가 안 맞으면 (anchor 못 찾음 등) 그 mutation 만 skip + skip-list 기록, 나머지 진행. anchor 가 exact-match 될 때만 적용한다 (빈칸 > 잘못 채우기).

### Stage C — Verify (compile gate + rendered diff)

1. **Compile gate**: build 재실행. baseline 대비 _새_ 에러 / `undefined reference` / **`multiply defined` label** 경고 증가분 계산 (경고지만 `multiply defined` 는 `\ref` 가 엉뚱한 대상을 가리키는 실제 버그라 게이트에 포함). 단 _시각 레이아웃_(본문 페이지 한도·footnote split·widow/orphan·overfull) 은 여기서 보지 않는다 — 그건 연구팀 review(autopilot-draft)의 책임이고, 수정은 사용자 몫이다. apply 에 build-반복 시각 게이트를 넣지 않는다(비용).
   - 증가분 0 → 통과.
   - 증가분 > 0 → 원인 mutation 식별 (마지막 commit 부터 이진 탐색 또는 직전 commit revert 후 재컴파일). 해당 commit `git revert` + skip-list 기록. 자동 격리 불가하면 **fail loudly + halt** — branch 는 그대로 두고 사용자에게 보고 (canonical 은 애초에 안 건드렸으므로 안전).
   - PDF 가 아예 안 나오면 halt — compile gate 통과한 branch 만 handback (미통과 시 fail loudly + halt).
2. **Rendered diff**: `latexdiff <base>.tex <head>.tex > diff.tex` → 컴파일 → `_internal/apply/latexdiff.pdf`. 추가=파랑, 삭제=빨강. 이게 사용자의 검토 화면 (paste 하며 읽던 것을 렌더 결과에서 한 번에). latexdiff 가 복잡한 매크로/표에서 실패하면 `git diff base..head -- '*.tex'` 텍스트로 fallback (merge 막지 않음).

### Stage D — Handback (사용자 검토 → merge 가 paste 를 대체)

직접 merge 하지 않는다 — branch 위 결과를 사용자에게 넘기고, 사용자의 `git merge` 가 곧 checkpoint (옛 paste 자리).

report (≤8줄, 한국어):
```
✓ autopilot-apply — {cheatsheet 식별} → {source}
• branch: apply/{name} (base {short-hash})
• 적용: {N}개 mutation (commit별), skip: {K}개
• compile: 새 에러 {0 / N}건 (baseline 대비)
• rendered diff: _internal/apply/latexdiff.pdf  ← 먼저 이걸 검토
• skip 목록: M{id}(STRUCT), M{id}(anchor 불일치) ...   (있을 때만)

검토 후:
  git merge apply/{name}        # 받아들이기 (= 기존 paste 자리)
  git diff main..apply/{name}   # 텍스트로 다시 보기
  git revert <commit>           # 특정 mutation만 되돌리기
  git branch -D apply/{name}    # 전부 버리기
```

**Apply 산출물 절차 (autopilot-draft artifact 연동, handback 시 필수)** — apply 는 draft 가 만든 artifact 를 입력으로 받고, 적용 결과를 _세 자리_ 에 일관되게 기록한다. **plan 본문(cheatsheet 의 위치·LaTeX·이유)은 절대 불변**, 진행 상태·이력만 갱신:

1. **Cheatsheet 체크박스 동기화** (`draft/draft.md`) — 적용 성공 mutation 의 anchor 를 _반영 전→완료_ 로 전환: `- [ ] **⏳ 반영 전**` → `- [x] **📌 반영 완료**` (체크 + ⏳→📌 + 라벨 교체). skip 은 ⏳(반영 전) 유지 + 한 줄 사유. 철회·false-positive 는 cheatsheet 본문서 _제거_ 하고 `_internal/apply/apply_log.md` 에 로그 (사용자 paste 대상 아님 — 내부 기록). 사용자가 손으로 [x] 갈아끼우던 작업의 자동화 — preview 만으로 적용/잔여 파악.
2. **pipeline_summary.md `## Apply 이력` 연동** (draft artifact 루트) — 실행마다 한 행 append: `{date} | branch {name} ({base}..{head}) | 적용 {N} / skip {K} | compile 새에러 {n} | mutation: {id 목록}`. draft pipeline 의 하위 이력으로 누적 (부분 적용·재실행 시 행 추가 — 어느 mutation 이 언제 적용됐는지 추적).
3. **`_internal/apply/`** — `apply_log.md`(mutation별 적용/skip/commit-hash 상세) + `apply_state.yaml`(`--from` 재개용) + `baseline.log`/`postfix.log`(compile gate 증거).

cheatsheet plan 본문은 재작성하지 않는다 — 틀렸으면 `autopilot-refine` / `autopilot-draft --from draft` 로 먼저 고친다 (Constraints 참조).

### `--from <stage>` 재개
`preflight` / `apply` / `verify` / `handback`. branch·base hash·source·cheatsheet 경로는 `_internal/apply/apply_state.yaml` 에서 복원.

```yaml
pipeline: autopilot-apply
target: latex
cheatsheet: <path>
source: <path-to-real-source>
isolation: branch
branch: apply/<name>
base_commit: <hash>
applied: [M3, M5, M7]
skipped: [{id: M9, reason: STRUCT}]
last_completed_stage: verify
```

---

## Constraints

- **canonical source 불가침** — Stage B/C 의 모든 편집·컴파일은 branch/worktree 위에서만. 사용자가 merge 하기 전까지 main 브랜치 source 는 안 건드린다.
- **compile gate 통과한 branch 만 handback** — 통과 못 하면 fail loudly + halt.
- **baseline 없이는 compile gate 없다** — Stage A.6 baseline compile 생략 금지.
- **mutation 위치는 exact-match 만** — anchor 못 맞추면 그 mutation skip + 기록. 빈칸 > 잘못 채우기.
- **plan 을 만들지 않는다** — cheatsheet 내용을 _재해석·증보_ 하지 않고 적힌 대로 적용만. cheatsheet 가 틀렸으면 autopilot-refine/draft 로 먼저 고친다.
- **merge 는 사용자 몫** — autopilot-apply 는 절대 자동 merge 하지 않는다 (사용자 검토 checkpoint 보존).

---

## Examples

```
# 기본 — cheatsheet 를 main.tex 에 branch 위로 적용 + 컴파일 검증
/autopilot-apply "tfrestormer camera-ready cheatsheet 적용" --source latex/main.tex

# worktree 격리 (canonical 체크아웃 물리적 불가침)
/autopilot-apply "icml rebuttal mutation 적용" --source paper/main.tex --isolation worktree

# 컴파일 실패로 halt 된 뒤 verify 부터 재개
/autopilot-apply "tfrestormer cheatsheet" --from verify
```

## When NOT to use
- cheatsheet 자체를 수정 → `/autopilot-refine` / `/autopilot-draft --from draft`
- `.claude_reports/` markdown 산출물 편집 → `/autopilot-refine`
- 코드베이스 변경 → `/autopilot-code`
- cheatsheet 가 아직 없음 → `/autopilot-draft --mode paper` 먼저
