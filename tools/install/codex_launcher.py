"""Install and restore the transparent interactive Codex launcher."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile


SCHEMA = 1
STATE_NAME = "codex-launcher.json"


class CodexLauncherError(RuntimeError):
    """The launcher cannot be installed or restored without clobbering data."""


class CodexUnavailableError(CodexLauncherError):
    """The real Codex CLI is not installed yet."""


def _home() -> Path:
    raw = os.environ.get("HOME")
    return Path(raw).expanduser() if raw else Path.home()


def default_codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME")
    return Path(raw).expanduser() if raw else _home() / ".codex"


def default_bin_dir() -> Path:
    raw = os.environ.get("HARNESS_BIN_DIR")
    return Path(raw).expanduser() if raw else _home() / ".local" / "bin"


def state_path(codex_home: Path) -> Path:
    return codex_home / ".harness" / STATE_NAME


def wrapper_path(bin_dir: Path) -> Path:
    return bin_dir / "codex"


def wrapper_bytes() -> bytes:
    return b"""#!/bin/sh
set -eu
codex_runtime_home=${CODEX_HOME:-$HOME/.codex}
launcher=$codex_runtime_home/agent-harness/utilities/codex-launcher.py
if [ ! -f "$launcher" ]; then
  launcher=$HOME/.codex/agent-harness/utilities/codex-launcher.py
fi
if [ ! -f "$launcher" ]; then
  echo "agent-harness: Codex launcher projection is missing from runtime and default homes" >&2
  exit 69
