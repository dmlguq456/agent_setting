#!/usr/bin/env python3
"""Codex PreToolUse bridge for portable write guards and parent parking."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"
OPEN_DISPATCH_STATES = {"open", "running"}
MIN_PARK_WAIT_SECONDS = 300


def hook_block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def first_string(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def nested_mapping(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def nested_string(payload: dict[str, Any], *keys: str) -> str:
    direct = first_string(payload, *keys)
    if direct:
        return direct
    for key in ("context", "workspace", "session", "payload", "event", "input", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            found = nested_string(value, *keys)
            if found:
                return found
    return ""


def tool_name(payload: dict[str, Any]) -> str:
    direct = first_string(payload, "tool_name", "toolName", "matcher")
    if direct:
        return direct
    raw_tool = payload.get("tool")
    if isinstance(raw_tool, str) and raw_tool:
        return raw_tool
    tool = nested_mapping(payload, "tool", "toolUse", "tool_use")
    return first_string(tool, "name", "tool_name", "toolName")


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    direct = nested_mapping(payload, "tool_input", "toolInput", "input", "arguments", "args", "params")
    if direct:
        return direct
    tool = nested_mapping(payload, "tool", "toolUse", "tool_use")
    return nested_mapping(tool, "tool_input", "toolInput", "input", "arguments", "args", "params")


def cwd(payload: dict[str, Any]) -> Path:
    raw = nested_string(payload, "cwd", "working_directory", "workingDirectory")
    if raw:
        return Path(raw)
    return Path.cwd()


def normalize(base: Path, raw: str) -> str:
    if not raw or raw == "/dev/null":
        return ""
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    return str(path)


def patch_files(base: Path, text: str) -> list[str]:
    if not text:
        return []
    files: list[str] = []
    pattern = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.MULTILINE)
    for match in pattern.finditer(text):
        raw = match.group(1) or match.group(2) or ""
        file = normalize(base, raw.strip())
        if file:
            files.append(file)
    return files


def is_patch_tool(name: str) -> bool:
    return name in {"apply_patch", "ApplyPatch", "patch", "functions.apply_patch"} or name.endswith(".apply_patch")


def is_shell_tool(name: str) -> bool:
    return name in {"Bash", "bash", "Shell", "shell", "exec_command", "functions.exec_command"} or name.endswith(
        ".exec_command"
    )


def patch_text(payload: dict[str, Any], args: dict[str, Any]) -> str:
    direct = first_string(args, "patch", "patchText", "patch_text", "input") or first_string(
        payload, "patch", "patchText", "patch_text", "input", "text", "tool_input", "toolInput"
    )
    if direct:
        return direct

    # Freeform tool transports may wrap the raw patch below one or more
    # provider-owned envelope objects. Search mappings/lists only for an
    # unmistakable apply_patch payload instead of guessing a target path.
    pending: list[Any] = list(payload.values())
    while pending:
        value = pending.pop()
        if isinstance(value, str) and "*** Begin Patch" in value:
            return value
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return ""


def shell_command(payload: dict[str, Any], args: dict[str, Any]) -> str:
    return first_string(args, "command", "cmd", "script", "input") or first_string(
        payload, "command", "cmd", "script"
    )


def dispatch_jobs_path() -> Path:
    override = os.environ.get("AGENT_DISPATCH_JOBS")
    if override:
        return Path(override)
    agent_home = os.environ.get("AGENT_HOME")
    if agent_home and (Path(agent_home) / "core" / "CORE.md").is_file():
        return Path(agent_home) / ".dispatch" / "jobs.log"
    return ROOT / ".dispatch" / "jobs.log"


def dispatch_metadata(raw: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in raw.split(",") if "=" in part)


def open_child_attempts(session_id: str) -> dict[str, str]:
    """Return exact open attempts owned by this parent session/conductor."""

    if os.environ.get("AGENT_PARENT_PARK_BYPASS") == "1":
        return {}
    parent_attempt_id = os.environ.get("AGENT_DISPATCH_ATTEMPT_ID", "")
    if not session_id and not parent_attempt_id:
        return {}
    jobs = dispatch_jobs_path()
    try:
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return {}
    except OSError:
        # Registry availability is checked by the dispatch wrapper. A hook I/O
        # failure must not freeze every unrelated Codex tool globally.
        return {}

    latest: dict[str, tuple[str, str]] = {}
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        metadata = dispatch_metadata(fields[5])
        attempt_id = metadata.get("attempt_id", "")
        if not attempt_id:
            continue
        owned_by_session = bool(session_id) and metadata.get("parent_sid") == session_id
        owned_by_attempt = bool(parent_attempt_id) and metadata.get("parent_attempt_id") == parent_attempt_id
        if owned_by_session or owned_by_attempt:
            latest[attempt_id] = (fields[1], fields[4])
    return {
        attempt_id: slug
        for attempt_id, (state, slug) in latest.items()
        if state in OPEN_DISPATCH_STATES
    }


def local_contract_path(base: Path, raw: str, relative: str) -> bool:
    """Accept only the harness helper in ROOT or the caller's linked worktree."""

    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    expected = (ROOT / relative).resolve()
    if candidate == expected:
        return True
    resolved_base = base.resolve()
    for parent in (resolved_base, *resolved_base.parents):
        if (parent / "core" / "CORE.md").is_file():
            return candidate == (parent / relative).resolve()
    return False


