## Sub-Actions

### `/post-it` with no arguments = `show`

Run `python3 <agent-home>/tools/memory/mem.py recall "" --tier working --scope project` to preview working records for the current cwd. If none exist, suggest `/post-it add`.

### `/post-it add <category> <text>`

- `<category>` is one of `convention`, `resource`, `thread`, or `decision`; aliases are `conv`, `res`, `th`, and `dec`.
- Run `python3 <agent-home>/tools/memory/mem.py note "<text>" --type <type>`, mapping convention→`convention`, resource→`reference`, thread→`thread`, decision→`decision`.
- For `thread`, prefix the body with `[in-progress YYYY-MM-DD]` automatically.
- For `decision`, prefix the body with `YYYY-MM-DD:` automatically.
- Apply the user's text verbatim and immediately. Use `--confirm` to preview the diff.

### `/post-it resolve <hint>`

- Fuzzy-match `<hint>` against working records with `type=thread`.
- Default to preview → confirm: one match asks for confirmation, multiple matches ask for a numbered choice, and zero matches stops.
- Delete deterministically with `mem delete <id>`. With `--no-confirm`, immediately delete the single closest match.

### `/post-it decide <text>`

Run `python3 <agent-home>/tools/memory/mem.py note "<YYYY-MM-DD: text>" --type decision`. Apply the user's text immediately; use `--confirm` to review.

### `/post-it sweep [--no-confirm] [--scope project|user [<aspect>]]`

Compare artifacts with DB records and flag or expire graduated/stale items to keep post-it lean.

- **Automatic path** inside nudge or handoff: automatically flag only certain graduated/stale items, report one line, and keep ambiguous entries.
- **Manual path** through `/post-it sweep`: preview → confirm. With `--no-confirm`, process only certain entries immediately.

**Project scope (default)**:

1. Run `python3 <agent-home>/tools/memory/mem.py recall "" --tier working --scope project` to load every working record for the current cwd.
2. Compare them with `<artifact-root>/plans/*/`, `documents/*/`, `spec/`, `experiments/*/`, `git log --oneline -30`, and relevant code/documents.
3. Classify every record:
   - **graduated** — permanently represented in an artifact; candidate for expiration, with a one-line pointer to its destination.
   - **stale** — time-based lifecycle tier for `type=thread/decision/hint`:
     - **active**: <30d or connected to recent git activity → keep.
     - **stale candidate**: unchanged for about 30d or more and disconnected from git activity → candidate for expiration.
     - **archive**: unchanged for about 90d or more, or clearly completed → flag automatically with one-line reporting. `mem lifecycle` uses `WORKING_TTL_DAYS`. Graduated content already lives in an artifact, so drop rather than archive it.
   - **live** — still valid and present only in a working record. Conventions and references do not age; remove them only through graduation.
4. Preview three groups—graduated, stale, keep—and ask which entries to remove.
5. Trigger `mem lifecycle` or apply advisory handling.

`sweep` handles only working records. It never adds content to artifacts; the owning skill performs graduation.

**User scope (`--scope user <aspect>`)**:

- Load the profile record with `python3 <agent-home>/tools/memory/mem.py profile <stem>`.
- Compare each item under the exact legacy heading `## 사용자 수동 메모` with the structured section for the same aspect. Preview already-integrated items as removal candidates, then confirm.

### `/post-it promote [<hint>] [--scope user [<aspect>]]`

Graduate a user memo into a structured aspect section. This action is user-scope only.

**Storage model:** embed user memos inside the exact `## 사용자 수동 메모` block in the profile-record body. Do not create a separate `user-postit:` source record, which would be invisible to `mem profile`/`_derive_aspect` and therefore to other agents.

**Read-modify-write flow**:

1. In the `<aspect>` profile record, defaulting to `collab`, identify a stable and general item under `## 사용자 수동 메모`; use `<hint>` to select one when provided.
2. Propose wording for integration into the relevant structured section, then preview → confirm. This preserves analyze-user's read-only contract.
3. After confirmation:
   1. Read the current body with `python3 <agent-home>/tools/memory/mem.py profile <stem>`, which is newest-wins with rowid-DESC tie-breaking.
   2. Splice the note into the structured section and remove it from `## 사용자 수동 메모`.
   3. Write the entire new body with `python3 <agent-home>/tools/memory/mem.py add durable profile "<whole-new-body>" --scope global --source user-profile:<stem>`. The source matches analyze-user's logical record; expire the prior working record.
4. For large-scale formal restructuring, recommend `/analyze-user` instead. `promote` is for graduating one or two lightweight items.

> **Two-writer contract:** `/post-it promote --scope user` and `analyze-user update` both write `source user-profile:<stem>`, one logical record. analyze-user must read the existing body with tie-broken `mem profile <stem>`; raw `db_iter_records` risks splicing into a stale duplicate. `write_record` performs a source-keyed UPSERT on `(tier, scope, source)`, updating the record in place and preserving its ID rather than creating duplicates.

### `/post-it handoff [--no-confirm]`

Sweep first, then generate session-handoff hints.

1. Include a sweep that automatically prunes only certain graduated/stale items, keeps ambiguous entries, and reports one line.
2. Review the current conversation and create 5–10 bullets covering progress, the first next-session action, unresolved questions/blockers, and cautions.
   - Exclude content already persisted in artifacts/git or already present in another working record.
3. Default to preview → confirm. Let the user edit or add bullets.
4. After confirmation, record each bullet with `python3 <agent-home>/tools/memory/mem.py note "<hint-text>" --type hint`. `mem lifecycle` replaces or expires earlier hint records.
5. With `--no-confirm`, apply the sweep and hints immediately without review.

## Confirmation Summary

| Sub-action | Default | Override |
|---|---|---|
| `show` | Immediate | n/a |
| `add` / `decide` | Immediate, preserving user text verbatim | `--confirm` |
| `resolve` | Preview → confirm after fuzzy matching and advisory | `--no-confirm` |
| Manual `sweep` | Preview → confirm after agent classification | `--no-confirm` |
| Automatic `sweep` inside nudge/handoff | Automatically prune only certain entries, report one line, keep ambiguous entries | n/a |
| `promote` | Preview → confirm after agent proposal and structured-section edit | None; always confirm |
| `handoff` from an automatic nudge | Include sweep, show a short summary, confirm storage | `--no-confirm` |

Apply user-authored text immediately. Review content the agent generates or matches. Because the user does not read post-it directly, automatic pruning handles only certain entries and reports one line; require confirmation at the action level, not line by line.
