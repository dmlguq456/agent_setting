---
name: memory-v5-cluster-a
description: Unified Memory System v5 Cluster A — DB is sole SoT, user_profile/post-it standalone files removed, mem profile is the read source
metadata:
  type: project
---

Cluster A (spec `.claude_reports/spec/prd.md` §4, v5 Option 2) removes the `user_profile/` and `post-it.md` standalone-file mechanisms; `memory.db` `type=profile` records become the sole SoT and read source.

Key facts:
- 7 profile records exist (migration done): `source='user-profile:<stem>'`, scope=global, tier=durable, cwd_origin='global'. Stems: 01_paper_figure_style, 02_paper_writing_style, 03_presentation_strategy, 04_analysis_methodology, 05_domain_expertise, 06_collaboration_style, 07_coding_convention.
- New read CLI `mem profile <aspect>` (read-only) replaces `Read ~/.claude/user_profile/0X_*.md` in agents/skills/CLAUDE.md.
- Reference types when rewiring: (R) read-action → convert to `mem profile`; (D) descriptive 1순위/2순위 priority prose → keep meaning, change source token only; (X) asset paths (`user_profile/assets/`) → preserved.
- editorial-team.md and asset-pointer refs (autopilot-design, agent-modes/design/maker.md) were outside the original task list but matter for the grep gate / preserved assets.

**Path convention (critical):** cwd is a git worktree of `~/.claude`. Edit *worktree-relative* files (`agents/`, `skills/`, `tools/memory/mem.py`, `CLAUDE.md`) but write *absolute* `~/.claude/...` runtime paths inside the text (agents run from the live config dir).

**How to apply:** When this project's plans/code touch profile or post-it memory, the DB is authoritative; `mem profile`/`mem recall`/`mem inject` are the read faces. See [[mem-py-write-path]] for the write gap.
