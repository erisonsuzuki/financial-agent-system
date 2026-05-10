# AGENTS.md

## High-signal repo map
- Backend is FastAPI in `app/`; app entrypoint is `app/main.py` (routers are wired there).
- Frontend is Next.js App Router in `web/app/`.
- Agent system lives in `app/agents/` (`orchestrator_agent.py`, `tools.py`, configs in `app/agents/configs/`).
- Core API layers: routers in `app/routers/`, DB models in `app/models.py`, schemas in `app/schemas.py`, DB logic in `app/crud.py`.

## Commands you will actually need
- Start stack: `make up` (`api` on `:8000`, `web` on `:3000`, `db`).
- Dev web profile: `make up-dev` (starts `web-dev` on `:3001`).
- Stop: `make down` (or `make down-dev` for dev profile).
- API tests: `make test`.
- Single API test file: `make test file=tests/test_main.py`.
- Web checks: `npm run lint --prefix web`, `npm run test --prefix web`, `npm run build --prefix web`.
- Dependency/security audit: `make audit`.

## Verified workflow quirks
- API tests run inside Docker and use SQLite test DB via `tests/conftest.py`; they do not require Postgres.
- `tests/conftest.py` sets `JWT_SECRET_KEY` for tests; avoid assuming `.env` is loaded in pytest.
- `make test` supports only file-level targeting through `file=...`; use direct `docker compose exec api pytest ... -k ...` for test-name filtering.
- `web` container uses `FASTAPI_BASE_URL=http://api:8000` in Docker; local standalone web uses `.env` `FASTAPI_BASE_URL`.

## CI and env gotchas
- Health workflow is `.github/workflows/api-health-ping.yml` and uses GitHub Actions `vars.FASTAPI_BASE_URL`.
- That job is bound to environment `financial-agent-system`; set `FASTAPI_BASE_URL` in that environment’s Variables, not only repo-level variables.

## Change rules specific to this repo
- If you add/change environment variables, update `.env.sample` and `README.md` in the same change.
- Keep router handlers small and move DB-heavy logic into `app/crud.py` or service modules.
- Do not commit secrets from `.env` or real API keys.
