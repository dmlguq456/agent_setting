# Pipeline summary

Status: complete.

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

## Deferred integration

Root README Englishization remains with the runtime-activation owner. Legacy
`_ko.md`/`_en.md` dual-artifact schemas in capability and planning workflows are
not mechanically renamed in this cycle; they require a coordinated artifact
schema migration after the concurrent branch lands.
