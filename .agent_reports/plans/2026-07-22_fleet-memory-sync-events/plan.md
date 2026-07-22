---
status: active
created: 2026-07-22
---

# Fleet memory sync-event attribution implementation plan

## Goal

Add prospective, create-only write-journal events for records newly absorbed by `migrate`/`sync`, with literal `actor=sync` and source-derived logical `cwd`, while preserving all existing mutation telemetry and leaving the Fleet consumer unchanged unless an end-to-end acceptance test exposes a real incompatibility.

## Scope and governing contracts

- Sealed source: `e8938809d87e54474f5e7242a2552598c2636a0a` on linked worktree branch `fleet-memory-sync-events`.
- Route: `rt-d7392fcfbc9ce241`, node `plan`, staged `autopilot-code`, standard intensity/QA. This stage owns only this plan and `checklist.md`.
- Normative requirements come from the canonical artifact-root inputs `/home/Uihyeop/agent_setting/.agent_reports/spec/prd.md` (v22 D-37 at lines 286-292) and `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` (v15 F-19/F-35f text at lines 205-211 and 354). The research and r2 review establish the create-only implementation and explicitly reject `_write_actor(default="sync")`; the actor must bypass ambient actor resolution.
- The sealed route's satisfied `tracked_gate_evidence.spec_read` and completed spec-owner report are authoritative entry prerequisites. Immediately before the first source edit, execution must revalidate the required v22/v15 clause text at those absolute paths and fail closed on drift. The linked code worktree is not required to contain, stage, commit, or otherwise project canonical artifact-root spec edits.
- No relevant module analysis exists under the canonical `analysis_project/code/` directory; its current files concern installer/Skill audits, not memory or Fleet. Source and caller analysis below therefore comes directly from the sealed worktree plus the named research/review artifacts.
- Allowed implementation surface: `tools/memory/mem.py` and focused tests. `tools/fleet/collectors/memory.py` stays byte-unchanged unless the planned producer-to-consumer acceptance test fails for a genuine consumer reason.
- No schema migration, new journal action, journal replay, real-store migration, or historical backfill is in scope. `import_dump()` and the existing body-dedup source-persistence behavior are also out of scope.

## Current state analysis

### Producer and signature graph

| Surface | Current behavior and callers | Planning consequence |
|---|---|---|
| `tools/memory/mem.py:68-80` | `WRITE_EVENTS` resolves to an explicit path, store-adjacent fixture path, or XDG state; `WRITE_ACTORS` already includes `sync`. | Reuse the existing `add` action and `sync` actor. No format enum or consumer change is needed. |
| `tools/memory/mem.py:375-404` | `_decode_enc_cwd(enc)` returns an existing absolute `Path` for an encoded project directory or `None`. | Use this as the source of truth for auto-memory logical cwd and the encoded form of legacy cwd metadata. Do not use `project_key()` output as the journal cwd. |
| `tools/memory/mem.py:407-431` | `_canonical_cwd_key()` converts resolvable path-like input to `git:`/`id:`/`root:` keys for DB `cwd_origin`, otherwise preserving the raw value. | DB attribution and event attribution are deliberately different: preserve this helper and derive a separate absolute event cwd. |
| `tools/memory/mem.py:1000-1117` | `write_record(..., journal_action=None)` has three committed mutation branches: source-key upsert (`:1018-1051`), body-dedup reinforcement (`:1052-1077`), and new-row INSERT (`:1078-1115`). Any truthy `journal_action` currently journals all three. | Add an opt-in insert-only journal gate plus event actor/cwd forwarding. Default behavior must leave CLI add/note journaling on all three branches unchanged. |
| `tools/memory/mem.py:1250-1257` | `_write_actor()` gives `MEM_ACTOR`, then `MEM_DISTILL`, precedence over a default. | Never use `_write_actor(default="sync")` for absorption events. Pass the literal actor to `_append_write_event`. |
| `tools/memory/mem.py:1260-1291` | `_append_write_event()` accepts no cwd argument and always writes `MEM_CWD` or `os.getcwd()`. Direct callers include consume, lifecycle-expire, delete, restore, reinforce, prune, merge, graduate, reattribute, and drain-consumed (`:2322-3020`); `write_record()` is its only indirect caller. | Introduce a sentinel-backed optional per-event cwd so omitted arguments retain the exact fallback, while explicit missing source cwd omits the JSON field instead of falling back. |
| `tools/memory/mem.py:2084-2230` | `migrate(apply=True)` scans auto-memory, registered/current post-its, global profiles, and legacy Markdown. Every absorption calls `write_record(..., quiet=True)` without journaling. `existing_src` skips known sources before any write. | Opt each source loop into the same `add`/literal-`sync`/insert-only contract and supply its logical cwd independently of DB `cwd_origin`. |
| `tools/memory/mem.py:3555-3574` | `sync()` calls `migrate(apply=True)` and then lifecycle/index/export. | Keep the signature and sequence unchanged. A repeat-sync test must use a fixture with no expiring record so any journal delta is attributable to absorption. |
| `tools/memory/mem.py:3731-3743` | CLI `add` and `note` are the only current `write_record(..., journal_action=...)` callers. `migrate` and `sync` are exposed at `:3759-3760` and `:3786-3787`. | Grep confirms no external Python caller needs a signature update. Add only trailing keyword parameters so existing positional and keyword calls remain valid. |

