# Entry Skill Layer — code-test retry r4 verification matrix

Date: 2026-07-16
Stage: `code-test` retry after `dev_logs/code-execute-correction-r4.md`
Source: read-only verification of the uncommitted diff from
`23c86beaa613571a583f65e869da6b72013a2ad4`
Verdict: **FAIL**

## Assurance and runtime contract

`preflight.sh qa-policy thorough code` reported
`quality_reviewers=2x-deep-reviewers+2x-fast-reviewers`,
`assurance_scope=plan-check:selected-independent-pass:final-verify`, and the
rule that independence may be claimed only for a separate Codex agent,
headless worker, or external pass. This registered depth-2 `code-test` worker
is independent of the execute worker. A stage worker may not dispatch, so no
claim is made that the optional four additional reviewers ran; the required
fallback is this independent worker pass plus inline thorough semantic review.

The Codex `verification-runner` tool-contract check passed with `status=ok`.
Every project verification command below ran through the adapter-owned runner
with a 180-240 second bound. Source remained read-only: its 105-row porcelain
status hash was `f48074ef0d04ab653d0208f54004792929d44559833ba6ec16f54477a3575a42`
before and after verification.

## Command matrix

| Surface | Bounded command | Exit | Result / evidence | Classification |
|---|---|---:|---|---|
| Generation freshness | `env PYTHONDONTWRITEBYTECODE=1 python3 tools/generate.py --check` | 0 | Manifest current; delta baselines bound; 12 core projection groups current | PASS |
| Deterministic generation | two `python3 tools/generate.py` runs plus `--check` in a `/tmp` copy | 0 | Second-run content hash matched: `c579ff672e05bba30fa38b6c55cd5d1993fc39e6bb8fcf001602e7050f3ff55d` | PASS |
| Conformance | `bash tools/skill-conformance/check.sh` | 0 | 13 entries per runtime tree; owner links, 27 classifications, routing boundaries, and language neutrality passed | PASS |
| Routing | `sh tools/routing-contract.test.sh` | 0 | All routing-contract assertions passed | PASS |
| Strict footprint | `python3 tools/context-footprint.py --root . --skip-runtime --skip-hooks --timeout 30 --strict` | 0 | 29 exact surfaces loaded; all five entry-router trees have 13 entries; no warnings | PASS |
| Topology | `env PYTHONDONTWRITEBYTECODE=1 python3 tools/capability_topology.test.py` | 0 | 8 tests passed | PASS |
| Adaptation boundary | `sh tools/check-adaptation-boundary.sh` | 0 | Boundary checks passed; only the documented 91-reference warning remains | PASS |
| Entry-layer repository gate | `env PYTHONDONTWRITEBYTECODE=1 python3 tools/entry-skill-layer.test.py` | 0 | Four runtime-tree budgets, 39 owner docs, and all three draft-strategy delegate documents passed | PASS; r3 gate gap fixed |
| Projection behavior, corrected tree | `sh tools/generated-projections.test.sh` in a current `/tmp` copy | 1 | First failure: `legacy artifact root was not selected for orientation` | Known unrelated baseline |
| Projection behavior, starting commit | same command in a `23c86bea...` `/tmp` archive | 1 | Exact same first failure and message | Baseline unchanged |
| Python syntax | `python3 -m py_compile` over the seven changed/new Python helpers with `/tmp` pycache | 0 | Clean; no source pycache write | PASS |
| Shell syntax | `sh -n` for three covered POSIX scripts and `bash -n tools/skill-conformance/check.sh` | 0 | Clean | PASS |
| Diff hygiene | `git diff --check 23c86bea...` | 0 | No whitespace errors | PASS |
| Deny zones | status assertion over worker bootstrap/types, utilities, Codex/OpenCode bins, Claude dispatch, and fleet paths | 0 | No tracked or untracked deny-zone change | PASS |
| Primary checkout | `git -C /home/Uihyeop/agent_setting diff --quiet` and cached equivalent | 0 / 0 | No tracked or staged primary-checkout source change; untracked rows are only this canonical artifact cycle | PASS |
| Worker-bootstrap v5 | base diff, byte count, and SHA-256 | 0 | Kernel and all four fragments exactly unchanged | PASS |
| Claim language | changed-line scan for masking/token/billing/cost/savings/ROI/bytes | 0 | Prose occurrences are explicit prohibitions or static UTF-8 byte limits; code only measures bytes | PASS |
| Independent owner audit | manifest-derived path/anchor, metadata, lossless, and parity audit | 0 | 39 owner documents, 375 concrete paths, 90 anchors, 65 exact descriptions, and both Claude projections passed | PASS |
| Draft-strategy backlink | same independent audit | 0 | All three links reach an actually present owner heading; the gate explicitly iterates all three delegate docs | PASS; prior P0 fixed |
| Capability owner-status coverage | manifest-derived check of all 13 capability contracts | 1 | Generated owner-status row present for 10, missing for `analyze-project`, `analyze-user`, and `audit` | **Newly detected blocking plan defect** |

