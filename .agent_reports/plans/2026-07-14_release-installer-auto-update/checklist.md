# Release installer and automatic update checklist

- [x] Managed agent-home resolution works without `.git`.
- [x] `install.sh` bootstraps from an integrity-checked release without clone.
- [x] Release metadata requires the expected archive and SHA-256 assets.
- [x] Extraction rejects traversal, escaping symlinks/hardlinks, and special files.
- [x] Publish uses version roots plus atomic `current`/launcher pointers.
- [x] Initial install activates selected runtimes as packaged `builder`.
- [x] Managed update is no-op or pointer repair on identical version/checksum.
- [x] Managed update rolls forward and rolls back transactionally, including actual profile drift.
- [x] Linked/foreign runtime sources are skipped and never fetched/pulled.
- [x] Auto-update supports systemd user timer, LaunchAgent, pin, opt-out, and manual fallback.
- [x] Release workflow creates deterministic archive and checksum assets from a verified tag.
- [x] English/Korean README use one-line install and concise strengths; no standalone plugin pitch.
- [x] Isolated release lifecycle/security tests pass.
- [x] Existing runtime activation, profile, and extension tests pass.
- [x] Generated projection, conformance, adaptation, and doctor checks pass.
- [x] Specs and pipeline records are finalized.