### Source-specific logical cwd

| Absorption source | DB `cwd_origin` remains | New event `cwd` |
|---|---|---|
| Auto-memory `projects/<enc>/memory/*.md` | `_canonical_cwd_key(<enc>)` | Decode `<enc>` to an existing absolute directory and emit that path; if decode fails, omit `cwd`. |
| Registered/current post-it | `project_key(repo_root, seed=False)` | Resolved absolute `repo_root` (`post-it.md` is `<repo>/.agent_reports/post-it.md` or legacy artifact equivalent), independent of process cwd and `MEM_CWD`. |
| `user_profile/*.md` | literal `global` | Explicitly no cwd field. |
| Legacy Markdown with frontmatter | `_canonical_cwd_key(meta.cwd_origin)` | Existing absolute path or decoded existing encoded path only; otherwise no cwd field. |
| Legacy Markdown without usable cwd metadata | existing process-derived DB behavior | Explicitly no cwd field for the absorption event. |

### Fleet consumer

- `tools/fleet/collectors/memory.py:23-26` already counts `action in ("add", "note")`; `sync` is intentionally not a distill actor.
- `_repo_key()` (`:103-118`) accepts a non-empty journal `cwd`, passes it to `project_of()`, and honestly omits rows with neither cwd nor project.
- `collect()` (`:142-217`) includes `add` in today's totals/recent and builds `by_repo` from today's cwd-bearing events. Therefore the existing consumer contract already supports the planned producer record.
- `tools/fleet/model.py:74-122` groups absolute paths, including `*-wt`/`*_worktrees` collapsing. An `agent-note`-like repo path will group under `agent-note`.

### Existing test coverage and gaps

- `tools/memory/mem_cluster_j.test.sh` is hermetic and currently covers 11 mutation actions, actor resolution, fail-open rotation, `mem log`, doctor, and store-adjacent journal isolation, but no migrate/sync absorption events.
- `tools/memory/mem_repairs_v15.test.sh:99-123` covers canonical auto-memory/post-it DB `cwd_origin`, not journal cwd or actor.
- `tools/memory/mem_cluster_e.test.sh:307-336` covers encoded-cwd decoder round trips and broader migration idempotency.
- `tools/fleet/tests/test_f19_memory.py:144-179` covers synthetic cwd grouping/omission; it does not consume a real migrate-produced row.
- Baseline on the sealed commit: `bash tools/memory/mem_cluster_j.test.sh` passed 33/33; `cd tools && python3 -m unittest fleet.tests.test_f19_memory -v` passed 26/26.

## Change plan

### Phase 0 — Revalidate the sealed entry gate and approved path set

Dependency: none. Complete this phase in the execution stage immediately before the first source edit; do not substitute a linked-worktree spec snapshot.

0.1. Confirm HEAD is still `e8938809d87e54474f5e7242a2552598c2636a0a`, the sealed route still reports satisfied `tracked_gate_evidence.spec_read`, and the completed spec-owner report remains attached to the route. Then run this exact-content gate against the canonical absolute inputs:

