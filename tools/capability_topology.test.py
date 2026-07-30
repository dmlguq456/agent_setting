#!/usr/bin/env python3
import copy, hashlib, importlib.util, json, unittest
from pathlib import Path

P = Path(__file__).with_name("capability_topology.py")
S = importlib.util.spec_from_file_location("topology", P); T = importlib.util.module_from_spec(S); S.loader.exec_module(T)

PRESERVED_FULL_FIELD_DIGESTS = {
    ("autopilot-apply", ("default",)): (
        "8a9f8b6ed8947359dde0f5c524a08fbcd023ad517f50b01d4e9bc778a00ba240",
        "ef01f5c116d199aaee0f86d845921face1f7a7a5095ac73d30ad9a40d4b0233f",
    ),
    ("autopilot-code", ("audit", "debug", "dev")): (
        "3307317d2c647620e4408870a08d8a293a2c2649c37baf2cf7418221b44c0fbf",
        "1eb37bfd5ab71fc7e9edc437503624f991cc585d7806dc46af7e2910911fb9f4",
    ),
    ("autopilot-design", ("default",)): (
        "c6436bab0cc4e1262be118f17d2b24f435984d68f5704a26ca55d7a75fa6a2a9",
        "55e3c44a67bba7579e3805464b8ba464951c9edc2cb05356aa696bfcb864281b",
    ),
    ("autopilot-draft", ("doc", "paper", "presentation")): (
        "2ff4688c5963ba0a63d21acfeed0f762503142187597aa5d1744e858193bc8d3",
        "24338ba81e05c0bc6ccad3ee5af02dfb9a1ec6b49dbd9e2302ae49147296ce13",
    ),
    ("autopilot-lab", ("setup",)): (
        "0afe453d9d0373f932b0cdf9ef4606581de132f1a6c665f49c61b1aa9c04d5a2",
        "9a26c0fea9a635d94f784379941c90a25d35ad7d2bcf1c3f21a1fcd5fad57183",
    ),
    ("autopilot-lab", ("eval",)): (
        "f5b459f6ff8fa7cbd7c83e220504b157cccd33dffbf58d63ebc70efd2bb038ad",
        "47160a6d9acf73cf29ff137dcb90c1af3036148530af2a1628162692078f1e24",
    ),
    ("autopilot-note", ("default",)): (
        "d53f04455ec719c1a10fe096e6c6a3a7d91b6bc1b48773819b624d7c9fff5e03",
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    ),
    ("autopilot-refine", ("default",)): (
        "e94e06c314ace9bd06b4acb705811af9d179acaa331ef628138c1f2376d3c91b",
        "d39b4446e7c7fca7def4629560d9ee10a342b536fa644ffee8023c5f06326203",
    ),
    ("autopilot-research", ("academic", "market", "technology")): (
        "786e54143e67bb126a2d8459c2bb66ca284562a51f27fc65463de14552d29621",
        "1c314d9a1c578256757109a35b0f08548d22391b3f079df0a790fe3534bfc057",
    ),
    ("autopilot-ship", ("default",)): (
        "2b26f9570e5e09a0bae0d7a58eb03133638e062a5edba3cd1a000e38d70512ca",
        "57f7c9ab1e362f246f0056927122c19163479334380cf84ab9a8785e620dcbf4",
    ),
    ("autopilot-spec", ("api", "app", "cli", "library", "research", "update")): (
        "fc9d3fc4daec7b5ce38a313c807db844d3ad437a77df9287de189b9e2085394e",
        "8b421239d9a414c5d0ce1b91e9314ceee13b9fa9ac075d374fb92eb59e8437af",
    ),
}


