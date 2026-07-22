#!/usr/bin/env python3
"""Fail-closed semantic QA for 48 kHz full-band report spectrograms."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote


PROFILE = "spectrogram-report-48k-full-band"
SCHEMA_VERSION = 1
FULL_BAND_HZ = (0.0, 24000.0)
FULL_BAND_TERM_RE = re.compile(r"전\s*대역|full[\s-]?band", re.IGNORECASE)
BROADBAND_TERM_RE = re.compile(r"광\s*대역|broad[\s-]?band", re.IGNORECASE)
HIGH_FREQUENCY_TERM_RE = re.compile(r"고\s*주파|high[\s-]?frequency", re.IGNORECASE)
FREQUENCY_RANGE_RE = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*(?P<low_unit>k?hz)?\s*"
    r"(?:[-–—~]|to)\s*"
    r"(?P<high>\d+(?:\.\d+)?)\s*(?P<high_unit>k?hz)",
    re.IGNORECASE,
)
HIGH_FREQUENCY_RANGE_RE = re.compile(
    r"(?:고\s*주파|high[\s-]?frequency)\s*(?:대역|band)?\s*[\(\[{:：]?\s*"
    r"(?P<low>\d+(?:\.\d+)?)\s*(?P<low_unit>k?hz)?\s*"
    r"(?:[-–—~]|to)\s*"
    r"(?P<high>\d+(?:\.\d+)?)\s*(?P<high_unit>k?hz)",
    re.IGNORECASE,
)
SENSITIVE_RE = re.compile(
    r"전\s*대역|full[\s-]?band|광\s*대역|broad[\s-]?band|고\s*주파|high[\s-]?frequency",
    re.IGNORECASE,
)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+['\"][^'\"]*['\"])?\)")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(?:[^\n]*)$")
RAW_HTML_BLOCK_RE = re.compile(
    r"<(?P<tag>address|article|aside|blockquote|body|caption|center|code|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|html|iframe|legend|li|main|menu|nav|noframes|ol|optgroup|option|p|pre|script|section|style|summary|table|tbody|td|tfoot|th|thead|title|tr|ul)\b[^>]*>.*?</(?P=tag)\s*>",
    re.IGNORECASE | re.DOTALL,
)

TOP_KEYS = {"schema_version", "profile", "figure_groups", "metrics", "claims"}
FIGURE_KEYS = {
    "id", "kind", "png_path", "sample_rate_hz", "min_hz", "max_hz",
    "dynamic_range_db", "shared_scale_per_figure", "colormap", "panels",
    "visual_review",
}
PANEL_KEYS = {"id", "vmin_db", "vmax_db"}
STFT_KEYS = {"sample_rate_hz", "window_samples"}
# USER-CONFIRMED 2026-07-22 window law: STFT window samples per native sample
# rate. Rates outside this mapping have no confirmed law and warn instead of
# failing (the unit doctrine picks the nearest of these window values).
STFT_WINDOW_LAW = {8000.0: 256.0, 16000.0: 512.0, 48000.0: 1024.0}
REVIEW_KEYS = {
    "reviewed_png", "png_sha256", "reviewer", "reviewed_at", "evidence",
    "y_axis_0_24khz", "ticks_readable", "colorbar_present",
    "shared_scale_confirmed", "labels_readable",
}
METRIC_KEYS = {"id", "min_hz", "max_hz"}
CLAIM_KEYS = {"id", "text", "type", "claimed_band_hz", "evidence"}
EVIDENCE_KEYS = {"kind", "id"}
REVIEW_BOOL_KEYS = (
    "y_axis_0_24khz", "ticks_readable", "colorbar_present",
    "shared_scale_confirmed", "labels_readable",
)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def strip_fenced_code(value: str) -> str:
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in value.splitlines(keepends=True):
        candidate = line.rstrip("\r\n")
        if fence_character is None:
            match = FENCE_OPEN_RE.match(candidate)
            if match:
                run = match.group(1)
                fence_character = run[0]
                fence_length = len(run)
                output.append("\n" if line.endswith(("\n", "\r")) else "")
            else:
                output.append(line)
            continue
        closing = re.match(
            rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
            candidate,
        )
        if closing:
            fence_character = None
            fence_length = 0
        output.append("\n" if line.endswith(("\n", "\r")) else "")
    return "".join(output)


def strip_inline_code_spans(value: str) -> str:
    runs = list(re.finditer(r"`+", value))
    characters = list(value)
    index = 0
    while index < len(runs):
        opener = runs[index]
        backslashes = 0
        cursor = opener.start() - 1
        while cursor >= 0 and value[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2:
            index += 1
            continue
        closer_index = index + 1
        while closer_index < len(runs) and len(runs[closer_index].group(0)) != len(opener.group(0)):
            closer_index += 1
        if closer_index >= len(runs):
            index += 1
            continue
        closer = runs[closer_index]
        for position in range(opener.start(), closer.end()):
            if characters[position] not in {"\n", "\r"}:
                characters[position] = " "
        index = closer_index + 1
    return "".join(characters)


def strip_nonprose_markdown(value: str) -> str:
    value = strip_fenced_code(value)
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.DOTALL)
    value = RAW_HTML_BLOCK_RE.sub(" ", value)
    value = strip_inline_code_spans(value)
    return re.sub(r"(?m)^(?: {4}|\t).*$", " ", value)


def normalize_markdown(value: str) -> str:
    value = strip_nonprose_markdown(value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r" \1 ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r" \1 ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"~~([^~]+)~~", r" \1 ", value)
    value = re.sub(r"[`*_#>|]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def claim_id(text: str) -> str:
    digest = hashlib.sha256(normalize_markdown(text).encode("utf-8")).hexdigest()
    return f"claim-{digest[:16]}"


def frequency_ranges_hz(text: str, pattern: re.Pattern[str] = FREQUENCY_RANGE_RE) -> list[tuple[float, float]]:
    ranges: list[tuple[float, float]] = []
    for match in pattern.finditer(normalize_markdown(text)):
        high_unit = match.group("high_unit").lower()
        low_unit = (match.group("low_unit") or high_unit).lower()
        low_scale = 1000.0 if low_unit == "khz" else 1.0
        high_scale = 1000.0 if high_unit == "khz" else 1.0
        ranges.append((float(match.group("low")) * low_scale, float(match.group("high")) * high_scale))
    return ranges


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Validate a complete PNG stream and return dimensions."""
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    if len(payload) < 45 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    position = 8
    ihdr: bytes | None = None
    compressed = bytearray()
    seen_plte = False
    plte_entries = 0
    seen_idat = False
    idat_closed = False
    seen_iend = False
    while position < len(payload):
        if position + 12 > len(payload):
            return None
        length = struct.unpack(">I", payload[position : position + 4])[0]
        chunk_type = payload[position + 4 : position + 8]
        if not re.fullmatch(rb"[A-Za-z]{4}", chunk_type):
            return None
        chunk_end = position + 12 + length
        if chunk_end > len(payload):
            return None
        chunk_data = payload[position + 8 : position + 8 + length]
        stored_crc = struct.unpack(">I", payload[position + 8 + length : chunk_end])[0]
        if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != stored_crc:
            return None
        if ihdr is None:
            if chunk_type != b"IHDR" or length != 13:
                return None
            ihdr = chunk_data
        elif chunk_type == b"IHDR":
            return None
        if chunk_type not in {b"IHDR", b"PLTE", b"IDAT", b"IEND"} and not (chunk_type[0] & 0x20):
            return None
        if chunk_type == b"PLTE":
            if seen_plte or seen_idat or length < 3 or length > 768 or length % 3:
                return None
            color_type = ihdr[9]
            bit_depth = ihdr[8]
            if color_type in {0, 4}:
                return None
            plte_entries = length // 3
            if color_type == 3 and plte_entries > 2**bit_depth:
                return None
            seen_plte = True
        if chunk_type == b"IDAT":
            if idat_closed:
                return None
            if ihdr[9] == 3 and not seen_plte:
                return None
            seen_idat = True
            if len(compressed) + length > 256 * 1024 * 1024:
                return None
            compressed.extend(chunk_data)
        elif seen_idat and chunk_type != b"IEND":
            idat_closed = True
        if chunk_type == b"IEND":
            if length != 0 or not seen_idat:
                return None
            seen_iend = True
            position = chunk_end
            break
        position = chunk_end
    if ihdr is None or not seen_iend or position != len(payload):
        return None

    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    valid_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if (
        width < 1
        or height < 1
        or bit_depth not in valid_depths.get(color_type, set())
        or compression != 0
        or filter_method != 0
        or interlace not in {0, 1}
    ):
        return None
    if color_type == 3 and (not seen_plte or plte_entries < 1):
        return None
    bits_per_pixel = channels[color_type] * bit_depth

    row_shapes: list[tuple[int, int]] = []
    if interlace == 0:
        row_shapes.append((height, (width * bits_per_pixel + 7) // 8))
    else:
        for start_x, start_y, step_x, step_y in (
            (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
            (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2),
        ):
            pass_width = 0 if width <= start_x else (width - start_x + step_x - 1) // step_x
            pass_height = 0 if height <= start_y else (height - start_y + step_y - 1) // step_y
            if pass_width and pass_height:
                row_shapes.append((pass_height, (pass_width * bits_per_pixel + 7) // 8))
    expected_size = sum(rows * (row_bytes + 1) for rows, row_bytes in row_shapes)
    if expected_size > 512 * 1024 * 1024:
        return None
    try:
        inflater = zlib.decompressobj()
        decoded = inflater.decompress(bytes(compressed), expected_size + 1)
        decoded += inflater.flush()
    except zlib.error:
        return None
    if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail or len(decoded) != expected_size:
        return None
    offset = 0
    for rows, row_bytes in row_shapes:
        for _ in range(rows):
            if decoded[offset] > 4:
                return None
            offset += row_bytes + 1
    return width, height


def resolve_asset(base: Path, raw: str) -> Path:
    path = Path(unquote(raw))
    if not path.is_absolute():
        path = base / path
    return path.resolve()


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


class Verifier:
    def __init__(self, manifest_path: Path, report_path: Path, manifest: Any, report: str):
        self.manifest_path = manifest_path
        self.report_path = report_path
        self.manifest = manifest
        self.report = report
        self.normalized_report = normalize_markdown(report)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.figures: dict[str, tuple[float, float]] = {}
        self.metrics: dict[str, tuple[float, float]] = {}

    def error(self, code: str, detail: str) -> None:
        self.errors.append(f"{code}: {detail}")

    def warn(self, code: str, detail: str) -> None:
        self.warnings.append(f"{code}: {detail}")

    def object_keys(
        self, value: Any, required: set[str], allowed: set[str], where: str
    ) -> bool:
        if not isinstance(value, dict):
            self.error("invalid-type", f"{where} must be an object")
            return False
        missing = required - value.keys()
        unknown = value.keys() - allowed
        if missing:
            self.error("missing-field", f"{where}: {', '.join(sorted(missing))}")
        if unknown:
            self.error("unknown-field", f"{where}: {', '.join(sorted(unknown))}")
        return not missing and not unknown

    def nonempty_string(self, value: Any, where: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            self.error("invalid-string", f"{where} must be a non-empty string")
            return False
        return True

    def exact_number(self, value: Any, expected: float, where: str) -> bool:
        if not is_number(value) or float(value) != expected:
            self.error("profile-mismatch", f"{where} must equal {expected:g}; got {value!r}")
            return False
        return True

    def report_image_paths(self) -> set[Path]:
        found: set[Path] = set()
        rendered_markdown = strip_nonprose_markdown(self.report)
        for match in IMAGE_RE.finditer(rendered_markdown):
            backslashes = 0
            cursor = match.start() - 1
            while cursor >= 0 and rendered_markdown[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2:
                continue
            raw = match.group(1) or match.group(2)
            if raw and not re.match(r"^[a-z]+://", raw, re.IGNORECASE):
                try:
                    found.add(resolve_asset(self.report_path.parent, raw.split("#", 1)[0]))
                except (OSError, ValueError, RuntimeError) as exc:
                    self.error("invalid-path", f"report image path {raw!r}: {exc}")
        return found

    def verify_stft(self, stft: Any, where: str) -> None:
        """Enforce the USER-CONFIRMED (2026-07-22) per-rate STFT window law.

        The block is optional per figure; absence is never an error. When
        present, a known sample rate must carry its confirmed window size, and
        an unknown sample rate produces a warning rather than a failure.
        """
        if not self.object_keys(stft, STFT_KEYS, STFT_KEYS, where):
            return
        rate, window = stft["sample_rate_hz"], stft["window_samples"]
        valid = True
        if not is_number(rate) or rate <= 0:
            self.error("invalid-stft", f"{where}.sample_rate_hz must be a positive number")
            valid = False
        if not is_number(window) or window <= 0 or float(window) != int(window):
            self.error("invalid-stft", f"{where}.window_samples must be a positive integer")
            valid = False
        if not valid:
            return
        expected = STFT_WINDOW_LAW.get(float(rate))
        if expected is None:
            known = ", ".join(f"{r:g}" for r in sorted(STFT_WINDOW_LAW))
            self.warn(
                "stft-window-unverified",
                f"{where}: no confirmed window law for sample_rate_hz={rate:g} "
                f"(confirmed rates: {known}); use the nearest confirmed window",
            )
        elif float(window) != expected:
            self.error(
                "stft-window-mismatch",
                f"{where}: sample_rate_hz={rate:g} requires window_samples={expected:g}; "
                f"got {window!r}",
            )

    def verify_figure(self, figure: Any, index: int, report_images: set[Path]) -> None:
        where = f"figure_groups[{index}]"
        if not self.object_keys(figure, FIGURE_KEYS, FIGURE_KEYS | {"stft"}, where):
            return
        figure_id = figure["id"]
        if not self.nonempty_string(figure_id, f"{where}.id"):
            return
        if figure_id in self.figures:
            self.error("duplicate-id", f"duplicate figure group {figure_id!r}")
            return
        if figure["kind"] != "spectrogram":
            self.error("profile-mismatch", f"{where}.kind must be 'spectrogram'")
        self.exact_number(figure["sample_rate_hz"], 48000.0, f"{where}.sample_rate_hz")
        self.exact_number(figure["min_hz"], FULL_BAND_HZ[0], f"{where}.min_hz")
        self.exact_number(figure["max_hz"], FULL_BAND_HZ[1], f"{where}.max_hz")
        if figure["shared_scale_per_figure"] is not True:
            self.error("profile-mismatch", f"{where}.shared_scale_per_figure must be true")
        if not is_number(figure["dynamic_range_db"]) or figure["dynamic_range_db"] <= 0:
            self.error("invalid-range", f"{where}.dynamic_range_db must be positive")
        self.nonempty_string(figure["colormap"], f"{where}.colormap")
        if "stft" in figure:
            self.verify_stft(figure["stft"], f"{where}.stft")

        png_raw = figure["png_path"]
        png_path: Path | None = None
        if self.nonempty_string(png_raw, f"{where}.png_path"):
            try:
                png_path = resolve_asset(self.manifest_path.parent, png_raw)
            except (OSError, ValueError, RuntimeError) as exc:
                self.error("invalid-path", f"{where}.png_path {png_raw!r}: {exc}")
            if png_path is not None:
                dimensions = png_dimensions(png_path)
                if dimensions is None or dimensions[0] < 1 or dimensions[1] < 1:
                    self.error("invalid-png", f"{where}.png_path is missing or not a valid PNG: {png_path}")
                if png_path not in report_images:
                    self.error("unlinked-figure", f"report does not link {png_raw!r}")

        panels = figure["panels"]
        scales: list[tuple[float, float]] = []
        panel_ids: set[str] = set()
        if not isinstance(panels, list) or not panels:
            self.error("missing-panel", f"{where}.panels must be a non-empty array")
        else:
            for panel_index, panel in enumerate(panels):
                panel_where = f"{where}.panels[{panel_index}]"
                if not self.object_keys(panel, PANEL_KEYS, PANEL_KEYS, panel_where):
                    continue
                panel_id = panel["id"]
                if not self.nonempty_string(panel_id, f"{panel_where}.id"):
                    continue
                if panel_id in panel_ids:
                    self.error("duplicate-id", f"duplicate panel {panel_id!r} in {figure_id!r}")
                panel_ids.add(panel_id)
                vmin, vmax = panel["vmin_db"], panel["vmax_db"]
                if not is_number(vmin) or not is_number(vmax) or vmax <= vmin:
                    self.error("invalid-scale", f"{panel_where} requires numeric vmin_db < vmax_db")
                    continue
                scales.append((float(vmin), float(vmax)))
            if scales:
                if any(scale != scales[0] for scale in scales[1:]):
                    self.error("unshared-scale", f"{where}.panels do not use one vmin_db/vmax_db pair")
                if is_number(figure["dynamic_range_db"]):
                    actual = scales[0][1] - scales[0][0]
                    if not math.isclose(actual, float(figure["dynamic_range_db"]), abs_tol=1e-9):
                        self.error(
                            "dynamic-range-mismatch",
                            f"{where}.dynamic_range_db={figure['dynamic_range_db']!r}, panel range={actual:g}",
                        )

        review = figure["visual_review"]
        if self.object_keys(review, REVIEW_KEYS, REVIEW_KEYS, f"{where}.visual_review"):
            reviewed_png = review["reviewed_png"]
            if self.nonempty_string(reviewed_png, f"{where}.visual_review.reviewed_png") and png_path:
                try:
                    reviewed_path = resolve_asset(self.manifest_path.parent, reviewed_png)
                except (OSError, ValueError, RuntimeError) as exc:
                    self.error("invalid-path", f"{where}.visual_review.reviewed_png {reviewed_png!r}: {exc}")
                    reviewed_path = None
                if reviewed_path is not None:
                    if reviewed_path != png_path:
                        self.error("review-target-mismatch", f"{where} review must target png_path")
                    expected_hash = review["png_sha256"]
                    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                        self.error("invalid-hash", f"{where}.visual_review.png_sha256 must be lowercase SHA-256")
                    elif png_dimensions(reviewed_path) is not None:
                        try:
                            actual_hash = file_sha256(reviewed_path)
                        except OSError as exc:
                            self.error("invalid-png", f"{where} reviewed PNG is unreadable: {exc}")
                        else:
                            if actual_hash != expected_hash:
                                self.error("stale-review", f"{where} PNG changed after visual review")
            for key in ("reviewer", "evidence"):
                self.nonempty_string(review[key], f"{where}.visual_review.{key}")
            reviewed_at = review["reviewed_at"]
            if not isinstance(reviewed_at, str):
                self.error("invalid-time", f"{where}.visual_review.reviewed_at must be ISO-8601")
            else:
                try:
                    parsed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("timezone required")
                except ValueError:
                    self.error("invalid-time", f"{where}.visual_review.reviewed_at needs a timezone")
            for key in REVIEW_BOOL_KEYS:
                if review[key] is not True:
                    self.error("visual-review-failed", f"{where}.visual_review.{key} must be true")

        self.figures[figure_id] = FULL_BAND_HZ

    def verify_metric(self, metric: Any, index: int) -> None:
        where = f"metrics[{index}]"
        if not self.object_keys(metric, METRIC_KEYS, METRIC_KEYS, where):
            return
        metric_id = metric["id"]
        if not self.nonempty_string(metric_id, f"{where}.id"):
            return
        if metric_id in self.metrics or metric_id in self.figures:
            self.error("duplicate-id", f"duplicate evidence ID {metric_id!r}")
            return
        minimum, maximum = metric["min_hz"], metric["max_hz"]
        if (
            not is_number(minimum)
            or not is_number(maximum)
            or minimum < 0
            or maximum <= minimum
            or maximum > FULL_BAND_HZ[1]
        ):
            self.error("invalid-range", f"{where} requires 0 <= min_hz < max_hz <= 24000")
            return
        self.metrics[metric_id] = (float(minimum), float(maximum))

    def required_claim_band(self, claim: dict[str, Any], where: str) -> tuple[float, float] | None:
        claim_type = claim["type"]
        if not isinstance(claim_type, str):
            self.error("invalid-claim-type", f"{where}.type must be a string")
            return None
        if claim_type in {"full_band", "broadband"}:
            if "claimed_band_hz" in claim:
                self.error("derived-band-only", f"{where}.claimed_band_hz must be omitted for {claim_type}")
            prose_ranges = frequency_ranges_hz(claim["text"])
            if prose_ranges and any(
                not (
                    math.isclose(minimum, FULL_BAND_HZ[0], abs_tol=1e-9)
                    and math.isclose(maximum, FULL_BAND_HZ[1], abs_tol=1e-9)
                )
                for minimum, maximum in prose_ranges
            ):
                self.error(
                    "contradictory-full-band-range",
                    f"{where}.text contains a range other than 0–24 kHz for {claim_type}",
                )
            return FULL_BAND_HZ
        if claim_type != "high_frequency":
            self.error("invalid-claim-type", f"{where}.type is not supported")
            return None
        band = claim.get("claimed_band_hz")
        if not isinstance(band, list) or len(band) != 2 or not all(is_number(v) for v in band):
            self.error("missing-claim-band", f"{where}.claimed_band_hz is required for high_frequency")
            return None
        minimum, maximum = float(band[0]), float(band[1])
        if minimum < 0 or maximum <= minimum or maximum > FULL_BAND_HZ[1]:
            self.error(
                "invalid-claim-band",
                f"{where}.claimed_band_hz must satisfy 0 <= min < max <= 24000",
            )
            return None
        prose_ranges = frequency_ranges_hz(claim["text"], HIGH_FREQUENCY_RANGE_RE)
        if not any(
            math.isclose(minimum, prose_minimum, abs_tol=1e-9)
            and math.isclose(maximum, prose_maximum, abs_tol=1e-9)
            for prose_minimum, prose_maximum in prose_ranges
        ):
            self.error(
                "claim-range-not-in-text",
                f"{where}.text must attach the same explicit Hz/kHz range to its high-frequency term",
            )
        return minimum, maximum

    def verify_claim_type_binding(self, normalized: str, claim_type: Any, where: str) -> None:
        if not isinstance(claim_type, str):
            return  # required_claim_band reports the type error once.
        has_full_band = bool(FULL_BAND_TERM_RE.search(normalized))
        has_broadband = bool(BROADBAND_TERM_RE.search(normalized))
        has_high_frequency = bool(HIGH_FREQUENCY_TERM_RE.search(normalized))
        if has_high_frequency and (has_full_band or has_broadband):
            self.error(
                "mixed-band-claim",
                f"{where}.text mixes full/broadband and high-frequency terms; register separate claim spans",
            )
            return
        if has_full_band and claim_type != "full_band":
            self.error("claim-type-mismatch", f"{where} full-band wording requires type=full_band")
        elif has_broadband and claim_type not in {"broadband", "full_band"}:
            self.error(
                "claim-type-mismatch",
                f"{where} broadband wording requires type=broadband or full_band",
            )
        elif has_high_frequency and claim_type != "high_frequency":
            self.error(
                "claim-type-mismatch",
                f"{where} high-frequency wording requires type=high_frequency",
            )

    def verify_claims(self, claims: Any) -> None:
        if not isinstance(claims, list):
            self.error("invalid-type", "claims must be an array")
            return
        registered_spans: list[tuple[int, int]] = []
        claim_ids: set[str] = set()
        for index, claim in enumerate(claims):
            where = f"claims[{index}]"
            if not self.object_keys(claim, {"id", "text", "type", "evidence"}, CLAIM_KEYS, where):
                continue
            text = claim["text"]
            if not self.nonempty_string(text, f"{where}.text"):
                continue
            normalized = normalize_markdown(text)
            self.verify_claim_type_binding(normalized, claim["type"], where)
            expected_id = claim_id(text)
            claim_identifier = claim["id"]
            valid_claim_id = self.nonempty_string(claim_identifier, f"{where}.id")
            if valid_claim_id and claim_identifier != expected_id:
                self.error("claim-id-mismatch", f"{where}.id must be {expected_id}")
            if valid_claim_id:
                if claim_identifier in claim_ids:
                    self.error("duplicate-id", f"duplicate claim ID {claim_identifier!r}")
                claim_ids.add(claim_identifier)
            start = 0
            found = False
            while True:
                position = self.normalized_report.find(normalized, start)
                if position < 0:
                    break
                found = True
                registered_spans.append((position, position + len(normalized)))
                start = position + max(1, len(normalized))
            if not found:
                self.error("claim-not-found", f"{where}.text is absent after Markdown normalization")

            required_band = self.required_claim_band(claim, where)
            evidence = claim["evidence"]
            if not isinstance(evidence, list) or not evidence:
                self.error("missing-evidence", f"{where}.evidence must be a non-empty array")
                continue
            for evidence_index, item in enumerate(evidence):
                item_where = f"{where}.evidence[{evidence_index}]"
                if not self.object_keys(item, EVIDENCE_KEYS, EVIDENCE_KEYS, item_where):
                    continue
                kind, evidence_id = item["kind"], item["id"]
                if not isinstance(kind, str):
                    self.error("invalid-evidence-kind", f"{item_where}.kind must be a string")
                    continue
                if not self.nonempty_string(evidence_id, f"{item_where}.id"):
                    continue
                ranges = self.figures if kind == "figure_group" else self.metrics if kind == "metric" else None
                if ranges is None:
                    self.error("invalid-evidence-kind", f"{item_where}.kind must be figure_group or metric")
                    continue
                actual_band = ranges.get(evidence_id)
                if actual_band is None:
                    self.error("unknown-evidence", f"{item_where} references {evidence_id!r}")
                    continue
                if required_band and not (
                    actual_band[0] <= required_band[0] and actual_band[1] >= required_band[1]
                ):
                    self.error(
                        "unsupported-claim",
                        f"{item_where} band {actual_band} does not contain {required_band}",
                    )

        for match in SENSITIVE_RE.finditer(self.normalized_report):
            if not any(start <= match.start() and match.end() <= end for start, end in registered_spans):
                excerpt_start = max(0, match.start() - 35)
                excerpt_end = min(len(self.normalized_report), match.end() + 35)
                self.error(
                    "unregistered-band-claim",
                    repr(self.normalized_report[excerpt_start:excerpt_end]),
                )

    def run(self) -> list[str]:
        if not self.object_keys(self.manifest, TOP_KEYS, TOP_KEYS, "manifest"):
            return self.errors
        if self.manifest["schema_version"] != SCHEMA_VERSION:
            self.error("unsupported-schema", f"schema_version must equal {SCHEMA_VERSION}")
        if self.manifest["profile"] != PROFILE:
            self.error("unsupported-profile", f"profile must equal {PROFILE!r}")
        report_images = self.report_image_paths()
        figures = self.manifest["figure_groups"]
        if not isinstance(figures, list) or not figures:
            self.error("missing-figure", "figure_groups must be a non-empty array")
        else:
            for index, figure in enumerate(figures):
                self.verify_figure(figure, index, report_images)
        metrics = self.manifest["metrics"]
        if not isinstance(metrics, list):
            self.error("invalid-type", "metrics must be an array")
        else:
            for index, metric in enumerate(metrics):
                self.verify_metric(metric, index)
        self.verify_claims(self.manifest["claims"])
        return self.errors


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"{path}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a 48 kHz full-band report spectrogram manifest",
        add_help=False,
    )
    parser.add_argument("--manifest")
    parser.add_argument("--report")
    parser.add_argument("-h", "--help", action="store_true")
    args, extras = parser.parse_known_args(argv)
    if args.help:
        print("usage: figure-semantic-verify.py --manifest <manifest.json> --report <report.md>")
        return 0
    if extras or not args.manifest or not args.report:
        print("status=failed\nreason=usage", file=sys.stderr)
        return 64
    try:
        manifest_path = Path(args.manifest).resolve()
        report_path = Path(args.report).resolve()
        manifest_text = load_text(manifest_path)
        report = load_text(report_path)
        manifest = json.loads(manifest_text, object_pairs_hook=reject_duplicate_keys)
    except DuplicateKeyError as exc:
        print(f"status=failed\nreason=duplicate-field\ndetail={exc}", file=sys.stderr)
        return 66
    except (FileNotFoundError, UnicodeError, json.JSONDecodeError, OSError, ValueError, RuntimeError) as exc:
        print(f"status=failed\nreason=input-error\ndetail={exc}", file=sys.stderr)
        return 66
    verifier = Verifier(manifest_path, report_path, manifest, report)
    errors = verifier.run()
    for warning in verifier.warnings:
        print(f"warning={warning}", file=sys.stderr)
    if errors:
        print("status=failed", file=sys.stderr)
        print(f"error_count={len(errors)}", file=sys.stderr)
        for error in errors:
            print(f"error={error}", file=sys.stderr)
        return 2
    print("status=ok")
    print(f"profile={PROFILE}")
    print("check=metadata,shared-scale,claim-evidence,visual-review,png-link,stft-window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
