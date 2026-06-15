---
name: cluster-a-rewire-scope
description: v5 Cluster A user_profile-file removal — the rewire/grep scope must reach beyond agents/skills into the 3 canonical family docs (CONVENTIONS/WORKFLOW/README)
metadata:
  type: project
---

When rewiring `Read user_profile/0X_*.md` → `mem profile <stem>` for v5 Cluster A (DB-as-SoT), the inventory must NOT stop at `agents/ agent-modes/ skills/ CLAUDE.md`. Three **canonical family docs** also carry live `user_profile/0X_*.md` PATH references that break on deletion:

- `CONVENTIONS.md:589` (§7 store-arch table) names `user_profile/*.md` as the profile **source** — v5 inverts this (DB is source). `CONVENTIONS.md:593` lists `mem {...}` CLI **without `profile`** and glosses `export --target profile` as `user_profile view`.
- `WORKFLOW.md:73` (§3 scaffold convention-prepend) has `user_profile/07_coding_convention.md`(2순위) — same (D) form as `analyze-project/SKILL.md:152`.
- `README.md` is a `/sync-skills`-generated mirror — do NOT hand-edit; run `/sync-skills` after the SKILL/agent rewire to regenerate (else it ships stale `user_profile/` source-language at lines ~90/139/201/274).

**Why:** the round_1/round_2 §B grep gate scopes to `agents/ agent-modes/ skills/ CLAUDE.md`, so it prints "OK: no residual refs" while CONVENTIONS/WORKFLOW/README still reference deleted files — a false green, the same false-OK class the earlier fixes chased, one directory ring out.

**How to apply:** widen the §B grep to include `CONVENTIONS.md WORKFLOW.md`; treat README as regenerated (gate on sync-skills having run). CONVENTIONS lines 405 (jobs.log) and 427/429 (matrix label "coding_convention" aspect name) are NOT file-path refs — don't touch. See [[memory-v5-cluster-a]], [[mem-py-write-path]].

**Cross-skill contract (post-it promote ↔ analyze-user):** no CLI splices into an existing record body (`mem add` is always a fresh write_record). So "splice into the `## 사용자 수동 메모` block" = agent must `mem profile <stem>` (tie-broken read) → text-splice → `mem add` whole body with `--source user-profile:<stem>`. A separate `user-postit:<aspect>` source record is INVISIBLE to `mem profile` (which keys on `user-profile:` via `_derive_aspect`). Both writers must share the `user-profile:<stem>` source and read via the tie-broken `mem profile`, or the user's promoted memo gets orphaned on the next analyze-user update.
