# Final verification

- GitHub Actions Release run `29318001526`: PASS, including repository tests,
  deterministic build, and four-asset publish.
- Public release: `v1.0.1`, non-draft, non-prerelease, target `main`.
- Assets: `agent-harness.tar.gz`, `agent-harness.tar.gz.sha256`, `install.sh`,
  `install.sh.sha256`.
- GitHub latest metadata resolves to `v1.0.1`; public installer checksum passes.
- Public installer contains `dmlguq456/agent_setting@v1.0.1` and rejects a
  `--version v1.0.0` override with exit 64 before mutation.
- Isolated public install activates Claude Code, Codex, and OpenCode with the
  builder profile; all strict doctors report fresh; `harness update` reports
  managed release up-to-date at `v1.0.1`.
- Scheduler activation was deliberately suppressed in the isolated test;
  generated systemd-user configuration reported `configured-manual`.

One test-probe false failure expected the final GitHub CDN URL to retain the
release tag path. GitHub redirects assets to a signed CDN URL, so the probe was
corrected to verify latest API metadata plus embedded repository/tag and asset
checksum. No product change was required.
