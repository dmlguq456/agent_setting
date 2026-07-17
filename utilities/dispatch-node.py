#!/usr/bin/env python3
"""Materialize a registry route node onto existing adapter dispatch wrappers."""
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROLE_MODE={"deep maker":"dev/refactor","fast implementer":"dev/backend","deep reviewer":"qa/test","fast reviewer":"qa/review","fast writer":"docs/writing","deep orchestrator":"ops/orchestration","orchestrator":"ops/orchestration"}

# SD-66 fix-forward: deterministic dispatch_evidence -> wrapper-argument binding
# for depth-2 route nodes (PRD §13.7.6, acceptance ③). Only same/cross-harness
# headless fallback hops carry a checked tuple; native-subagent/inline hops are
# not wrapper dispatch and are never consulted here.
FALLBACK_HOPS = {"same-harness-headless", "cross-harness-headless"}
EVIDENCE_TUPLE_FIELDS = (
    "parent_harness", "parent_transport", "parent_sandbox",
    "child_harness", "launch_authority", "status", "probe_source",
)
EVIDENCE_FLAG_MAP = {
    "launch_authority": "--launch-authority",
    "parent_harness": "--parent-harness",
    "parent_transport": "--parent-transport",
    "parent_sandbox": "--parent-sandbox",
    "status": "--nested-eligibility",
    "probe_source": "--eligibility-source",
}
FAILURE_CLASS_FLAG = "--eligibility-failure-class"


class DispatchNodeError(Exception):
    """Structured fail-loud diagnostic for evidence binding/conflict."""

    def __init__(self, reason, **fields):
        super().__init__(reason)
        self.reason = reason
        self.fields = fields


def _normalized_failure_class(row):
    return row.get("failure_class") or ""


def select_checked_tuple(route, node, adapter):
    """Pick the one supported checked tuple for `adapter` at this node.

    Walks the node's `dispatch_fallback` entries in ascending ordinal order,
    considering only same/cross-harness-headless hops whose candidate
    `child_harness` equals `adapter`. The first ordinal offering a candidate
    for this adapter is authoritative; it must be unambiguous, `supported`,
    and have exactly one matching counterpart in the route's top-level
    `dispatch_evidence.tuples` (matched on identity + status + probe_source +
    normalized failure_class; `probe_time` is deliberately excluded).
    """
    fallbacks = sorted(
        (f for f in node.get("dispatch_fallback", []) if f.get("hop") in FALLBACK_HOPS),
        key=lambda f: f.get("ordinal", 0),
    )
    for entry in fallbacks:
        matches = [c for c in entry.get("candidates", []) if c.get("child_harness") == adapter]
        if not matches:
            continue
        if len(matches) > 1:
            raise DispatchNodeError(
                "dispatch-evidence-ambiguous-candidate",
                ordinal=str(entry.get("ordinal")), adapter=adapter,
            )
        candidate = matches[0]
        if candidate.get("status") != "supported":
            raise DispatchNodeError(
                "dispatch-evidence-candidate-unsupported",
                ordinal=str(entry.get("ordinal")), adapter=adapter,
                status=str(candidate.get("status")),
            )
        top_tuples = route.get("dispatch_evidence", {}).get("tuples", [])
        counterparts = [
            t for t in top_tuples
            if all(t.get(f) == candidate.get(f) for f in EVIDENCE_TUPLE_FIELDS)
            and _normalized_failure_class(t) == _normalized_failure_class(candidate)
        ]
        if not counterparts:
            raise DispatchNodeError(
                "dispatch-evidence-no-top-level-counterpart",
                ordinal=str(entry.get("ordinal")), adapter=adapter,
            )
        if len(counterparts) > 1:
            raise DispatchNodeError(
                "dispatch-evidence-conflicting-counterparts",
                ordinal=str(entry.get("ordinal")), adapter=adapter,
                count=str(len(counterparts)),
            )
        return counterparts[0]
    raise DispatchNodeError("dispatch-evidence-no-eligible-fallback", adapter=adapter)


def strip_leading_separator(adapter_args):
    return adapter_args[1:] if adapter_args[:1] == ["--"] else adapter_args


