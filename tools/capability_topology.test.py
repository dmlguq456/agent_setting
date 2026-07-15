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
    def test_depth_and_resource_depth(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][0]["depth"]=3; self.assertRaises(T.TopologyError,T.validate_registry,r)
        r=copy.deepcopy(self.r); lab=next(x for x in r["recipes"] if x["capability"]=="autopilot-lab"); lab["standard_plus"]["nodes"][-1]["depth"]=2; self.assertRaises(T.TopologyError,T.validate_registry,r)
    def test_reviewer_and_map_scopes(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["standard_plus"]["nodes"][1]["write_scope"]=["source/**"]; self.assertRaises(T.TopologyError,T.validate_registry,r)
        r=copy.deepcopy(self.r); d=next(x for x in r["recipes"] if x["capability"]=="autopilot-design"); d["standard_plus"]["nodes"][0]["write_scope"]=["design/**"]; self.assertRaises(T.TopologyError,T.validate_registry,r)
    def test_concurrent_overlap(self):
        r=copy.deepcopy(self.r); d=next(x for x in r["recipes"] if x["capability"]=="autopilot-design"); d["standard_plus"]["nodes"][1]["depends_on"]=[]; d["standard_plus"]["nodes"][1]["write_scope"]=["shards/refs/**"]; self.assertRaisesRegex(T.TopologyError,"overlap",T.validate_registry,r)

if __name__ == "__main__": unittest.main()
