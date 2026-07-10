# Instrumentation — stage-dispatch (SD-OPEN-1 accumulation + SD-12 token/time + SD-OPEN-2)

> **Measurement only — no threshold decisions this phase.** SD-OPEN-1 (micro-stage
> inline threshold) accumulates evidence; the threshold is NOT set here (§12-5).

## J1 — per-stage-dispatch record format

Record one row per dispatched stage run:

| field | source | note |
|---|---|---|
| `stage` | dispatch `--worker-role` | code-plan/execute/test/report |
| `profile` | jobs.log `profile=` | `full-bootstrap` (no `--profile`) vs `code-<stage>` (SD-12 minimal) |
| `model_role` | jobs.log `model_role=` | deep maker / fast implementer / fast reviewer / fast writer |
| `wall_clock_s` | jobs.log ts: `open`→`done` delta | per-stage latency |
| `conductor_ctx_proxy` | conductor turn token count (proxy) | thin-conductor context pressure |

### Seed row — Phase-1 pilot (continuity, 2026-07-10)

| stage | profile | model_role | wall_clock_s | conductor_ctx_proxy |
|---|---|---|---|---|
| code-plan | full-bootstrap | deep maker | 218 | (pilot — not captured) |
| code-execute | full-bootstrap | fast implementer | 255 | (pilot — not captured) |
| code-test | full-bootstrap | fast reviewer | 46 | (pilot — not captured) |
| code-report | full-bootstrap | fast writer | 28 | (pilot — not captured) |

Phase-2 adds the `code-<stage>` minimal profiles (SD-12). Future runs should log a
matching `profile=code-<stage>` row so full-bootstrap-vs-minimal token/time can be
compared. No comparison is drawn yet — accumulate only.

## J2 — SD-OPEN-2 curator observation (observation only, §8.5.6 · §13)

Per stage session, note (do not intervene):

| observable | how | note |
|---|---|---|
| curator fired? | SessionEnd mem distiller runs when `MEM_DISTILL_ENABLE=1` (settings env) | yes/no per stage session |
| duplicate `mem add`? | compare stage-session distiller output to conductor's | watch for N-stage duplication |

Cross-check already in place: `stage-dispatch-reminder.sh` and `conductor-stop-gate.sh`
both guard `MEM_DISTILL=1` recursion, so hook firing during a distiller sub-session is
suppressed. **No intervention this phase** — record observations for a later decision.

## Notes
- The wrapper already appends `profile=` to jobs.log (dispatch-headless.py) — no code
  change needed to *record* the profile; the SD-12 profiles (Phase D) make the
  minimal-bootstrap arm available for comparison.
- Micro-stage inline threshold (SD-OPEN-1) is deliberately left unset.
