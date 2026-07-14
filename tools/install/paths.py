"""Centralized path resolution for the installer.

Honor ``AGENT_HOME`` and ``HOME`` overrides so tests can use temporary homes.
"""

import os
from pathlib import Path


def agent_home():
    """Return the repository root (``AGENT_HOME``).

    Use the environment override when set; otherwise find the nearest ancestor
    containing ``.git``.
    """
    env_home = os.environ.get("AGENT_HOME")
    if env_home:
        return Path(env_home)

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent

    raise RuntimeError(
        "could not resolve agent_home: AGENT_HOME is unset and "
        f"no .git directory was found above {here}."
    )


def runtime_home(runtime, scope="global"):
    """Return the installation home for a runtime and scope."""
    if runtime == "claude":
        return Path.home() / ".claude"
    if runtime == "codex":
        return Path.home() / ".codex"
    if runtime == "opencode":
        if scope == "project":
            return Path.cwd() / ".opencode"
        return Path.home() / ".config" / "opencode"
    raise ValueError(f"unknown runtime: {runtime!r}")


def opencode_data_home():
    """Return OpenCode's runtime-owned data directory (read-only to installer)."""
    return Path.home() / ".local" / "share" / "opencode"


def harness_state_dir(runtime, scope="global"):
    """Return the installer-owned state directory (``<runtime_home>/.harness``)."""
    return runtime_home(runtime, scope) / ".harness"


def resolve_source(relpath):
    """Resolve a repository-relative path to an absolute path."""
    return agent_home() / relpath


def source_exists(relpath):
    """Return whether a source exists, following directory symlinks."""
    return resolve_source(relpath).exists()