fi
exec python3 "$launcher" "$@"
"""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_bytes(path: Path, payload: bytes, mode: int) -> None:
    if path.is_symlink():
        raise CodexLauncherError(f"refusing atomic write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_json(path: Path, value: dict) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _atomic_bytes(path, payload, 0o600)


def _load_state(path: Path) -> dict | None:
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32_768:
        raise CodexLauncherError(f"unsafe Codex launcher state: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CodexLauncherError(f"invalid Codex launcher state: {path}") from exc
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise CodexLauncherError(f"unsupported Codex launcher state: {path}")
    return value


def _validate_home(codex_home: Path, *, create: bool) -> int:
    if not codex_home.is_absolute() or codex_home.is_symlink():
        raise CodexLauncherError(f"CODEX_HOME must be an absolute real directory: {codex_home}")
    if not codex_home.exists():
        if not create:
            return 0o700
        codex_home.mkdir(parents=True, exist_ok=True)
    info = codex_home.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise CodexLauncherError(f"CODEX_HOME is not owned by the current user: {codex_home}")
    return stat.S_IMODE(info.st_mode)


def _validate_state_directory(codex_home: Path, *, create: bool) -> None:
    directory = codex_home / ".harness"
    if directory.is_symlink():
        raise CodexLauncherError(f"Codex harness state directory must not be a symlink: {directory}")
    if not directory.exists():
        if not create:
            return
        directory.mkdir(mode=0o700)
    info = directory.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise CodexLauncherError(f"Codex harness state is not owner-controlled: {directory}")


def _absolute_link_target(path: Path) -> Path:
    raw = Path(os.readlink(path))
    return raw if raw.is_absolute() else (path.parent / raw).absolute()


def is_harness_wrapper(command: Path) -> bool:
    """Detect any install's launcher ingress, not just this target path.

    A fresh HOME can inherit a PATH whose `codex` is another installation's
    wrapper; binding to it makes the launcher exec itself forever.
    """
    try:
        if command.is_symlink() or not command.is_file() or command.stat().st_size > 4096:
            return False
        payload = command.read_bytes()
    except OSError:
        return False
    return b"agent-harness" in payload and b"codex-launcher.py" in payload


def _validate_real_command(command: Path, target: Path) -> Path:
    command = command.expanduser().absolute()
    if command == target.absolute():
        raise CodexLauncherError("real Codex command resolves to the launcher path")
    if not command.exists() or command.is_dir() or not os.access(command, os.X_OK):
        raise CodexLauncherError(f"real Codex command is unavailable: {command}")
    if is_harness_wrapper(command):
        raise CodexLauncherError(
            f"real Codex command resolves to an agent-harness launcher wrapper: {command}"
        )
    return command


def _discover_real_command_after_launcher(target: Path) -> Path | None:
    """Find a Codex executable later on PATH, excluding any harness ingress."""

    for raw_directory in os.environ.get("PATH", "").split(os.pathsep):
        if not raw_directory:
            continue
        candidate = (Path(raw_directory).expanduser() / "codex").absolute()
        if candidate == target.absolute():
            continue
        if not candidate.exists() or candidate.is_dir() or not os.access(candidate, os.X_OK):
            continue
        if is_harness_wrapper(candidate):
            continue
        return candidate
    return None


def _discover_initial_binding(target: Path, real_command: str | None) -> tuple[Path, dict]:
    discovered = Path(real_command).expanduser() if real_command else None
    if discovered is None:
        resolved = shutil.which("codex")
        if not resolved:
            raise CodexUnavailableError("Codex command was not found on PATH")
        discovered = Path(resolved)
        if is_harness_wrapper(discovered.absolute()):
            fallback = _discover_real_command_after_launcher(target)
            if fallback is None:
                raise CodexUnavailableError(
                    "PATH resolves codex to another harness launcher wrapper and no "
                    "real Codex command was found behind it"
                )
            discovered = fallback

    if target.exists() or target.is_symlink():
        if not target.is_symlink():
            # A release interrupted after writing the deterministic ingress but
            # before persisting its state must be recoverable.  Adopt only our
            # byte-exact wrapper and preserve a usable Codex binding for
            # uninstall; every other regular file remains a hard collision.
            if not _wrapper_matches(target, _digest(wrapper_bytes())):
                raise CodexLauncherError(
                    f"refusing to replace a real file at the launcher path: {target}"
                )
            if discovered.absolute() == target.absolute():
                discovered = _discover_real_command_after_launcher(target)
            if discovered is None:
                raise CodexUnavailableError("real Codex command was not found after the launcher")
            real = discovered
            previous = {"kind": "symlink", "target": str(discovered.absolute())}
            return _validate_real_command(real, target), previous
        if discovered.absolute() != target.absolute():
            raise CodexLauncherError(
                f"foreign Codex symlink already occupies the launcher path: {target}"
            )
        raw_target = os.readlink(target)
        real = _absolute_link_target(target)
        previous = {"kind": "symlink", "target": raw_target}
    else:
        real = discovered
        previous = {"kind": "missing"}
    return _validate_real_command(real, target), previous


def _wrapper_matches(target: Path, expected_digest: str) -> bool:
    if target.is_symlink() or not target.is_file():
        return False
    try:
        return _digest(target.read_bytes()) == expected_digest
    except OSError:
        return False


def _current_binding(target: Path) -> dict:
    if not target.exists() and not target.is_symlink():
        return {"kind": "missing"}
    if target.is_symlink():
        return {"kind": "symlink", "target": os.readlink(target)}
    if target.is_file():
        return {
            "kind": "file",
            "payload": target.read_bytes(),
            "mode": stat.S_IMODE(target.stat().st_mode),
        }
    raise CodexLauncherError(f"Codex launcher drift would clobber a foreign path: {target}")


def _restore_wrapper(target: Path, previous: dict) -> None:
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            raise CodexLauncherError(f"launcher path became a directory: {target}")
        target.unlink()
    kind = previous.get("kind")
    if kind == "missing":
        return
    if kind == "file" and isinstance(previous.get("payload"), bytes):
        _atomic_bytes(target, previous["payload"], int(previous.get("mode", 0o755)))
        return
    if kind != "symlink" or not isinstance(previous.get("target"), str):
        raise CodexLauncherError("launcher state has an invalid previous binding")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".restore-tmp")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(previous["target"])
    os.replace(temporary, target)


def install(
    *,
    codex_home: Path | None = None,
    bin_dir: Path | None = None,
    real_command: str | None = None,
    dry_run: bool = False,
) -> dict:
    codex_home = (codex_home or default_codex_home()).expanduser().absolute()
    bin_dir = (bin_dir or default_bin_dir()).expanduser().absolute()
    target = wrapper_path(bin_dir)
    state_file = state_path(codex_home)
    payload = wrapper_bytes()
    payload_digest = _digest(payload)
    current_mode = _validate_home(codex_home, create=not dry_run)
    _validate_state_directory(codex_home, create=not dry_run)
    existing = _load_state(state_file)
    previous_mode = current_mode
    rollback_wrapper: dict

    if existing is not None:
        if existing.get("wrapper_path") != str(target):
            raise CodexLauncherError("installed Codex launcher uses a different bin directory")
        recorded_real = str(existing.get("real_command", ""))
        try:
            real = _validate_real_command(
                Path(recorded_real), target
            )
        except CodexLauncherError:
            replacement = (
                Path(real_command).expanduser()
                if real_command
                else _discover_real_command_after_launcher(target)
            )
            if replacement is None:
                raise CodexUnavailableError(
                    "recorded Codex command disappeared and no replacement was found on PATH"
                )
            real = _validate_real_command(replacement, target)
        previous = existing.get("previous_wrapper")
        if not isinstance(previous, dict):
            raise CodexLauncherError("installed Codex launcher lacks restoration metadata")
        recorded_mode = existing.get("previous_codex_home_mode")
        if isinstance(recorded_mode, int):
            previous_mode = recorded_mode
        if _wrapper_matches(target, payload_digest) and str(real) == recorded_real:
            return {
                "action": "managed-launcher",
                "status": "unchanged",
                "target": str(target),
                "real_command": str(real),
            }
        recorded_digest = str(existing.get("wrapper_sha256", ""))
        if target.is_file() and not target.is_symlink() and not _wrapper_matches(
            target, recorded_digest
        ):
            raise CodexLauncherError(f"Codex launcher drift would clobber a foreign file: {target}")
        rollback_wrapper = _current_binding(target)
        if rollback_wrapper.get("kind") == "symlink" and not (
            previous.get("kind") == "symlink"
            and rollback_wrapper.get("target") == previous.get("target")
        ):
            raise CodexLauncherError(f"Codex launcher drift would clobber a foreign file: {target}")
    else:
        real, previous = _discover_initial_binding(target, real_command)
        rollback_wrapper = previous

    if dry_run:
        return {
            "action": "managed-launcher",
            "status": "planned",
            "target": str(target),
            "real_command": str(real),
        }

    prepared = {
        "schema": SCHEMA,
        "phase": "prepared",
        "wrapper_path": str(target),
        "wrapper_sha256": payload_digest,
        "real_command": str(real),
        "previous_wrapper": previous,
        "previous_codex_home_mode": previous_mode,
    }
    state_existed = existing is not None
    _atomic_json(state_file, prepared)
    try:
        os.chmod(codex_home, previous_mode & ~0o077)
        if target.exists() or target.is_symlink():
            target.unlink()
        _atomic_bytes(target, payload, 0o755)
        prepared["phase"] = "installed"
        _atomic_json(state_file, prepared)
    except Exception:
        _restore_wrapper(target, rollback_wrapper)
        os.chmod(codex_home, current_mode if state_existed else previous_mode)
        if state_existed:
            _atomic_json(state_file, existing)
        else:
            state_file.unlink(missing_ok=True)
        raise
    return {
        "action": "managed-launcher",
        "status": "created" if existing is None else "repaired",
        "target": str(target),
        "real_command": str(real),
    }


def uninstall(
    *,
    codex_home: Path | None = None,
    bin_dir: Path | None = None,
    dry_run: bool = False,
) -> dict:
    codex_home = (codex_home or default_codex_home()).expanduser().absolute()
    _validate_home(codex_home, create=False)
    _validate_state_directory(codex_home, create=False)
    state_file = state_path(codex_home)
    state = _load_state(state_file)
    if state is None:
        return {"action": "managed-launcher", "status": "not-installed"}
    target = Path(str(state.get("wrapper_path", "")))
    expected = str(state.get("wrapper_sha256", ""))
    requested_target = wrapper_path((bin_dir or default_bin_dir()).expanduser().absolute())
    if target != requested_target:
        raise CodexLauncherError("installed Codex launcher uses a different bin directory")
    if target.exists() and not _wrapper_matches(target, expected):
        raise CodexLauncherError(f"refusing to overwrite modified Codex launcher: {target}")
    if dry_run:
        return {"action": "managed-launcher", "status": "planned-restore", "target": str(target)}
    previous = state.get("previous_wrapper")
    if not isinstance(previous, dict):
        raise CodexLauncherError("installed Codex launcher lacks restoration metadata")
    _restore_wrapper(target, previous)
    previous_mode = state.get("previous_codex_home_mode")
    if isinstance(previous_mode, int) and codex_home.is_dir() and not codex_home.is_symlink():
        os.chmod(codex_home, previous_mode)
    state_file.unlink(missing_ok=True)
    return {"action": "managed-launcher", "status": "restored", "target": str(target)}


def status(*, codex_home: Path | None = None, bin_dir: Path | None = None) -> dict:
    codex_home = (codex_home or default_codex_home()).expanduser().absolute()
    if not codex_home.exists():
        return {"installed": False, "healthy": False, "detail": "not-installed"}
    _validate_home(codex_home, create=False)
    _validate_state_directory(codex_home, create=False)
    state = _load_state(state_path(codex_home))
    if state is None:
        return {"installed": False, "healthy": False, "detail": "not-installed"}
    target = wrapper_path((bin_dir or default_bin_dir()).expanduser().absolute())
    real = Path(str(state.get("real_command", "")))
    real_healthy = (
        real.is_absolute()
        and real != target
        and real.exists()
        and not real.is_dir()
        and os.access(real, os.X_OK)
    )
    healthy = (
        state.get("phase") == "installed"
        and state.get("wrapper_path") == str(target)
        and _wrapper_matches(target, str(state.get("wrapper_sha256", "")))
        and real_healthy
    )
    return {
        "installed": True,
        "healthy": healthy,
        "detail": "ok" if healthy else ("real-command-unavailable" if not real_healthy else "drift"),
        "target": str(target),
        "real_command": state.get("real_command"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("install", "uninstall", "status"))
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--bin-dir", type=Path)
    parser.add_argument("--real-command")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.operation == "install":
            result = install(
                codex_home=args.codex_home,
                bin_dir=args.bin_dir,
                real_command=args.real_command,
                dry_run=args.dry_run,
            )
        elif args.operation == "uninstall":
            result = uninstall(
                codex_home=args.codex_home,
                bin_dir=args.bin_dir,
                dry_run=args.dry_run,
            )
        else:
            result = status(codex_home=args.codex_home, bin_dir=args.bin_dir)
    except CodexLauncherError as exc:
        if args.json:
            print(json.dumps({"status": "blocked", "error": str(exc)}))
        else:
            print(f"codex-launcher: blocked: {exc}", file=os.sys.stderr)
        return 3
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
