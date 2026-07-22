# Fleet v16 execute correction artifact

- route: `rt-dfec3aabe921b37f`
- node: `execute`
- attempt: `att-0018128bffc840b593304e17006d3c5a`
- assigned contract: `code-execute`
- mode: `dev/backend`
- QA: `standard` (`plan-check:selected-independent-pass:final-verify` required)
- write scope: canonical Fleet sources/tests, central title governor, checklist/dev logs; mirror synchronized only after canonical verification
- commit/push/merge/cleanup: not performed

## Implemented correction

- `tools/fleet/projection.py`: owner/conductor stage labels now derive from every active sealed route node in record order. A single generic child displays its node ID; agreeing parallel children display `{claim-a,claim-b}`. Route identity, progress, active nodes, and fail-closed conflict behavior remain attached.
- `tools/fleet/tests/test_f36_work_projection.py`: real Session `_build_lines` coverage at 168/120/100/60 with reversed child input, explicit-invalid preservation, and generic single/parallel owner regressions.
- `tools/fleet/tests/test_f28_route.py`, `test_f28_breadcrumb.py`, `test_f30_process_view.py`: sealed `survey -> {claim-a,claim-b} -> synth` fixture coverage for record order, fan-in, metadata, public snapshot, breadcrumb, process card, and fixed-pipeline absence.
- `tools/fleet/demo.py`: deterministic provider-disabled composed-DAG owner with two active sibling jobs and seeded survey completion. Group smoke visibly renders `stage {claim-a,claim-b} 1/4`; process smoke renders `rt-63788ad6 — 1/4 nodes` and both child chunks, including `ctx` rows.
- `tools/fleet/tests/test_f39_title_quota.py`: hermetic governor-root/limit/kill-switch environment handling, exact provider-call count, central governor parity/admission (four title leases, fifth rejected), and live-WAL source immutability regression.
- `utilities/model-worker-governor.py`: title class ceiling aligned to Fleet hard ceiling `4`, preserving global total and rolling-start checks.
- `tools/fleet/refresh_title.py`: OpenCode refresher now snapshots only the private DB plus existing WAL, never source SHM; source DB/WAL/SHM/journal signatures include device, inode, size, mode, mtime_ns, ctime_ns and are compared before/after copy. Linux reflink is preferred with streaming fallback; the worker reuses one private connection for table selection and delta reading with `mode=ro&cache=private`.
- Plan/checklist/dev-log wording now explicitly permits ephemeral consistency-checked DB+WAL snapshots while forbidding persistent copies and source DB/WAL/SHM writes.

## Verification evidence

1. Focused correction tests: `python3 -m unittest tools.fleet.tests.test_f28_route tools.fleet.tests.test_f28_breadcrumb tools.fleet.tests.test_f30_process_view tools.fleet.tests.test_f36_work_projection tools.fleet.tests.test_f39_title_quota` — **76/76 PASS**.
2. Fleet discovery via Codex verification runner — **781/781 PASS**; one pre-existing `ResourceWarning` in `test_f27_control.py:521`.
3. `python3 utilities/compose_route.test.py` — **9/9 PASS**.
4. `python3 utilities/capability_route.test.py` — **30/30 PASS**.
5. `python3 utilities/capability-route.py verify --route tools/fleet/tests/fixtures/route/synth_composed_survey.json --cwd "$PWD"` — **PASS**, route `rt-63788ad671654b75`, sealed hash verified.
6. Provider-disabled `--once --view group` — **PASS**; exact main Session primary row includes `stage {claim-a,claim-b} 1/4`.
7. Provider-disabled `--once --view process` — **PASS**; composed card includes `claim-a`, `claim-b`, route progress, and per-job `ctx` chunks; degrade cards also render.
8. Provider-disabled `--json | python3 -m json.tool` — **PASS**.
9. `python3 -m compileall -q tools/fleet adapters/claude/tools/fleet` — **PASS**.
10. Prescribed rsync, canonical/mirror `diff -rq`, `test_mirror_parity`, and `git diff --check` — **PASS**.
11. `bash tools/adaptation-guard.test.sh` — **PASS**.
12. `bash tools/check-adaptation-boundary.sh` — **FAIL** on repository-existing blockers: missing valid baseline hashes for `adapters/claude/hooks/mem-distill-dispatch.sh` and `adapters/claude/utilities/agent-worklog-state.sh`, and `adapters/claude/CLAUDE.md` at 16385 bytes over the 16384-byte ceiling; also reports 130 documented concrete Claude/model references.

## Contract notes

- Spec drift: the active artifact-root `spec/pipeline_state.yaml` is for the unrelated `unified-memory-system` project (`mode: [library, cli]`), while this approved route targets Fleet v16. The mismatch is disclosed; Fleet scope follows the assigned route prompt.
- The PRD read succeeded, but the Codex spec-read marker could not be written because `.spec-grounding` is read-only.
- No live/default/custom provider call was used by verification.
- The adaptation-boundary red gate prevents completion-marker binding. This stage verdict is therefore **FAIL**.
