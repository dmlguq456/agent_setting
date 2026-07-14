# Checklist — release-bound bootstrap

- [x] Specs v5/v7 and prior snapshots are consistent.
- [x] Release build emits deterministic archive and installer assets plus checksums.
- [x] Installer embeds distribution code and exact repository/tag from one Git ref.
- [x] Latest installer rejects cross-version and cross-repository overrides.
- [x] Root compatibility shim never reads raw distribution code.
- [x] README English/Korean and INSTALL_LAYOUT use release URLs.
- [x] Release workflow publishes all required assets.
- [x] Security, lifecycle, runtime, profile, extension, generation, and boundary gates pass.
- [x] `v1.0.1` public release and isolated install pass.
