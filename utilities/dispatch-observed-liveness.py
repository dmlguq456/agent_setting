#!/usr/bin/env python3
"""Print the shared pure observed-liveness verdict for one exact attempt."""

from __future__ import annotations

import argparse
from pathlib import Path

from codex_dispatch_terminal import terminal_envelope_observed
from dispatch_contract import observed_attempt_liveness, parse_registry_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    try:
        lines = args.jobs.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
    except OSError:
        return 69
    matches: list[tuple[str, dict[str, str]]] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        metadata = parse_registry_metadata(fields[5])
        if metadata.get("attempt_id") == args.attempt_id:
            matches.append((fields[1], metadata))
    if len(matches) != 1:
        return 69
    status, metadata = matches[0]
    observed = observed_attempt_liveness(
        status,
        metadata,
        terminal_envelope=terminal_envelope_observed(metadata.get("log_file")),
    )
    print(f"state={observed.state}")
    print(f"reason={observed.reason}")
    print(f"process_state={observed.process_state}")
    print(f"process_reason={observed.process_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