```sh
python3 - <<'PY'
from pathlib import Path

checks = {
    Path("/home/Uihyeop/agent_setting/.agent_reports/spec/prd.md"): (
        "**v22 2026-07-22**",
        "### 5.12.1 D-37",
        "**sync/migrate 흡수 규범**",
        "ambient `MEM_ACTOR`/`MEM_DISTILL`과 무관한 literal `sync`",
        "**prospective-only**",
        "historical backfill",
    ),
    Path("/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md"): (
        "**v15 2026-07-22**",
        "F-19 (메모리 관측 패널",
        "F-35f (memory 호환)",
        "`action=add`·literal `actor=sync`",
        "historical backfill",
    ),
}
for path, needles in checks.items():
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"spec gate failed: {path}: missing {missing}")
    print(f"spec gate ok: {path}")
PY
```

This is a text-drift check, not a request to land spec changes in the code worktree. A failure returns to the owner/spec owner; execution must not attempt to repair or commit canonical specs.

0.2. Record the clean sealed baseline and treat `tools/memory/mem.py` plus `tools/memory/mem_cluster_j.test.sh` as the complete approved code/test path set. `tools/fleet/collectors/memory.py` may be proposed only after the real producer-row acceptance in Phase 3 proves a collector incompatibility; capture that evidence and obtain owner scope approval before editing it.

### Phase 1 — Extend event plumbing without changing default callers

Dependency: Phase 0 complete. Steps 1.1-1.3 are ordered because the migrate changes consume the new plumbing.

1.1. In `tools/memory/mem.py` near the journal constants/pure path helpers, add one private sentinel (for example `_WRITE_EVENT_CWD_UNSET = object()`) and a small source-cwd decoder that:

- accepts an encoded cwd or absolute-path metadata;
- returns a resolved existing absolute path string;
- returns `None` for empty, relative, nonexistent, or undecodable input;
- does not call `project_key()` and does not mutate DB metadata.

1.2. Extend `_append_write_event()` with one trailing optional `cwd` parameter defaulting to the sentinel.

- Sentinel/default: preserve the current `MEM_CWD or os.getcwd()` field exactly for every existing caller.
- Explicit path: write that path as `cwd`, ignoring `MEM_CWD` and process cwd.
- Explicit `None`/missing source: omit the `cwd` key entirely (not `null`, empty, or fallback).
- Preserve timestamp, snippet sanitation, `MEM_SID`, bounded rotation, and fail-open `OSError` handling.

1.3. Extend `write_record()` with trailing keyword-only-in-practice options such as `journal_insert_only=False`, `journal_actor=None`, and `journal_cwd=_WRITE_EVENT_CWD_UNSET`, then forward them on every journal call.

- Source upsert and body-dedup branches append only when `journal_action` is set and `journal_insert_only` is false.
- The new INSERT branch appends whenever `journal_action` is set.
- Existing CLI add/note calls omit the new options, so their upsert/dedup/INSERT telemetry and ambient actor/cwd fallback remain unchanged.
- Absorption callers will pass `journal_action="add"`, `journal_insert_only=True`, `journal_actor="sync"`, and an explicit source cwd or `None`.

### Phase 2 — Opt the four migration sources into create-only telemetry

Dependency: Phase 1 complete. The four source-loop edits are logically independent once the shared signature exists, but should be reviewed together as one contract.

2.1. Auto-memory loop (`tools/memory/mem.py:2100-2121`): derive event cwd from `mp.parent.parent.name` with the source-cwd decoder while leaving `src` and DB `cwd_origin` unchanged; pass the create-only sync journal options to `write_record()`.

2.2. Post-it loop (`:2128-2167`): derive the event cwd from `root_dir.resolve()` and pass it with the same journal options. The existing `post-it:<encoded-root>:<body-hash>` source key remains unchanged.

2.3. Global profile loop (`:2174-2189`): pass explicit `journal_cwd=None` with literal sync actor and insert-only journaling. This produces an ordinary recent/today `add` but never a false repo group.

2.4. Legacy Markdown loop (`:2196-2222`): compute event cwd independently from raw frontmatter `cwd_origin` before DB canonicalization. Emit only a valid existing absolute/decode result; pass explicit `None` for missing/invalid metadata, including no-frontmatter files.

2.5. Do not update `existing_src` logic, source values, `created` reporting, body-dedup reinforcement behavior, DB schema, lifecycle, `sync()`, dump export, or journal rotation. Existing-source skips never enter `write_record`; same-run source upserts and body dedup enter it but are silenced by `journal_insert_only`.

### Phase 3 — Add focused hermetic producer/consumer acceptance tests

