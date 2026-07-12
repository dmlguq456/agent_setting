"""_json_assert.py — tiny CLI helper for e2e_lifecycle.sh.

Usage: python3 _json_assert.py <json-file> '<python-expr-using-d>'
Loads <json-file> as `d`, evals the boolean expr, exit 0 if truthy, 1 if
falsy, 2 on error (bad JSON / expr exception). Kept separate from
tools/install/** since that tree is read-only for this test stage.
"""
import json
import sys


def main():
    if len(sys.argv) != 3:
        print("usage: _json_assert.py <json-file> <expr>", file=sys.stderr)
        return 2
    path, expr = sys.argv[1], sys.argv[2]
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as exc:
        print(f"JSON load failed: {exc}", file=sys.stderr)
        return 2
    try:
        # Everything (including `d`) must live in *globals*, with no separate
        # locals dict: nested generator/comprehension expressions (e.g.
        # all(any(...) for x in y)) get their own frame that resolves free
        # names via LOAD_GLOBAL only — a name present solely in a `locals`
        # dict passed to eval() is invisible from inside such nested scopes,
        # even though it resolves fine for the top-level expression itself.
        result = eval(
            expr,
            {"__builtins__": {}, "d": d, "len": len, "any": any, "all": all, "set": set, "sorted": sorted},
        )
    except Exception as exc:
        print(f"expr eval failed: {exc}", file=sys.stderr)
        return 2
    if not result:
        print(f"expr was falsy: {expr}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
