---
slug: 2026-07-10_stage-dispatch-phase1
mode: dev
intensity: strong
qa: standard
status: in_progress
spec: .agent_reports/spec/stage-dispatch/prd.md
---

# stage-dispatch — Phase 1 (contract revision + wrapper increment + autopilot-code pilot)

spec-significance: within-spec (SD-7 §9 영향 표면 표를 실행 — spec 이 이미 방향 확정, 코드/문구 개정만)

## Goal (Phase 1 only)

Realize the §9 impact-surface table of `spec/stage-dispatch/prd.md`: turn each autopilot-code
sub-skill stage (code-plan/execute/test/report) into the `standard+` default of being dispatched
as its own depth-2 headless session (thin conductor + file-only handoff). `direct/quick` stay inline.
Contract docs + adapter bootstraps + a minimal wrapper increment + one instrumented pilot.

Out of scope: Phase 2 (fleet stage-row labels §9-13, drill regression case §9-14, other autopilot-*
spread), `loops/**`, `tools/fleet/**` (other-session-owned — do not touch), and *fixing* the
SD-OPEN-1 threshold (pilot only collects data).

## Verification (from SoT)

- `bash tools/check-adaptation-boundary.sh` → `OK` (baseline is currently green; the drill byte-equiv
  FAIL the task warned about is not present at baseline — note in report).
- `python3 tools/context-footprint.py --skip-hooks` → no new budget warnings (claude skill-metadata
  < 10000, codex active < 8000; bootstrap chars kept minimal).
- Reference-anchor grep on the reversed/added phrases (see checklist).
- `bash -n` on edited shell, `python3 -m py_compile` on edited wrapper.
- Pilot: fixture repo cycle emits `depth=2, parent=<conductor>` rows to a *fixture-local* jobs.log
  (real registry untouched), stage artifacts (plan→dev_logs→test→report) normal, per-stage
  token/time table recorded here.

## Surface checklist (core-first: read core → edit core → edit adapters)

| # | Surface | Edit |
|---|---|---|
| 1 | `core/OPERATIONS.md §5.10 ③` | depth-2 용도에 파이프 스테이지-워커 클래스 병기 + standard+ 스테이지 기본 분사 |
| 2 | `core/OPERATIONS.md §5.10 ④` | depth-2 write = 스테이지-워커 클래스별 소유(§6 표); 리뷰 워커 read-only 유지 |
| 3 | `core/WORKFLOW.md §1.1` | standard+ 행에 스테이지 분사 기본; direct/quick inline 명시 |
| 4 | `core/WORKFLOW.md §5` | autopilot-code 팀이 각 스테이지 headless 세션 *안*에서 실행 |
| 5 | `core/CONVENTIONS.md §1` | Dispatch policy 스테이지=depth-2 기본 + depth 계약에 스테이지-워커 클래스 |
| 5b| `core/CONVENTIONS.md §2.3` | 스테이지↔model role 매핑 연결부 (SD-5) |
| 6 | `core/DESIGN_PRINCIPLES.md §8` + 부록 | file-only handoff 범위를 headless 스테이지→conductor 로 승격; 2026-07-06 반전 이력 |
| 7 | `skills/autopilot-code/references/context-and-guards.md:51` + SKILL.md | 스테이지 분사 금지 → 기본 권장 반전(우려 해소 근거 병기) |
| 8 | `skills/autopilot-code/references/dev-pipeline.md` | standard+ 스테이지 분사 오케스트레이션 / direct·quick inline |
| 9 | `skills/{code-plan,code-execute,code-test,code-report}/SKILL.md` | 독립 세션 진입점 계약(입력=산출물 경로); 팀 위임은 세션 안 유지 |
| 10 | `adapters/claude/CLAUDE.md §0(C)` | "분사는 main 전용·깊이 1" → conductor(depth-1)가 스테이지를 depth-2 로 |
| 11 | `adapters/codex/AGENTS.md` · `adapters/opencode/AGENTS.md` | 스테이지 분사를 depth-2 정규 용법으로 병기 (parity) |
| 12 | `adapters/claude/bin/dispatch-headless.py` | 재작성 X — depth_note 를 depth-aware 로 (depth-2 스테이지 계약 주입) |

## Wrapper analysis (SD-9)

`dispatch-headless.py` already supports `--depth {1,2}`, `--parent`, `--worker-role`, `--owner`,
`role_map`, `missing-dispatch-parent`(64), `invalid-depth-two-intensity`(64). The only gap for stage
dispatch: `depth_note` (line ~159) is a fixed depth-1 string injected regardless of `--depth`, so a
depth-2 stage worker is told the depth-1 contract ("open bounded depth-2 sub-workers"). Minimal
increment = make `depth_note` depth-aware: depth-2 workers get the file-only + no-further-headless +
write-class contract. No rewrite. stage-dispatch helper deferred to post-pilot (SD-9).

## Pilot design (SD-OPEN-1 instrumentation)

- Fixture repo under `/tmp` (drill g6 pattern: bare origin + clone + trivial multi-file change).
- Conductor dispatches each stage via `dispatch-headless.py --depth 2 --parent <conductor-slug>
  --worker-role code-<stage> --owner autopilot-code` with a **fixture-local** `--jobs`/registry so the
  real `~/.claude/.dispatch/jobs.log` stays clean.
- Verify: (a) fixture jobs.log has 4 stage rows `depth=2,parent=…,worker_role=code-*`; (b) each stage
  reads only prior artifact files; (c) record per-stage token/wall-clock in `dev_logs/pilot_metrics.md`.
- Concurrency ≤ 5 = conductor(1)+active stage(1)=2 (sequential), well under cap.
