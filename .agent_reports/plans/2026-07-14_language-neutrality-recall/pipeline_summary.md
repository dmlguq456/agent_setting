# Pipeline summary

Status: phase 5 runtime-prose batch validated; broader Englishization remains in progress.

## Phase 4 memory semantic boundary

- Semantic choices about storing, retrieving, promoting, merging, and pruning
  memory belong to the acting agent.
- Deterministic memory code is limited to mechanical integrity, isolation,
  lifecycle execution, pending protection, bounded telemetry, and recovery.
- The automatic prompt classifier and recall injection path are retired;
  explicit multilingual retrieval remains.

This cycle is isolated from the concurrent runtime-activation implementation.
Its source ownership is language policy, role/mode output contracts, and memory
recall semantics; installer and root README files are excluded.

## Result

- User-facing artifact language now follows the user's communication language
  by default, with explicit audience and publication contracts taking priority.
- Runtime bootstraps and active role-mode output contracts no longer impose
  Korean as a fixed locale.
- Active compatibility/Claude Skills and team routers no longer impose Korean
  for chat reports or internal return summaries. Explicit publication and
  target-artifact language contracts remain.
- Prompt-submit bridges no longer classify prompts or inject memory. Agents
  decide contextually when retrieval may help and then invoke explicit recall.
- Korean users retain CJK tokenization and particle-normalized retrieval. The
  focused retrieval and hook suites pass.

## Phase 4 result

- Removed the semantic `mem recall --auto` implementation and its fixed
  keyword, score, and threshold machinery.
- Removed prompt capture and automatic recall injection from Claude Code,
  Codex, and OpenCode runtime bridges. The old shared hook is a silent,
  fail-open compatibility shim only.
- Reframed shared and adapter distillation prompts so the acting agent owns
  storing, reinforcing, merging, pruning, graduating, and reattribution
  decisions. Scripts retain mechanical validation, pending protection,
  transaction safety, recovery, and bounded telemetry.
- Kept explicit multilingual retrieval intact, including CJK tokenization and
  Korean particle normalization.

## Phase 5 runtime-prose result

- Removed the fixed `convention|lesson` filter from `promote-candidates`.
  Institutionalization review now exposes a bounded view of all visible durable
  records; record type and strength remain evidence for the agent, not gates.
- Converted shared and Claude memory lifecycle hooks, briefing context,
  dispatch liveness/wait, usage checks, workflow signals, legacy index checks,
  and the web-figure utility to English source prose and diagnostics.
- Rewrote `tools/memory/README.md` as a fully English operational reference,
  including the D-40 agent-judgment boundary and the multilingual retrieval
  contract.
- The selected production files now contain zero Korean prose lines. Remaining
  non-installer runtime occurrences are concentrated in `tools/memory/mem.py`;
  Codex mode-sync strings are compatibility match literals for still-Korean
  canonical mode fragments.

## Phase 2 Englishization batch

- Translated all 27 portable capability contracts and their catalog summaries.
- Regenerated 27 Codex Skills, 27 OpenCode Skills, 27 OpenCode commands, and
  the affected Claude/Codex plugin projections.
- Reduced Korean-bearing lines on capability-derived runtime surfaces from
  253 to 4. The four remaining lines are projections of the same legacy
  `## 사용자 수동 메모` DB-schema literal, retained for data compatibility.
- Replaced fixed Korean-output instructions in 23 hand-authored Skill files
  with the audience-language contract and synchronized Claude compatibility
  copies.
- Extended `tools/skill-conformance/check.sh` to reject fixed user-facing
  Korean-language directives while permitting conditional mirrors, Korean
  retrieval fixtures, and schema literals.

## Verification evidence

- Manifest and all affected Claude/Codex/OpenCode projection checks: pass.
- Skill conformance: pass, 26 invocation classifications plus audience-language neutrality.
- Retired recall-hook compatibility regression: 4/4 pass.
- Multilingual retrieval regression: 21/21 pass, including Korean particle normalization and type-neutral promotion review.
- Distillation dispatch regression: 36/36 pass.
- Distillation lifecycle regression: 37/37 pass; turn-nudge regression: 11/11 pass.
- Adaptation boundary: pass.
- Portable guards: 343/343 pass.
- Dispatch liveness, wait, concurrency, and usage-check focused suites: pass.

## Phase 3 metadata and runtime-script batch

- Converted the exposed frontmatter metadata for all 26 hand-authored active
  Skills (`description`, `blurb`, and argument hints) to English.
- Converted comments and deterministic diagnostics in 21 small non-installer
  runtime scripts across hooks, memory wrappers, and adapter dispatch/sync
  helpers. The selected batch now has zero Korean prose lines.
- Reduced Korean-bearing lines in active non-test hook scripts from 333 to
  213. The remaining lines are concentrated in the larger memory lifecycle
  hooks and are still pending translation.
- Preserved Korean recall queries, particle/tokenizer data, DB-schema literals,
  and compatibility match strings because they are functional multilingual
  support rather than source-document prose.
- Re-ran shell/Python syntax checks, portable guards, skill conformance,
  adapter projection freshness, adaptation boundary, and manifest freshness.

## Deferred integration

Root README Englishization remains with the runtime-activation owner. Legacy
`_ko.md`/`_en.md` dual-artifact schemas in capability and planning workflows are
not mechanically renamed in this cycle; they require a coordinated artifact
schema migration after the concurrent branch lands.
