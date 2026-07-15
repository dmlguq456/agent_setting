# Checklist

- [x] Portable sibling-adapter contract is canonical.
- [x] Claude, Codex, and OpenCode bootstraps are each <=16,384 bytes.
- [x] Active skill metadata surfaces are each <=7,000 chars and duplicate activation is rejected.
- [x] Skill conformance scans all three native adapter trees plus the Claude compatibility mirror.
- [x] Normal/unknown/repeated hook samples inject 0 bytes; allowed transition directive remains <=240 bytes.
- [x] Stored footprint baseline rejects >5% regression.
- [x] Generated projections and manifests are current.
- [x] Adapter boundary, conformance, footprint, and runtime doctor checks pass or record a precise runtime-only limitation.
- [x] Source changes are committed, integrated, and pushed in this completion flow.