Dependency: Phase 2 complete. Modify only `tools/memory/mem_cluster_j.test.sh`; keep all fixtures under its existing temporary roots and set `MEM_STORE`, `MEM_PROJECTS`, `MEM_PROFILE`, and `MEM_WRITE_EVENTS` explicitly so no real DB/profile/journal is read or written.

3.1. Add a general-caller regression block proving an ordinary CLI add still uses `MEM_CWD` when set and process cwd when it is unset. Also exercise manual source upsert/body-dedup journaling so the insert-only gate is shown to be opt-in rather than global.

3.2. Add a hostile-environment auto-memory fixture:

- create an existing logical repo directory named like `agent-note` and an auto-memory file under its encoded projects directory;
- run `migrate --apply` from a different process cwd with `MEM_CWD=/wrong/repo`, `MEM_DISTILL=1`, and `MEM_ACTOR=curator`;
- assert exactly one new row and one journal event with `action=add`, literal `actor=sync`, and the decoded absolute logical repo path;
- assert the event did not inherit any hostile attribution input.

3.3. Add a deterministic registered-post-it producer-to-Fleet fixture independent of the auto-memory proof:

- allocate an existing repo root whose exact basename is `agent-note`, write `<repo>/.agent_reports/post-it.md`, and register that exact resolved file with the fixture store;
- run `migrate --apply` from a different process cwd under the same hostile `MEM_CWD`, `MEM_DISTILL`, and `MEM_ACTOR` values;
- resolve the inserted DB row by its `post-it:` source and assert its single journal row has `action=add`, literal `actor=sync`, and `cwd` exactly equal to the resolved repo root (not merely a path with the same basename);
- import `fleet.collectors.memory` with `PYTHONPATH="$ROOT/tools"`, call `collect()` at the current local date against the actual producer journal, and assert `by_repo["agent-note"]` exists with exactly that row's `action=add` and `actor=sync`.

This registered-post-it path is the mandatory producer/consumer acceptance gate for leaving `tools/fleet/collectors/memory.py` unchanged; the auto-memory fixture remains mandatory for the D-37 acceptance criterion.

3.4. Keep migration idempotency independent of `sync()`: snapshot DB row count, relevant strength/source values, and journal line count after the first `migrate --apply`, run a second explicit `migrate --apply`, and assert all snapshots are unchanged. This repeat-migrate assertion is the create-only/idempotency proof; do not use `sync` as its substitute.

3.5. Exercise `sync()` only as the lifecycle/index/export integration gate after the separate repeat-migrate proof. Every acceptance invocation of `sync` must go through one test helper that enforces all of the following:

- the scenario owns a newly allocated `mktemp -d` `MEM_STORE`, verifies it was empty when allocated, and proves it is outside every Git worktree with `git -C "$MEM_STORE" rev-parse --is-inside-work-tree` returning nonzero; the store may then be seeded by the immediately preceding fixture migrate but is never reused by another scenario;
- the command line explicitly supplies `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`, the isolated `MEM_STORE`, `MEM_PROJECTS`, `MEM_PROFILE`, and `MEM_WRITE_EVENTS`; no raw/unwrapped `mem.py sync` invocation is permitted in the suite;
- immediately before and after each invocation, capture content-sensitive snapshots of the real runtime store, profile directory, write journal, and dump (`/home/Uihyeop/agent_setting/memory`, `/home/Uihyeop/agent_setting/user_profile`, the effective XDG `agent-memory/write-events.jsonl`, and `/home/Uihyeop/agent_setting/memory/dump.jsonl`) plus `git status --porcelain=v1 -z`, unstaged diff, and staged diff for the code worktree; `cmp` all before/after snapshots and fail on any delta;
- the fixture has no expiring working record; after the fenced sync, assert DB row count and journal line count remain unchanged, the FTS/index mirrors are consistent where available, and the isolated `dump.jsonl` exists and represents the isolated DB.

The explicit dump flags are required even though the fresh store is non-Git. They fence future fixture drift from staging, committing, or pushing any dump.

3.6. Add isolated create-only edge fixtures:

