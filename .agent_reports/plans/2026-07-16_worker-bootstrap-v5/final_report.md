# Worker bootstrap isolation v5 — Final report

## Result

GREEN. Registered workers now receive one portable minimal kernel, exactly one
worker type, and one assigned capability/stage contract. Caller-supplied prompts
are wrapped by all three dispatchers. Detailed evidence stays in the canonical
artifact and the terminal return is exactly artifact path, verdict, and blocker.

Claude masked profiles no longer request blanket reads of the four main core
documents. Their declarations are typed and their attach layer contains only
runtime attachment/residual-inheritance guidance plus selected specialization.
Codex and OpenCode no longer explicitly load their full adapter bootstrap in a
worker prompt.

## Support boundary

- Claude profile projection: supported.
- Codex project `AGENTS.md` physical masking: runtime auto-discovery may remain;
  checked prompt-isolation fallback.
- OpenCode physical project-instruction masking: unverified; checked
  prompt-isolation fallback.

No total-token or cost reduction is claimed. The measured static typed worker
bootstrap range is 1,862–2,028 bytes, with a 1,571-byte shared kernel.
