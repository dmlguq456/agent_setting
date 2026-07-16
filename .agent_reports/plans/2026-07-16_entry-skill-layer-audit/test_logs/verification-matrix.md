# Entry Skill Layer — code-test verification matrix

Date: 2026-07-16
Stage: `code-test`
Source: uncommitted diff from `23c86beaa613571a583f65e869da6b72013a2ad4`
Verdict: **FAIL**

## Assurance and runtime contract

`preflight.sh qa-policy thorough code` reported:

- `quality_reviewers=2x-deep-reviewers+2x-fast-reviewers`
- `assurance_scope=plan-check:selected-independent-pass:final-verify`
- independence may be claimed only for a separate worker/external pass
- fallback: report inline review when additional independent agents are unavailable

This registered `code-test` worker is independent of the execute worker. It did
not dispatch the additional reviewer set because a depth-2 stage may not
dispatch; no 2+2 reviewer claim is made. Semantic review was performed inline
and is recorded in `_internal/test_reviews/code-test.md`.

The Codex `verification-runner` contract check passed (`status=ok`). Every
project verification command below was run through that runner with a bounded
timeout.

## Command matrix

| Level | Command | Exit | Result / evidence | Baseline classification |
|---|---|---:|---|---|
| Generated | `PYTHONDONTWRITEBYTECODE=1 python3 tools/generate.py --check` | 0 | Manifest current; 12 projection groups current | PASS |
| Conformance | `bash tools/skill-conformance/check.sh` | 0 | 13 entries on each tree; canonical/Claude 26,825 bytes, max 2,217; Codex 35,173/max 2,843; OpenCode 33,717/max 2,731; 27 invocation classifications | PASS |
| Routing | `sh tools/routing-contract.test.sh` | 0 | All routing checks passed | The three planning-baseline stale assertions are fixed in scope |
| Static footprint | `python3 tools/context-footprint.py --root . --skip-runtime --skip-hooks --timeout 30 --strict` | 0 | No warnings; worker kernel 1,571; owner 2,028; stage 1,906; review 1,878; support 1,862 | PASS for existing surfaces, but requested entry-router footprint coverage is absent; see review finding 3 |
| Topology | `python3 tools/capability_topology.test.py` | 0 | 8 tests passed | PASS |
| Projection behavior | `sh tools/generated-projections.test.sh` | 1 | First failure: `legacy artifact root was not selected for orientation` | Unchanged unrelated planning baseline; not introduced by this refactor |
| Adaptation boundary | `sh tools/check-adaptation-boundary.sh` | 1 | New tools lack projection decisions; missing Claude projections; four classification failures plus two missing-file failures | **New regression** |
| Targeted entry gate | `python3 tools/entry-skill-layer.test.py` | 0 | Exactly 13; all four Skill trees fit size budget | PASS, but insufficient semantic coverage; see review |
| Python syntax | `python3 -m py_compile` for six changed/new Python files with pycache in `/tmp` | 0 | Clean | PASS |
| Shell syntax | `bash -n tools/skill-conformance/check.sh`; `sh -n tools/routing-contract.test.sh` | 0 | Clean | PASS |
| Diff hygiene | `git diff --check 23c86bea...` | 0 | No whitespace errors | PASS |
| Deny-zone diff | `git diff --quiet 23c86bea... -- roles/worker-bootstrap.md roles/worker-types utilities adapters/codex/bin adapters/opencode/bin` | 0 | No worker-bootstrap, worker-type, utility/dispatch, Codex-bin, or OpenCode-bin change | PASS |
| Primary checkout | `git -C /home/Uihyeop/agent_setting diff --quiet` | 0 | No tracked primary-checkout source diff | PASS |
| Moved-body comparator | Starting `skills/<entry>/SKILL.md` body versus current canonical owner, ignoring only leading blank lines | 0 | 13/13 lossless | PASS for text preservation |
| Moved-reference resolver | Resolve `references/*.md` and `../../*.md` occurrences from each owner document on canonical, Claude-native, and Claude-plugin trees | 1 | 345/345 occurrences resolve to missing paths | **New regression** |

## Worker-bootstrap v5 evidence

All files are byte-identical to the starting commit:

| File | Bytes | SHA-256 |
|---|---:|---|
| `roles/worker-bootstrap.md` | 1,571 | `41fec729e64d5f8afdf9b418bb626f80c3fa68e4528a6c2f19144dd5b2d103ce` |
| `roles/worker-types/owner.md` | 455 | `e184b62f560b14afbc58f479379b16624b07fe5dd06541cb053e887be5261666` |
| `roles/worker-types/review.md` | 305 | `e1d884cf2a9ebc0f923fda441f291c311f0a6f0a7a004adadf88a7a2c2067287` |
| `roles/worker-types/stage.md` | 333 | `6c81b6fa87acd80fe64e85e5d5a943a976263aae1690cc26784768bbe545bf6f` |
| `roles/worker-types/support.md` | 289 | `1dbe513c1edcaf9be4b4e4e57ac372353cb795607dee7d7747b52bb06415308d` |

The measured combined v5 surfaces remain exactly 1,862–2,028 bytes.

## Final command verdict

The generated, conformance, routing, static-footprint, topology, syntax, and
diff checks pass, and the one projection-test failure matches the documented
unrelated baseline. The adaptation boundary introduces a new regression, and
the independent moved-reference resolver finds pervasive new breakage.
Therefore the completion gate is not met.
