# Entry Skill Layer — code-test retry verification matrix

Date: 2026-07-16  
Stage: `code-test` retry after `code-execute-correction-r3.md`  
Source: read-only verification of the uncommitted diff from `23c86beaa613571a583f65e869da6b72013a2ad4`  
Verdict: **FAIL**

## Assurance and runtime contract

`preflight.sh qa-policy thorough code` reported
`quality_reviewers=2x-deep-reviewers+2x-fast-reviewers`,
`assurance_scope=plan-check:selected-independent-pass:final-verify`, and the
rule that independence may be claimed only for a separate Codex agent,
headless worker, or external pass. This registered depth-2 `code-test` worker
is independent of the execute worker. It did not dispatch the optional 2+2
reviewer set because stage workers may not dispatch; the semantic review is
therefore an independent worker pass with inline thorough review, not a claim
that four additional reviewers ran.

The Codex `verification-runner` contract check passed with `status=ok`. All
project verification commands were executed through that adapter-owned runner
with 60–240 second bounds. The parent explicitly required the full original
matrix, so verification continued after the semantic backlink failure.

Two initial environment-prefixed invocations returned exit 69 because
`PYTHONDONTWRITEBYTECODE=1` was presented as the executable; both were rerun as
`env PYTHONDONTWRITEBYTECODE=1 ...` and passed. Two early inline semantic-audit
attempts were discarded because the audit code itself mishandled a regex
replacement and then an empty-path same-document anchor. The corrected
independent audit below is the authoritative result.

## Command matrix

| Surface | Bounded command | Exit | Result / evidence | Classification |
|---|---|---:|---|---|
| Generation | `env PYTHONDONTWRITEBYTECODE=1 python3 tools/generate.py --check` | 0 | Manifest current; delta baselines bound; 12 core projection groups current | PASS |
| Conformance | `bash tools/skill-conformance/check.sh` | 0 | 13 entries per tree; canonical/Claude 26,825 bytes (max 2,217), Codex 35,173 (max 2,843), OpenCode 33,717 (max 2,731); owner-link and invocation-policy gates passed | PASS |
| Routing | `sh tools/routing-contract.test.sh` | 0 | All routing-contract assertions passed | PASS |
| Exact strict footprint | `python3 tools/context-footprint.py --root . --skip-runtime --skip-hooks --timeout 30 --strict` | 0 | Exact 13-entry total/max surfaces loaded for canonical, Claude, Claude plugin, Codex, and OpenCode; 29-surface baseline loaded; no warnings | PASS |
| Topology | `python3 tools/capability_topology.test.py` | 0 | 8 tests passed | PASS |
| Adaptation boundary | `sh tools/check-adaptation-boundary.sh` | 0 | Boundary checks passed; only the documented 91-reference warning remains | PASS; prior new regression fixed |
| Targeted entry gate | `env PYTHONDONTWRITEBYTECODE=1 python3 tools/entry-skill-layer.test.py` | 0 | 13 routers; four tree budgets; 3 owner trees × 13 owner documents accepted | PASS, but the draft-strategy backlink is outside this gate |
| Projection behavior, corrected tree | `sh tools/generated-projections.test.sh` in a `/tmp` read-only-source copy | 1 | First failure: `legacy artifact root was not selected for orientation` | Known baseline |
| Projection behavior, starting commit | same command in a `/tmp` archive of `23c86bea...` | 1 | Exact same first failure and message | Confirms no projection regression at this level |
| Python syntax | `env PYTHONPYCACHEPREFIX=/tmp/entry-skill-pycache-r3 python3 -m py_compile` over 7 changed/new Python files | 0 | Clean; no source pycache writes | PASS |
| Shell syntax | `sh -n` for changed/covered POSIX scripts and `bash -n tools/skill-conformance/check.sh` | 0 | Clean | PASS |
| Diff hygiene | `git diff --check 23c86bea...` | 0 | No whitespace errors | PASS |
| Deny zones | clean-status assertion for worker bootstrap/types, utilities, Codex/OpenCode bins, fleet, and dispatch paths | 0 | No deny-zone change or untracked file | PASS |
| Primary checkout | tracked/cached cleanliness assertions in `/home/Uihyeop/agent_setting` | 0 | No tracked or staged primary-checkout source change; the only untracked item is the canonical `.agent_reports/plans/2026-07-16_entry-skill-layer-audit/` artifact cycle | PASS |
| Worker-bootstrap v5 | byte counts, SHA-256, and baseline diff | 0 | Kernel 1,571 bytes; owner/review/stage/support fragments unchanged | PASS |
| Claim-language diff | changed-line search for mask/token/billing/cost/savings/ROI/bytes | 0 | All prose occurrences are explicit prohibitions (`must not claim`, `do not infer`) or static UTF-8 byte measurements; code occurrences only compute bytes | PASS |
| Independent router/owner audit | manifest-derived Python audit | 1 overall; all owner/runtime assertions completed first | Exactly 13 routers; 65 exact manifest descriptions across five surfaces; 39 owner docs; 111 Markdown paths and 90 anchors resolved; 13 relocated owner bodies lossless; 26 Claude copies byte-identical; 26 native runtime routers compact | PASS for these assertions; overall exit belongs to the next row |
| Draft-strategy authority backlink | same independent audit | 1 | All 3 trees point to an existing owner file but a nonexistent `#paste-ready-cheatsheet-format--separate-user-and-tracking-surfaces` section | **FAIL** |

## Exact context-footprint evidence

| Surface | Entries | Total bytes | Max bytes | Exact baseline |
|---|---:|---:|---:|---:|
| canonical | 13 | 26,825 | 2,217 | match |
| Claude native | 13 | 26,825 | 2,217 | match |
| Claude plugin | 13 | 26,825 | 2,217 | match |
| Codex native | 13 | 35,173 | 2,843 | match |
| OpenCode native | 13 | 33,717 | 2,731 | match |

Existing worker combined surfaces also remain exact: owner 2,028, stage 1,906,
review 1,878, support 1,862 bytes. The report contains no static-byte-to-token,
billing, cost, savings, or ROI inference.

## Worker-bootstrap v5 hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `roles/worker-bootstrap.md` | 1,571 | `41fec729e64d5f8afdf9b418bb626f80c3fa68e4528a6c2f19144dd5b2d103ce` |
| `roles/worker-types/owner.md` | 455 | `e184b62f560b14afbc58f479379b16624b07fe5dd06541cb053e887be5261666` |
| `roles/worker-types/review.md` | 305 | `e1d884cf2a9ebc0f923fda441f291c311f0a6f0a7a004adadf88a7a2c2067287` |
| `roles/worker-types/stage.md` | 333 | `6c81b6fa87acd80fe64e85e5d5a943a976263aae1690cc26784768bbe545bf6f` |
| `roles/worker-types/support.md` | 289 | `1dbe513c1edcaf9be4b4e4e57ac372353cb795607dee7d7747b52bb06415308d` |

## Final command verdict

The prior owner-path, adaptation-inventory, and exact footprint regressions are
fixed. The legacy projection failure has the same first failure and output in
the current and starting-commit snapshots. However, the draft-strategy authority backlink
still does not reach an owner section on any of the three required trees, and
the targeted gate does not cover that cross-Skill reference. The completion
gate is therefore not met.
