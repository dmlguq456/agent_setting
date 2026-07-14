# Final report — release-bound bootstrap

## Outcome

The mutable bootstrap/release mismatch is closed. A public installation now
executes distribution code and installs an archive produced from one immutable
GitHub `repository@tag`.

## User paths

- Latest: `https://github.com/dmlguq456/agent_setting/releases/latest/download/install.sh`
- Pinned: `https://github.com/dmlguq456/agent_setting/releases/download/<tag>/install.sh`
- Former raw-main command: compatibility redirect to the latest release asset.

## Release

- Version: `v1.0.1`
- Implementation: `b85a95d7`
- Release workflow: `29318001526` (success)
- Public isolated install and update verification: pass

## Boundary

The installer sidecar and archive sidecar detect asset corruption. Publisher
authenticity remains anchored to the repository's GitHub Release and HTTPS
account; the checksums are not independent signatures.
