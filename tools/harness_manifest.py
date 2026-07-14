#!/usr/bin/env python3
"""Canonical harness manifest loader, validator, and profile resolver.

`harness-manifest.json` owns portable product metadata. Runtime-specific
procedure bodies and fallbacks remain in their adapter sources; generated
catalogs and native projections consume this module instead of parsing one
another.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "harness-manifest.json"
MANIFEST_PATH = ROOT / MANIFEST_NAME
SCHEMA_VERSION = 1
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "product",
    "capabilities",
    "roles",
    "modes",
    "packs",
    "profiles",
    "kernel",
    "ownership",
}


class ManifestError(ValueError):
    """The canonical product manifest is missing or internally inconsistent."""


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _expect_string_list(value, field: str) -> list[str]:
    _expect(isinstance(value, list), f"{field} must be a list")
    _expect(all(isinstance(item, str) and item for item in value), f"{field} must contain strings")
    _expect(len(value) == len(set(value)), f"{field} contains duplicates")
    return value


def _expect_sorted_mapping(value, field: str) -> dict:
    _expect(isinstance(value, dict), f"{field} must be an object")
    keys = list(value)
    _expect(keys == sorted(keys), f"{field} keys must be sorted")
    return value


def _closure(start: Iterable[str], graph: dict[str, list[str]], kind: str) -> list[str]:
    result: set[str] = set()
    visiting: set[str] = set()

    def visit(item: str) -> None:
        _expect(item in graph, f"unknown {kind}: {item}")
        if item in result:
            return
        _expect(item not in visiting, f"{kind} dependency cycle at {item}")
        visiting.add(item)
        for dependency in graph[item]:
            visit(dependency)
        visiting.remove(item)
        result.add(item)

    for item in start:
        visit(item)
    return sorted(result)


def load(path: Path | str | None = None, *, validate_manifest: bool = True) -> dict:
    manifest_path = Path(path) if path is not None else MANIFEST_PATH
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"canonical manifest missing: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid canonical manifest JSON: {manifest_path}: {exc}") from exc
    _expect(isinstance(data, dict), "canonical manifest root must be an object")
    if validate_manifest:
        validate(data, manifest_path.parent)
    return data


def validate(data: dict, root: Path = ROOT) -> None:
    _expect(set(data) == REQUIRED_TOP_LEVEL, "canonical manifest top-level keys do not match schema")
    _expect(data["schema_version"] == SCHEMA_VERSION, f"unsupported schema_version: {data['schema_version']}")

    product = data["product"]
    _expect(isinstance(product, dict), "product must be an object")
    _expect(product.get("id") == "agent-harness", "product.id must be agent-harness")
    _expect(isinstance(product.get("manifest_version"), str), "product.manifest_version must be a string")
    runtimes = _expect_string_list(product.get("runtimes"), "product.runtimes")
    _expect(runtimes == ["claude", "codex", "opencode"], "product.runtimes must be sorted and complete")

    capabilities = _expect_sorted_mapping(data["capabilities"], "capabilities")
    roles = _expect_sorted_mapping(data["roles"], "roles")
    modes = _expect_sorted_mapping(data["modes"], "modes")
    packs = _expect_sorted_mapping(data["packs"], "packs")
    profiles = _expect_sorted_mapping(data["profiles"], "profiles")
    _expect(capabilities, "capabilities cannot be empty")
    _expect(roles, "roles cannot be empty")
    _expect(packs, "packs cannot be empty")
    _expect(set(profiles) == {"starter", "builder", "full"}, "profiles must be starter, builder, and full")
    _expect(product.get("default_profile") in profiles, "product.default_profile must name a profile")

    capability_graph: dict[str, list[str]] = {}
    for identifier, spec in capabilities.items():
        _expect(
            not identifier.startswith("external-"),
            f"capability {identifier} uses the reserved external extension prefix",
        )
        _expect(isinstance(spec, dict), f"capability {identifier} must be an object")
        _expect(set(spec) == {"group", "family", "modes", "summary", "argument_shape", "requires"},
                f"capability {identifier} fields do not match schema")
        for field in ("group", "family", "summary", "argument_shape"):
            _expect(isinstance(spec[field], str), f"capability {identifier}.{field} must be a string")
        _expect_string_list(spec["modes"], f"capability {identifier}.modes")
        requires = spec["requires"]
        _expect(isinstance(requires, dict) and set(requires) == {"capabilities", "roles"},
                f"capability {identifier}.requires fields do not match schema")
        capability_graph[identifier] = _expect_string_list(
            requires["capabilities"], f"capability {identifier}.requires.capabilities"
        )
        required_roles = _expect_string_list(requires["roles"], f"capability {identifier}.requires.roles")
        for role in required_roles:
            _expect(role in roles, f"capability {identifier} references unknown role {role}")
        _expect((root / "capabilities" / f"{identifier}.md").is_file(),
                f"capability source missing: capabilities/{identifier}.md")
    for identifier in capabilities:
        _closure([identifier], capability_graph, "capability")
    discovered_capabilities = {
        path.stem for path in (root / "capabilities").glob("*.md") if path.name != "README.md"
    }
    _expect(discovered_capabilities == set(capabilities),
            "capability source set differs from canonical manifest")

    for role, spec in roles.items():
        _expect(isinstance(spec, dict) and set(spec) == {"portable_role", "responsibility"},
                f"role {role} fields do not match schema")
        _expect(all(isinstance(spec[field], str) and spec[field] for field in spec),
                f"role {role} fields must be non-empty strings")

    for mode, spec in modes.items():
        _expect(isinstance(spec, dict), f"mode {mode} must be an object")
        _expect(set(spec).issubset({"role", "status", "internal"}) and {"role", "status"} <= set(spec),
                f"mode {mode} fields do not match schema")
        _expect(spec["role"] in roles, f"mode {mode} references unknown role {spec['role']}")
        _expect(spec["status"] in {"portable-persona", "portable-with-tool-contract", "adapter-coupled"},
                f"mode {mode} has invalid status")
        _expect((root / "roles" / "modes" / f"{mode}.md").is_file(),
                f"mode source missing: roles/modes/{mode}.md")
    discovered_modes = {
        path.relative_to(root / "roles" / "modes").with_suffix("").as_posix()
        for path in (root / "roles" / "modes").glob("*/*.md")
    }
    _expect(discovered_modes == set(modes), "mode source set differs from canonical manifest")

    pack_graph: dict[str, list[str]] = {}
    for pack, spec in packs.items():
        _expect(isinstance(spec, dict) and set(spec) == {"requires", "capabilities"},
                f"pack {pack} fields do not match schema")
        pack_graph[pack] = _expect_string_list(spec["requires"], f"pack {pack}.requires")
        pack_capabilities = _expect_string_list(spec["capabilities"], f"pack {pack}.capabilities")
        for identifier in pack_capabilities:
            _expect(identifier in capabilities, f"pack {pack} references unknown capability {identifier}")
    for pack in packs:
        _closure([pack], pack_graph, "pack")

    for profile, spec in profiles.items():
        _expect(isinstance(spec, dict), f"profile {profile} must be an object")
        _expect(set(spec).issubset({"summary", "packs", "roles"}) and {"summary", "packs"} <= set(spec),
                f"profile {profile} fields do not match schema")
        _expect(isinstance(spec["summary"], str) and spec["summary"], f"profile {profile}.summary required")
        for pack in _expect_string_list(spec["packs"], f"profile {profile}.packs"):
            _expect(pack in packs, f"profile {profile} references unknown pack {pack}")
        for role in _expect_string_list(spec.get("roles", []), f"profile {profile}.roles"):
            _expect(role in roles, f"profile {profile} references unknown role {role}")

    kernel = data["kernel"]
    _expect(isinstance(kernel, dict) and set(kernel) == {"always_on", "agents"},
            "kernel fields do not match schema")
    _expect_string_list(kernel["always_on"], "kernel.always_on")
    _expect_string_list(kernel["agents"], "kernel.agents")
    ownership = data["ownership"]
    _expect(isinstance(ownership, dict) and set(ownership) == {"generated", "adapter_owned"},
            "ownership fields do not match schema")
    _expect_string_list(ownership["generated"], "ownership.generated")
    _expect_string_list(ownership["adapter_owned"], "ownership.adapter_owned")

    full = resolve_profile(data, "full")
    _expect(set(full["capabilities"]) == set(capabilities), "full profile must expose every capability")
    _expect(set(full["roles"]) == set(roles), "full profile must expose every portable role")
    starter = resolve_profile(data, "starter")
    _expect(len(starter["capabilities"]) * 2 <= len(full["capabilities"]),
            "starter capability metadata must be at most 50% of full")


def resolve_profile(data: dict, profile: str | None = None) -> dict:
    profiles = data["profiles"]
    name = profile or data["product"]["default_profile"]
    _expect(name in profiles, f"unknown profile: {name}")

    pack_graph = {key: value["requires"] for key, value in data["packs"].items()}
    selected_packs = _closure(profiles[name]["packs"], pack_graph, "pack")
    capability_roots: list[str] = []
    for pack in selected_packs:
        capability_roots.extend(data["packs"][pack]["capabilities"])
    capability_graph = {
        key: value["requires"]["capabilities"] for key, value in data["capabilities"].items()
    }
    capabilities = _closure(capability_roots, capability_graph, "capability")

    roles = set(profiles[name].get("roles", []))
    for identifier in capabilities:
        roles.update(data["capabilities"][identifier]["requires"]["roles"])
    modes = sorted(mode for mode, spec in data["modes"].items() if spec["role"] in roles)
    payload = {
        "name": name,
        "packs": selected_packs,
        "capabilities": capabilities,
        "roles": sorted(roles),
        "modes": modes,
        "kernel_agents": sorted(data["kernel"]["agents"]),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    payload["digest"] = hashlib.sha256(encoded).hexdigest()
    payload["counts"] = {
        "capabilities": len(capabilities),
        "roles": len(roles),
        "modes": len(modes),
    }
    return payload


def profile_names(data: dict | None = None) -> tuple[str, ...]:
    manifest = data if data is not None else load()
    return tuple(sorted(manifest["profiles"]))


def default_profile(data: dict | None = None) -> str:
    manifest = data if data is not None else load()
    return manifest["product"]["default_profile"]


if __name__ == "__main__":
    manifest = load()
    print(json.dumps({name: resolve_profile(manifest, name) for name in profile_names(manifest)},
                     ensure_ascii=False, indent=2))
