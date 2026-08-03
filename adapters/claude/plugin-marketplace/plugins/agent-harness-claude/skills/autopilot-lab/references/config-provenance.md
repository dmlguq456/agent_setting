# Config provenance

Config lifecycle is explicit: adopted defaults live in `configs/`, new or
unadopted experiment settings in `configs_exp/<slug>/`, and historical
model/checkpoint reproductions in `configs_legacy/`. A repository declaration
overrides the recorded `config_layout` label. It does not currently remap
`resolve`'s physical roots: bare, `exp:`, and `legacy:` references always
resolve against `configs/`, `configs_exp/`, and `configs_legacy/` regardless
of the declared name.

Before a full run, resolve a config without root fallback and seal it with
`tools/lab-config-provenance.py`. The seal copies the exact bytes to the
artifact root and writes a manifest containing `schema_version`, `config_ref`,
`run_id`, `source_path`, `source_sha256`, `source_commit`, `source_dirty`,
`snapshot_path`, and `snapshot_sha256`. `verify` is fail-closed; retries with
the same inputs are idempotent.

Example:

```sh
python3 tools/lab-config-provenance.py resolve --repo . --ref exp:demo/train.yaml
python3 tools/lab-config-provenance.py run-id --slug demo --config-ref exp:demo/train.yaml --config-sha256 HASH
python3 tools/lab-config-provenance.py seal --repo . --config exp:demo/train.yaml --slug demo --run-id RUN --out "$ARTIFACT_ROOT/experiments/demo/_internal/configs"
```

Pass the resulting manifest to smoke attestation and the registered resource
runner. Evaluation uses that snapshot or manifest, never a checkpoint
directory name. Existing runs remain unchanged; record an
`existing_run_exception` for an explicit compatibility handoff. Promotion is
a recommendation to the code/spec owner and never overwrites `configs/`
without user approval.

`smoke-attestation verify` cannot by itself detect that a config manifest was
ever expected: it only checks that a claimed `config_sha256` binds to a
snapshot already present in `inputs`, and does nothing when `config_sha256`
is absent. An attestation built without `--config-manifest` therefore passes
standalone `verify` even when a sealed manifest exists elsewhere. The actual
enforcement point for a `--config-manifest` launch with an attestation
missing the matching config hash is `utilities/resource-runner.py start`,
which rejects the launch (exit 65) before the log, process, or registry row
are created.
