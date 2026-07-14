# Implementation log

## Portable contracts

- Added audience-language-first as the first response-policy clause for
  user-facing documents and artifacts. Explicit target, publication, external
  audience, existing artifact, and repository documentation language contracts
  take precedence.
- Generalized editorial design principles and active portable modes so they no
  longer force Korean output.
- Kept main conversational response language implicit; the new contract governs
  user-facing artifacts rather than imposing a fixed chat locale.

## Runtime realizations

- Removed fixed Korean response/report clauses from Claude, Codex, and OpenCode
  bootstraps and Claude/Codex headless worker prompts.
- Added the portable audience-language clause to all three bootstraps.
- Updated the Claude editorial router and the portable, Claude, and generated
  Codex mode projections. Regenerated the Claude installable plugin copy.
- Removed remaining fixed Korean user-output and summary directives from active
  compatibility/Claude Skills and the development, planning, research, QA, and
  external-review routers. Preserved explicit publication and canonical source
  language contracts.
- Kept the legacy English-source plus `_ko.md` compatibility mirror schema
  intact. The planning router now treats it as a Korean-target compatibility
  path rather than a universal output default.

## Recall semantics

- Snapshotted memory PRD v15 and updated the live PRD to v16.
- Removed `_RECALL_SIGNAL_WORDS`, signal-word stripping, and the
  phrase-dependent explicit/implicit automatic-recall modes.
- Applied one content-based qualification rule to every eligible project prompt
  and fixed automatic telemetry mode to `automatic`.
- Preserved Korean/CJK tokenization support, including particle normalization;
  language support is evidence extraction, not a trigger phrase list.
- Updated hook documentation, injection heading, and regression descriptions.

## Parallel boundary

The concurrent runtime-activation branch owns `README.md`, `INSTALL_LAYOUT.md`,
and `tools/install/**`; none of those paths changed here.
