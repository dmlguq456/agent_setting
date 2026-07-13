# Pipeline summary

Status: complete.

Codex fleet rows now use the native state DB title immediately, with the JSONL name index
as compatibility fallback. Claude and Codex share a neutral sidecar/provider contract;
Haiku remains the default while a shell-free wrapper can select another small model.
Latest main was integrated without conflict; the change adds no adaptation-boundary failure.