## Corrected P0 evidence

All three delegate files now link to
`../../autopilot-draft/references/owner-execution.md#paste-ready-cheatsheet-format--separate-user-and-tracking-surfaces`.
The named heading is physically present at line 83 in canonical,
Claude-native, and Claude-plugin owner documents, and both three-file groups
are byte-identical. `tools/entry-skill-layer.test.py` explicitly loops
`OWNER_TREES` and resolves each
`draft-strategy/references/delegate-prompt.md`; executing the gate passed.

The independent losslessness check compared each starting-commit Skill body
after only the documented one-level link relocation against the current owner
document. Twelve owners are exact. `autopilot-draft` retains all prior lines
and has one insertion of 14 lines for the new authority section; there are no
deletes or replacements. All 39 moved owner documents resolve their concrete
paths and anchors.

## Exact entry footprints

| Surface | Entries | Total bytes | Max bytes | Exact baseline |
|---|---:|---:|---:|---:|
| canonical | 13 | 26,825 | 2,217 | match |
| Claude native | 13 | 26,825 | 2,217 | match |
| Claude plugin | 13 | 26,825 | 2,217 | match |
| Codex native | 13 | 35,173 | 2,843 | match |
| OpenCode native | 13 | 33,717 | 2,731 | match |

All 65 descriptions across those five surfaces exactly equal the manifest's
`use_when + " " + not_for` values. Canonical, Claude-native, and Claude-plugin
entry trees are byte-identical; Codex/OpenCode remain compact sibling-native
projections.

## Worker-bootstrap v5 hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `roles/worker-bootstrap.md` | 1,571 | `41fec729e64d5f8afdf9b418bb626f80c3fa68e4528a6c2f19144dd5b2d103ce` |
| `roles/worker-types/owner.md` | 455 | `e184b62f560b14afbc58f479379b16624b07fe5dd06541cb053e887be5261666` |
| `roles/worker-types/review.md` | 305 | `e1d884cf2a9ebc0f923fda441f291c311f0a6f0a7a004adadf88a7a2c2067287` |
| `roles/worker-types/stage.md` | 333 | `6c81b6fa87acd80fe64e85e5d5a943a976263aae1690cc26784768bbe545bf6f` |
| `roles/worker-types/support.md` | 289 | `1dbe513c1edcaf9be4b4e4e57ac372353cb795607dee7d7747b52bb06415308d` |

Combined rendered worker surfaces remain exactly owner 2,028, stage 1,906,
review 1,878, and support 1,862 bytes.

## Adaptation and baseline classification

`core/ADAPTATION_INVENTORY.md` classifies `sync-entry-skill-layer.py` and
`entry-skill-layer.test.py` as portable canonical-only / deferred projection;
both boundary inventories and the canonical-only allowlist include them. The
boundary gate passes. The generated-projections failure is unchanged from the
starting commit and is not a refactor regression.

## Blocking completion-gate mismatch

The approved plan/checklist require all 13 generated capability contract blocks
to identify the post-approval owner. Only 10 do. In `tools/build-manifest.py`,
`entry_layer` is emitted under `if spec["group"] == "entry"`; the authoritative
router classification is instead `spec["invocation"]["class"] ==
"entry-router"`. Consequently the entry routers in groups `pre` and `ops` --
`analyze-project`, `analyze-user`, and `audit` -- lack the generated
`Entry load phase` / owner-contract row. Existing gates do not assert exact
13-row capability coverage.

The same approved portable-source section also calls for alignment in
`core/DESIGN_PRINCIPLES.md` and `capabilities/README.md`. Neither file changed,
and neither currently contains the compact-router -> post-approval owner ->
assigned-stage distinction. These unchecked checklist items remain incomplete.

## Final command verdict

Correction r4 fixes the prior P0 backlink and its three-document gate coverage.
Every requested runtime, projection, link, footprint, metadata, adaptation,
protected-surface, and baseline check otherwise passes. The all-13 capability
owner-status requirement and two approved portable documentation updates are
still incomplete, so the code-test completion gate is not met.
