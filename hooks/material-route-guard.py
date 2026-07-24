#!/usr/bin/env python3
"""Require a current-session autopilot-code route for material source work.

The default mode consumes Claude hook JSON.  A small CLI is also exposed for
deterministic conformance tests and adapters that can supply the same fields:

  material-route-guard.py bind --route <route.json> --cwd <dir> --session <id>
  material-route-guard.py check --tool <Edit|Write|Bash> [--file <path>] \
      [--command <shell>] --cwd <dir> --session <id>
  material-route-guard.py clear --session <id>

Only a verified capability-route record is authority.  Skill invocation and
the capability-grounding/spec marker families are intentionally not read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR_NAME = ".route-grounding"
MARKER_SCHEMA = 1
MAX_MARKERS = 512
MAX_MARKER_AGE_SECONDS = 14 * 24 * 60 * 60
INTENSITIES = {
    "direct",
    "quick",
    "standard",
    "strong",
    "thorough",
    "adversarial",
}
EDIT_TOOLS = {
    "Edit",
    "Write",
    "MultiEdit",
    "NotebookEdit",
    "edit",
    "write",
    "multi_edit",
    "multiedit",
    "notebook_edit",
}
SOURCE_SUFFIXES = {
    ".asm", ".bash", ".c", ".cc", ".clj", ".cljs", ".cpp", ".cs",
    ".css", ".cu", ".cuh", ".cxx", ".dart", ".elm", ".erl", ".ex",
    ".exs", ".fish", ".fs", ".fsx", ".go", ".groovy", ".h", ".hh",
    ".hpp", ".hrl", ".htm", ".html", ".hxx", ".ipynb", ".java",
    ".jl", ".js", ".jsx", ".kt", ".kts", ".less", ".lua", ".m",
    ".mm", ".mjs", ".php", ".pl", ".pm", ".proto", ".ps1", ".py",
    ".pyi", ".r", ".rb", ".rs", ".sass", ".scala", ".scss", ".sh",
    ".sol", ".sql", ".svelte", ".swift", ".tcl", ".ts", ".tsx",
    ".vue", ".zig", ".zsh",
}
EXCLUDED_PARTS = {
    ".agent_reports",
    ".claude_reports",
    ".config",
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".route-grounding",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "artifacts",
    "build",
    "config",
    "configs",
    "coverage",
    "dist",
    "docs",
    "documentation",
    "node_modules",
    "scratch",
    "tmp",
    "vendor",
}
DENIAL = (
    "material 작업인데 route 미선언 (silent no-route). hotfix라도 "
    "autopilot-code(최소 --intensity direct)로 진입하라."
)


class RouteError(RuntimeError):
    """The presented route proof is missing or invalid."""


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )


def resolve_agent_home(explicit: str | None = None) -> Path:
    for candidate in (explicit, os.environ.get("AGENT_HOME")):
        if candidate and (Path(candidate) / "core" / "CORE.md").is_file():
            return Path(candidate).resolve()
    resolver = ROOT / "utilities" / "agent-home.sh"
    try:
        result = _run([str(resolver)])
        candidate = Path(result.stdout.strip())
        if result.returncode == 0 and (candidate / "core" / "CORE.md").is_file():
            return candidate.resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return ROOT


def session_key(session_id: str) -> str:
    if not session_id or len(session_id.encode("utf-8", "replace")) > 1024:
        raise RouteError("session-id-missing")
    return hashlib.sha256(b"material-route-session-v1\0" + session_id.encode()).hexdigest()


def state_dir(agent_home: Path) -> Path:
    return agent_home / STATE_DIR_NAME


def marker_path(agent_home: Path, session_id: str) -> Path:
    return state_dir(agent_home) / f"{session_key(session_id)}.json"


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    data = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def gc_markers(agent_home: Path, keep: Path | None = None) -> None:
    directory = state_dir(agent_home)
    try:
        entries = [
            item for item in directory.iterdir()
            if item.name.endswith(".json") and not item.is_symlink()
        ]
    except OSError:
        return
    now = time.time()
    ranked: list[tuple[float, Path]] = []
    for item in entries:
        try:
            info = item.stat()
        except OSError:
            continue
        if not stat.S_ISREG(info.st_mode):
            continue
        ranked.append((info.st_mtime, item))
    ranked.sort(reverse=True)
    for index, (mtime, item) in enumerate(ranked):
        if item == keep:
            continue
        if now - mtime > MAX_MARKER_AGE_SECONDS or index >= MAX_MARKERS:
            try:
                item.unlink()
            except OSError:
                pass


def _nearest_existing(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def git_root(path: Path) -> Path | None:
    nearest = _nearest_existing(path)
    probe = nearest if nearest.is_dir() else nearest.parent
    result = _run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"])
    if result.returncode or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def project_root(cwd: Path, target: Path | None = None) -> Path:
    return git_root(target or cwd) or git_root(cwd) or cwd.resolve()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_material_source(path: Path, repo: Path | None = None) -> bool:
    path = path.resolve(strict=False)
    repo = repo or git_root(path)
    # Scratch and non-project paths are deliberately outside this gate.
    if repo is None or not _within(path, repo):
        return False
    relative = path.relative_to(repo)
    if any(part.lower() in EXCLUDED_PARTS for part in relative.parts[:-1]):
        return False
    if path.suffix.lower() in SOURCE_SUFFIXES:
        return True
    try:
        return path.is_file() and not path.suffix and os.access(path, os.X_OK)
    except OSError:
        return False


def current_commit(root: Path) -> str:
    result = _run(["git", "-C", str(root), "rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "unversioned"


def _load_route(path: Path) -> dict[str, Any]:
    try:
        if not path.is_absolute() or path.is_symlink() or path.stat().st_size > 2_000_000:
            raise RouteError("route-file-unsafe")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise RouteError("route-file-unreadable") from exc
    if not isinstance(value, dict):
        raise RouteError("route-record-invalid")
    return value


def verify_route(
    route_file: Path,
    expected_root: Path,
    agent_home: Path,
    *,
    expected_route_id: str | None = None,
    expected_node: str | None = None,
) -> dict[str, Any]:
    if route_file.is_symlink():
        raise RouteError("route-file-unsafe")
    route_file = route_file.resolve(strict=False)
    route = _load_route(route_file)
    if route.get("capability") != "autopilot-code":
        raise RouteError("route-capability-not-autopilot-code")
    if route.get("effective_intensity") not in INTENSITIES:
        raise RouteError("route-intensity-invalid")
    route_cwd = Path(str(route.get("cwd", ""))).resolve(strict=False)
    if route_cwd != expected_root.resolve():
        raise RouteError("route-cwd-mismatch")
    artifact_root = Path(str(route.get("artifact_root", ""))).resolve(strict=False)
    if not artifact_root.is_absolute() or not _within(route_file, artifact_root):
        raise RouteError("route-file-outside-artifact-root")
    verifier = agent_home / "utilities" / "capability-route.py"
    if not verifier.is_file():
        raise RouteError("route-verifier-unavailable")
    result = _run(
        [
            sys.executable,
            str(verifier),
            "verify",
            "--route", str(route_file),
            "--cwd", str(expected_root),
        ]
    )
    if result.returncode:
        raise RouteError("route-record-verification-failed")
    if route.get("source_commit") != current_commit(expected_root):
        raise RouteError("route-source-commit-stale")
    if expected_route_id and route.get("route_id") != expected_route_id:
        raise RouteError("route-id-mismatch")
    if expected_node:
        nodes = route.get("nodes")
        if not isinstance(nodes, list) or expected_node not in {
            node.get("id") for node in nodes if isinstance(node, dict)
        }:
            raise RouteError("route-node-mismatch")
    return route


def bind_route(
    route_file: Path,
    cwd: Path,
    session_id: str,
    agent_home: Path,
) -> dict[str, Any]:
    root = project_root(cwd)
    route = verify_route(route_file, root, agent_home)
    path = marker_path(agent_home, session_id)
    marker = {
        "schema_version": MARKER_SCHEMA,
        "session_key": session_key(session_id),
        "route_file": str(route_file.resolve()),
        "route_id": route["route_id"],
        "route_hash": route["route_hash"],
        "cwd": str(root),
        "source_commit": route["source_commit"],
        "created_at_ns": time.time_ns(),
    }
    _atomic_json(path, marker)
    gc_markers(agent_home, keep=path)
    return marker


def clear_route(session_id: str, agent_home: Path) -> None:
    try:
        path = marker_path(agent_home, session_id)
        if not path.is_symlink():
            path.unlink(missing_ok=True)
    except (OSError, RouteError):
        pass
    gc_markers(agent_home)


def session_route(session_id: str, root: Path, agent_home: Path) -> dict[str, Any]:
    path = marker_path(agent_home, session_id)
    try:
        if path.is_symlink() or path.stat().st_size > 16_384:
            raise RouteError("session-marker-unsafe")
        marker = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise RouteError("session-route-missing") from exc
    if not isinstance(marker, dict) or marker.get("schema_version") != MARKER_SCHEMA:
        raise RouteError("session-marker-invalid")
    if marker.get("session_key") != session_key(session_id):
        raise RouteError("session-marker-foreign")
    if Path(str(marker.get("cwd", ""))).resolve(strict=False) != root.resolve():
        raise RouteError("session-marker-cwd-mismatch")
    route_file = Path(str(marker.get("route_file", "")))
    route = verify_route(
        route_file,
        root,
        agent_home,
        expected_route_id=str(marker.get("route_id", "")),
    )
    if route.get("route_hash") != marker.get("route_hash"):
        raise RouteError("session-marker-route-hash-mismatch")
    return route


def worker_route(root: Path, agent_home: Path) -> dict[str, Any] | None:
    route_file = os.environ.get("AGENT_ROUTE_FILE", "")
    route_id = os.environ.get("AGENT_ROUTE_ID", "")
    route_node = os.environ.get("AGENT_ROUTE_NODE", "")
    if not route_file and not route_id and not route_node:
        return None
    if not route_file or not route_id:
        raise RouteError("worker-route-binding-incomplete")
    return verify_route(
        Path(route_file),
        root,
        agent_home,
        expected_route_id=route_id,
        expected_node=route_node or None,
    )


def require_route(session_id: str, root: Path, agent_home: Path) -> None:
    worker = worker_route(root, agent_home)
    if worker is not None:
        return
    session_route(session_id, root, agent_home)


def _shell_segments(command: str) -> Iterable[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token and all(character in ";&|" for character in token):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def _route_compile_argv(segment: list[str]) -> list[str] | None:
    """Return compile arguments only for an actual router invocation.

    A loose token search lets harmless commands such as
    `echo capability-route.py compile --output old-route.json` bind an old
    record.  Accept only direct execution or a Python interpreter launching
    the router, with optional leading environment assignments/`command`.
    """

    index = 0
    while index < len(segment) and re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*=.*", segment[index]
    ):
        index += 1
    if index < len(segment) and segment[index] == "command":
        index += 1
    if index >= len(segment):
        return None
    executable = Path(segment[index]).name
    if re.fullmatch(r"python(?:3(?:\.\d+)?)?", executable):
        index += 1
        if index >= len(segment) or Path(segment[index]).name != "capability-route.py":
            return None
    elif executable != "capability-route.py":
        return None
    index += 1
    if index >= len(segment) or segment[index] != "compile":
        return None
    return segment[index + 1:]


def route_compile_outputs(command: str, cwd: Path) -> list[Path]:
    outputs: list[Path] = []
    command_cwd = cwd.resolve(strict=False)
    for segment in _shell_segments(command):
        if segment and segment[0] == "cd" and len(segment) == 2 and not segment[1].startswith("-"):
            command_cwd = _resolve_path(command_cwd, segment[1])
            continue
        tail = _route_compile_argv(segment)
        if tail is None:
            continue
        for offset, value in enumerate(tail):
            raw = ""
            if value == "--output" and offset + 1 < len(tail):
                raw = tail[offset + 1]
            elif value.startswith("--output="):
                raw = value.split("=", 1)[1]
            if raw:
                path = Path(os.path.expanduser(raw))
                outputs.append(
                    (command_cwd / path).resolve() if not path.is_absolute() else path.resolve()
                )
    unique = []
    for path in outputs:
        if path not in unique:
            unique.append(path)
    return unique


def _resolve_path(base: Path, raw: str) -> Path:
    path = Path(os.path.expanduser(raw))
    return (base / path).resolve(strict=False) if not path.is_absolute() else path.resolve(strict=False)


def _git_commit_segments(
    command: str,
    base: Path,
    *,
    depth: int = 0,
) -> list[tuple[Path, bool, str, list[str]]]:
    if depth > 4:
        return []
    found: list[tuple[Path, bool, str, list[str]]] = []
    current_cwd = base.resolve()
    for segment in _shell_segments(command):
        if not segment:
            continue
        if Path(segment[0]).name in {"sh", "bash", "zsh", "dash", "ksh"}:
            try:
                shell_index = segment.index("-c")
            except ValueError:
                shell_index = -1
            if shell_index >= 0 and shell_index + 1 < len(segment):
                found.extend(
                    _git_commit_segments(
                        segment[shell_index + 1], current_cwd, depth=depth + 1
                    )
                )
                continue
        if segment[0] == "cd" and len(segment) == 2 and not segment[1].startswith("-"):
            current_cwd = _resolve_path(current_cwd, segment[1])
            continue
        git_index = next(
            (index for index, value in enumerate(segment) if Path(value).name == "git"),
            None,
        )
        if git_index is None:
            continue
        index = git_index + 1
        command_cwd = current_cwd
        while index < len(segment):
            token = segment[index]
            if token == "-C" and index + 1 < len(segment):
                command_cwd = _resolve_path(command_cwd, segment[index + 1])
                index += 2
                continue
            if token.startswith("-C") and len(token) > 2:
                command_cwd = _resolve_path(command_cwd, token[2:])
                index += 1
                continue
            if token == "--work-tree" and index + 1 < len(segment):
                command_cwd = _resolve_path(command_cwd, segment[index + 1])
                index += 2
                continue
            if token.startswith("--work-tree="):
                command_cwd = _resolve_path(command_cwd, token.split("=", 1)[1])
                index += 1
                continue
            if token in {"-c", "--config-env", "--exec-path", "--git-dir", "--work-tree"}:
                index += 2
                continue
            if token.startswith("-"):
                index += 1
                continue
            break
        if index >= len(segment) or segment[index] != "commit":
            continue
        args = segment[index + 1:]
        all_tracked = False
        path_mode = "default"
        paths: list[str] = []
        value_options = {
            "-C", "--reuse-message", "-c", "--reedit-message", "-F", "--file",
            "-m", "--message", "--author", "--date", "--fixup", "--squash",
            "--cleanup", "--trailer", "-S", "--gpg-sign",
        }
        positional = False
        offset = 0
        while offset < len(args):
            token = args[offset]
            if positional:
                paths.append(token)
                offset += 1
                continue
            if token == "--":
                positional = True
                offset += 1
                continue
            if token in {"-a", "--all"} or (
                token.startswith("-") and not token.startswith("--") and "a" in token[1:]
            ):
                all_tracked = True
            if token in {"-i", "--include"}:
                path_mode = "include"
            if token in {"-o", "--only"}:
                path_mode = "only"
            if token.startswith(("--include=", "--only=")):
                path_mode = "include" if token.startswith("--include=") else "only"
                paths.append(token.split("=", 1)[1])
                offset += 1
                continue
            if re.match(r"^-[io].+", token):
                path_mode = "include" if token.startswith("-i") else "only"
                paths.append(token[2:])
                offset += 1
                continue
            if token == "--pathspec-from-file":
                # The referenced path list is intentionally not opened by a
                # hook. Conservatively inspect all staged and tracked changes.
                all_tracked = True
                offset += 2
                continue
            if token.startswith("--pathspec-from-file="):
                all_tracked = True
                offset += 1
                continue
            if token in value_options:
                offset += 2
                continue
            if any(token.startswith(option + "=") for option in value_options if option.startswith("--")):
                offset += 1
                continue
            if token.startswith("-") and not token.startswith("--"):
                # Short options may be bundled (`-am message`).  A value-taking
                # flag at the end consumes the following token; without this,
                # the commit message is misclassified as a pathspec and a real
                # `git commit -am` source change can evade the staged-scope read.
                short = token[1:]
                consumes_next = any(
                    short.endswith(flag) for flag in ("m", "F", "C", "c")
                )
                offset += 2 if consumes_next and offset + 1 < len(args) else 1
                continue
            if token.startswith("-"):
                offset += 1
                continue
            paths.append(token)
            offset += 1
        found.append((command_cwd, all_tracked, path_mode, paths))
    return found


def _diff_entries(repo: Path, *, cached: bool, paths: list[str] | None = None) -> list[tuple[str, list[str]]]:
    command = ["git", "-C", str(repo), "diff"]
    if cached:
        command.append("--cached")
    command += ["--name-status", "-z", "--find-renames=100%"]
    if _run(["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"]).returncode == 0:
        command.append("HEAD")
    if paths:
        command += ["--", *paths]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
    if result.returncode:
        return []
    fields = result.stdout.split(b"\0")
    entries: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(fields) and fields[index]:
        status_text = fields[index].decode("utf-8", "surrogateescape")
        index += 1
        count = 2 if status_text.startswith(("R", "C")) else 1
        names = [
            fields[index + item].decode("utf-8", "surrogateescape")
            for item in range(count)
            if index + item < len(fields) and fields[index + item]
        ]
        index += count
        entries.append((status_text, names))
    return entries


def commit_has_material(
    repo: Path,
    all_tracked: bool,
    path_mode: str,
    paths: list[str],
) -> bool:
    root = git_root(repo)
    if root is None:
        return False
    if paths and path_mode in {"default", "only"}:
        # Plain pathspecs and --only commit those paths without including an
        # unrelated staged change. Read both index and worktree so an unborn
        # branch cannot hide a staged initial source file.
        entries = _diff_entries(root, cached=True, paths=paths)
        entries += _diff_entries(root, cached=False, paths=paths)
    else:
        entries = _diff_entries(root, cached=True)
        if all_tracked or path_mode == "include":
            entries += _diff_entries(root, cached=False, paths=paths or None)
    for status_text, names in entries:
        if status_text == "R100":
            continue
        if any(is_material_source(root / name, root) for name in names):
            return True
    return False


def check_action(
    tool: str,
    cwd: Path,
    session_id: str,
    agent_home: Path,
    *,
    file_path: str = "",
    command: str = "",
) -> None:
    if tool in EDIT_TOOLS:
        if not file_path:
            return
        target = _resolve_path(cwd, file_path)
        repo = git_root(target)
        if not is_material_source(target, repo):
            return
        require_route(session_id, project_root(cwd, target), agent_home)
        return
    if tool not in {"Bash", "bash", "Shell", "shell"} or not command:
        return
    for command_cwd, all_tracked, path_mode, paths in _git_commit_segments(command, cwd):
        repo = git_root(command_cwd)
        if repo is None or not commit_has_material(repo, all_tracked, path_mode, paths):
            continue
        require_route(session_id, repo, agent_home)


def deny_json(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"{DENIAL} [reason={reason}]",
                }
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def hook_main(payload: dict[str, Any], agent_home: Path) -> int:
    event = str(payload.get("hook_event_name") or "")
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve(strict=False)
    session_id = str(payload.get("session_id") or "")
    if event == "SessionEnd":
        if session_id:
            clear_route(session_id, agent_home)
        return 0
    if event == "PostToolUse" and tool in {"Bash", "bash", "Shell", "shell"}:
        outputs = route_compile_outputs(str(tool_input.get("command") or ""), cwd)
        if session_id and len(outputs) == 1:
            try:
                bind_route(outputs[0], cwd, session_id, agent_home)
            except (RouteError, OSError, subprocess.SubprocessError):
                pass
        return 0
    if event != "PreToolUse":
        return 0
    try:
        check_action(
            tool,
            cwd,
            session_id,
            agent_home,
            file_path=str(
                tool_input.get("file_path")
                or tool_input.get("notebook_path")
                or tool_input.get("path")
                or ""
            ),
            command=str(tool_input.get("command") or ""),
        )
    except RouteError as exc:
        deny_json(str(exc))
    except (OSError, subprocess.SubprocessError):
        deny_json("route-guard-check-failed")
    return 0


def cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-home")
    sub = parser.add_subparsers(dest="action", required=True)
    bind = sub.add_parser("bind")
    bind.add_argument("--route", required=True)
    bind.add_argument("--cwd", required=True)
    bind.add_argument("--session", required=True)
    check = sub.add_parser("check")
    check.add_argument("--tool", required=True)
    check.add_argument("--file", default="")
    check.add_argument("--command", default="")
    check.add_argument("--cwd", required=True)
    check.add_argument("--session", required=True)
    clear = sub.add_parser("clear")
    clear.add_argument("--session", required=True)
    args = parser.parse_args(argv)
    agent_home = resolve_agent_home(args.agent_home)
    try:
        if args.action == "bind":
            bind_route(Path(args.route), Path(args.cwd), args.session, agent_home)
        elif args.action == "check":
            check_action(
                args.tool,
                Path(args.cwd),
                args.session,
                agent_home,
                file_path=args.file,
                command=args.command,
            )
        else:
            clear_route(args.session, agent_home)
    except RouteError as exc:
        print(f"{DENIAL} [reason={exc}]", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError):
        print(f"{DENIAL} [reason=route-guard-check-failed]", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        return cli(sys.argv[1:])
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    return hook_main(payload, resolve_agent_home())


if __name__ == "__main__":
    raise SystemExit(main())
