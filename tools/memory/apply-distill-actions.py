#!/usr/bin/env python3
"""Apply memory distillation JSON-lines actions.

The distiller model only proposes JSON objects. This script owns shape checks,
snapshot membership checks, and argv-only calls into mem.py.
"""
import argparse
import json
import subprocess
import sys


def _load_snapshot_ids(path):
    if not path:
        return set()
    try:
        with open(path, encoding="utf-8") as fh:
            return set(fh.read().split())
    except OSError:
        return set()


def apply_actions(out_path, mem_path, mode="increment", snapshot_ids_path=""):
    # In curate mode this is a destructive allowlist, not every id printed in the
    # snapshot. `curate-snapshot` deliberately omits PROTECTED PENDING handoff/
    # thread ids, so model output cannot prune or merge them through this layer.
    destructive_ids = _load_snapshot_ids(snapshot_ids_path)

    def member(rid):
        return (mode != "curate") or (rid in destructive_ids)

    try:
        with open(out_path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        lines = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        try:
            rec = json.loads(line)
        except Exception:
            sys.stderr.write(f"[distill-parse] skip malformed: {line[:120]!r}\n")
            continue
        if not isinstance(rec, dict):
            sys.stderr.write("[distill-parse] skip non-object\n")
            continue

        action = rec.get("action")
        if action is None and rec.get("tier") and rec.get("type") and isinstance(rec.get("body"), str):
            action = "add"

        # `mem delete` is a user-controlled path and is never a curator action.
        # Keep this explicit so a future mem.py delete surface cannot accidentally
        # become reachable from untrusted distiller output.
        if action == "delete":
            sys.stderr.write("[distill-parse] skip delete: unsupported destructive action\n")
            continue

        # increment = add-only, enforced (not merely prompted). The turn-nudge/fast
        # tier reads untrusted transcript delta with no snapshot whitelist, so a
        # prompt-injected model could name id-mutations (prune/merge/graduate/...)
        # that member() would wave through under mode != "curate" (always True).
        # Reject id-mutations outside curate mode so only the snapshot-grounded deep
        # curator can ever delete/merge/graduate. Closes the P-25 whitelist bypass
        # for every adapter at the shared applier (deterministic, §0.5).
        if action in ("reinforce", "prune", "graduate", "reattribute", "merge") and mode != "curate":
            sys.stderr.write(f"[distill-parse] skip {action}: id-mutation not allowed in {mode} mode (add-only)\n")
            continue

        if action == "add":
            tier = rec.get("tier")
            rtype = rec.get("type")
            body = rec.get("body")
            if tier not in ("working", "durable"):
                sys.stderr.write(f"[distill-parse] skip bad tier: {tier!r}\n")
                continue
            if not isinstance(rtype, str) or not rtype:
                sys.stderr.write("[distill-parse] skip missing/empty type\n")
                continue
            if not isinstance(body, str) or not body:
                sys.stderr.write("[distill-parse] skip missing/empty body\n")
                continue
            if len(body) > 2000:
                sys.stderr.write(f"[distill-parse] skip body too long ({len(body)})\n")
                continue
            subprocess.run(["python3", mem_path, "add", tier, rtype, body])

        elif action in ("reinforce", "prune", "graduate", "reattribute"):
            rid = rec.get("id")
            if not isinstance(rid, str) or not rid:
                sys.stderr.write(f"[distill-parse] skip {action}: missing id\n")
                continue
            if not member(rid):
                sys.stderr.write(f"[distill-parse] skip non-destructive-allowlist id ({action}): {rid!r}\n")
                continue
            if action == "graduate":
                subprocess.run(["python3", mem_path, "graduate", rid, "--to", "durable"])
            else:
                subprocess.run(["python3", mem_path, action, rid])

        elif action == "merge":
            ids = rec.get("ids")
            canonical = rec.get("canonical")
            if (not isinstance(ids, list) or len(ids) < 2
                    or not all(isinstance(i, str) and i for i in ids)):
                sys.stderr.write("[distill-parse] skip merge: bad ids\n")
                continue
            if not isinstance(canonical, str) or canonical not in ids:
                sys.stderr.write("[distill-parse] skip merge: bad canonical\n")
                continue
            if not all(member(i) for i in ids):
                sys.stderr.write("[distill-parse] skip merge: id outside destructive allowlist\n")
                continue
            subprocess.run(["python3", mem_path, "merge", "--canonical", canonical, *ids])

        else:
            sys.stderr.write(f"[distill-parse] skip unknown action: {action!r}\n")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("out_path")
    parser.add_argument("mem_path")
    parser.add_argument("--mode", choices=("increment", "curate"), default="increment")
    parser.add_argument("--snapshot-ids", default="")
    args = parser.parse_args(argv)
    return apply_actions(args.out_path, args.mem_path, args.mode, args.snapshot_ids)


if __name__ == "__main__":
    raise SystemExit(main())
