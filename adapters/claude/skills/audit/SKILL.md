---
name: audit
description: "Use when doing a post-hoc audit of artifacts/pipeline (drift/consistency/gaps). 산출물·파이프 사후 점검 — drift·일관성·누락 진단 보고"
argument-hint: "<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]"
metadata:
  group: ops
  fam: ops
  modes: []
  blurb: "산출물·파이프 사후 점검 — drift·일관성·누락 진단 보고"
---

# audit

산출물·파이프 사후 점검 entry (read-only). Stage A→E (type 감지 → scope 결정 → P1 baseline ingestion → aspect lint → 보고 → auto-fix chain dispatch) 로 drift·일관성·누락을 진단한다. 이 파일은 라우터와 stage 계약만 담고, stage별 세부 절차·진단 축 정의·보고서 템플릿·예시는 필요할 때 아래 reference를 Read 한다.

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 본 skill은 입력 artifact를 _수정하지 않음_ — 점검 보고서만 생성. 보고서는 `{artifact_dir}/_internal/audit/audit_{YYYY-MM-DDTHHMM}.md`에 기록.
> `<artifact-root>` 해석·치환(`.agent_reports` 우선, legacy `.claude_reports` fallback): [CONVENTIONS §5.1](../../core/CONVENTIONS.md#51-workspace-assumption-전제).

## Position in autopilot family

`audit` is the **read-only inspection** counterpart to `autopilot-refine`:
- `autopilot-refine` reads + writes (proposes diff, applies on confirm, versions).
- `audit` reads only (lints, reports issues, never edits).

Use `audit` when:
- 누적 minor drift batch 점검 — autopilot-refine의 Default Invocation Rule에 따라 minor는 직접 Edit + `pipeline_summary.md` 상세 log만 남기므로, 누적된 minor를 audit이 일괄 점검하는 게 정상 워크플로우.
- 새 산출물 인계 전 sanity check.
- 다른 사람이 만든 artifact 평가.

Use `autopilot-refine` when:
- 구체적 major-level 수정 의도가 있고 곧장 적용까지 가져갈 때 (3-criteria 충족 — 사용자 명시 / 구조적 대규모 / 외부 검토 직전).

## Dual-perspective audit (doc / research 전용)

doc / research artifact에 대한 audit은 **두 관점**으로 동시 점검한다:

| Perspective | 무엇을 보는가 | 산출물 섹션 |
|---|---|---|
| **P1 — vs last major baseline** | `pipeline_summary.md`의 `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션 + `_internal/versions/v{N}/` 스냅샷 diff. 누적된 minor가 _집합적으로_ artifact를 어디로 drift시켰는지. | `## Perspective 1 — 누적 minor drift` |
| **P2 — vs universal principles** | 현재 artifact 상태를 Stage C aspect lint (facts / style / structure / cross-ref / coverage)로 점검. 시점 무관 정합성. | `## Perspective 2 — Universal principles` |

**왜 두 관점이 필요한가**:
- P1만 보면 — "변경된 것"만 보이고 "오래 전부터 누적된 미해결 issue"는 놓침.
- P2만 보면 — 현재 상태 평가는 정확하지만 "어느 minor가 issue를 introduce 했는지" 추적 불가 → revert 또는 major refine 시 baseline 설정이 어려움.
- 둘을 cross-correlate 하면: P2의 issue가 P1의 minor log audit-flag와 매칭되는지 확인 → "최근 도입된 issue (fix 우선순위 高)" vs "기존 잔존 issue (next cycle 처리 OK)" 분류 가능.

**plans type**: minor log 컨벤션 없음 → P1 skip, P2만 실행 (현 동작과 동일).

## Cadence (언제 audit 실행)

| 트리거 | 동작 |
|---|---|
| **사용자 명시 `/audit <artifact>`** (기본) | 즉시 실행 |
| **AUDIT_HINT_THRESHOLD 도달** (default 5 minors since last major) | 직전 작업 (minor Edit 또는 autopilot-refine) 종료 후 chat alert: `⚠ {N} minor edits accumulated since v{N} — recommend /audit {artifact_short_name}`. _자동 실행 X_ — 사용자가 invoke. |
| **자동 fix chain dispatch에서 spawned audit** | autopilot-refine 또는 autopilot-code의 fix routing에서 호출 시 |

threshold는 doc/research artifact의 `pipeline_summary.md` `## 마이너 변경 로그` 섹션의 entry 수 또는 `## 버전 히스토리` 표의 `v{N}_M` 형식 row 수로 계산.

## Language Rule

All user-facing output (chat report, audit log) in natural **Korean** (no translationese — write Korean natively, don't translate from an English draft).

## Argument Parsing

    /audit <artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--no-fact-check]

- `<artifact_path>` (REQUIRED): one of
  - Absolute path to a `<artifact-root>/{plans,research,documents}/*` directory
  - Fuzzy short name (e.g., `se-seminar-tfrestormer`) — resolved via `ls -d <artifact-root>/{plans,research,documents}/*$ARG* 2>/dev/null`. 1 match → use; multiple → ask user (adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) — ScheduleWakeup 10분; 답 없으면 가장 최근 수정 artifact); 0 → error.
