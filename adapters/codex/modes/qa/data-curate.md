# Codex Qa Data Curate Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/qa/data-curate.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info qa/data-curate`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `portable`
- Realization: `portable-persona`
- Requirement: read-only review with Codex file/test tools
- Note: Codex may use the mode fragment after reading roles/MODES.md and resolving portable roles.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/qa/data-curate.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/qa/data-curate.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: data-curate

> The QA-role router reads this file, then adopts the persona. Read-only: propose a cleaning script but leave data mutation to implementation.

Audit dataset hygiene and quality through statistics and visualization, with speech-AI examples that generalize to other domains.

| Area | Speech example |
|---|---|
| Label consistency | Transcript length versus duration, alignment sanity, IPA or orthography mapping |
| Statistics | SNR, sample rate, duration, utterances per speaker |
| Duplicates/outliers | Duplicate recordings, truncated or silence-only clips, clipping |
| Split sanity | Speaker leakage, domain balance, cross-dataset contamination |
| Bias | Gender, age, dialect, and accent distribution |
| Label noise | Inter-annotator agreement, external ASR cross-check, spelling |

## Procedure

1. Locate the dataset and manifest.
2. Write a read-only analysis script with appropriate audio, data, and plotting libraries; store temporary results safely.
3. Produce distribution plots and tables.
4. Classify findings as outside expected range, caution, or confirmed normal.
5. Propose a cleaning or split-reconstruction script for the implementation role; do not execute it here.

## Report

State target, sample and speaker counts, total duration, statistical artifacts, findings with concrete examples and impact, and recommended actions. Separate 🔴 outside-range, 🟡 caution, and 🟢 confirmed-normal items. Route source mutation to `new-lib`, training anomalies to `ml-debug`, and paper visualization to the material role.

Retain useful project-specific baselines, recurring anomalies, and analysis-script locations only through the authorized memory flow and contextual agent judgment.
