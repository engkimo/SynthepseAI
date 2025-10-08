# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `core/` (agents, flows, LLM, knowledge; tools in `core/tools/`).
- Entrypoints: `main.py`, `example.py`, and samples in `examples/`.
- Documentation in `docs/`; automation scripts in `scripts/`; CI in `.github/`.
- Workspace artifacts in `workspace/` (ephemeral; do not commit).

## Build, Test, and Development Commands
- Create env: `python -m venv venv && source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Configure: `cp .env.example .env` then set `OPENAI_API_KEY` and related vars.
- Optional (GraphRAG): `docker-compose up -d`
- Run locally: `python main.py --goal "..." [--workspace ./workspace]`
- Examples: `python example.py`
- Tests: `python -m unittest discover -s tests -p "test_*.py"` or `python test_enhanced_knowledge_sync.py`

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; format with Black (`black .`).
- Use type hints and docstrings for public APIs.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep modules focused; prefer small, composable utilities under `core/`.

## Testing Guidelines
- Framework: `unittest`.
- Location: place new tests under `tests/` as `test_*.py`; legacy root tests remain supported.
- Scope: cover `core/` logic and error paths; keep tests deterministic.
- External calls: mock services; rely on built-in “mock mode” when no API keys are set.

## Commit & Pull Request Guidelines
- Commits: small, descriptive, present imperative (e.g., `fix:`, `feat:`, `chore(security):`). Reference issues (`#123`).
- PRs must include: what/why, test plan and outputs, screenshots/logs when relevant, and updated docs/config samples.
- Use `.github` workflows to manage labels/milestones when needed; see `docs/10-github-workflow.md`.
- For larger changes, include an architecture note in `docs/`.

## Security & Configuration Tips
- Never commit secrets. Use `.env` (git-ignored); update `.env.example` when adding variables.
- Keep `config.json` free of private tokens; prefer environment variables.
- If DGL compatibility issues occur, run `source set_env.sh`.

