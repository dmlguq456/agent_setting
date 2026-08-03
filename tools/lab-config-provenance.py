#!/usr/bin/env python3
"""Resolve, seal, verify, and package experiment configuration provenance."""
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

ERROR = 65

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fail(message):
    print("lab-config-provenance:", message, file=sys.stderr)
    raise SystemExit(ERROR)

def repo_path(repo, raw):
    root = Path(repo).resolve(strict=True)
    candidate = (root / raw).resolve(strict=False) if not Path(raw).is_absolute() else Path(raw).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        fail("path escapes repository")
    if candidate.exists():
        try:
            candidate.resolve(strict=True).relative_to(root)
        except ValueError:
            fail("symlink escapes repository")
    return candidate

def layout(repo, requested):
    if requested != "auto": return requested
    root = Path(repo)
    declaration = root / ".lab-config-layout"
    if declaration.is_file(): return "declared/" + declaration.read_text().strip()
    conventions = root / "analysis_project/code/experiment_conventions.md"
    if conventions.is_file():
        for line in conventions.read_text().splitlines():
            if line.lower().startswith("lab-config-layout:"):
                return "declared/" + line.split(":", 1)[1].strip()
    return "structured" if (root / "configs").is_dir() else "legacy/unstructured"

def _under(root, base_name, rest):
    if ".." in Path(rest).parts: fail("path traversal is not allowed")
    base = Path(root) / base_name
    path = repo_path(root, str(Path(base_name, rest)))
    try:
        path.relative_to(base)
    except ValueError:
        fail("reference escapes its lifecycle root")
    return path

def resolve_ref(repo, ref, requested="auto"):
    root = Path(repo).resolve(strict=True); lay = layout(root, requested)
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in ref):
        fail("control characters are not allowed in a config reference")
    if ".." in Path(ref).parts: fail("path traversal is not allowed")
    if ref.startswith("exp:"):
        rest = ref[4:]; parts = Path(rest).parts
        if len(parts) < 2: fail("experiment reference requires slug/name")
        path = _under(root, "configs_exp", rest)
        namespace = "exp"
    elif ref.startswith("legacy:"):
        rest = ref[7:]
        path = _under(root, "configs_legacy", rest)
        namespace = "legacy"
    elif Path(ref).is_absolute() or "/" in ref or "\\" in ref:
        path = repo_path(root, ref); namespace = "path"
    else:
        if lay != "structured": fail("bare config is unavailable outside a structured layout")
        path = repo_path(root, str(Path("configs", ref))); namespace = "default"
    if not path.is_file(): fail("config does not exist: " + str(path))
    return {"layout": lay, "root": str(root), "namespace": namespace, "config_ref": ref, "path": str(path)}

def normalize(value):
    value = re.sub(r"[^A-Za-z0-9._-]", "-", value)
    return re.sub(r"-+", "-", value)

def run_id(slug, config_ref, config_sha256, attempt=None):
    stem = normalize(Path(config_ref).name.rsplit(".", 1)[0])
    material = "\n".join([slug, config_ref, config_sha256 or ""]).encode()
    result = f"{normalize(slug)}__{stem}__{hashlib.sha256(material).hexdigest()[:12]}"
    return result + (f"__a{attempt}" if attempt is not None else "")

def git_info(repo):
    root = Path(repo)
    try: commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: commit = "unknown"
    dirty = subprocess.run(["git", "-C", str(root), "diff", "--quiet"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0
    return commit, dirty

def cmd_resolve(a): print(json.dumps(resolve_ref(a.repo, a.ref, a.layout), sort_keys=True))

def cmd_seal(a):
    resolved = resolve_ref(a.repo, a.config, "auto")
    source = Path(resolved["path"]); digest = sha(source); out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    snapshot = out / f"{digest}{source.suffix}"
    if snapshot.exists() and sha(snapshot) != digest: fail("snapshot filename/content mismatch")
    if not snapshot.exists(): snapshot.write_bytes(source.read_bytes())
    commit, dirty = git_info(a.repo)
    ref = a.config_ref or resolved["config_ref"]
    manifest = {"schema_version": 1, "config_ref": ref, "run_id": a.run_id,
                "source_path": str(source), "source_sha256": digest, "source_commit": commit,
                "source_dirty": dirty, "snapshot_path": str(snapshot), "snapshot_sha256": sha(snapshot),
                "config_layout": resolved["layout"]}
    target = out / f"{a.run_id}.manifest.json"
    if target.exists() and json.loads(target.read_text()) != manifest: fail("manifest already exists with different inputs")
    if not target.exists(): target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, sort_keys=True))

def cmd_verify(a):
    m = json.loads(Path(a.manifest).read_text()); snap = Path(m["snapshot_path"])
    if not snap.is_file() or sha(snap) != m["snapshot_sha256"]: fail("snapshot hash mismatch")
    if snap.stem != m["snapshot_sha256"]: fail("snapshot filename/hash mismatch")
    source = Path(m["source_path"])
    if source.exists() and sha(source) != m["source_sha256"]: fail("source hash mismatch")
    print("lab_config_manifest=valid")

def cmd_package(a):
    root = Path(a.repo); text = "\n".join((root / n).read_text() for n in ("pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in") if (root / n).is_file())
    missing = [name for name in ("configs", "configs_exp", "configs_legacy") if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text)]
    result = {"packaged": not missing, "missing": missing}; print(json.dumps(result, sort_keys=True))
    if missing: raise SystemExit(ERROR)

def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("resolve"); x.add_argument("--repo", required=True); x.add_argument("--ref", required=True); x.add_argument("--layout", choices=("auto", "structured", "unstructured"), default="auto"); x.set_defaults(fn=cmd_resolve)
    x = s.add_parser("run-id"); x.add_argument("--slug", required=True); x.add_argument("--config-ref", required=True); x.add_argument("--config-sha256"); x.add_argument("--attempt", type=int); x.set_defaults(fn=lambda a: print(run_id(a.slug, a.config_ref, a.config_sha256, a.attempt)))
    x = s.add_parser("seal"); x.add_argument("--repo", required=True); x.add_argument("--config", required=True); x.add_argument("--slug"); x.add_argument("--run-id", required=True); x.add_argument("--out", required=True); x.add_argument("--config-ref"); x.set_defaults(fn=cmd_seal)
    x = s.add_parser("verify"); x.add_argument("--manifest", required=True); x.set_defaults(fn=cmd_verify)
    x = s.add_parser("package-data"); x.add_argument("--repo", required=True); x.set_defaults(fn=cmd_package)
    a = p.parse_args()
    try: a.fn(a)
    except (KeyError, json.JSONDecodeError, OSError, ValueError) as e: fail(str(e))
if __name__ == "__main__": main()