def parse_long_options(tokens: list[str], valued: set[str], switches: set[str]) -> dict[str, list[str]] | None:
    parsed: dict[str, list[str]] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if "=" in token and token.startswith("--"):
            option, value = token.split("=", 1)
            if option not in valued or not value:
                return None
            parsed.setdefault(option, []).append(value)
            index += 1
            continue
        if token in switches:
            parsed.setdefault(token, []).append("1")
            index += 1
            continue
        if token not in valued or index + 1 >= len(tokens):
            return None
        parsed.setdefault(token, []).append(tokens[index + 1])
        index += 2
    return parsed


def exact_park_control(base: Path, command: str, attempts: dict[str, str]) -> bool:
    """Allow only an exact-attempt blocking wait or typed harvest command."""

    # Shell composition could append arbitrary work after an allowed wait.
    if not command or re.search(r"[\n\r;&|<>`]", command) or "$(" in command:
        return False
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False
    if not tokens:
        return False

    if local_contract_path(base, tokens[0], "utilities/dispatch-wait.sh"):
        options = parse_long_options(
            tokens[1:],
            {"--attempt-id", "--interval", "--max"},
            set(),
        )
        if options is None or len(options.get("--attempt-id", [])) != 1:
            return False
        if options["--attempt-id"][0] not in attempts:
            return False
        if any(len(values) != 1 for values in options.values()):
            return False
        try:
            wait_seconds = int(options.get("--max", ["600"])[0])
            interval = int(options.get("--interval", ["20"])[0])
        except ValueError:
            return False
        return MIN_PARK_WAIT_SECONDS <= wait_seconds <= 600 and 1 <= interval <= 60

    if (
        len(tokens) >= 2
        and local_contract_path(base, tokens[0], "adapters/codex/bin/preflight.sh")
        and tokens[1] == "harvest"
    ):
        options = parse_long_options(
            tokens[2:],
            {"--attempt-id", "--status", "--completion"},
            {"--mark-done", "--keep-home", "--failure-detail"},
        )
        if options is None or len(options.get("--attempt-id", [])) != 1:
            return False
        if options["--attempt-id"][0] not in attempts:
            return False
        if any(len(values) != 1 for values in options.values()):
            return False
        return options.get("--status", ["open"])[0] == "open"

    return False


def park_control_allowed(name: str, payload: dict[str, Any], args: dict[str, Any], attempts: dict[str, str]) -> bool:
    # Transport continuations do no new project work. Codex currently does not
    # rerun PreToolUse for write_stdin after the originating unified exec call,
    # while the orchestration bridge can expose a typed wait(cell_id) instead.
    if name in {"wait", "functions.wait", "write_stdin", "functions.write_stdin"}:
        return True
    if name.endswith(".wait") or name.endswith(".write_stdin"):
        return True
    return is_shell_tool(name) and exact_park_control(cwd(payload), shell_command(payload, args), attempts)


