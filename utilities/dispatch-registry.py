#!/usr/bin/env python3
"""Manage the canonical global dispatch attempt registry."""

from __future__ import annotations

import argparse
from pathlib import Path

from dispatch_contract import DispatchContractError, reconcile_local_registry


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--global-jobs", type=Path, required=True)
    reconcile.add_argument("--local-jobs", type=Path, required=True)
    args = p.parse_args()
    try:
        count, malformed = reconcile_local_registry(args.global_jobs.resolve(), args.local_jobs.resolve())
    except DispatchContractError as exc:
        print("check=failed")
        print(f"reason={exc.reason}")
        print(f"detail={exc.detail}")
        return 73
    print("check=ok")
    print(f"global_registry={args.global_jobs.resolve()}")
    print(f"local_registry={args.local_jobs.resolve()}")
    print(f"reconciled={count}")
    print(f"malformed={malformed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
