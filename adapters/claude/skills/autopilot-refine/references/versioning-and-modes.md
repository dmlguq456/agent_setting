# autopilot-refine — Versioning & mode detail

Router(`../SKILL.md`)의 `## Default Invocation Rule` / `## Verification rigor` / `## Mode Forms` 에서 참조되는 세부. minor log 형식, major 적용 동작, why-this-split rationale, adversarial-tier propagation, mode-forms default/STRUCT-halt 근거, tunable constants.

### Minor log entry 형식 (반드시 준수 — 추적성 핵심)

`pipeline_summary.md`의 (a) 버전 히스토리 표에 1줄 row 추가 + (b) `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션에 상세 block 추가 (newest entry 위쪽).

**(a) 버전 히스토리 row** (기존 표에 append):

```markdown
| v{N}_M | YYYY-MM-DD | (minor) 한 줄 요지 ≤120자 |
```

**(b) 마이너 변경 로그 entry** (없으면 섹션 신규 생성 — 위치: `## 미해결 이슈` 직전 또는 표 직후):

```markdown
### v{N}_M — YYYY-MM-DD HH:MM
- **Trigger**: 사용자 prompt verbatim 한 줄 인용 (≤80자)
- **Scope**: minor (직접 Edit, no snapshot)
- **Rationale**: 왜 minor로 분류했는지 (3-criteria 중 어디에도 해당 안 함 / 단일 entry 단위 / etc.)
- **Files touched**:
  - `relative/path/file1.md` — 무엇을 어떻게 바꿨는지 1-2줄
  - `relative/path/file2.md` — 무엇을 어떻게 바꿨는지 1-2줄
- **Cross-ref / deps**: 다른 mutation·label·downstream artifact와의 의존 (없으면 "—")
- **Audit-flag**: 향후 audit이 점검해야 할 측면 — `facts`/`style`/`structure`/`cross-ref`/`coverage` 중 해당 (none이면 "—")
- **Reversibility**: 이 변경을 되돌리려면 어디를 어떻게 (Edit 위치 + 원본 wording) — 없으면 "git revert 또는 last major snapshot reference"
```

> **Audit-flag**는 핵심 — 누적 minor 점검 시 audit이 각 entry의 audit-flag를 collate해 dual-perspective 첫 번째 pass (vs last major)를 효율적으로 scope.

**(c) 각 affected file frontmatter `changelog:` 1줄 entry** — file의 YAML frontmatter에 `changelog:` array가 정의돼 있으면, 새 version entry를 array 최상단에 insert:

```yaml
changelog:
  - version: v{N}_M
    date: "{YYYY-MM-DDTHH:MM}"
    applied: {count}
    overridden: 0
    entries:
      - |
        [MINOR {scope}] [direct Edit]: {1줄 변경 요약, ≤200자}
  - version: v{N}_{M-1}
    ... (기존 entries 보존)
```

frontmatter `changelog:` 필드 자체가 없는 file은 skip. **이 step은 pipeline_summary 마이너 로그 entry (위 b) 와 중복 layer**지만, in-file frontmatter는 git-tracked file 자체에 남아 `git log {file}` + frontmatter scan만으로 해당 파일의 변경 lineage 추적 가능 — pipeline_summary가 손상되거나 cross-artifact reference 시점에 유용.

### Major 적용 시 동작

`autopilot-refine` 자동 invoke (selected intensity/QA 사용):

1. Stage A-D 정상 흐름 (investigate → diff preview → 자동 apply → snapshot)
2. snapshot: `_internal/versions/v{N+1}/` 생성
3. **누적 minor log migration**: pipeline_summary.md의 `## 마이너 변경 로그 (v{N} → next major)` 섹션 전체를 _verbatim_ 으로 새 major의 `## v{N+1} 변경 사항` 섹션 안 `### 누적 마이너 변경 사항 (v{N}_1 → v{N}_M)` sub-block 으로 migrate. 활성 마이너 로그 섹션 clear (다음 major까지 빈 상태).
4. `## 버전 히스토리` 표에 major row `| **v{N+1}** | ... | (major) ... |` 추가

### Why this split

대부분 일상 변경은 entry-level minor — 매 minor마다 refine flow (QA agent invocation + snapshot + version bump)를 묶는 건 cost 대비 가치 낮음. 단 **추적성은 유지**: 모든 minor가 `pipeline_summary.md` minor log에 trigger / files / audit-flag / reversibility까지 기록되므로 last major 이후 변경 이력은 _완전히_ 보존된다. 누적된 minor가 일정 임계치를 넘으면 audit이 **dual-perspective** (vs last major snapshot diff + vs universal principles)로 batch 점검 → fix chain dispatch. major는 _진짜 ceremony 시점_ (외부 검토 직전·구조 재설계·cycle 재진입)에만 refine flow의 ceremony cost를 발생시킨다.

### adversarial-tier propagation (from `## Verification rigor`)

> **`adversarial` propagation**: at this tier, after the thorough reviewers return, spawn external adversary (`Agent(codex-review-team)` in Claude adapter) with (a) the proposed diff, (b) the artifact's intent (from `pipeline_summary.md`), and (c) the source ground-truth (research: `cards/*.md`; doc: `analysis/*.md` + existing strategy/draft). Surface external findings alongside internal reviewer findings before the user-confirm step. If the external adversary flags a blocking issue, mark it in the diff preview as `⚠ External: <issue>` so the user can decide whether to apply, revise, or abort.

### Mode Forms notes (from `## Mode Forms`)

> **Default = 자동 apply 근거**: family 다른 멤버(`autopilot-research/code/doc`)는 모두 confirm 없이 pipeline 끝까지 실행 — autopilot 정신. refine만 default가 confirm이면 이름과 mismatch. Safety net: (a) `_internal/versions/v{prev}/` 스냅샷, (b) `pipeline_summary.md` 통합 history, (c) `git diff` 즉시 검토, (d) Stage B.5 `⚠ Unverified/Style` marker가 본문에 박혀 사후 git diff에서 식별 가능, (e) audit auto-fix chain dispatch와 정합.

> **STRUCT halt (escape hatch)**: 변경이 5+ files / 전체 section rewrite / autopilot pipeline 재실행 필요로 분류되면 _자동 apply 안 함_. halt + 사용자에게 heavier flow 권장 (`/autopilot-research --from analyze` 또는 `/autopilot-draft --from strategy`). 이건 default 변경 후에도 유지.

### Tunable constants

| Constant | Default | Description |
|---|---|---|
| `AUDIT_HINT_THRESHOLD` | 5 | Number of refine cycles after which Stage D emits a `/audit` recommendation hint. Set to a higher value (e.g., 10) to reduce hint frequency; set to `0` to disable the hint entirely. |
