"""Pure, production-disabled token-budget forecast and paired evaluator."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter, deque
from pathlib import Path
from typing import Any

from .token_budget import DIRECTIVE_TEXTS, directive_for_band, policy_band


CANDIDATE_ID = "offline-forecast-v1"
CONTRACT_VERSION = 1
EVALUATOR_VERSION = "token-budget-evaluator-v1"
ARMS = ("control", "static", "dynamic")
EXCLUSION_REASONS = (
    "missing_arm",
    "pairing_fingerprint_mismatch",
    "counter_unknown_or_degraded",
    "counter_decreased",
    "required_output_missing",
    "runner_failure",
    "rubric_missing_or_changed",
    "manifest_changed",
)
WORKLOAD_FIELDS = (
    "experiment_id", "workload_id", "stratum", "prompt_sha256",
    "artifact_bundle_sha256", "rubric_version", "rubric_sha256",
    "required_checks", "safety_checks", "model_id", "runtime_id",
    "runtime_config_sha256", "reasoning_effort", "intensity",
    "dispatch_depth", "qa_contract", "seed", "arm_order",
)
RESULT_FIELDS = (
    "experiment_id", "workload_id", "arm", "manifest_sha256",
    "config_fingerprint", "status", "exclusion_reason",
    "session_counter_status", "session_total_tokens_start",
    "session_total_tokens_end", "session_token_delta", "hook_invocations",
    "zero_injections", "emissions", "directive_utf8_bytes_total",
    "directive_exact_tokens", "exact_tokenizer_provenance",
    "required_checks_pass", "safety_checks_pass", "hard_regression",
    "quality_score", "quality_evaluator_id",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def candidate_code_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def fixture_set_sha256(replay_payload: Any) -> str:
    return canonical_sha256(replay_payload)


def manifest_sha256(manifest: dict[str, Any]) -> str:
    return canonical_sha256(manifest)


def config_fingerprint(declaration: dict[str, Any]) -> str:
    """Hash every frozen workload pairing field without copying prompt content."""

    return canonical_sha256({field: declaration.get(field) for field in WORKLOAD_FIELDS})


def validate_manifest(manifest: dict[str, Any], *, verify_code: bool = False) -> None:
    expected = {
        "contract_version": CONTRACT_VERSION,
        "candidate_id": CANDIDATE_ID,
        "tight_pct": 70,
        "critical_pct": 85,
        "history_window": 3,
        "forecast_step": "median_non_negative_context_pct_increment",
        "unknown_behavior": "static_equivalent_no_early_emission",
        "directive_ids": ["tight-v1", "critical-v1"],
        "quality_tolerance": 0.02,
        "minimum_complete_triplets": 30,
        "production_enabled": False,
    }
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"manifest field {key} is not frozen v1")
    if manifest.get("bootstrap") != {"resamples": 10000, "seed": 20260713}:
        raise ValueError("manifest bootstrap contract mismatch")
    for key in ("candidate_code_sha256", "fixture_set_sha256"):
        value = manifest.get(key)
        if not _is_sha256(value):
            raise ValueError(f"manifest {key} must be sha256")
    if verify_code and manifest["candidate_code_sha256"] != candidate_code_sha256():
        raise ValueError("candidate code hash mismatch")


def _pct(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 99:
        return float(value)
    return None


def _decision(directive_id: str | None, reason: str, observed_band: str,
              forecast_pct: float | None) -> dict[str, Any]:
    text = DIRECTIVE_TEXTS.get(directive_id, "")
    return {
        "directive_id": directive_id,
        "directive_utf8_bytes": len(text.encode("utf-8")),
        "reason": reason,
        "observed_band": observed_band,
        "forecast_pct": None if forecast_pct is None else round(forecast_pct, 6),
    }


def replay_policy(records: list[dict[str, Any]], manifest: dict[str, Any], *, arm: str) -> dict[str, Any]:
    """Replay control/static/frozen dynamic policy over content-free records."""

    validate_manifest(manifest)
    if arm not in ARMS:
        raise ValueError("unknown experiment arm")
    history: deque[float] = deque(maxlen=manifest["history_window"])
    previous_valid_pct: float | None = None
    previous_band = "normal"
    latched: set[str] = set()
    decisions = []

    for raw in records:
        if not isinstance(raw, dict):
            raise ValueError("replay record must be an object")
        pct = _pct(raw.get("context_used_pct"))
        status = raw.get("status", "observed")
        observed_band = policy_band(pct, manifest["tight_pct"], manifest["critical_pct"])
        static_signal = pct is not None
        valid = status == "observed" and pct is not None
        reset_after_decrease = False
        if valid and previous_valid_pct is not None:
            increment = pct - previous_valid_pct
            if increment < 0:
                valid = False
                reset_after_decrease = True
                history.clear()
            else:
                history.append(increment)
        forecast = None
        if valid and history:
            forecast = min(99.0, pct + statistics.median(history))

        if valid and forecast is not None:
            for band, threshold in (("tight", manifest["tight_pct"]),
                                    ("critical", manifest["critical_pct"])):
                if pct < threshold and forecast < threshold:
                    latched.discard(band)

        directive_id = None
        reason = "zero"
        static_transition = static_signal and observed_band in {"tight", "critical"} and observed_band != previous_band
        if arm == "control":
            reason = "control_zero"
        elif arm == "static":
            if static_transition:
                directive_id, _ = directive_for_band(observed_band)
                reason = "observed_transition"
        else:
            if not valid or forecast is None:
                if static_transition and observed_band not in latched:
                    directive_id, _ = directive_for_band(observed_band)
                    latched.add(observed_band)
                    reason = "observed_transition"
                elif static_transition:
                    reason = "episode_duplicate_suppressed"
                else:
                    reason = "unknown_or_insufficient_no_early_emission"
            else:
                targets = (("critical", manifest["critical_pct"]),
                           ("tight", manifest["tight_pct"]))
                for band, threshold in targets:
                    if pct < threshold <= forecast and band not in latched:
                        directive_id, _ = directive_for_band(band)
                        latched.add(band)
                        reason = "forecast_transition"
                        break
                if directive_id is None and static_transition:
                    if observed_band not in latched:
                        directive_id, _ = directive_for_band(observed_band)
                        latched.add(observed_band)
                        reason = "observed_transition"
                    else:
                        reason = "episode_duplicate_suppressed"
        decisions.append(_decision(directive_id, reason, observed_band, forecast))
        if static_signal:
            previous_band = observed_band
        if valid or reset_after_decrease:
            previous_valid_pct = pct

    return {
        "contract_version": CONTRACT_VERSION,
        "candidate_id": CANDIDATE_ID,
        "arm": arm,
        "decisions": decisions,
        "emissions": sum(item["directive_id"] is not None for item in decisions),
        "directive_utf8_bytes_total": sum(item["directive_utf8_bytes"] for item in decisions),
        "production_enabled": False,
    }


def replay_all(payload: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError("replay input requires records")
    return {
        "contract_version": CONTRACT_VERSION,
        "candidate_id": CANDIDATE_ID,
        "manifest_sha256": manifest_sha256(manifest),
        "input_sha256": canonical_sha256(payload),
        "arms": {arm: replay_policy(records, manifest, arm=arm) for arm in ARMS},
        "synthetic_non_evidentiary": bool(payload.get("synthetic_non_evidentiary", False)),
        "production_enabled": False,
    }


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_is_nonempty_string(item) for item in value)


def _valid_declaration_schema(value: dict[str, Any]) -> bool:
    if set(value) != set(WORKLOAD_FIELDS):
        return False
    string_fields = (
        "experiment_id", "workload_id", "stratum", "rubric_version",
        "model_id", "runtime_id", "reasoning_effort", "intensity",
        "qa_contract",
    )
    if not all(_is_nonempty_string(value.get(field)) for field in string_fields):
        return False
    if not all(_is_sha256(value.get(field)) for field in (
            "prompt_sha256", "artifact_bundle_sha256", "rubric_sha256",
            "runtime_config_sha256")):
        return False
    if not _is_string_list(value.get("required_checks")) or not _is_string_list(value.get("safety_checks")):
        return False
    if not _is_non_negative_int(value.get("dispatch_depth")):
        return False
    seed = value.get("seed")
    if seed is not None and not _is_non_negative_int(seed):
        return False
    order = value.get("arm_order")
    return isinstance(order, list) and len(order) == len(ARMS) and set(order) == set(ARMS)


def _valid_directive_accounting(emissions: int, directive_bytes: int) -> bool:
    """Require totals to be exactly representable by frozen directive payloads."""

    if emissions == 0:
        return directive_bytes == 0
    if directive_bytes <= 0 or directive_bytes > emissions * 240:
        return False
    lengths = sorted({len(text.encode("utf-8")) for text in DIRECTIVE_TEXTS.values()})
    if len(lengths) == 1:
        return directive_bytes == emissions * lengths[0]
    if len(lengths) != 2:
        return False
    low, high = lengths
    remainder = directive_bytes - emissions * low
    return 0 <= remainder <= emissions * (high - low) and remainder % (high - low) == 0


def _valid_tokenizer_provenance(value: Any) -> bool:
    return (_is_nonempty_string(value)
            and len(value.split("/")) >= 3
            and all(part.strip() for part in value.split("/")))


def _valid_complete_result_schema(value: dict[str, Any]) -> bool:
    if set(value) != set(RESULT_FIELDS):
        return False
    if value.get("status") != "complete" or value.get("exclusion_reason") is not None:
        return False
    if (not _is_nonempty_string(value.get("experiment_id"))
            or not _is_nonempty_string(value.get("workload_id"))
            or value.get("arm") not in ARMS
            or not _is_sha256(value.get("manifest_sha256"))
            or not _is_sha256(value.get("config_fingerprint"))
            or value.get("session_counter_status") != "observed"):
        return False
    start = value.get("session_total_tokens_start")
    end = value.get("session_total_tokens_end")
    delta = value.get("session_token_delta")
    if not (_is_non_negative_int(start) and _is_non_negative_int(end)
            and _is_non_negative_int(delta) and end >= start and delta == end - start):
        return False
    counts = tuple(value.get(field) for field in (
        "hook_invocations", "zero_injections", "emissions",
        "directive_utf8_bytes_total"))
    if not all(_is_non_negative_int(item) for item in counts):
        return False
    invocations, zero_injections, emissions, directive_bytes = counts
    if invocations != zero_injections + emissions:
        return False
    if not _valid_directive_accounting(emissions, directive_bytes):
        return False
    exact_tokens = value.get("directive_exact_tokens")
    provenance = value.get("exact_tokenizer_provenance")
    if ((exact_tokens is None) != (provenance is None)
            or (exact_tokens is not None and (
                not _is_non_negative_int(exact_tokens) or exact_tokens == 0
                or emissions == 0 or not _valid_tokenizer_provenance(provenance)))):
        return False
    if value.get("arm") == "control" and (
            emissions != 0 or directive_bytes != 0 or exact_tokens is not None):
        return False
    return (
        isinstance(value.get("required_checks_pass"), bool)
        and isinstance(value.get("safety_checks_pass"), bool)
        and isinstance(value.get("hard_regression"), bool)
        and _is_score(value.get("quality_score"))
        and _is_nonempty_string(value.get("quality_evaluator_id"))
    )


def _normalize_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(payload))
    workloads = value.get("workloads")
    if isinstance(workloads, list):
        for workload in workloads:
            results = workload.get("results") if isinstance(workload, dict) else None
            if isinstance(results, list):
                results.sort(key=lambda item: str(item.get("arm")) if isinstance(item, dict) else "")
        workloads.sort(key=lambda item: str(item.get("declaration", {}).get("workload_id")) if isinstance(item, dict) else "")
    return value


def _exclusion_for(workload: Any, expected_manifest: str) -> tuple[str | None, dict[str, Any] | None]:
    if not isinstance(workload, dict):
        return "required_output_missing", None
    declaration = workload.get("declaration")
    results = workload.get("results")
    if not isinstance(declaration, dict) or not isinstance(results, list):
        return "required_output_missing", None
    declaration_schema_valid = _valid_declaration_schema(declaration)
    by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
    for item in results:
        if isinstance(item, dict) and item.get("arm") in by_arm:
            by_arm[item["arm"]].append(item)
    reasons: set[str] = set()
    if any(len(by_arm[arm]) != 1 for arm in ARMS) or len(results) != 3:
        reasons.add("missing_arm")
    flat = [items[0] for items in by_arm.values() if len(items) == 1]
    if flat:
        fingerprints = {item.get("config_fingerprint") for item in flat}
        expected_fingerprint = config_fingerprint(declaration)
        if (len(fingerprints) != 1 or None in fingerprints
                or fingerprints != {expected_fingerprint}
                or any(item.get("experiment_id") != declaration.get("experiment_id")
                       or item.get("workload_id") != declaration.get("workload_id") for item in flat)):
            reasons.add("pairing_fingerprint_mismatch")
        if any(item.get("session_counter_status") != "observed" for item in flat):
            reasons.add("counter_unknown_or_degraded")
        for item in flat:
            start, end, delta = (item.get("session_total_tokens_start"),
                                 item.get("session_total_tokens_end"),
                                 item.get("session_token_delta"))
            if _is_non_negative_int(start) and _is_non_negative_int(end) and end < start:
                reasons.add("counter_decreased")
            elif not (_is_non_negative_int(start) and _is_non_negative_int(end)
                      and _is_non_negative_int(delta) and delta == end - start):
                reasons.add("counter_unknown_or_degraded")
        if any(item.get("status") == "failed" for item in flat):
            reasons.add("runner_failure")
        for item in flat:
            explicit = item.get("exclusion_reason")
            status = item.get("status")
            if set(item) != set(RESULT_FIELDS):
                reasons.add("required_output_missing")
            if status == "invalid":
                if explicit in EXCLUSION_REASONS:
                    reasons.add(explicit)
                else:
                    reasons.add("required_output_missing")
            elif status not in {"complete", "failed"}:
                reasons.add("required_output_missing")
        if any(item.get("manifest_sha256") != expected_manifest for item in flat):
            reasons.add("manifest_changed")
        evaluators = {item.get("quality_evaluator_id") for item in flat}
        if (not declaration.get("rubric_version") or not declaration.get("rubric_sha256")
                or len(evaluators) != 1 or None in evaluators):
            reasons.add("rubric_missing_or_changed")
        for item in flat:
            if item.get("status") == "complete" and not _valid_complete_result_schema(item):
                reasons.add("required_output_missing")
    if not declaration_schema_valid:
        reasons.add("pairing_fingerprint_mismatch")
    if not all(_is_sha256(declaration.get(field)) for field in (
            "prompt_sha256", "artifact_bundle_sha256", "runtime_config_sha256")):
        reasons.add("pairing_fingerprint_mismatch")
    if not _is_sha256(declaration.get("rubric_sha256")):
        reasons.add("rubric_missing_or_changed")
    if declaration.get("arm_order") is not None and sorted(declaration.get("arm_order", [])) != sorted(ARMS):
        reasons.add("pairing_fingerprint_mismatch")
    reason = next((candidate for candidate in EXCLUSION_REASONS if candidate in reasons), None)
    if reason is not None:
        return reason, None
    return None, {"declaration": declaration, "results": {item["arm"]: item for item in flat}}


def _paired_bootstrap(samples: list[dict[str, float]], *, resamples: int, seed: int) -> dict[str, dict[str, float | None]]:
    names = (
        "quality_dynamic_vs_control", "quality_dynamic_vs_static",
        "observed_delta_control_vs_dynamic_nonbilling",
        "observed_delta_static_vs_dynamic_nonbilling",
    )
    if not samples:
        return {name: {"mean": None, "lower_95": None} for name in names}
    points = {name: sum(sample[name] for sample in samples) / len(samples) for name in names}
    distributions = {name: [] for name in names}
    rng = random.Random(seed)
    count = len(samples)
    for _ in range(resamples):
        indices = [rng.randrange(count) for _ in range(count)]
        for name in names:
            distributions[name].append(sum(samples[index][name] for index in indices) / count)
    lower_index = max(0, math.ceil(0.05 * resamples) - 1)
    return {
        name: {
            "mean": round(points[name], 12),
            "lower_95": round(sorted(distributions[name])[lower_index], 12),
        }
        for name in names
    }


def evaluate(payload: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Evaluate strict complete triplets; never mutate production or adopt."""

    validate_manifest(manifest)
    normalized = _normalize_input(payload)
    workloads = normalized.get("workloads") if isinstance(normalized, dict) else None
    if not isinstance(workloads, list):
        raise ValueError("evaluation input requires workloads")
    experiment_id = normalized.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id:
        raise ValueError("evaluation input requires experiment_id")
    expected_manifest = manifest_sha256(manifest)
    workload_id_counts = Counter(
        item.get("declaration", {}).get("workload_id")
        for item in workloads if isinstance(item, dict)
        and isinstance(item.get("declaration"), dict)
        and _is_nonempty_string(item["declaration"].get("workload_id"))
    )
    included = []
    excluded = []
    reason_counts: Counter[str] = Counter()
    for workload in workloads:
        declaration = workload.get("declaration", {}) if isinstance(workload, dict) else {}
        workload_id = declaration.get("workload_id", "unknown")
        reason, triplet = _exclusion_for(workload, expected_manifest)
        if declaration.get("experiment_id") != experiment_id:
            reason, triplet = "pairing_fingerprint_mismatch", None
        if workload_id_counts.get(workload_id, 0) != 1:
            reason, triplet = "pairing_fingerprint_mismatch", None
        if reason:
            reason_counts[reason] += 1
            excluded.append({"workload_id": workload_id, "reason": reason})
        else:
            included.append(triplet)

    minimum = manifest["minimum_complete_triplets"]
    strata = Counter(item["declaration"]["stratum"] for item in included)
    declared_strata = {item.get("declaration", {}).get("stratum") for item in workloads if isinstance(item, dict)}
    declared_strata.discard(None)
    g1 = len(included) >= minimum and (len(declared_strata) <= 1 or all(strata[name] >= 10 for name in declared_strata))
    g2 = g1 and all(item["results"][arm]["session_counter_status"] == "observed" for item in included for arm in ARMS)
    g3 = g2 and all(
        result["required_checks_pass"] and result["safety_checks_pass"] and not result["hard_regression"]
        for item in included for result in item["results"].values()
    )

    samples = []
    bytes_by_arm = {arm: 0 for arm in ARMS}
    emissions_by_arm = {arm: 0 for arm in ARMS}
    for item in included:
        results = item["results"]
        samples.append({
            "quality_dynamic_vs_control": results["dynamic"]["quality_score"] - results["control"]["quality_score"],
            "quality_dynamic_vs_static": results["dynamic"]["quality_score"] - results["static"]["quality_score"],
            "observed_delta_control_vs_dynamic_nonbilling": results["control"]["session_token_delta"] - results["dynamic"]["session_token_delta"],
            "observed_delta_static_vs_dynamic_nonbilling": results["static"]["session_token_delta"] - results["dynamic"]["session_token_delta"],
        })
        for arm in ARMS:
            bytes_by_arm[arm] += results[arm]["directive_utf8_bytes_total"]
            emissions_by_arm[arm] += results[arm]["emissions"]
    metrics = _paired_bootstrap(
        samples, resamples=manifest["bootstrap"]["resamples"],
        seed=manifest["bootstrap"]["seed"])
    tolerance = -manifest["quality_tolerance"]
    quality_ready = all(metrics[name]["lower_95"] is not None for name in (
        "quality_dynamic_vs_control", "quality_dynamic_vs_static"))
    g4 = g3 and quality_ready and all(metrics[name]["lower_95"] >= tolerance for name in (
        "quality_dynamic_vs_control", "quality_dynamic_vs_static"))
    g5 = g4 and metrics["observed_delta_control_vs_dynamic_nonbilling"]["lower_95"] > 0
    g6 = g5 and metrics["observed_delta_static_vs_dynamic_nonbilling"]["lower_95"] > 0
    if not g1 or not g2:
        verdict = "insufficient"
    elif not all((g3, g4, g5, g6)):
        verdict = "reject"
    else:
        verdict = "eligible_for_user_review"

    metrics["directive_utf8_bytes_by_arm"] = bytes_by_arm
    metrics["emissions_by_arm"] = emissions_by_arm
    return {
        "contract_version": CONTRACT_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "experiment_id": experiment_id,
        "manifest_sha256": expected_manifest,
        "input_sha256": canonical_sha256(normalized),
        "verdict": verdict,
        "complete_triplets": len(included),
        "excluded_triplets": len(excluded),
        "included_workload_ids": [item["declaration"]["workload_id"] for item in included],
        "excluded_workloads": excluded,
        "exclusion_reason_counts": {reason: reason_counts.get(reason, 0) for reason in EXCLUSION_REASONS},
        "gates": {
            "G1_sample": "pass" if g1 else "fail",
            "G2_integrity": "pass" if g2 else "fail",
            "G3_safety_required": "pass" if g3 else "fail",
            "G4_quality": "pass" if g4 else "fail",
            "G5_control_confidence": "pass" if g5 else "fail",
            "G6_static_comparison": "pass" if g6 else "fail",
        },
        "metrics": metrics,
        "observed_delta_metric_label": "observed session-token delta difference (non-billing)",
        "bootstrap": manifest["bootstrap"],
        "adoption_decision": "pending_user_decision",
        "production_dynamic_enabled": False,
    }