- duplicate identical post-it bullets in one registered post-it file: first call INSERTs and journals once; second hits source upsert and adds no second event;
- preseed a same-tier/scope/cwd record and absorb a distinct post-it source whose raw body normalizes to the same body: strength reinforcement occurs but the absorption journal remains unchanged;
- preseed a record with the exact auto-memory source key and a journal sentinel, then run the first post-change migrate: the sentinel remains the only line (prospective no-backfill/existing-source skip);
- absorb an auto-memory source whose encoded project cannot resolve, a global profile, legacy Markdown with absent cwd metadata, and legacy Markdown with invalid/nonexistent cwd metadata under hostile `MEM_CWD` and a wrong process cwd; resolve each event by the inserted record/source and assert the raw JSON object does not contain the `cwd` key at all (not `"cwd": null`, an empty string, the ambient value, or process fallback);
- absorb legacy Markdown with valid encoded and valid absolute cwd metadata, asserting each event carries exactly the resolved logical cwd.

3.7. Add an explicit `mem log --json --actor sync` acceptance assertion after the mixed manual/sync fixture. Parse the JSON, assert `count == len(events)`, every returned row is `actor=sync` and `action=add`, and its ID set equals the absorption-event IDs expected from that fixture; prove the manual row is excluded.

3.8. Keep `tools/fleet/tests/test_f19_memory.py` unchanged unless step 3.3 fails because the existing consumer cannot group the valid post-it producer event. If such a failure is real, stop implementation expansion, record the exact journal row, `collect()` result, and traceback/assertion, then obtain owner direction before editing the consumer because the approved minimal plan assumes consumer compatibility.

### Phase 4 — Verification, projection/parity, and handoff

Dependency: Phase 3 complete.

4.1. Run every canonical `tools/memory/*.test.sh` suite. No canonical memory suite is excluded: the shared `write_record()` / `_append_write_event()` plumbing is broad enough that the full ten-suite regression net is the completion gate.

```sh
set -eu
for suite in \
  tools/memory/distill.test.sh \
  tools/memory/empty-store-guard.test.sh \
  tools/memory/inject.test.sh \
  tools/memory/mem_cluster_e.test.sh \
  tools/memory/mem_cluster_e_gamma.test.sh \
  tools/memory/mem_cluster_j.test.sh \
  tools/memory/mem_repairs_v15.test.sh \
  tools/memory/mem_retrieval_v14.test.sh \
  tools/memory/pending_drain.test.sh \
  tools/memory/retrieval-eval.test.sh
do
  bash "$suite"
done
```

An exclusion is permitted only if a suite is demonstrably unavailable for a named runtime/tool-contract reason. Record the exact suite, command, exit status, and unavailable contract; a failure is not an exclusion and does not satisfy the gate.

4.2. Run full Fleet unittest discovery, then verify syntax/help and adapter projections:

```sh
(
  cd tools
  python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v
)
python3 tools/memory/mem.py --help >/dev/null
test "$(readlink adapters/claude/tools/memory/mem.py)" = "../../../../tools/memory/mem.py"
AGENT_HOME="$PWD" adapters/codex/tools/memory/mem.py --help >/dev/null
AGENT_HOME="$PWD" adapters/opencode/tools/memory/mem.py --help >/dev/null
./tools/check-adaptation-boundary.sh
```

The Claude memory projection is a symlink to canonical `tools/memory/mem.py`; Codex and OpenCode are launchers that execute the canonical file through `AGENT_HOME`. Do not edit these adapter files. If a projection check fails because of a pre-existing environment/runtime wiring issue rather than the diff, record it as unsupported runtime evidence instead of changing unrelated runtime-owned configuration.

4.3. Enforce the approved-path boundary with an executable check that includes tracked and untracked paths, then run whitespace validation:

```sh
python3 - <<'PY'
import subprocess

allowed = {
    "tools/memory/mem.py",
    "tools/memory/mem_cluster_j.test.sh",
}
raw = subprocess.check_output(
    ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]
)
changed = set()
entries = raw.decode("utf-8", "surrogateescape").split("\0")
i = 0
while i < len(entries):
    entry = entries[i]
    if not entry:
        i += 1
        continue
    status = entry[:2]
    path = entry[3:]
    changed.add(path)
    if "R" in status or "C" in status:
        i += 1
        if i < len(entries) and entries[i]:
            changed.add(entries[i])
    i += 1
extra = changed - allowed
if extra:
    raise SystemExit(f"unapproved changed paths: {sorted(extra)}")
missing = allowed - changed
if missing:
    raise SystemExit(f"expected implementation paths missing from diff: {sorted(missing)}")
print("approved-path diff ok:", sorted(changed))
PY
git diff --check
```

