# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `core/` (agents, flows, llm, knowledge; tools in `core/tools/`).
- Entrypoints: `main.py`, `example.py`, and runnable samples in `examples/`.
- Docs in `docs/`, CI in `.github/`, helper scripts in `scripts/`.
- Ephemeral runtime artifacts are written under `workspace/` (do not commit).

## Build, Test, and Development Commands
- Create env
  - `python -m venv .venv && source .venv/bin/activate`
- Install dependencies
  - `pip install -r requirements.txt`
- Configure environment
  - `cp .env.example .env` then set `OPENAI_API_KEY` (or see `README_OPENROUTER.md`).
  - Optional (GraphRAG): `docker-compose up -d`
  - If DGL issues occur: `source set_env.sh`
- Run locally
  - `python main.py --goal "..." [--workspace ./workspace] [--debug]`
- Examples
  - `python example.py`
- Tests
  - `python -m unittest discover -s tests -p "test_*.py"`
  - or `python test_enhanced_knowledge_sync.py` (legacy root test)

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation. Format with Black: `black .`.
- Use type hints and docstrings for public APIs.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep modules focused; prefer small, composable utilities under `core/`.

## Testing Guidelines
- Framework: `unittest`. Place new tests under `tests/` as `test_*.py`.
- Keep tests deterministic; mock external services. The system supports a "mock mode" when API keys are absent.
- Aim for coverage on core logic and error paths.

## Commit & Pull Request Guidelines
- Commits: small, descriptive, imperative. Examples: `feat:`, `fix:`, `chore(security):`. Reference issues (e.g., `#123`).
- PRs must include: what/why, test plan and outputs, logs/screenshots when relevant, and updates to docs/config samples. Follow `PR_DESCRIPTION.md`.
- Use `.github` workflows; see `docs/10-github-workflow.md` for labels/milestones.

## Security & Configuration Tips
- Never commit secrets. Use `.env` (git-ignored) and update `.env.example` when adding variables.
- Keep `config.json` free of tokens; prefer environment variables.
- Do not commit files under `workspace/`. Generated reports/plots should be stored under `workspace/artifacts/<plan_id>/`.

## Agent-Specific Notes
- Add new tools under `core/tools/` and register them with the relevant agent.
- When adding features that emit artifacts, write to `workspace/artifacts/<plan_id>/` so outputs are easy to locate and review.

