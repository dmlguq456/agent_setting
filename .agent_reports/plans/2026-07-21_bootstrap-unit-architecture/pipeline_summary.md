# Pipeline Summary — Bootstrap-Unit Architecture

Single source of truth for this planning cycle's status & history.

## Goal
Consolidate bespoke sub-agent personas into composable **units** projected onto two
distinct-lifecycle surfaces (native sub-agent / registered dispatch worker), replicating
the `models.conf` SoT+guard pattern for behavior. Persona minimization is domain-graded;
the capability layer is restructured last. Origin: user direction (harness-wide, "꽤나 중요한 방향").

## Artifacts
- `architecture-spec.md` — target model, 11 decisions, domain floor, guards, 5-phase plan, risk register. **PRIMARY.**
- `_internal/investigation/current-state-map.md` — 7-stream parallel audit synthesis (file:line grounded).
- `_internal/investigation/raw-findings.md` — per-stream raw findings.

## Status
| Stage | State |
|---|---|
| Parallel investigation (7 surfaces) | ✅ done (workflow, 8 agents, 0 err, 552k tok) |
| Target architecture design (11 decisions) | ✅ done |
| Adversarial 2-way cross-harness verification (v1→v2) | ✅ done |
| Skill-setting review (6-stream + Codex cross-harness) | ✅ done (`_internal/skill-review/`) |
| **User decisions locked** | ✅ 승격(compiler enforced) + 재홈(teams→unit catalog) + max-scale parallel |
| **v3 spec (EXECUTION)** | ✅ `architecture-spec-v3.md` |
| Unit-def schema + shared fragments | ✅ `roles/units/_schema.md`, `_shared/{stance,triage-output,dual-io,memory-flow}.md` |
| Round 1: catalog ×7 + topologies design + call-site inventory | ✅ 9/9 (C1 committed: 26 units +3,582줄) |
| Round 2: apply T/R/G/U (4 parallel) | ✅ 4/4 — topologies enforced·66 file rewiring·team 삭제·guard 신설 |
| Finalization (main): unit dispatch 배선(--unit ×5 hop), legacy reader 6곳 리포인트, core docs, legacy 삭제, 전체 regen | ✅ |
| Full battery 16/16 + generate --check + 양 guard | ✅ green |
| Commits C2(2e1ce56e)·C3(2c38c933)·C4(a3493fbc) | ✅ (경로 분할, stage-dispatch 무접촉) |
| portable-guards (clean worktree) | ✅ C5(839454e4): 제품 회귀 1건 수정 + 드릴 15건 현대화, PASS=351/베이스라인 대비 회귀 0 |
| **최종 2-way cross-harness verify** | ✅ 양 leg verdict 회수 — Codex 9건 + Claude 6건 CONFIRMED(수렴: boundary guard·codex role-map·profiles), end-to-end 체인은 실증 clean(compile→seal→bootstrap→dry-run, unit 변조 거부) |
| 지적 반영 (Codex 9 + Claude 6 전건) | ✅ C6(63f521c8): 서브스킬 미러 27 확장(치명), unit 바인딩 강제(guard mismatch+wrapper 3+model-role=unit 권위), composed gate 검증, codex/opencode 매핑 재홈(role-map·capability-map·plan family), boundary 전면 sweep(74→1, 잔여=선재 __pycache__), manifest modes+2(report·plan-author→codex 투영 27), profiles/fragments v3화, guards 정합 |
| 최종 게이트 | ✅ 배터리 17/17 · generate --check · 양 guard green · **clean-worktree portable-guards PASS=354 FAIL=2**(베이스라인 대비 실회귀 0, 선재 red 4→2로 개선 — codex doctor 쌍 치유) |
| **push** | ✅ `306e0bd8..63f521c8` origin/main — 마이그레이션 완결 (C1–C6) |

## Residual (비차단, 범위 외)
- boundary 잔여 1: `__pycache__` 노출 (pre-migration 선재)
- guards 잔여 2: `adapter loop runtime logs ignore`(선재, drill env), `opencode role wrapper opencode-default`(별도 adapter-model-config 변경 유래)
- 용어 sweep: `adapters/codex/{preflight.sh,README.md,AGENTS.md}`의 role-profile 문서 어휘 잔존 (doc-level)
- spec 소유 외 참조: harness-layer-sync PRD 등 타 스펙의 구조 서술은 각 스펙 세션 소관 |

## Key findings that shaped the design
- Migration is **consolidation, not rewrite**: codex/opencode agents already generated; dispatch already kernel+overlay; nodes already carry role+kind.
- **Claude native agents are the outlier** — hand-authored, model hardcoded, guard-exempt, actively drifted (sonnet primary vs opus plugin).
- Two persona-duplication seams: role→tier (native frontmatter) and domain body (roles/modes vs agent-modes, diverged EN/KO).
- Thick "tool" fragments (pdf DPI, figure-semantic-verify, spectrogram LAW) are irreducible domain law → relocate, never delete.

## History
- 2026-07-21: investigation workflow run; architecture-spec drafted (11 decisions); adversarial verification launched.
- 2026-07-21: 2-way cross-harness verification (Claude-side + Codex) — both FIX-NEEDED; **both independently converged on a granularity flaw** (unit=mode-persona vs node-worker). Spec revised to **v2**: three-entity model (unit/team/node), floor per-unit, native=team aggregation, write_scope node-owned, dispatch reads authored .md (no hot-path overlay), pilot=mechanical units, Phase 0 = drift-resolving. Log: `_internal/verification/verification-log.md`.
