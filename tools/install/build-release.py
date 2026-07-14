#!/usr/bin/env python3
"""Build deterministic GitHub Release assets from one committed Git ref."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path


ARCHIVE_NAME = "agent-harness.tar.gz"
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _run_git(root: Path, *args: str, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def build(root: Path, version: str, output: Path, ref: str) -> tuple[Path, Path]:
    if not VERSION_RE.fullmatch(version):
        raise SystemExit(f"invalid release version: {version!r}")
    _run_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    epoch = int(
        _run_git(root, "show", "-s", "--format=%ct", ref).stdout.decode().strip()
    )
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / ARCHIVE_NAME
    checksum_path = output / (ARCHIVE_NAME + ".sha256")

    with tempfile.TemporaryDirectory(prefix="agent-harness-release-") as temp:
        tar_path = Path(temp) / "source.tar"
        with tar_path.open("wb") as handle:
            _run_git(
                root,
                "archive",
                "--format=tar",
                "--prefix=agent-harness/",
                ref,
                "--",
                ".",
                ":(exclude).agent_reports",
                ":(exclude).claude_reports",
                stdout=handle,
            )
        marker = tarfile.TarInfo("agent-harness/RELEASE_VERSION")
        marker.mode = 0o644
        marker.uid = marker.gid = 0
        marker.uname = marker.gname = "root"
        marker.mtime = epoch
        payload = (version + "\n").encode("utf-8")
        marker.size = len(payload)
        with tarfile.open(tar_path, "a") as bundle:
            bundle.addfile(marker, io.BytesIO(payload))

        with tar_path.open("rb") as source, archive_path.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9
            ) as compressed:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    compressed.write(chunk)

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {ARCHIVE_NAME}\n", encoding="ascii")
    os.chmod(archive_path, 0o644)
    os.chmod(checksum_path, 0o644)
    return archive_path, checksum_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", default="dist")
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    archive, checksum = build(
        root, args.version, Path(args.output).resolve(), args.ref
    )
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
