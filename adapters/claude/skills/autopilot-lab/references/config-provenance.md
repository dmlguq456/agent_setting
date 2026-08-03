# Config provenance

Config lifecycle is explicit: adopted defaults live in `configs/`, new or
unadopted experiment settings in `configs_exp/<slug>/`, and historical
model/checkpoint reproductions in `configs_legacy/`. A `.lab-config-layout.json`
root declaration (`{"schema_version": 1, "layout": "<name>", "roots":
{"default": "<dir>", "exp": "<dir>", "legacy": "<dir>"}}`) remaps `resolve`'s
physical roots, not just the recorded `config_layout` label — bare, `config:`,
`exp:`, and `legacy:` references then resolve against the declared
directories, with longest-match attribution when roots nest. A plain-text
`.lab-config-layout` file or `experiment_conventions.md` label only sets the
label; `resolve` always exposes the actually-used `roots` and
`layout_declaration` so a label-only declaration is never silently assumed to
have remapped anything.

Before a full run, resolve a config without root fallback and seal it with
`tools/lab-config-provenance.py`. The seal copies the exact bytes to a
directory derived from a required `--artifact-root` and writes a manifest
containing `schema_version` (2), `config_ref`, `run_id`, `source_path`,
`source_sha256`, `source_commit`, `source_dirty`, `source_git_state`,
`snapshot_path`, and `snapshot_sha256`. `verify` is fail-closed; retries with
the same inputs are idempotent. Case-insensitive filesystems are an explicit
non-goal (Linux-only harness).

Example:

```sh
python3 tools/lab-config-provenance.py resolve --repo . --ref exp:demo/train.yaml
python3 tools/lab-config-provenance.py run-id --slug demo --config-ref exp:demo/train.yaml --config-sha256 HASH
python3 tools/lab-config-provenance.py seal --repo . --config exp:demo/train.yaml --slug demo --artifact-root "$ARTIFACT_ROOT"
```

`--run-id` is optional on `seal` — omit it to have the tool emit the computed
run ID; if given, it must match the computed value exactly.

Pass the resulting manifest to smoke attestation and the registered resource
runner. Evaluation uses that snapshot or manifest, never a checkpoint
directory name. Existing runs remain unchanged; record an
`existing_run_exception` for an explicit compatibility handoff. Promotion is
a recommendation to the code/spec owner and never overwrites `configs/`
without user approval.

**Limits (by design):** attestation requires the config source file to exist
at attest time — a manifest whose source was later deleted stays
`verify`-valid and snapshot-reproducible, but cannot back a *new*
attestation, since the smoke gate is meant to guarantee the bytes a run will
actually read. A sealed manifest is not portable on its own: `verify`
requires the hash-named snapshot to sit beside it in the same
`_internal/configs/` directory, so move the manifest together with that
directory.

The smoke attestation now binds both the config snapshot and its source:
`payload()` verifies the config manifest against the full `verify` contract
before running the command, and adds top-level `config_sha256`,
`config_source_sha256`, and `config_source_path` alongside snapshot and source
rows in `inputs`. `verify()` requires an input row whose path matches
`config_source_path` and whose digest matches `config_source_sha256` — a
snapshot-only input can no longer satisfy that check, since source and
snapshot bytes are identical by construction and a hash-only check would be
vacuous. The actual enforcement point for a `--config-manifest` launch whose
run ID, config hash, or source path disagrees with the sealed manifest is
`utilities/resource-runner.py start`, which rejects the launch (exit 65)
before the log, process, or registry row are created.
