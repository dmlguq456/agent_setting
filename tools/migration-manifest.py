#!/usr/bin/env python3
"""D-5: read-only, deterministic migration manifest for a physical artifact root.

`scan` inventories one physical root (existence, counts, bytes, optional
hashes, stale-path text references, lock/open-route/live-job/nested-root
signals, and a rollback sketch) into a JSONL file plus a Markdown summary.
`sweep` runs `scan` over every root named in a `roots.yaml` file. Both are
strictly read-only: nothing is written inside `--root`/`--dest`, only under
`--out` (I1). Timestamps and other non-reproducible metadata live only in
`run_meta.json`; the per-root `.jsonl` is byte-for-byte reproducible so a
second pass can prove determinism before any future apply step is allowed to
depend on this manifest (I6).

stdlib-only, by design: this tool runs against arbitrary, possibly stale or
oversized physical directories before any harness dependency can be trusted
to still be importable there.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = 1
OLD_PATH_PATTERNS = {
    "claude_reports": re.compile(r"\.claude_reports\b"),
    "absolute_home": re.compile(r"(?<![\w/])/home/[^\s\"'()]+"),
}
LOCK_NAMES = (".pipeline-lock", ".route-grounding", ".capability-grounding", ".spec-grounding", ".core-grounding")
DEFAULT_REF_SCAN_MAX_BYTES = 1024 * 1024
RECORD_RANK = {"dir": 0, "file": 1, "symlink": 2, "error": 3, "root_summary": 4}


class ManifestError(ValueError):
    pass


# --- I9: JSON-compatible strict-subset YAML reader (stdlib-only) -----------

def _strict_yaml_load(text: str):
    """Parse the narrow YAML subset this tool accepts as input: nested block
    mappings/sequences of plain scalars only. Anchors, tags, merge keys, and
    multiline scalars are rejected outright (I9) rather than silently
    misread."""
    for token in ("&", "*", "!", "<<", "|", ">"):
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            content = stripped.split(" #", 1)[0].rstrip()
            if token in ("|", ">") and (content.endswith(token) or content.endswith(token + "-") or content.endswith(token + "+")):
                raise ManifestError(f"unsupported YAML block scalar indicator: {token!r}")
            if token in ("&", "*", "!", "<<") and token in content:
                raise ManifestError(f"unsupported YAML construct: {token!r}")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]

    def indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def parse_scalar(raw: str):
        raw = raw.strip()
        if raw == "":
            return None
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        return raw

    def parse_block(start: int, indent: int):
        if start >= len(lines):
            return None, start
        first = lines[start]
        if indent_of(first) != indent:
            raise ManifestError(f"YAML indentation mismatch at: {first!r}")
        if first.strip().startswith("- "):
            items = []
            i = start
            while i < len(lines) and indent_of(lines[i]) == indent and lines[i].strip().startswith("- "):
                rest = lines[i].strip()[2:]
                if ":" in rest and not rest.startswith(('"', "'")):
                    # inline mapping start on the same line as the sequence dash
                    key, _, value = rest.partition(":")
                    sub_indent = indent + 2
                    entry = {key.strip(): parse_scalar(value)}
                    i += 1
                    while i < len(lines) and indent_of(lines[i]) >= sub_indent and not lines[i].strip().startswith("- "):
                        k2, _, v2 = lines[i].strip().partition(":")
                        entry[k2.strip()] = parse_scalar(v2)
                        i += 1
                    items.append(entry)
                else:
                    items.append(parse_scalar(rest))
                    i += 1
            return items, i
        mapping = {}
        i = start
        while i < len(lines) and indent_of(lines[i]) == indent:
            key, sep, value = lines[i].partition(":")
            if not sep:
                raise ManifestError(f"expected 'key: value' at: {lines[i]!r}")
            key = key.strip()
            value = value.strip()
            i += 1
            if value == "":
                if i < len(lines) and indent_of(lines[i]) > indent:
                    child, i = parse_block(i, indent_of(lines[i]))
                    mapping[key] = child
                else:
                    mapping[key] = None
            else:
                mapping[key] = parse_scalar(value)
        return mapping, i

    if not lines:
        return {}
    result, consumed = parse_block(0, indent_of(lines[0]))
    if consumed != len(lines):
        raise ManifestError("trailing unparsed YAML content")
    return result


# --- filesystem classification ----------------------------------------------

def _read_mountinfo():
    try:
        text = Path("/proc/self/mountinfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        parts = line.split(" - ")
        if len(parts) != 2:
            continue
        left = parts[0].split()
        right = parts[1].split()
        if len(left) < 5 or len(right) < 1:
            continue
        mount_point = left[4]
        fstype = right[0]
        rows.append((mount_point, fstype))
    return rows


def _filesystem_kind(path: Path, mountinfo=None) -> str:
    mountinfo = _read_mountinfo() if mountinfo is None else mountinfo
    if not mountinfo:
        return "unknown"
    resolved = str(path)
    best = None
    for mount_point, fstype in mountinfo:
        if resolved == mount_point or resolved.startswith(mount_point.rstrip("/") + "/") or mount_point == "/":
            if best is None or len(mount_point) > len(best[0]):
                best = (mount_point, fstype)
    if best is None:
        return "unknown"
    fstype = best[1]
    if fstype in ("nfs", "nfs4"):
        return "nfs"
    if fstype in ("ext4", "ext3", "ext2", "xfs", "btrfs", "overlay", "tmpfs", "vfat", "zfs"):
        return "local"
    return "unknown"


def _is_git(path: Path) -> bool:
    """F5: True when `path` sits inside a Git working tree, not only when it
    is itself a repository root. A physical migration root is very often a
    subdirectory (`.agent_reports`) of the checkout that owns it; the earlier
    single-level check (`path/.git` only) reported `git: false` for exactly
    that common shape."""
    current = path
    while True:
        try:
            if (current / ".git").exists():
                return True
        except OSError:
            pass
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _mirror_map_lookup(mirror_map, root_key: str):
    if not mirror_map:
        return None
    return mirror_map.get(root_key)


def _bisync_impact(mirror_map, mirror) -> str:
    """F5: real classification instead of a fixed instructional string.
    `mirror_map` absent/empty means no data was supplied at all -- distinct
    from a root that was checked and found not to be mirrored."""
    if not mirror_map:
        return "unknown"
    return "mirrored" if mirror is not None else "not-mirrored"


_JOBS_LOG_MIN_FIELDS = 4  # timestamp, status, install root, worktree path


def _resolve_agent_home(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    env = os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
    if env:
        return Path(env)
    script = Path(__file__).resolve().parents[1] / "utilities" / "agent-home.sh"
    if not script.is_file():
        return None
    try:
        result = subprocess.run(
            ["sh", str(script)], capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip())


def _live_job_signal(root: Path, agent_home: Path | None) -> str:
    """F5/I7: `live | none | unknown`, from bounded path-metadata parsing of
    `<agent-home>/.dispatch/jobs.log` only -- never job stdout, session
    transcripts, or credentials. Each line is
    `timestamp\tstatus\tinstall-root\tworktree-path\tslug\tmeta`; only
    `status` and `worktree-path` are read. `unknown` means the registry could
    not be located or read, never a data point about the root itself."""
    if agent_home is None:
        return "unknown"
    jobs_log = agent_home / ".dispatch" / "jobs.log"
    try:
        text = jobs_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    root_str = str(root)
    live = False
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) < _JOBS_LOG_MIN_FIELDS:
            continue
        status, worktree = fields[1], fields[3]
        if worktree == root_str or worktree.startswith(root_str + os.sep):
            if status == "open":
                live = True
                break
    return "live" if live else "none"


# --- scan ---------------------------------------------------------------

def _relative_posix(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    return PurePosixPath(*rel.parts).as_posix()


def _old_path_ref_counts(path: Path, max_bytes: int):
    try:
        size = os.stat(path, follow_symlinks=False).st_size
    except OSError:
        return None, True
    if size > max_bytes:
        return None, True
    try:
        data = path.read_bytes()
    except (OSError, UnicodeDecodeError):
        return None, True
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, False
    counts = {name: len(pattern.findall(text)) for name, pattern in OLD_PATH_PATTERNS.items()}
    return counts, False


def _walk_sorted(root: Path):
    """Deterministic top-down walk. Does not follow symlinks (I4); a symlinked
    directory is recorded as a symlink entry and never entered."""
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda e: os.fsencode(e.name))
        except OSError as exc:
            yield ("error", current, exc)
            continue
        subdirs = []
        for entry in entries:
            try:
                is_symlink = entry.is_symlink()
            except OSError as exc:
                yield ("error", Path(entry.path), exc)
                continue
            path = Path(entry.path)
            if is_symlink:
                yield ("symlink", path, None)
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError as exc:
                yield ("error", path, exc)
                continue
            if is_dir:
                yield ("dir", path, None)
                subdirs.append(path)
            else:
                yield ("file", path, None)
        # reverse push so pop() visits subdirs in sorted order (deterministic, I2)
        for sub in reversed(subdirs):
            stack.append(sub)


def _safe_iterdir(path: Path):
    try:
        return list(path.iterdir())
    except OSError:
        return []


# F5: `open_route_present` must recognize D-2's canonical location plus all
# four legacy ones, using one shared classifier -- the previous version only
# checked `.routes`/`_routes` directory names and root-level `*-route.json`
# files, silently missing `routes/` and the canonical `.runtime/routes/`.
_ROUTE_CONTAINER_RELPATHS = {("routes",), ("_routes",), (".routes",), (".runtime", "routes")}


def _dir_has_open_route(path: Path) -> bool:
    for child in _safe_iterdir(path):
        if not (child.is_file() and child.name.endswith(".json")
                and not child.name.endswith(".outcome.json")):
            continue
        if not (child.with_name(child.stem + ".outcome.json")).exists():
            return True
    return False


def scan_root(root: Path, *, dest: Path | None, do_hash: bool, ref_scan_max_bytes: int,
              mirror_map: dict, root_key: str, agent_home: Path | None = None) -> tuple[list[dict], dict]:
    root = root.resolve()
    records: list[dict] = []
    file_count = dir_count = symlink_count = 0
    total_bytes = 0
    ref_scan_skipped = 0
    complete = True
    lock_present = False
    open_route_present = False
    nested_artifact_root = False

    if not root.is_dir():
        summary = _root_summary(
            root, dest, mirror_map, root_key, file_count=0, dir_count=0, symlink_count=0,
            total_bytes=0, complete=False, lock_present=False, open_route_present=False,
            nested_artifact_root=False, ref_scan_skipped=0, agent_home=agent_home,
        )
        return records, summary

    for kind, path, exc in _walk_sorted(root):
        rel = _relative_posix(root, path)
        if kind == "error":
            complete = False
            errno_name = errno.errorcode.get(getattr(exc, "errno", None), "EUNKNOWN")
            records.append({"record_type": "error", "path": rel, "errno": errno_name})
            continue
        if kind == "dir":
            dir_count += 1
            records.append({"record_type": "dir", "path": rel})
            if path.name in LOCK_NAMES:
                lock_present = True
            try:
                # F5: nested-root detection must recognize legacy
                # `.claude_reports` alongside `.agent_reports`.
                if rel and rel != "." and ((path / ".agent_reports").is_dir()
                                            or (path / ".claude_reports").is_dir()):
                    nested_artifact_root = True
            except OSError:
                pass
            rel_parts = tuple(PurePosixPath(rel).parts) if rel != "." else ()
            if rel_parts in _ROUTE_CONTAINER_RELPATHS:
                open_route_present = open_route_present or _dir_has_open_route(path)
            continue
        if kind == "symlink":
            symlink_count += 1
            records.append({"record_type": "symlink", "path": rel})
            continue
        # file
        file_count += 1
        if path.name in LOCK_NAMES:
            lock_present = True
        try:
            size = os.stat(path, follow_symlinks=False).st_size
        except OSError as e:
            complete = False
            errno_name = errno.errorcode.get(getattr(e, "errno", None), "EUNKNOWN")
            records.append({"record_type": "error", "path": rel, "errno": errno_name})
            continue
        total_bytes += size
        record = {"record_type": "file", "path": rel, "size": size}
        if path.name.endswith("-route.json") and not path.name.endswith(".outcome.json"):
            sidecar = path.with_name(path.stem + ".outcome.json")
            if not sidecar.exists():
                open_route_present = True
        refs, skipped = _old_path_ref_counts(path, ref_scan_max_bytes)
        if skipped:
            ref_scan_skipped += 1
            record["ref_scan_skipped"] = True
        elif refs is not None:
            record["old_path_refs"] = refs
        if do_hash:
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                record["sha256"] = digest
            except OSError:
                # F5: a hash read failure is a real incompleteness, not a
                # silent gap -- the caller asked for `--hash` and did not get
                # one, so the manifest must say so and refuse to claim it is
                # a complete inventory.
                record["hash_error"] = True
                complete = False
        records.append(record)

    records.sort(key=lambda r: (RECORD_RANK[r["record_type"]], os.fsencode(r["path"])))
    summary = _root_summary(
        root, dest, mirror_map, root_key, file_count=file_count, dir_count=dir_count,
        symlink_count=symlink_count, total_bytes=total_bytes, complete=complete,
        lock_present=lock_present, open_route_present=open_route_present,
        nested_artifact_root=nested_artifact_root, ref_scan_skipped=ref_scan_skipped,
        agent_home=agent_home,
    )
    return records, summary


# F6: a `dest` that already exists as a plain file (or an unreadable
# directory) used to crash `any(dest.iterdir())` with `NotADirectoryError`/
# `PermissionError`. This resolves to a typed collision state instead of
# either exception or a bare boolean.
def _destination_conflict_state(dest: Path | None) -> str:
    if dest is None:
        return "none"
    try:
        if not dest.exists():
            return "none"
        if dest.is_symlink():
            return "symlink"
        if dest.is_file():
            return "file"
        if not dest.is_dir():
            return "other"
        return "populated" if any(dest.iterdir()) else "none"
    except OSError:
        return "unreadable"


def _root_summary(root: Path, dest: Path | None, mirror_map, root_key, *, file_count, dir_count,
                   symlink_count, total_bytes, complete, lock_present, open_route_present,
                   nested_artifact_root, ref_scan_skipped, agent_home: Path | None = None) -> dict:
    dest_resolved = str(dest.resolve()) if dest else None
    dest_exists = dest.exists() if dest else False
    mirror = _mirror_map_lookup(mirror_map, root_key)
    conflict_state = _destination_conflict_state(dest)
    return {
        "record_type": "root_summary",
        "path": ".",
        "schema_version": SCHEMA_VERSION,
        "source": str(root),
        "source_exists": root.is_dir(),
        "destination": dest_resolved,
        "destination_exists": dest_exists,
        "destination_conflict": conflict_state != "none",
        "destination_conflict_state": conflict_state,
        "file_count": file_count,
        "dir_count": dir_count,
        "symlink_count": symlink_count,
        "total_bytes": total_bytes,
        "git": _is_git(root),
        "filesystem": _filesystem_kind(root),
        "onedrive_mirror": mirror is not None,
        "onedrive_mirror_target": mirror,
        "lock_present": lock_present,
        "open_route_present": open_route_present,
        "live_job": _live_job_signal(root, agent_home),
        "nested_artifact_root": nested_artifact_root,
        "ref_scan_skipped_count": ref_scan_skipped,
        "rollback_command": f"# no move performed; a future apply step would revert with: mv {dest_resolved or '<dest>'} {root}",
        "bisync_impact": _bisync_impact(mirror_map, mirror),
        "complete": complete,
    }


# --- JSON serialization (I3) ------------------------------------------------

def _dump_jsonl(records: list[dict]) -> str:
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for r in records]
    return "\n".join(lines) + ("\n" if lines else "")


# --- I1 guard ----------------------------------------------------------

def _reject_out_inside_investigated(out_dir: Path, *investigated: Path | None):
    out_resolved = out_dir.resolve(strict=False)
    for candidate in investigated:
        if candidate is None:
            continue
        try:
            candidate_resolved = candidate.resolve(strict=False)
        except OSError:
            continue
        if out_resolved == candidate_resolved or str(out_resolved).startswith(str(candidate_resolved) + os.sep):
            raise ManifestError(
                f"--out ({out_resolved}) must not be inside an investigated root ({candidate_resolved}) -- I1"
            )


# --- two-pass determinism (I6) ---------------------------------------

def _sorted_all(records: list[dict], summary: dict) -> list[dict]:
    all_records = records + [summary]
    all_records.sort(key=lambda r: (RECORD_RANK[r["record_type"]], os.fsencode(r["path"])))
    return all_records


def _scan_twice(root: Path, *, dest, do_hash, ref_scan_max_bytes, mirror_map, root_key, agent_home=None):
    records_a, summary_a = scan_root(root, dest=dest, do_hash=do_hash, ref_scan_max_bytes=ref_scan_max_bytes,
                                      mirror_map=mirror_map, root_key=root_key, agent_home=agent_home)
    records_b, summary_b = scan_root(root, dest=dest, do_hash=do_hash, ref_scan_max_bytes=ref_scan_max_bytes,
                                      mirror_map=mirror_map, root_key=root_key, agent_home=agent_home)
    # F6: comparing only `records_a`/`records_b` let a second-pass mutation of
    # `root_summary` alone (the thing that actually lands in the JSONL output)
    # slip through undetected -- both passes' *complete* output, records plus
    # summary, must match byte-for-byte.
    bytes_a = _dump_jsonl(_sorted_all(records_a, summary_a))
    bytes_b = _dump_jsonl(_sorted_all(records_b, summary_b))
    determinism_ok = bytes_a == bytes_b and summary_a["complete"] and summary_b["complete"]
    return records_a, summary_a, determinism_ok


def _write_root_output(out_dir: Path, key: str, records: list[dict], summary: dict, determinism_ok: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    body = _dump_jsonl(_sorted_all(records, summary))
    path = out_dir / f"{key}.jsonl"
    path.write_text(body, encoding="utf-8")
    return path


ACTION_CODES = {"K": "keep", "N": "no-op/absorb", "L": "low-risk pilot", "S": "split/decompose", "R": "remove/retire"}


def _write_summary_md(out_dir: Path, entries: list[dict]) -> Path:
    lines = ["# Migration manifest summary", "", "| key | source | exists | files | dirs | bytes | git | fs | complete | determinism |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for entry in entries:
        summary = entry["summary"]
        lines.append(
            f"| {entry['key']} | {summary['source']} | {summary['source_exists']} | "
            f"{summary['file_count']} | {summary['dir_count']} | {summary['total_bytes']} | "
            f"{summary['git']} | {summary['filesystem']} | {summary['complete']} | "
            f"{'verified' if entry['determinism_ok'] else 'unverified'} |"
        )
    path = out_dir / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_run_meta(out_dir: Path, *, command: str, entries: list[dict]) -> Path:
    import time
    payload = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "generated_at_unix": time.time(),
        "roots": [{"key": e["key"], "determinism": "verified" if e["determinism_ok"] else "unverified"} for e in entries],
    }
    path = out_dir / "run_meta.json"
    path.write_text(json.dumps(payload, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# --- CLI -----------------------------------------------------------------

def _load_mirror_map(path: str | None) -> dict:
    if not path:
        return {}
    text = Path(path).read_text(encoding="utf-8")
    data = _strict_yaml_load(text)
    return data or {}


# F6: sweep keys become filenames (`<key>.jsonl`) under `--out` -- an
# unvalidated key let `key: ../escaped` write a sibling file outside `--out`
# entirely. Path-component-only, no traversal.
_SWEEP_KEY_RE = re.compile(r'^[A-Za-z0-9._-]+$')


def cmd_scan(args) -> int:
    root = Path(args.root)
    dest = Path(args.dest) if args.dest else None
    out_dir = Path(args.out)
    _reject_out_inside_investigated(out_dir, root, dest)
    mirror_map = _load_mirror_map(args.mirror_map)
    agent_home = _resolve_agent_home(args.agent_home)
    key = root.resolve().name or "root"
    records, summary, determinism_ok = _scan_twice(
        root, dest=dest, do_hash=args.hash, ref_scan_max_bytes=args.ref_scan_max_bytes,
        mirror_map=mirror_map, root_key=key, agent_home=agent_home,
    )
    _write_root_output(out_dir, key, records, summary, determinism_ok)
    entries = [{"key": key, "summary": summary, "determinism_ok": determinism_ok}]
    _write_summary_md(out_dir, entries)
    _write_run_meta(out_dir, command="scan", entries=entries)
    if not determinism_ok:
        print(f"migration-manifest: determinism unverified for {key}", file=sys.stderr)
        return 1
    print(f"migration-manifest: scanned {key} ({summary['file_count']} files, {summary['total_bytes']} bytes)")
    return 0


def cmd_sweep(args) -> int:
    roots_data = _strict_yaml_load(Path(args.roots).read_text(encoding="utf-8"))
    entries_spec = roots_data.get("roots") if isinstance(roots_data, dict) else roots_data
    if not isinstance(entries_spec, list) or not entries_spec:
        raise ManifestError("roots.yaml must declare a non-empty 'roots' list")
    out_dir = Path(args.out)
    mirror_map = _load_mirror_map(args.mirror_map) if getattr(args, "mirror_map", None) else {}
    agent_home = _resolve_agent_home(args.agent_home)
    investigated = []
    seen_keys = set()
    for row in entries_spec:
        if not isinstance(row, dict) or "key" not in row or "path" not in row:
            raise ManifestError(f"invalid roots.yaml entry: {row!r}")
        key = row["key"]
        if not isinstance(key, str) or not _SWEEP_KEY_RE.match(key):
            raise ManifestError(f"roots.yaml key must be a bare path component: {key!r} -- I1")
        if key in seen_keys:
            raise ManifestError(f"duplicate roots.yaml key: {key!r}")
        seen_keys.add(key)
        investigated.append(Path(row["path"]))
        if row.get("dest"):
            investigated.append(Path(row["dest"]))
    _reject_out_inside_investigated(out_dir, *investigated)

    entries = []
    any_incomplete = False
    for row in entries_spec:
        key = row["key"]
        root = Path(row["path"])
        dest = Path(row["dest"]) if row.get("dest") else None
        records, summary, determinism_ok = _scan_twice(
            root, dest=dest, do_hash=args.hash, ref_scan_max_bytes=args.ref_scan_max_bytes,
            mirror_map=mirror_map, root_key=key, agent_home=agent_home,
        )
        _write_root_output(out_dir, key, records, summary, determinism_ok)
        entries.append({"key": key, "summary": summary, "determinism_ok": determinism_ok, "expected_action": row.get("expected_action")})
        any_incomplete = any_incomplete or not determinism_ok
    _write_summary_md(out_dir, entries)
    _write_run_meta(out_dir, command="sweep", entries=entries)
    print(f"migration-manifest: swept {len(entries)} roots into {out_dir}")
    return 1 if any_incomplete else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--root", required=True)
    scan_p.add_argument("--dest")
    scan_p.add_argument("--out", required=True)
    scan_p.add_argument("--hash", action="store_true")
    scan_p.add_argument("--ref-scan-max-bytes", type=int, default=DEFAULT_REF_SCAN_MAX_BYTES)
    scan_p.add_argument("--mirror-map")
    scan_p.add_argument("--agent-home", help="defaults to $AGENT_HOME, then utilities/agent-home.sh")

    sweep_p = sub.add_parser("sweep")
    sweep_p.add_argument("--roots", required=True)
    sweep_p.add_argument("--out", required=True)
    sweep_p.add_argument("--hash", action="store_true")
    sweep_p.add_argument("--ref-scan-max-bytes", type=int, default=DEFAULT_REF_SCAN_MAX_BYTES)
    sweep_p.add_argument("--mirror-map")
    sweep_p.add_argument("--agent-home", help="defaults to $AGENT_HOME, then utilities/agent-home.sh")

    args = parser.parse_args()
    try:
        if args.command == "scan":
            return cmd_scan(args)
        return cmd_sweep(args)
    except ManifestError as exc:
        print(f"migration-manifest: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