- `--scope` (default `auto`): which aspect set to check. **사용자 명시는 1순위 (override)**. 명시 없으면 audit이 artifact 특성 (mode / refine 횟수 / status / 구조)을 보고 _스스로 적절한 aspect set 선택_. 명시 값은 `facts | style | structure | cross-ref | coverage | all` 중 하나로 type-specific aspect group에 매핑 (Stage B 표 참조).
- `--read-only` (default for plans): if specified for `plans` type, skip any aspect that requires _executing_ tests / lints — only static inspection (file diff, TODO grep, code review heuristics). For `research` / `documents` types, `--read-only` is implicit and the flag is a no-op (warn: "audit는 research/documents에 대해 항상 read-only").
- `--report-only`: skip the auto-fix chain (Stage E). With this flag, `/audit` produces the report and stops — same as previous default behavior. Use when you want only inspection without follow-up edits.
- `--no-fact-check`: opt-out flag honored per `feedback_factcheck_principles.md` Principle 0. If present, the `facts` aspect (and the `coverage` aspect's cards-set diff) are **skipped** before Stage C aspect dispatch — i.e., the aspect skip happens at the _pre-check_ stage, not via filtering after lint runs. Other aspects (style / structure / cross-ref / Tier / cross-card / test / lint / code review / TODO) still run. Stage D report emits an informational line at the top of "Aspects checked": `ℹ facts/coverage aspects: skipped via --no-fact-check flag (memory feedback_factcheck_principles Principle 0)`. This is the _only_ allowed disable mechanism for fact verification; ad-hoc prompt evasion must not be honored.

## Process

`Stage A → B (B.1/B.2) → B.5 → C → D (D.5) → E` 순서로 진행한다. 각 Stage의 절차 전문(단서 표·lint 정의·템플릿·프롬프트)은 아래 reference에 verbatim 보존 — 해당 Stage 실행 시 그 파일을 Read 한다.

| Stage | 내용 | Reference |
|---|---|---|
| Stage A | Detect artifact type (plans / research / documents) | `references/scope-and-baseline.md` |
| Stage B · B.1 · B.2 | Determine effective scope — auto-scope 단서 표 + type-specific aspect 매핑 | `references/scope-and-baseline.md` |
| Stage B.5 | Minor log baseline ingestion (doc / research 전용 — P1 입력) | `references/scope-and-baseline.md` |
| Stage C | Per-aspect lint — pre-check + documents / research / plans aspect 정의 전문 | `references/aspect-lints.md` |
| Stage D · D.5 | Report 템플릿 전문 + 편집팀 polish + chat 출력 양식 | `references/report-and-autofix.md` |
| Stage E | Auto-fix chain (default — `--report-only` opt-out) | `references/report-and-autofix.md` |

## Constraints

- **Audit pass is read-only** — Stage A-D never modify the audited artifact (the audit log is written under `_internal/audit/`). Stage E _dispatches a separate skill_ (`autopilot-code` or `autopilot-refine`) which then makes edits per its own confirmation flow. With `--report-only`, Stage E is skipped entirely.
- **No web fetch** — all lookups are local (`<artifact-root>/*` files only). Cards grep, Style Guide read, regex scan. Cost is small.
- **No agent invocation** — `/audit` is a single-Claude task. No 연구팀 / 품질관리팀 subagent calls. (Future enhancement may add intensity-derived rigor tiers with agent-backed lint; out of scope for v1.)
- **Type-specific aspects** — research aspects do not run on documents artifacts and vice versa. `--scope cross-ref` on plans warns and skips.
- **Suggestion only (Stage A-D)** — every 🔴 / 🟡 finding may include a "Suggested fix" line. Stage E dispatches these suggestions to the appropriate skill, which follows its own protocol (autopilot-refine: default 자동 apply + STRUCT halt + 사후 git diff 검토; autopilot-code: phase QA gates + safety commit + final report).

## When NOT to use

- 산출물을 _수정_하고 싶은 경우 → `/autopilot-refine`.
- 단일 typo / cosmetic 점검 → 그냥 `grep` / `Read`.
- Full pipeline 재실행 필요 → `/autopilot-{research,doc,code}` 또는 `--from <stage>`.
- 산출물 자체가 존재하지 않음 (사전 분석부터 필요) → `/analyze-project` 또는 `/autopilot-research`.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/scope-and-baseline.md` | 모든 호출 (Stage A~B.5 진입 전, 필수) | Stage A(Detect artifact type), Stage B(effective scope — B.1 auto-scope detection 단서 표 / B.2 type-specific aspect mapping), Stage B.5(minor log baseline ingestion — P1 입력·diff·cross-correlate·chat 출력) |
| `references/aspect-lints.md` | Stage C aspect lint 실행 시 | per-aspect lint — pre-check(`--no-fact-check`), documents aspects(cards source resolution + facts/style/structure/cross-ref/coverage), research aspects(cards 정합성/Tier/coverage/cross-card), plans aspects(test results/lint/code review/TODO·미구현/semantic-deterministic consistency) |
| `references/report-and-autofix.md` | Stage D~E 보고·후속 시 | Stage D 보고서 템플릿 전문, Stage D.5 편집팀 polish, chat 출력 양식, Stage E auto-fix chain(skip 조건·fix prompt·dispatch·logging·rationale) |
| `references/examples-and-checklist.md` | 호출 예시·`--report-only` 후속 판단 자리 | 호출 Examples, Post-Audit Checklist(`--report-only` 사용 시 후속) |
