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
import re
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "harness-manifest.json"
MANIFEST_PATH = ROOT / MANIFEST_NAME
SCHEMA_VERSION = 3
UNIT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")
UNIT_WORKER_TYPES = {"owner", "stage", "review", "support"}
UNIT_FLOORS = {"near-zero", "low", "moderate", "high", "highest"}
INVOCATION_CLASSES = {
    "entry-router",
    "model-support",
    "parent-invoked",
    "user-only",
}
GENERIC_INVOCATION_PHRASES = (
    "use when needed",
    "use when invoking the portable",
)
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "product",
    "capabilities",
    "units",
    "modes",
    "packs",
    "profiles",
    "kernel",
    "ownership",
}
UNIT_FIELDS = ("family", "role", "worker_type", "floor")


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


def _unit_frontmatter(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    _expect(raw.startswith("---"), f"unit file missing frontmatter: {path}")
    parts = raw.split("---", 2)
    _expect(len(parts) >= 3, f"unit file frontmatter unterminated: {path}")
    return parts[1]


def _frontmatter_scalar(frontmatter: str, key: str) -> str:
    match = re.search(r"(?m)^%s:[ \t]*(.+?)[ \t]*$" % re.escape(key), frontmatter)
    if not match:
        return ""
    value = re.sub(r"[ \t]+#.*$", "", match.group(1)).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
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
    units = _expect_sorted_mapping(data["units"], "units")
    modes = _expect_sorted_mapping(data["modes"], "modes")
    packs = _expect_sorted_mapping(data["packs"], "packs")
    profiles = _expect_sorted_mapping(data["profiles"], "profiles")
    _expect(capabilities, "capabilities cannot be empty")
    _expect(units, "units cannot be empty")
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
        _expect(set(spec) == {
                    "group", "family", "modes", "summary", "invocation",
                    "argument_shape", "requires",
                },
                f"capability {identifier} fields do not match schema")
        for field in ("group", "family", "summary", "argument_shape"):
            _expect(isinstance(spec[field], str), f"capability {identifier}.{field} must be a string")
        _expect_string_list(spec["modes"], f"capability {identifier}.modes")
        invocation = spec["invocation"]
        _expect(
            isinstance(invocation, dict)
            and set(invocation) == {"class", "use_when", "not_for"},
            f"capability {identifier}.invocation fields do not match schema",
        )
        invocation_class = invocation["class"]
        use_when = invocation["use_when"]
        not_for = invocation["not_for"]
        _expect(invocation_class in INVOCATION_CLASSES,
                f"capability {identifier} has invalid invocation class {invocation_class}")
        _expect(isinstance(use_when, str) and use_when,
                f"capability {identifier}.invocation.use_when must be a non-empty string")
        _expect(isinstance(not_for, str) and not_for,
                f"capability {identifier}.invocation.not_for must be a non-empty string")
        lowered = f"{use_when} {not_for}".lower()
        _expect(not any(phrase in lowered for phrase in GENERIC_INVOCATION_PHRASES),
                f"capability {identifier} uses a generic or circular invocation trigger")
        _expect(not_for.startswith("Not for "),
                f"capability {identifier}.invocation.not_for must start with 'Not for '")
        if invocation_class == "entry-router":
            _expect(use_when.startswith("Use when "),
                    f"entry-router {identifier} use_when must start with 'Use when '")
            _expect((root / "capabilities" / f"{identifier}.md").is_file(),
                    f"entry-router {identifier} must declare a portable owner contract")
        elif invocation_class == "parent-invoked":
            _expect(use_when.startswith("Use only when "),
                    f"parent-invoked {identifier} use_when must start with 'Use only when '")
            _expect("top-level" in not_for.lower(),
                    f"parent-invoked {identifier} must exclude top-level routing")
        elif invocation_class == "model-support":
            _expect(use_when.startswith("Use when "),
                    f"model-support {identifier} use_when must start with 'Use when '")
            _expect("primary" in not_for.lower(),
                    f"model-support {identifier} must exclude primary routing")
        requires = spec["requires"]
        _expect(isinstance(requires, dict) and set(requires) == {"capabilities", "units"},
                f"capability {identifier}.requires fields do not match schema")
        capability_graph[identifier] = _expect_string_list(
            requires["capabilities"], f"capability {identifier}.requires.capabilities"
        )
        required_units = _expect_string_list(requires["units"], f"capability {identifier}.requires.units")
        for unit in required_units:
            _expect(unit in units, f"capability {identifier} references unknown unit {unit}")
        _expect((root / "capabilities" / f"{identifier}.md").is_file(),
                f"capability source missing: capabilities/{identifier}.md")
    for identifier in capabilities:
        _closure([identifier], capability_graph, "capability")
    discovered_capabilities = {
        path.stem for path in (root / "capabilities").glob("*.md") if path.name != "README.md"
    }
    _expect(discovered_capabilities == set(capabilities),
            "capability source set differs from canonical manifest")
    _expect(any(spec["invocation"]["class"] == "entry-router" for spec in capabilities.values()),
            "at least one entry-router capability is required")

    for unit, spec in units.items():
        _expect(bool(UNIT_ID_PATTERN.match(unit)), f"unit {unit} id must look like <family>/<name>")
        _expect(isinstance(spec, dict) and set(spec) == set(UNIT_FIELDS),
                f"unit {unit} fields do not match schema")
        _expect(all(isinstance(spec[field], str) and spec[field] for field in UNIT_FIELDS),
                f"unit {unit} fields must be non-empty strings")
        _expect(spec["family"] == unit.split("/", 1)[0],
                f"unit {unit} family must equal its id prefix")
        _expect(spec["worker_type"] in UNIT_WORKER_TYPES, f"unit {unit} has invalid worker_type")
        _expect(spec["floor"] in UNIT_FLOORS, f"unit {unit} has invalid floor")
        source = root / "roles" / "units" / f"{unit}.md"
        _expect(source.is_file(), f"unit source missing: roles/units/{unit}.md")
        frontmatter = _unit_frontmatter(source)
        for field in UNIT_FIELDS:
            declared = _frontmatter_scalar(frontmatter, field)
            _expect(declared == spec[field],
                    f"unit {unit}.{field} drifted from catalog frontmatter "
                    f"({spec[field]!r} != {declared!r})")
    discovered_units = {
        path.parent.name + "/" + path.stem
        for path in (root / "roles" / "units").glob("*/*.md")
        if not path.parent.name.startswith("_") and not path.name.startswith("_")
    }
    _expect(discovered_units == set(units), "unit catalog set differs from canonical manifest")

    for mode, spec in modes.items():
        _expect(isinstance(spec, dict), f"mode {mode} must be an object")
        _expect(set(spec).issubset({"unit", "status", "internal"}) and "status" in spec,
                f"mode {mode} fields do not match schema")
        if "unit" in spec:
            _expect(spec["unit"] in units, f"mode {mode} references unknown unit {spec['unit']}")
        else:
            _expect(spec.get("internal") is True,
                    f"mode {mode} must reference a unit unless marked internal")
        _expect(spec["status"] in {"portable-persona", "portable-with-tool-contract", "adapter-coupled"},
                f"mode {mode} has invalid status")
        if "unit" in spec:
            _expect((root / "roles" / "units" / f"{spec['unit']}.md").is_file(),
                    f"mode source missing: roles/units/{spec['unit']}.md")
    discovered_units = {
        path.relative_to(root / "roles" / "units").with_suffix("").as_posix()
        for path in (root / "roles" / "units").glob("*/*.md")
        if not path.name.startswith("_") and not path.parent.name.startswith("_")
    }
    _expect(discovered_units == set(units), "unit catalog set differs from canonical manifest")

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
        _expect(set(spec).issubset({"summary", "packs", "units"}) and {"summary", "packs"} <= set(spec),
                f"profile {profile} fields do not match schema")
        _expect(isinstance(spec["summary"], str) and spec["summary"], f"profile {profile}.summary required")
        for pack in _expect_string_list(spec["packs"], f"profile {profile}.packs"):
            _expect(pack in packs, f"profile {profile} references unknown pack {pack}")
        for unit in _expect_string_list(spec.get("units", []), f"profile {profile}.units"):
            _expect(unit in units, f"profile {profile} references unknown unit {unit}")

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
    _expect(set(full["units"]) == set(units), "full profile must expose every catalog unit")
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

    units = set(profiles[name].get("units", []))
    for identifier in capabilities:
        units.update(data["capabilities"][identifier]["requires"]["units"])
    families = {unit.split("/", 1)[0] for unit in units}
    roles = {data["units"][unit]["role"] for unit in units}
    modes = sorted(
        mode for mode, spec in data["modes"].items()
        if (spec["unit"] in units if "unit" in spec else mode.split("/", 1)[0] in families)
    )
    payload = {
        "name": name,
        "packs": selected_packs,
        "capabilities": capabilities,
        "units": sorted(units),
        "roles": sorted(roles),
        "modes": modes,
        "kernel_agents": sorted(data["kernel"]["agents"]),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    payload["digest"] = hashlib.sha256(encoded).hexdigest()
    payload["counts"] = {
        "capabilities": len(capabilities),
        "units": len(units),
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
