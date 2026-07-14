#!/usr/bin/env python3
"""Explicit isolated replay/evaluator CLI; never imported by production hooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from fleet.token_experiment import (  # noqa: E402
    canonical_json,
    evaluate,
    fixture_set_sha256,
    replay_all,
    validate_manifest,
)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("replay", "evaluate"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", required=True)
        command.add_argument("--input", required=True)
    return ap


def load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        manifest = load_json(args.manifest)
        payload = load_json(args.input)
        validate_manifest(manifest, verify_code=True)
        if args.command == "replay":
            if manifest["fixture_set_sha256"] != fixture_set_sha256(payload):
                raise ValueError("fixture set hash mismatch")
            result = replay_all(payload, manifest)
        else:
            result = evaluate(payload, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"token-budget-experiment: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
