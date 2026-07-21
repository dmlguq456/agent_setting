# Role Mode Inventory

`roles/modes/` contains the canonical mode-level personas and procedures used by
portable role profiles. Runtime adapters either project these fragments into a
native mode surface or consume them through an adapter mapping. A projection may
add runtime realization details and is not required to be byte-identical; the
portable behavior starts here, while concrete tools and fallbacks remain
adapter-owned.

## Universal Review Stance

Every review- or verification-type mode in this inventory — the qa family
(`code-review`, `plan-review`, `test`, `security-review`, `data-curate`), the
research review and verification modes (`plan-review`, `fact-check`,
`claim-verify`), and the design `critic`/`verifier` and editorial `review`
modes — operates under the refute-by-default adversarial stance of
`CONVENTIONS §1.1`, regardless of the intensity that dispatched it. The
reviewer tries to falsify the artifact, names at least one concrete failure
mode, and treats inadequate evidence as not proven rather than a pass. A mode
file may reinforce this stance in its own words but never lowers it.
`claim-verify` is default-refute and fully satisfies it. `security-review` is
adversarial in its threat-tracing but deliberately deviates on output: its
high-confidence filter (confidence 8–10, drop ambiguity) may name zero
findings, so its silence means "no HIGH/MEDIUM found," never "proven safe."
That domain-justified deviation on the name-a-failure-mode and not-proven
prongs is a declared carve-out, not automatic satisfaction of the stance. This
is a stance inside whatever check runs, distinct from the separate cross-harness
adversary *pass* that only higher intensities add.

## Status Classes

| Status | Meaning |
|---|---|
| `portable-persona` | Runtime-neutral role behavior. Can be reused by adapters with minimal wrapping. |
| `portable-with-tool-contract` | Mostly portable, but assumes named deterministic tools or external CLIs that an adapter must provide or replace. |
| `mixed` | A family whose individual modes span both portable-persona and portable-with-tool-contract status. |
| `adapter-coupled` | Contains a runtime-specific invocation or path that must be split out before the fragment can be canonical. This is a migration state, not a supported portable contract. |

## Inventory

| Mode family | Files | Portable status | Adapter requirement |
|---|---|---|---|
| `dev` | `backend`, `frontend`, `new-lib`, `refactor` | `portable-persona` | Keep the personas shared. Renderable frontend work still obeys the active adapter's visual-verification requirements. |
| `editorial` | `translate`, `polish`, `review` | `portable-persona` | Keep shared; adapter only maps invocation and edit tools. |
| `qa` | `code-review`, `data-curate`, `ml-debug`, `plan-review`, `security-review`, `test` | mixed | Review and static security modes are portable personas. `test` requires an adapter-provided verification runner or an explicit unavailable report. |
| `research` | `plan-review`, `research-survey`, `fact-check`, `claim-verify` | mixed | Planning, survey, and local fact-check modes are portable personas. `claim-verify` requires an adapter-provided external verification contract. |
| `material` | `browser-fetch`, `data-script`, `figure-gen`, `pdf-extract`, `web-image-search` | `portable-with-tool-contract` | Requires adapter-provided browser/pdf/script/web fetch tools plus memory wrapper or `<agent-home>` memory CLI resolution. |
| `design` | `_design_rules`, `maker`, `critic`, `verifier` | `portable-with-tool-contract` | Render/check semantics are portable; concrete browser rendering, screenshots, console capture, DOM inspection, and image generation are adapter-owned tool surfaces. |

## Adapter Rule

Adapters consume these canonical fragments through their own bootstrap and mode
mapping. Claude Code keeps concrete mode files under
`adapters/claude/agent-modes/`; Codex generates native guides under
`adapters/codex/modes/`; OpenCode currently resolves support and fallbacks
through its adapter mapping rather than a generic native mode directory. The
active adapter bootstrap and `mode-info <family/mode>` output are authoritative
for the runtime realization. An adapter must not claim a mode is supported
unless it provides:

- equivalent tools or documented fallbacks;
- runtime-neutral `<agent-home>` path resolution;
- a mapping from each named tool contract to the adapter runtime;
- a clear unsupported report when the mode depends on a missing visual/browser
  or verification harness.

Adapter `mode-info <family/mode>` should report machine-readable
`tool_contract`, optional `tool_contract_check`, `runtime_surface`, and
`fallback` fields for conditional or unsupported modes so callers can decide
whether the runtime has an equivalent native surface, can run a deterministic
check, or must downgrade.
