#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PROFILE = load("portable_model_profile", ROOT / "utilities" / "model_profile.py")
WRAPPERS = {
    adapter: load(
        f"{adapter}_profile_wrapper",
        ROOT / "adapters" / adapter / "bin" / "dispatch-headless.py",
    )
    for adapter in ("claude", "codex", "opencode")
}


def args(adapter: str, profile: str, **overrides):
    budget_key = {"claude": "effort", "codex": "reasoning", "opencode": "variant"}[adapter]
    values = {
        "model_profile": profile,
        "registered_worker": 1,
        "dispatch_depth": 2,
        "worker_type": "stage",
        "inherit_model_settings": False,
        "model_role": "fast implementer",
        "model": None,
        budget_key: None,
        "capacity_retry": 0,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class ModelProfileTest(unittest.TestCase):
    def test_portable_profiles_resolve_to_declared_adapter_budgets(self):
        expected = {
            "claude": {
                "deep": ("opus", "xhigh"),
                "balanced-deep": ("opus", "medium"),
                "light": ("sonnet", "medium"),
            },
            "codex": {
                "deep": ("gpt-5.6-sol", "xhigh"),
                "balanced-deep": ("gpt-5.6-sol", "medium"),
                "light": ("gpt-5.6-luna", "medium"),
            },
            "opencode": {
                "deep": ("opencode-go/glm-5.2", "runtime-default"),
                "balanced-deep": ("opencode-go/glm-5.2", "runtime-default"),
                "light": ("opencode-go/deepseek-v4-pro", "runtime-default"),
            },
        }
        for adapter, profiles in expected.items():
            for profile, pair in profiles.items():
                with self.subTest(adapter=adapter, profile=profile):
                    resolved = PROFILE.resolve_profile(
                        adapter,
                        ROOT / "adapters" / adapter / "config" / "models.conf",
                        profile,
                    )
                    self.assertEqual((resolved["model"], resolved["budget"]), pair)

    def test_route_profile_is_primary_and_preserves_semantic_role(self):
        for adapter, wrapper in WRAPPERS.items():
            with self.subTest(adapter=adapter):
                resolved = wrapper.resolve_model_settings(args(adapter, "balanced-deep"))
                self.assertEqual(resolved["source"], "profile")
                self.assertEqual(resolved["role"], "fast implementer")
                self.assertEqual(resolved["profile"], "balanced-deep")
                self.assertNotEqual(resolved["model"], "inherit")

    def test_owner_profile_does_not_need_a_stage_role(self):
        for adapter, wrapper in WRAPPERS.items():
            with self.subTest(adapter=adapter):
                resolved = wrapper.resolve_model_settings(args(
                    adapter, "deep", dispatch_depth=1, worker_type="owner", model_role=None
                ))
                self.assertEqual(resolved["role"], "_kernel/owner")
                self.assertEqual(resolved["profile"], "deep")

    def test_mini_is_denied_for_registered_substantive_topology(self):
        for adapter, wrapper in WRAPPERS.items():
            with self.subTest(adapter=adapter), self.assertRaises(wrapper.ModelSelectionError) as caught:
                wrapper.resolve_model_settings(args(adapter, "mini"))
            self.assertEqual(caught.exception.reason, "invalid-dispatch-model-profile")

    def test_concrete_override_requires_checked_capacity_retry(self):
        cases = {
            "claude": {"model": "sonnet", "effort": "medium"},
            "codex": {"model": "gpt-5.6-luna", "reasoning": "medium"},
            "opencode": {"model": "opencode-go/deepseek-v4-pro", "variant": "runtime-default"},
        }
        for adapter, concrete in cases.items():
            wrapper = WRAPPERS[adapter]
            with self.subTest(adapter=adapter), self.assertRaises(wrapper.ModelSelectionError) as caught:
                wrapper.resolve_model_settings(args(adapter, "deep", **concrete))
            self.assertEqual(caught.exception.reason, "model-profile-override-forbidden")
            resolved = wrapper.resolve_model_settings(
                args(adapter, "deep", capacity_retry=1, **concrete)
            )
            self.assertEqual(resolved["source"], "profile+capacity")
            self.assertEqual(resolved["model"], concrete["model"])

    def test_opencode_deep_demotes_to_balanced_deep_with_typed_granularity(self):
        conf = ROOT / "adapters" / "opencode" / "config" / "models.conf"
        balanced = PROFILE.resolve_profile("opencode", conf, "balanced-deep")
        self.assertEqual(balanced["tier"], "balanced-deep")
        self.assertEqual(balanced["model"], "opencode-go/glm-5.2")
        self.assertEqual(balanced["granularity"], "exact")

        deep = PROFILE.resolve_profile("opencode", conf, "deep")
        self.assertEqual(deep["tier"], "balanced-deep")
        self.assertEqual(deep["model"], "opencode-go/glm-5.2")
        self.assertEqual(deep["granularity"], "deep-vacant-demoted-to-balanced-deep")

    def test_claude_codex_granularity_unaffected_by_per_profile_key(self):
        for adapter, expected in {"claude": "full", "codex": "full"}.items():
            conf = ROOT / "adapters" / adapter / "config" / "models.conf"
            for profile in ("deep", "balanced-deep"):
                with self.subTest(adapter=adapter, profile=profile):
                    resolved = PROFILE.resolve_profile(adapter, conf, profile)
                    self.assertEqual(resolved["granularity"], expected)

    def test_opencode_runtime_default_omits_unverified_variant_flag(self):
        wrapper = WRAPPERS["opencode"]
        resolved = wrapper.resolve_model_settings(args("opencode", "balanced-deep"))
        with tempfile.TemporaryDirectory() as temp_dir:
            command = wrapper.shell_command(
                argparse.Namespace(
                    resolved_model_settings=resolved,
                    worktree=temp_dir,
                    agent="build",
                ),
                Path(temp_dir) / "prompt.txt",
                Path(temp_dir) / "worker.log",
            )
        self.assertIn("--model", command)
        self.assertNotIn("--variant", command)


if __name__ == "__main__":
    unittest.main()
