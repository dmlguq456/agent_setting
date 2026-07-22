#!/usr/bin/env python3
import copy, importlib.util, json, unittest
from pathlib import Path

P = Path(__file__).with_name("capability_topology.py")
S = importlib.util.spec_from_file_location("topology", P); T = importlib.util.module_from_spec(S); S.loader.exec_module(T)

class TestTopology(unittest.TestCase):
    def setUp(self): self.r = T.load_registry()
    def test_exact_coverage_and_digest(self):
        result = T.validate_registry(self.r); self.assertEqual((10, 22), (result["capabilities"], result["recipes"])); self.assertEqual(T.registry_digest(self.r), T.registry_digest(json.loads(json.dumps(self.r, sort_keys=True))))
    def test_missing_coverage(self):
        r=copy.deepcopy(self.r); r["recipes"].pop(); self.assertRaises(T.TopologyError, T.validate_registry, r)
    def test_cycle(self):
        r=copy.deepcopy(self.r); n=r["recipes"][0]["standard_plus"]["nodes"]; n[0]["depends_on"]=[n[-1]["id"]]; self.assertRaisesRegex(T.TopologyError,"cycle",T.validate_registry,r)
    def test_dispatch_depth_and_resource_boundary(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["dispatch_depth"]=3; self.assertRaises(T.TopologyError,T.validate_registry,r)
        r=copy.deepcopy(self.r); lab=next(x for x in r["recipes"] if x["capability"]=="autopilot-lab"); lab["standard_plus"]["nodes"][-1]["dispatch_depth"]=2; self.assertRaises(T.TopologyError,T.validate_registry,r)
    def test_every_bare_depth_key_and_wrong_max_are_rejected(self):
        for location in ("recipe","quick","standard_plus","node"):
            for key in ("depth","owner_depth","max_depth"):
                r=copy.deepcopy(self.r); recipe=r["recipes"][0]
                target={
                    "recipe":recipe,
                    "quick":recipe["quick"],
                    "standard_plus":recipe["standard_plus"],
                    "node":recipe["standard_plus"]["nodes"][0],
                }[location]
                target[key]=2
                with self.subTest(location=location,key=key):
                    self.assertRaises(T.TopologyError,T.validate_registry,r)
        r=copy.deepcopy(self.r)
        r["recipes"][0]["standard_plus"]["max_dispatch_depth"]=1
        self.assertRaisesRegex(T.TopologyError,"max_dispatch_depth",T.validate_registry,r)
    def test_namespace_vocabularies_fail_closed(self):
        r=copy.deepcopy(self.r); r["execution_surfaces"].append("mystery")
        self.assertRaisesRegex(T.TopologyError,"execution-surface",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["fallback_hops"]=["mystery"]
        self.assertRaisesRegex(T.TopologyError,"fallback hops",T.validate_registry,r)
    def test_reviewer_and_map_scopes(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][1]["write_scope"]=["source/**"]; self.assertRaises(T.TopologyError,T.validate_registry,r)
        r=copy.deepcopy(self.r); d=next(x for x in r["recipes"] if x["capability"]=="autopilot-design"); d["standard_plus"]["nodes"][0]["write_scope"]=["design/**"]; self.assertRaises(T.TopologyError,T.validate_registry,r)
    def test_concurrent_overlap(self):
        r=copy.deepcopy(self.r); d=next(x for x in r["recipes"] if x["capability"]=="autopilot-design"); d["standard_plus"]["nodes"][1]["depends_on"]=[]; d["standard_plus"]["nodes"][1]["write_scope"]=["shards/refs/**"]; self.assertRaisesRegex(T.TopologyError,"overlap",T.validate_registry,r)
    def test_spec_scope_requires_owner_or_precondition(self):
        r=copy.deepcopy(self.r); code=next(x for x in r["recipes"] if x["capability"]=="autopilot-code")
        execute=next(n for n in code["standard_plus"]["nodes"] if n["id"]=="execute")
        execute["write_scope"]=["spec/**"]
        self.assertRaisesRegex(T.TopologyError,"spec write scope requires",T.validate_registry,r)
        execute["guard_preconditions"]=["artifact-order-prechecked"]
        T.validate_registry(r)
    def test_tracking_and_rollout_schema_fail_closed(self):
        r=copy.deepcopy(self.r); r["tracking_values"]=["tracked"]
        self.assertRaisesRegex(T.TopologyError,"tracking_values",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["rollout"]["route_compiler"]="report-only"
        self.assertRaisesRegex(T.TopologyError,"enforced",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["rollout"]["legacy_low_level_dispatch"]=True
        self.assertRaisesRegex(T.TopologyError,"retired",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["schema_version"]=2
        self.assertRaisesRegex(T.TopologyError,"read-only",T.validate_registry,r)
    def test_unknown_unit_ref_fails_closed(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["unit"]="dev/does-not-exist"
        self.assertRaisesRegex(T.TopologyError,"unknown unit",T.validate_registry,r)
        r=copy.deepcopy(self.r); del r["recipes"][0]["standard_plus"]["nodes"][0]["unit"]
        self.assertRaisesRegex(T.TopologyError,"unit ref required",T.validate_registry,r)
    def test_kind_worker_type_mismatch(self):
        r=copy.deepcopy(self.r); verify=r["recipes"][0]["standard_plus"]["nodes"][1]
        self.assertEqual(verify["kind"],"review-worker")
        verify["unit"]="dev/backend"; verify["role"]="fast implementer"
        self.assertRaisesRegex(T.TopologyError,"incompatible",T.validate_registry,r)
    def test_node_role_must_match_unit_role(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["role"]="deep maker"
        self.assertRaisesRegex(T.TopologyError,"differs from",T.validate_registry,r)
    def test_reserved_unit_pins(self):
        r=copy.deepcopy(self.r); handback=r["recipes"][0]["standard_plus"]["nodes"][2]
        self.assertEqual(handback["kind"],"capability-owner")
        handback["unit"]="qa/code-review"
        self.assertRaisesRegex(T.TopologyError,"reserved unit",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["unit"]="_kernel/owner"
        self.assertRaisesRegex(T.TopologyError,"reserved unit",T.validate_registry,r)
    def test_review_worker_requires_read_only_unit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)/"qa"; fake.mkdir()
            (fake/"fake.md").write_text(
                "---\nunit: qa/fake\nrole: fast reviewer\nworker_type: review\nread_only: false\n---\nbody\n",
                encoding="utf-8")
            old=T.UNITS; T.UNITS=Path(td); T._UNIT_CACHE.clear()
            try:
                node={"id":"x","kind":"review-worker","role":"fast reviewer","unit":"qa/fake"}
                with self.assertRaisesRegex(T.TopologyError,"read_only"):
                    T._validate_unit_ref({"capability":"t"},node,self.r)
            finally:
                T.UNITS=old; T._UNIT_CACHE.clear()
    def test_replication_declared_on_review_nodes(self):
        code=next(x for x in self.r["recipes"] if x["capability"]=="autopilot-code")
        self.assertEqual(code["standard_plus"]["replication"],
            {"node":"impl-review","min_intensity":"strong","ways":2,"independence_axis":"cross-harness"})
        note=next(x for x in self.r["recipes"] if x["capability"]=="autopilot-note")
        self.assertNotIn("replication",note["standard_plus"])
    def test_replication_validation_fails_closed(self):
        def broken(mutate):
            r=copy.deepcopy(self.r)
            code=next(x for x in r["recipes"] if x["capability"]=="autopilot-code")
            mutate(code["standard_plus"]["replication"])
            return r
        cases={
            "not in graph": lambda rep: rep.update(node="missing-node"),
            "must be a review-worker": lambda rep: rep.update(node="execute"),
            "standard\\+ tier": lambda rep: rep.update(min_intensity="quick"),
            "ways must be 2": lambda rep: rep.update(ways=3),
            "independence_axis must be cross-harness": lambda rep: rep.update(independence_axis="same-harness"),
            "requires exactly": lambda rep: rep.update(extra=True),
        }
        for pattern,mutate in cases.items():
            with self.subTest(pattern=pattern):
                self.assertRaisesRegex(T.TopologyError,pattern,T.validate_registry,broken(mutate))
    def test_gate_contract_missing_entry(self):
        r=copy.deepcopy(self.r); del r["completion_gate_contracts"]["apply-hash"]
        self.assertRaisesRegex(T.TopologyError,"completion_gate_contracts entry",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["completion_gate_contracts"]["apply-verify"]["unit"]="qa/test"
        self.assertRaisesRegex(T.TopologyError,"carrying node's unit",T.validate_registry,r)
    def test_unit_choices_membership(self):
        r=copy.deepcopy(self.r); code=next(x for x in r["recipes"] if x["capability"]=="autopilot-code")
        execute=next(n for n in code["standard_plus"]["nodes"] if n["id"]=="execute")
        execute["unit_choices"]=[c for c in execute["unit_choices"] if c!=execute["unit"]]
        self.assertRaisesRegex(T.TopologyError,"unit_choices",T.validate_registry,r)

if __name__ == "__main__": unittest.main()
