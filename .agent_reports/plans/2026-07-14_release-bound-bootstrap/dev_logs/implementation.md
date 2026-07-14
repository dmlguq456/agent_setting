# Implementation log

- Added deterministic `install.sh` and `install.sh.sha256` generation to the
  release builder.
- Embedded the tagged `distribution.py`, repository, and version in the public
  installer; blocked `--repository` and `--version` overrides with exit 64.
- Converted root `install.sh` into a download-then-execute compatibility redirect
  to the latest release asset. It no longer reads raw-main distribution code.
- Expanded the tag workflow from two to four release assets.
- Moved English/Korean README and INSTALL_LAYOUT commands to GitHub Release URLs.
- Updated installer v5 and productization v7 contracts with exact repository/tag
  binding and versioned installer URL pinning.

## Failure-mode corrections during implementation

- Replaced a nested `curl | sh` in the legacy redirect with complete temporary
  download followed by execution so a transfer failure cannot be hidden by the
  pipeline's last command status.
- Bound publisher repository as well as tag; otherwise another repository with
  the same tag name could be selected by an override.
