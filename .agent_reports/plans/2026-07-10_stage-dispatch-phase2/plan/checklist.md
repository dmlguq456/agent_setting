# Checklist — stage-dispatch Phase 2 (code-execute)

slug: 2026-07-10_stage-dispatch-phase2 · branch: stage-dispatch-phase2 · qa=standard · intensity=strong

## Decision Points
- **SD-14b① Stop probe (Phase A)**: `Stop` hook does **NOT** fire under `claude -p` (probe 2026-07-10, exit 1, no sentinel). Cross-check: CC issue #38651 (Stop empties `-p` output), #40506/#20063. → **Stop gate HELD** (E2 unregistered, on-disk only). SD-14 ships via depth_note + dispatch-wait.

## Phase status

- [x] **Phase A** — probe done. Verdict: Stop unfired → E2 registration held. Record: `_internal/dev_reviews/phaseA_stop_probe.md`.
- [x] **Phase B** — core doc increments (core-first)
  - [x] B1 OPERATIONS §5.10 one-shot wait contract + SD-13 spec precondition
  - [x] B2 WORKFLOW §5 diffusion rows + new autopilot-lab row
  - [x] B3 CONVENTIONS §1 capability-neutral clarifier
  - [x] B4 DESIGN_PRINCIPLES §8 SD-14 determinism note
- [x] **Phase C** — wrapper + dispatch-wait.sh
  - [x] C1 resolve_agent_home registry-gap fix
  - [x] C2 AGENT_DISPATCH_SELF_SLUG child env
  - [x] C3 depth-1 depth_note one-shot wait clause
  - [x] C4 utilities/dispatch-wait.sh + test
- [x] **Phase D** — SD-12 stage-worker profiles (4 fragments + 4 yaml + README + --check ok ×4, instance build clean)
- [x] **Phase E** — hooks
  - [x] E1 stage-dispatch-reminder.sh (SD-11, soft) REGISTERED + 5 conformance PASS
  - [x] E2 conductor-stop-gate.sh (SD-14b) — UNREGISTERED (held), on-disk + 4 CLI unit PASS
  - [x] E3 HOOKS.md catalog rows (parity note → Phase G)
- [x] **Phase F** — SD-10 dev-pipeline dispatch-first (closed 2-cond fallback, dispatch-headless.py×5, dispatch-wait per stage) + SKILL Stage Graph annotation
- [ ] **Phase G** — adapter bootstrap parity (claude/codex/opencode one-shot clause)
- [ ] **Phase H** — diffusion (draft/research/spec/design/lab stage-worker tables)
- [ ] **Phase I** — drill case handoff artifact (under plan dir, NOT loops/)
- [ ] **Phase J** — instrumentation + post-it handoff

## Safety commits
- `5ae8c8a` Phase A+B (probe verdict + core docs)
- `e97d916` Phase C (wrapper + dispatch-wait)
- `d27ab12` Phase D (profiles)
- `3dfb993` Phase E (hooks)
- (Phase F committed next)