def shell_write_files(base: Path, command: str) -> list[str]:
    if not command:
        return []
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []

    files: list[str] = []
    redirects = {">", ">>", "1>", "1>>", "2>", "2>>", "&>", "&>>", ">|"}
    separators = {"|", "&&", "||", ";"}
    mutation_commands = {"tee", "touch", "cp", "mv", "rm", "install", "rsync"}

    def add_file(raw: str) -> None:
        file = normalize(base, raw)
        if file:
            files.append(file)

    def split_command_operands(start: int) -> tuple[list[str], int]:
        operands: list[str] = []
        idx = start
        while idx < len(tokens):
            token = tokens[idx]
            if token in separators:
                break
            if token == "--":
                idx += 1
                continue
            if token.startswith("-"):
                idx += 1
                continue
            operands.append(token)
            idx += 1
        return operands, idx

    for idx, token in enumerate(tokens):
        if token in redirects and idx + 1 < len(tokens):
            add_file(tokens[idx + 1])
            continue
        match = re.match(r"^(?:[0-9]?>|[0-9]?>>|&>|&>>|>\|)(.+)$", token)
        if match:
            add_file(match.group(1))
        if token.startswith("of=") and len(token) > 3:
            add_file(token[3:])

    idx = 0
    while idx < len(tokens):
        command_name = Path(tokens[idx]).name
        if command_name == "sed":
            inline = False
            saw_script = False
            idx += 1
            while idx < len(tokens):
                token = tokens[idx]
                if token in separators:
                    break
                if token == "--":
                    idx += 1
                    continue
                if token == "-i" or token.startswith("-i."):
                    inline = True
                    idx += 1
                    continue
                if token in {"-e", "--expression", "-f", "--file"}:
                    idx += 2
                    continue
                if token.startswith("-"):
                    idx += 1
                    continue
                if not saw_script:
                    saw_script = True
                    idx += 1
                    continue
                if inline:
                    add_file(token)
                idx += 1
            continue

        if command_name not in mutation_commands:
            idx += 1
            continue

        operands, idx = split_command_operands(idx + 1)
        if command_name in {"cp", "install", "rsync"}:
            if len(operands) >= 2:
                add_file(operands[-1])
            continue
        for operand in operands:
            add_file(operand)

    return files


def target_files(payload: dict[str, Any]) -> list[str]:
    name = tool_name(payload)
    args = tool_input(payload)
    base = cwd(payload)

    if name in {"Write", "write", "Edit", "edit", "MultiEdit", "multi_edit", "multiedit"}:
        file = normalize(base, first_string(args, "file_path", "filePath", "path", "file"))
        return [file] if file else []

    if is_patch_tool(name):
        return patch_files(base, patch_text(payload, args))

    if is_shell_tool(name):
        return shell_write_files(base, shell_command(payload, args))

    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    name = tool_name(payload)
    args = tool_input(payload)
    session_id = nested_string(payload, "session_id", "sessionID", "thread_id", "threadID")
    if not session_id:
        session_id = first_string(nested_mapping(payload, "session"), "id")

    attempts = open_child_attempts(session_id)
    if attempts and not park_control_allowed(name, payload, args, attempts):
        attempt_list = ",".join(sorted(attempts))
        return hook_block(
            "parent-parked: open registered child attempt(s) "
            f"{attempt_list}; only exact dispatch-wait --attempt-id with --max 300..600 "
            "or exact preflight harvest is allowed; raw logs, source, artifacts, git, and other tools are blocked"
        )
    if os.environ.get("AGENT_PARENT_PARK_ONLY") == "1":
        return 0

    files = target_files(payload)
    if (name in {"Write", "write", "Edit", "edit", "MultiEdit", "multi_edit", "multiedit"} or is_patch_tool(name)) and not files:
        return hook_block(f"agent harness preflight could not determine target file for Codex tool {name}")

    session_id = session_id or "codex-hook"
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))

    for file in files:
        result = subprocess.run(
            [str(PREFLIGHT), "write", file, session_id],
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            detail = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
            return hook_block(detail or f"agent harness preflight failed for {file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
