#!/usr/bin/env python3
"""Select and launch the configured portable dispatch-depth-1 owner."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
_defaults_spec = importlib.util.spec_from_file_location(
    "dispatch_defaults", ROOT / "utilities" / "dispatch-defaults.py"
)
if _defaults_spec is None or _defaults_spec.loader is None:
    raise RuntimeError("cannot load dispatch-defaults.py")
_defaults = importlib.util.module_from_spec(_defaults_spec)
_defaults_spec.loader.exec_module(_defaults)

_FORBIDDEN = {
    "--worker-mode", "--model", "--reasoning", "--effort", "--variant",
    "--inherit-model-settings",
}
_MODEL_ENV = re.compile(
    r"^[A-Za-z0-9]+_DISPATCH_(MODEL|MODEL_ROLE|MODEL_PROFILE|REASONING|EFFORT|VARIANT)$"
)
_REQUIRED = {
    "--worktree", "--slug", "--capability", "--capability-mode", "--qa",
    "--intensity", "--dispatch-depth", "--worker-type", "--assigned-contract",
    "--owner", "--model-profile",
}


class OwnerError(ValueError):
    pass


def _load_defaults():
    config_path = _defaults.default_config_path()
    try:
        config = _defaults.load_and_validate(config_path, _defaults.default_topology_path())
    except (OSError, ValueError, _defaults.DefaultsConfigError) as exc:
        raise OwnerError(f"defaults-invalid:{exc}") from exc
    return config


def _parse(argv):
    if argv == ["--help"] or not argv:
        print("usage: dispatch-owner [--adapter <harness>] --dry-run|--register|--start ...")
        raise SystemExit(0)
    forwarded = []
    explicit = None
    values = {}
    actions = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--adapter":
            if i + 1 >= len(argv):
                raise OwnerError("adapter-missing")
            explicit = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--adapter="):
            explicit = arg.split("=", 1)[1]
            i += 1
            continue
        name, equal, value = arg.partition("=")
        if name in {"--dry-run", "--register", "--start"}:
            if equal:
                raise OwnerError(f"invalid-action:{arg}")
            actions.append(name)
            forwarded.append(arg)
            i += 1
            continue
        if name in _FORBIDDEN or (equal and name in _FORBIDDEN):
            raise OwnerError(f"forbidden-flag:{name}")
        if name in _REQUIRED:
            if equal:
                values[name] = value
                forwarded.append(arg)
            else:
                if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                    raise OwnerError(f"missing-value:{name}")
                values[name] = argv[i + 1]
                forwarded.extend((arg, argv[i + 1]))
                i += 2
                continue
        if name == "--jobs":
            if equal:
                values[name] = value
            else:
                if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                    raise OwnerError("missing-value:--jobs")
                values[name] = argv[i + 1]
            forwarded.append(arg)
            i += 1
            continue
        forwarded.append(arg)
        i += 1
    missing = sorted(flag for flag in _REQUIRED if not values.get(flag))
    if missing:
        raise OwnerError("missing-required:" + ",".join(missing))
    if len(actions) != 1:
        raise OwnerError("exactly-one-action-required")
    if values["--dispatch-depth"] != "1" or values["--worker-type"] != "owner":
        raise OwnerError("owner-tuple-required")
    if values["--model-profile"] not in {"deep", "balanced-deep", "light"}:
        raise OwnerError("invalid-model-profile")
    # Equal-form required options are forwarded unchanged; split-form options
    # were appended above.  Selector-only --adapter never crosses the boundary.
    return explicit, values, forwarded


def _eligible(state):
    """Match dispatch-route.sh's eligible(): only limited(...) is a hard failure.

    `unknown` (jobs.log unavailable) and `ok` both remain candidates, per
    usage-check.sh's documented contract that `unknown` means "the
    orchestrator decides," not a failure.
    """

    return state != "limited" and not state.startswith("limited(")


def _usage(jobs):
    cmd = [str(ROOT / "utilities" / "usage-check.sh"), "--harness", "all"]
    if jobs:
        cmd += ["--jobs", jobs]
    result = subprocess.run(cmd, text=True, capture_output=True, env=os.environ.copy())
    if result.returncode != 0:
        raise OwnerError("usage-check-failed")
    states = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0] in _defaults.KNOWN_HARNESSES:
            if fields[0] in states:
                raise OwnerError("eligibility-malformed")
            states[fields[0]] = fields[1]
    if set(states) != set(_defaults.KNOWN_HARNESSES):
        raise OwnerError("eligibility-malformed")
    return states


def _audit(status, adapter, source, configured, explicit, states, rejected=(), fallback=None, reason="none"):
    lines = [
        f"status={status}", f"adapter={adapter or '-'}", f"selection_source={source}",
        f"configured_candidates={','.join(configured)}",
        f"explicit_adapter={explicit or 'none'}",
    ]
    for harness in sorted(states):
        lines.append(f"eligibility.{harness}={states[harness]}")
    for n, item in enumerate(rejected, 1):
        lines.append(f"rejected.{n}={item}:usage-{states[item]}")
    if fallback:
        lines.append(f"fallback.1={fallback}:configured-candidates-ineligible")
    lines += [
        "trace.1=cascade=explicit>hard-eligibility>configured-normal",
        f"trace.2=explicit={explicit or 'none'};authorized={int(bool(explicit and explicit in _defaults.KNOWN_HARNESSES))}",
        "trace.3=eligibility=" + ",".join(f"{h}:{states[h]}" for h in sorted(states)),
        f"trace.4=configured={','.join(configured)};selected={adapter or '-'};source={source};deviation_reason={reason}",
    ]
    return lines


def _error(reason, configured=(), explicit=None, states=None):
    lines = _audit("unavailable", None, "none", configured, explicit, states or {})
    lines += [f"check=failed", f"reason={reason}", "child_spawned=0"]
    print("\n".join(lines))
    return 65


def main(argv):
    try:
        explicit, values, forwarded = _parse(argv)
        config = _load_defaults()
        configured = list(_defaults.query_owners(config))
        if explicit is not None and explicit not in _defaults.KNOWN_HARNESSES:
            raise OwnerError("explicit-adapter-unauthorized")
        jobs = values.get("--jobs", os.environ.get("AGENT_DISPATCH_JOBS", ""))
        states = _usage(jobs)
        rejected = [h for h in sorted(states) if not _eligible(states[h])]
        selected = None
        source = "none"
        reason = "none"
        if explicit and _eligible(states[explicit]):
            selected, source = explicit, "explicit"
        if selected is None:
            for harness in configured:
                if _eligible(states[harness]):
                    selected, source = harness, "configured-normal"
                    break
        if selected is None:
            for harness in sorted(_defaults.KNOWN_HARNESSES):
                if _eligible(states[harness]):
                    selected, source, reason = harness, "eligibility-fallback", "configured-candidates-ineligible"
                    break
        if selected is None:
            print("\n".join(_audit("unavailable", None, "none", configured, explicit, states, rejected=rejected)))
            print("check=failed\nreason=no-eligible-candidate\nchild_spawned=0")
            return 65
        wrapper = ROOT / "adapters" / selected / "bin" / "dispatch-headless.py"
        if not os.access(wrapper, os.X_OK):
            print("\n".join(_audit("unavailable", selected, source, configured, explicit, states,
                                      rejected=rejected if source != "explicit" else (),
                                      fallback=selected if source == "eligibility-fallback" else None,
                                      reason=reason)))
            print("check=failed\nreason=wrapper-unavailable\nchild_spawned=0")
            return 65
        print("\n".join(_audit("eligible", selected, source, configured, explicit, states,
                                  rejected=rejected if source != "explicit" else (),
                                  fallback=selected if source == "eligibility-fallback" else None,
                                  reason=reason)), flush=True)
        child_env = {
            key: value for key, value in os.environ.items() if not _MODEL_ENV.fullmatch(key)
        }
        child_env["AGENT_DISPATCH_OWNER_HARNESS"] = selected
        child = subprocess.run([str(wrapper), *forwarded], env=child_env)
        return child.returncode
    except (OwnerError, OSError) as exc:
        return _error(str(exc))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
