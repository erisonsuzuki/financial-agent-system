# AGENTS.md

## High-signal repo map
- Backend is FastAPI in `app/`; entrypoint is `app/main.py` and all routers are mounted there.
- Frontend is Next.js App Router in `web/app/`.
- Agent runtime is in `app/agents/` (`orchestrator_agent.py`, `tools.py`, configs in `app/agents/configs/`).
- Router endpoint behavior: `/agent/query/router` classifies intent deterministically via `classify_agent_request` in `app/agents/tools.py`, then invokes the selected agent through `orchestrator_agent`.
- Core API layering: HTTP handlers in `app/routers/`, persistence logic in `app/crud.py`, schema contracts in `app/schemas.py`, ORM models in `app/models.py`.

## Commands you will actually need
- Start stack: `make up` (`api` on `:8000`, `web` on `:3000`, `db`).
- Start stack with hot-reload web: `make up-dev` (`web-dev` on `:3001`).
- Stop: `make down` (or `make down-dev` for dev profile).
- API tests (Dockerized): `make test`.
- Single API test file: `make test file=tests/test_main.py`.
- Single test by name: `docker compose exec api pytest tests/test_router_endpoint.py -k invalid_agent`.
- Web checks: `npm run lint --prefix web`, `npm run test --prefix web`, `npm run build --prefix web`.
- Security/dependency checks: `make audit`.

## Verified workflow quirks
- API tests run inside Docker and use SQLite via `tests/conftest.py`; Postgres is not required for unit tests.
- Running `pytest` on host can fail if host Python lacks `psycopg`; prefer `make test` unless you intentionally run host env tests.
- `tests/conftest.py` sets `JWT_SECRET_KEY` and overrides `get_db`; do not assume `.env` is loaded in pytest.
- `make test` only supports file-level targeting (`file=...`); use direct `docker compose exec api pytest ... -k ...` for case-level filtering.
- Docker web services use `FASTAPI_BASE_URL=http://api:8000`; standalone local web reads `FASTAPI_BASE_URL` from `web` env.

## CI and env gotchas
- Health workflow is `.github/workflows/api-health-ping.yml` and uses GitHub Actions `vars.FASTAPI_BASE_URL`.
- That job is bound to environment `financial-agent-system`; set `FASTAPI_BASE_URL` in that environment’s Variables, not only repo-level variables.
- LLM env contract in `.env.sample`: `LLM_PROVIDER=groq`, `MAIN_MODEL`, `FALLBACK_MODEL`, `GROQ_API_KEY`.

## Change rules specific to this repo
- If you add/change environment variables, update `.env.sample` and `README.md` in the same change.
- Keep router handlers small and move DB-heavy logic into `app/crud.py` or service modules.
- Do not commit secrets from `.env` or real API keys.
- If you change routing behavior, update both `README.md` execution flow and `tests/test_router_endpoint.py` (routing metadata and fallback assertions).
