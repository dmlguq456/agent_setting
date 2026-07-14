# Pipeline summary

Status: phase 2 Englishization in progress.

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
- Automatic recall no longer recognizes fixed natural-language signal phrases;
  all eligible prompts use one content-based qualification path.
- Korean users retain CJK tokenization and particle-normalized retrieval. The
  focused retrieval and hook suites pass.

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
- Recall hook regression: 18/18 pass.
- Multilingual retrieval regression: 20/20 pass, including Korean particle normalization.
- Adaptation boundary: pass.
- Portable guards: pass.

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
