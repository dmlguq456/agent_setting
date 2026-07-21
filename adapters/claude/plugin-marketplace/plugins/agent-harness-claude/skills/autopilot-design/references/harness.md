# Visual Harness

The pipeline centers on a feedback loop in which the agent renders its own artifact, inspects pixels, and corrects defects.

| # | Component | Location | Responsibility |
|---|---|---|---|
| 1 | **Design MCP Server** | `~/.claude/tools/design-mcp/` (`mcp__design__*`) | `preview`, `screenshot`, `getConsoleLogs`, `eval_js`, `view_image`, and `image_metadata`; primary visual feedback loop |
| 2 | **Verifier unit** | `design/verifier` unit, dispatched as a sibling review node | Independent two-layer breakage gate and vision pass rate: zero-tolerance console, layout, and token checks followed by visual-consistency assessment |
| 3 | **Design rules** | `roles/units/design/_design-rules.md` | Prompt contract for slop avoidance, visual defaults, scale, HTML conventions, and variants |
| 4 | **Scaffolds** | `~/.claude/scaffolds/` | `deck_stage`, `tweaks_panel`, `device_frames`, `design_canvas`, and `image_slot` |
| 5 | **Converters** | `~/.claude/tools/design-mcp/convert.mjs` | PDF, self-contained HTML bundle, and PPTX |
| 6 | **Post-write hook** | `~/.claude/hooks/design-postwrite.sh` | Automatic console check after design HTML writes; opt out with `DESIGN_POSTWRITE_HOOK=0` |

`design-init` provisions, registers, and smoke-tests the Design MCP automatically. Missing local tooling does not stop the pipeline; see specification §0.5.