def collect_explicit_evidence(tokens, flags):
    """Scan trailing adapter args for `--flag value` and `--flag=value` forms.

    Non-evidence tokens are opaque and simply walked past; only recognized
    evidence flags are captured (including repeats, to catch a caller
    supplying the same flag twice with disagreeing values).
    """
    values = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        matched = False
        for flag in flags:
            if tok == flag:
                if i + 1 >= len(tokens):
                    raise DispatchNodeError("dispatch-evidence-flag-missing-value", flag=flag)
                values.setdefault(flag, []).append(tokens[i + 1])
                i += 2
                matched = True
                break
            prefix = flag + "="
            if tok.startswith(prefix):
                values.setdefault(flag, []).append(tok[len(prefix):])
                i += 1
                matched = True
                break
        if not matched:
            i += 1
    return values


def bind_dispatch_evidence(route, node, adapter, adapter_args):
    """Return the wrapper flags to append for a depth-2 route node's --start.

    Never silently overwrites a caller-supplied evidence flag: an explicit
    value equal to the record is accepted without duplication, and any
    explicit/record mismatch (or disagreeing duplicate explicit occurrences)
    stops before wrapper invocation via `DispatchNodeError`.
    """
    tuple_row = select_checked_tuple(route, node, adapter)
    record = {flag: str(tuple_row.get(field, "")) for field, flag in EVIDENCE_FLAG_MAP.items()}
    failure_class = _normalized_failure_class(tuple_row)
    if failure_class:
        record[FAILURE_CLASS_FLAG] = failure_class
    trailing = strip_leading_separator(adapter_args)
    explicit = collect_explicit_evidence(trailing, list(record.keys()))
    extra = []
    for flag, value in record.items():
        seen = explicit.get(flag, [])
        if not seen:
            extra += [flag, value]
            continue
        if any(v != value for v in seen):
            raise DispatchNodeError(
                "dispatch-evidence-explicit-conflict",
                flag=flag, explicit=",".join(seen), record=value,
            )
    return extra


def main():
 p=argparse.ArgumentParser(); p.add_argument("--route",required=True); p.add_argument("--node",required=True); p.add_argument("--adapter",choices=("claude","codex","opencode"),required=True); p.add_argument("--action",choices=("dry-run","register","start"),default="dry-run"); p.add_argument("--slug",required=True); p.add_argument("--qa",default="standard"); p.add_argument("--parent"); p.add_argument("--prompt-text",default="Execute the selected immutable route node and emit its completion evidence."); p.add_argument("adapter_args",nargs=argparse.REMAINDER)
 a=p.parse_args(); route=json.loads(Path(a.route).read_text()); subprocess.run([sys.executable,str(ROOT/"utilities/capability-route.py"),"verify","--route",a.route,"--cwd",route["cwd"]],check=True,stdout=subprocess.DEVNULL)
 node=next((x for x in route["nodes"] if x["id"]==a.node),None)
 if not node: raise SystemExit("unknown route node")
 if node["kind"]=="resource-runner": print("resource_runner="+str(ROOT/"utilities/resource-runner.py")+"\nroute_node="+a.node); return
 print("completion_marker="+str(Path(os.environ.get("AGENT_HOME", ROOT))/".dispatch/completion"/route["route_id"]/(node["id"]+".json")))
 wrapper=ROOT/"adapters"/a.adapter/"bin"/"dispatch-headless.py"
 argv=[sys.executable,str(wrapper),"--"+a.action,"--worktree",route["cwd"],"--slug",a.slug,"--capability",route["capability"],"--mode",ROLE_MODE.get(node.get("role"),"ops/orchestration"),"--qa",a.qa,"--intensity",route["effective_intensity"],"--depth",str(node.get("depth",1)),"--worker-role",node["kind"],"--owner",route["capability"],"--route-file",str(Path(a.route).resolve()),"--route-id",route["route_id"],"--route-hash",route["route_hash"],"--route-node",node["id"],"--registry-digest",route["registry_digest"],"--write-scope",";".join(node["write_scope"]),"--completion-gate",node["completion_gate"],"--prompt-text",a.prompt_text]
 if node.get("depth")==2:
  if not a.parent: raise SystemExit("depth-2 route node requires --parent")
  argv += ["--parent",a.parent]
  try:
   argv += bind_dispatch_evidence(route, node, a.adapter, a.adapter_args)
  except DispatchNodeError as e:
   print("check=failed"); print(f"reason={e.reason}")
   for k,v in e.fields.items(): print(f"{k}={v}")
   raise SystemExit(65)
 argv += strip_leading_separator(a.adapter_args); raise SystemExit(subprocess.run(argv).returncode)
if __name__=="__main__": main()