If Phase 3.3 produced and the owner approved genuine collector-change evidence, update the recorded approved set before editing and include `tools/fleet/collectors/memory.py` in this check; otherwise any collector diff fails the route.

4.4. Standard/code QA requires the route's separate independent `plan-check` pass plus final verification. This plan-author stage does not claim that independent pass. Baseline evidence is 33/33 Cluster J and 26/26 focused Fleet tests; post-change evidence must include every command, exit status, assertion count, isolation snapshot comparison, and warning in the canonical dev/test artifacts.

4.5. The linked worktree is an execution surface, not the integration owner. Execution/test/report stages must not commit, push, merge, rebase, or clean the worktree. The depth-1 owner alone reviews the final diff/evidence and performs any authorized commit, push, and cleanup after the full route gate passes.

## Risks and rollback

- **Sentinel regression:** treating explicit `None` as the default would silently reintroduce process/env misattribution. Global/decode-impossible omission tests and hostile-env tests are mandatory.
- **Over-broad insert-only gate:** applying it unconditionally would suppress current add/note upsert and dedup events. Keep the option false by default and test ordinary callers.
- **DB/event attribution mix-up:** storing absolute paths in `cwd_origin` would break canonical visibility fences; storing `git:`/`id:` keys in event cwd would break Fleet grouping. Derive and pass them separately.
- **Legitimate sync lifecycle events:** a repeat-sync assertion can fail if a fixture contains expired working rows. Use a fixed, non-expiring fixture and distinguish absorption events from unrelated lifecycle mutations when diagnosing failures.
- **Sync dump side channel:** `sync()` reaches `_commit_dump()` after export. Every acceptance call must set both `MEM_DUMP_COMMIT=0` and `MEM_DUMP_PUSH=0`, use a freshly allocated non-Git store, and prove the real runtime paths plus code worktree are byte/status unchanged before and after.
- **Spec locality drift:** the canonical v22/v15 requirements live under `/home/Uihyeop/agent_setting/.agent_reports/spec/`, not this linked code worktree. Revalidate their exact clauses immediately before execution and rely on the sealed route's satisfied spec-read evidence/spec-owner report; do not manufacture a code-worktree spec commit.
- **First-time volume/rotation:** a legitimate first absorption of many truly new sources can rotate the bounded journal and displace old observation rows. This is observational loss under the existing 256KB/500-line contract, not DB loss; do not add backfill or change rotation in this patch.
- **Fail-open telemetry:** an append failure still must not roll back the new DB row. Existing fail-open coverage remains required.
- **Rollback:** no schema/data migration is introduced. Reverting the `mem.py` and focused test diff stops future absorption events and restores old behavior. Already emitted prospective JSONL rows remain valid `add` events and need no deletion; never rewrite a real journal as rollback.

## Decision points

None. The PRDs and r2 review already fix the actor, action, create-only boundary, cwd sources, prospective-only policy, consumer boundary, and no-commit ownership.

## Planning-stage evidence and warnings

- Sealed HEAD and worktree cleanliness were verified before planning.
- The canonical root spec currently contains v22 D-37 create-only/literal-sync/prospective-only clauses, and the canonical Fleet spec contains the v15 F-19/F-35f clauses (the Fleet document header has since advanced to v16 without removing that v15 text). Installed-harness spec-read marker writes remain unavailable because the primary checkout's `.spec-grounding` is mounted read-only; the sealed route's satisfied `tracked_gate_evidence.spec_read` and completed spec-owner report are the authoritative prerequisite. This is a runtime marker limitation, not authority to edit or commit a linked-worktree spec projection.
- No source, spec, test, collector, adapter, git history, or runtime memory/journal was changed by this stage.

## Change history

- 2026-07-22, plan-check round 1 reconciliation: corrected governing inputs to the canonical absolute artifact-root specs and made the sealed spec-read/spec-owner evidence authoritative; added immediate pre-execution v22/v15 text revalidation; expanded verification to all ten canonical memory shell suites plus full Fleet unittest discovery; separated repeat `migrate --apply` idempotency from fenced `sync` lifecycle/index/export integration; added real runtime/worktree isolation snapshots, deterministic registered-post-it-to-Fleet proof, `mem log --json --actor sync`, strict absent-key cwd cases, and an executable two-path diff gate.
