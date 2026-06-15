---
name: mem-py-write-path
description: mem.py write_record dedup semantics and the source-keyed upsert gap that affects analyze-user/post-it DB authoring
metadata:
  type: project
---

`tools/memory/mem.py` write semantics (load-bearing for any plan that writes profile/working records):

- `write_record(tier, scope, rtype, body, ...)` (the only write primitive) dedups on `(tier, scope, normalized-body)` SHA hash via `find_dup()`. Identical body → returns existing id (no-op). **Changed body for the same `source` → mints a NEW id** (seed includes `today()`), leaving the old row in place.
- So `mem add ... --source user-profile:<stem>` is NOT an upsert. `migrate()` achieves idempotency by pre-checking existing `source` values and skipping, not replacing.
- There is **no `mem delete <id>` CLI** and **no source-keyed upsert**. Cleanup relies on `mem lifecycle` dup-flag (advisory) + `WORKING_TTL_DAYS` expiry for working tier.

**Why:** v5 Cluster A converts analyze-user (`update` mode) and `/post-it resolve`/`sweep` to DB authoring, which need replace/delete semantics that don't exist. A source-keyed upsert in `write_record` (REPLACE the existing-source row's id) is the proper fix.

**How to apply:** When planning DB-write features, do NOT assume `mem add` updates in place. Either flag the upsert as out-of-scope (documented dup-on-update limitation) or expand scope to add it. Read primitives are clean: `db_iter_records(con, where, params)` is the core; `_derive_aspect(meta, body)` returns the profile stem from `source=user-profile:<stem>`. See [[memory-v5-cluster-a]].
