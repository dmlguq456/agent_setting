# Final report — clone-free releases and automatic updates

## Outcome

Agent Harness now has two explicit delivery paths:

- general users install a managed, immutable packaged release with one command;
- maintainers keep an explicit linked checkout that the updater never fetches,
  pulls, or repoints.

## Implemented

- Root `install.sh` downloads the standalone stdlib distribution module.
- GitHub Release metadata must contain the fixed archive and SHA-256 sidecar.
- Safe extraction rejects traversal, escaping links, special files, oversized
  payloads, malformed metadata/state, and symlinked state/lock roots.
- XDG version roots, `current`, and the PATH launcher publish atomically after
  successful packaged activation.
- `harness update` routes managed installs to the release updater and preserves
  checkout drift/reapply behavior elsewhere.
- Version pins survive scheduled `--auto` checks. systemd user timers and
  LaunchAgents preserve install-time HOME/XDG/runtime overrides and refuse to
  enable without an owned managed release.
- Update rollback preserves the actual pre-change runtime profile, not only the
  distribution state's last recorded profile.
- The tag workflow uses minimum write permission, a commit-SHA-pinned checkout
  action, deterministic assets, and the full release/security regression gate.
- README/README.ko now lead with one-line install and five concrete strengths;
  the standalone “native first, plugins optional” pitch was removed.

## Trust boundary

The SHA-256 sidecar detects transfer or asset corruption. It is not an
independent publisher signature; authenticity is anchored to this repository's
GitHub Release and HTTPS publisher account.

## Verification

All nine deterministic gates in `test_logs/final.md` passed. Independent
security review finished with no HIGH or MEDIUM findings.

## Deployment follow-up

The code and workflow are ready. The public one-line path becomes live after
this branch is integrated into `main` and the first `v*` tag publishes
`agent-harness.tar.gz` plus its checksum asset.
