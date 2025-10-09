# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `core/` (agents, flows, llm, knowledge; tools in `core/tools/`).
- Entrypoints: `main.py`, `example.py`; samples in `examples/`.
- Tests in `tests/` as `test_*.py` (legacy root test supported).
- Docs in `docs/` (see `docs/20-continuous-thinking.md`), CI in `.github/`, helper scripts in `scripts/`.
- Runtime artifacts under `workspace/` (git-ignored). Task outputs go to `workspace/artifacts/<plan_id>/` and are continuously updated by the thinking loop.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Configure: `cp .env.example .env` and set `OPENAI_API_KEY` (or see `README_OPENROUTER.md`).
- Optional: GraphRAG `docker-compose up -d`; DGL issues `source set_env.sh`.
- Run: `python main.py --goal "..." [--workspace ./workspace] [--debug]`
- Examples: `python example.py`
- Tests: `python -m unittest discover -s tests -p "test_*.py"` or `python test_enhanced_knowledge_sync.py`

## Coding Style & Naming Conventions
- Python PEP 8 with 4-space indentation; format with Black: `black .`.
- Use type hints and docstrings for public APIs.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep modules focused and composable under `core/`.

## Testing Guidelines
- Framework: `unittest`; place new tests in `tests/` as `test_*.py`.
- Keep tests deterministic; mock externals. Without API keys, the system runs in “mock mode”.
- Cover core logic and error paths; avoid network dependence in CI.

## Commit & Pull Request Guidelines
- Commits: small, imperative; prefixes like `feat:`, `fix:`, `chore(security):`, `docs:`. Reference issues (e.g., `#123`).
- PRs include: what/why, test plan + outputs, logs/screenshots where relevant, and doc/config updates. Follow `PR_DESCRIPTION.md`.
- Use `.github` workflows; see `docs/10-github-workflow.md` for labels/milestones.

## Security & Configuration Tips
- Never commit secrets. Use `.env` (git-ignored) and update `.env.example` when adding variables.
- Keep `config.json` free of tokens; prefer environment variables.
- Do not commit `workspace/`. Store reports/plots in `workspace/artifacts/<plan_id>/`.

## Agent-Specific Notes
- Add new tools in `core/tools/` and register them with the relevant agent.
- When emitting artifacts, write to `workspace/artifacts/<plan_id>/` for easy discovery; artifacts are refined continuously.