def full_field_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


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
        r=copy.deepcopy(self.r); d=next(x for x in r["recipes"] if x["capability"]=="autopilot-design"); critic=next(n for n in d["standard_plus"]["nodes"] if n["id"]=="critic-review"); critic["depends_on"]=[]; critic["write_scope"]=["reviews/visual/verify/**"]; self.assertRaisesRegex(T.TopologyError,"overlap",T.validate_registry,r)
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
        for legacy in (2,3,4,5):
            r=copy.deepcopy(self.r); r["schema_version"]=legacy
            self.assertRaisesRegex(T.TopologyError,"read-only",T.validate_registry,r)
    def test_conditional_note_follow_up_coverage(self):
        expected={
            ("autopilot-code",("audit","debug","dev")):("report","report","final_report.md"),
            ("autopilot-draft",("doc","paper","presentation")):("finalize","finalize","final-artifact"),
            ("autopilot-lab",("setup",)):("full-run","full-run","experiment-artifact"),
            ("autopilot-lab",("eval",)):("sync","report","experiment-artifact"),
            ("autopilot-refine",("default",)):("transaction","transaction","revised-artifact"),
            ("autopilot-research",("academic","market","technology")):("claim-verify","report","research-artifact"),
        }
        observed={}
        for recipe in self.r["recipes"]:
            rows=recipe.get("conditional_follow_ups",[])
            if not rows: continue
            self.assertEqual(len(rows),1)
            row=rows[0]; source=row["source_outputs"][0]
            observed[(recipe["capability"],tuple(recipe["modes"]))]=(
                row["after"][0],source["node"],source["output"])
            self.assertEqual(row["activation_condition"],"agent-note-db-connected")
            self.assertEqual(row["on_unavailable"],"skip")
        self.assertEqual(observed,expected)
    def test_conditional_follow_up_validation_fails_closed(self):
        def code_recipe(registry):
            return next(x for x in registry["recipes"] if x["capability"]=="autopilot-code")
        r=copy.deepcopy(self.r); code_recipe(r)["conditional_follow_ups"][0]["activation_condition"]="mystery"
        self.assertRaisesRegex(T.TopologyError,"unknown activation",T.validate_registry,r)
        r=copy.deepcopy(self.r); code_recipe(r)["conditional_follow_ups"][0]["after"]=["execute"]
        self.assertRaisesRegex(T.TopologyError,"terminal nodes",T.validate_registry,r)
        r=copy.deepcopy(self.r); code_recipe(r)["conditional_follow_ups"][0]["source_outputs"][0]["output"]="missing.md"
        self.assertRaisesRegex(T.TopologyError,"not declared",T.validate_registry,r)
        r=copy.deepcopy(self.r); code_recipe(r)["conditional_follow_ups"][0]["capability"]="autopilot-code"
        self.assertRaisesRegex(T.TopologyError,"non-self",T.validate_registry,r)
        r=copy.deepcopy(self.r); code_recipe(r)["conditional_follow_ups"][0]["on_unavailable"]="fail"
        self.assertRaisesRegex(T.TopologyError,"must be skip",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["activation_conditions"]["agent-note-db-connected"]["success_state"]="configured"
        self.assertRaisesRegex(T.TopologyError,"activation contract mismatch",T.validate_registry,r)
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
    def test_parallel_group_declarations(self):
        code=next(x for x in self.r["recipes"] if x["capability"]=="autopilot-code")
        groups=code["standard_plus"]["parallel_groups"]
        self.assertEqual([g["id"] for g in groups],["frame","plan","impl-review"])
        self.assertEqual(groups[0]["width_by_intensity"],{
            "standard":2,"strong":3,"thorough":3,"adversarial":3})
        self.assertEqual(groups[1]["width_by_intensity"],{
            "strong":2,"thorough":3,"adversarial":3})
        self.assertEqual(groups[2]["width_by_intensity"],{
            "strong":2,"thorough":3,"adversarial":3})
        for group in groups:
            self.assertEqual(group["join_policy"],"all")
            self.assertEqual(group["independence_axes"],["cross-harness","model-profile","perspective"])
            self.assertEqual(group["legs"][0]["suffix"],"anchor")
        # Framing anchors (2-way from standard) exist exactly on the generative
        # recipes whose direction is set in-pipeline; prescriptive/bounded
        # recipes keep review-only strong anchors (user directive 2026-07-24).
        framing={"autopilot-code":"frame","autopilot-spec":"research","autopilot-draft":"material-strategy",
                 "autopilot-design":"refs","autopilot-research":"retrieval"}
        for recipe in self.r["recipes"]:
            anchors=recipe["standard_plus"].get("parallel_groups",[])
            standard_anchors=[a["node"] for a in anchors if a["min_intensity"]=="standard"]
            expected=framing.get(recipe["capability"])
            with self.subTest(capability=recipe["capability"],modes=recipe["modes"]):
                self.assertNotIn("replications",recipe["standard_plus"])
                self.assertEqual(standard_anchors,[expected] if expected else [])
        note=next(x for x in self.r["recipes"] if x["capability"]=="autopilot-note")
        self.assertEqual(note["standard_plus"].get("parallel_groups",[]),[])
    def test_parallel_group_validation_fails_closed(self):
        def broken(mutate,capability="autopilot-code"):
            r=copy.deepcopy(self.r)
            recipe=next(x for x in r["recipes"] if x["capability"]==capability)
            mutate(recipe["standard_plus"])
            return r
        def legacy_singular(g): g["replication"]=g.pop("parallel_groups")[2]
        code_cases={
            "legacy replication keys": legacy_singular,
            "non-empty list": lambda g: g.update(parallel_groups=[]),
            "require exactly": lambda g: g["parallel_groups"][2].update(extra=True),
            "duplicate parallel group/anchor": lambda g: g["parallel_groups"].append(dict(g["parallel_groups"][0])),
            "not in graph": lambda g: g["parallel_groups"][2].update(node="missing-node"),
            "requires a downstream consumer": lambda g: g["parallel_groups"][0].update(node="report"),
            "requires a direct review arbiter": lambda g: g["parallel_groups"][0].update(node="test"),
            "standard\\+ tier": lambda g: g["parallel_groups"][2].update(min_intensity="quick"),
            "widths must be monotonic integers": lambda g: g["parallel_groups"][2]["width_by_intensity"].update(strong=5),
            "cross-harness axis required":
                lambda g: g["parallel_groups"][2].update(independence_axes=["model-profile","perspective"]),
        }
        for pattern,mutate in code_cases.items():
            with self.subTest(pattern=pattern):
                self.assertRaisesRegex(T.TopologyError,pattern,T.validate_registry,broken(mutate))
        # kind vocabulary: a capability-owner node can never anchor a parallel group
        r=broken(lambda g: g["parallel_groups"][0].update(node="handback"),capability="autopilot-apply")
        self.assertRaisesRegex(T.TopologyError,"review, map, or pipeline worker",
            T.validate_registry,r)
        # anchor output shape: concrete files for stage anchors, '<dir>/**' only for map anchors
        r=broken(lambda g: next(n for n in g["nodes"] if n["id"]=="plan").update(outputs=["plan/**"]))
        self.assertRaisesRegex(T.TopologyError,"concrete",T.validate_registry,r)
        r=broken(lambda g: next(n for n in g["nodes"] if n["id"]=="research").update(
            outputs=["shards/spec-*/**"]),capability="autopilot-spec")
        self.assertRaisesRegex(T.TopologyError,"concrete",T.validate_registry,r)
    def test_registered_nodes_reject_mini_profile(self):
        r=copy.deepcopy(self.r)
        r["recipes"][0]["standard_plus"]["nodes"][0]["model_profile"]="mini"
        self.assertRaisesRegex(T.TopologyError,"mini/unregistered",T.validate_registry,r)
    def test_owner_profile_policy_and_semantic_owner_census(self):
        self.assertEqual(self.r["owner_profile_by_intensity"], {
            "quick": "balanced-deep", "standard": "deep", "strong": "deep",
            "thorough": "deep", "adversarial": "deep",
        })
        expected = {
            ("autopilot-apply", ("default",)): ["handback"],
            ("autopilot-lab", ("eval",)): ["sync"],
            ("autopilot-note", ("default",)): ["route-apply"],
            ("autopilot-refine", ("default",)): ["transaction"],
            ("autopilot-ship", ("default",)): ["release-setup"],
            ("autopilot-spec", ("api", "app", "cli", "library", "research", "update")): [
                "prd-transaction"
            ],
        }
        observed = {}
        for recipe in self.r["recipes"]:
            key = (recipe["capability"], tuple(recipe["modes"]))
            self.assertEqual(recipe["quick"]["model_profile"], "balanced-deep")
            owners = [
                node for node in recipe["standard_plus"]["nodes"]
                if node.get("kind") == "capability-owner"
                and node.get("unit") == "_kernel/owner"
            ]
            if owners:
                observed[key] = [node["id"] for node in owners]
            for node in owners:
                self.assertEqual(node["dispatch_depth"], 1)
                self.assertEqual(node["model_profile"], "deep")
                self.assertEqual(node["role"], "deep orchestrator")
        self.assertEqual(observed, expected)
    def test_owner_profile_policy_drift_fails_closed(self):
        r=copy.deepcopy(self.r); r["recipes"][0]["quick"]["model_profile"]="light"
        self.assertRaisesRegex(T.TopologyError,"must match",T.validate_registry,r)
        r=copy.deepcopy(self.r); r["owner_profile_by_intensity"]["strong"]="balanced-deep"
        self.assertRaisesRegex(T.TopologyError,"must be uniform",T.validate_registry,r)
        r=copy.deepcopy(self.r); owner=r["recipes"][0]["standard_plus"]["nodes"][2]
        owner["model_profile"]="balanced-deep"
        self.assertRaisesRegex(T.TopologyError,"semantic capability owner",T.validate_registry,r)
        r=copy.deepcopy(self.r); owner=r["recipes"][0]["standard_plus"]["nodes"][2]
        owner["dispatch_depth"]=2
        self.assertRaisesRegex(T.TopologyError,"semantic capability owner",T.validate_registry,r)
        r=copy.deepcopy(self.r); owner=r["recipes"][0]["standard_plus"]["nodes"][2]
        owner["role"]="deep maker"
        self.assertRaisesRegex(T.TopologyError,"reserved unit",T.validate_registry,r)
    def test_non_owner_nodes_and_parallel_groups_match_frozen_full_field_census(self):
        observed = {}
        for recipe in self.r["recipes"]:
            key = (recipe["capability"], tuple(recipe["modes"]))
            non_owners = [
                node for node in recipe["standard_plus"]["nodes"]
                if not (
                    node.get("kind") == "capability-owner"
                    and node.get("unit") == "_kernel/owner"
                )
            ]
            groups = recipe["standard_plus"].get("parallel_groups", [])
            observed[key] = (
                full_field_digest(non_owners),
                full_field_digest(groups),
            )
        self.assertEqual(observed, PRESERVED_FULL_FIELD_DIGESTS)
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
