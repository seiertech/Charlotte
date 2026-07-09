# Charlotte Providers

Providers are model execution adapters.

Charlotte stays agent-agnostic by separating the book workflow from the model backend.

Supported provider modes:

- `mock` — deterministic local placeholder, no API key required
- `openai_compatible` — any `/chat/completions` compatible endpoint
- `nim` — NVIDIA NIM using OpenAI-compatible chat completions shape

Secrets must be supplied through environment variables, not committed to GitHub.
