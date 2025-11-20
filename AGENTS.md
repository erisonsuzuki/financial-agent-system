# AGENTS.md

## Dev environment tips
- Use Docker Compose to run everything: `make up` (builds FastAPI API, Next.js web, Postgres). Stop/clean with `make down` / `make clean`. Logs: `make logs`. Shells: `make shell` (api), `make db-shell` (psql). Compose file: `docker-compose.yml`.
- Backend (FastAPI) lives in `app/`; entrypoint and dependencies via Poetry. Local tests: `make test` (runs `pytest` inside the api container). Dev server is automatically started by Compose; API served at `http://localhost:8000`.
- Frontend (Next.js App Router) lives in `web/`. Convenience Make targets: `make web-install`, `make web-dev`, `make web-build`, `make web-lint`. When running under Compose, web is served at `http://localhost:3000` and points to the API via `FASTAPI_BASE_URL` env.
- Agent configs are YAML in `app/agents/configs/`; orchestrator and tools in `app/agents/`. Router endpoints for agents in `app/routers/agent.py`. Web chat/dashboard in `web/app/dashboard/`.
- Key env vars: copy `.env.sample` → `.env`. API expects Postgres creds and LLM settings (`LLM_PROVIDER`, `GOOGLE_MODEL`, `GOOGLE_API_KEY`/`OLLAMA_*`, `JWT_SECRET_KEY`, `INTERNAL_API_URL`). Web honors `FASTAPI_BASE_URL` (set to `http://api:8000` in Compose). Render deploy uses `render.yaml`.
- Makefile shortcuts for agent calls: `make agent-register q="..."`, `make agent-manage q="..."`, `make agent-analyze q="..."`.

## Testing instructions
- API tests: `make test` (runs `pytest` in the api container). Tests use in-memory SQLite (see `tests/conftest.py`); mock external services (e.g., market data) as needed.
- Frontend lint: `make web-lint` (currently `next lint`; note deprecation warning for Next 16—switch to `eslint .` when upgrading).
- Frontend build check: `make web-build`. Dev server: `make web-dev`.
- Run specific API tests: `docker compose exec api pytest tests/test_<name>.py -k "<filter>"`.
- Add/update tests when modifying tools, routers, or agent configs. Mock external calls (HTTP, LLM) to keep tests hermetic.
- Debugging tips: reproduce within the container (`docker compose exec api bash`), check env (`printenv`), and verify pytest uses the in-memory DB (not Postgres).

## PR instructions
- Ensure `make test` (API) and `make web-lint` / `make web-build` (web) pass before submitting.
- Keep changes aligned with the agent architecture: update YAML configs in `app/agents/configs/` and tool bindings as needed; adjust FastAPI routers and tests accordingly.
- Add/adjust README or docs in `docs/` when altering workflows, env vars, or endpoints.
- Document any new env vars and ensure `.env.sample` stays in sync.

### Docker & Containerization
- Build/start all services: `make up`. Stop: `make down`. Full cleanup (containers/images/volumes): `make clean`.
- Web and API images built from `web/Dockerfile` and `app/Dockerfile`. Volumes mount `./app` and `./tests` into the api container for live reload; Postgres data persisted via `postgres_data` volume.
- Ports: API `8000:8000`, Web `3000:3000`, Postgres internal (no host port). Health check on Postgres via `pg_isready`.
- Logs: `make logs` or `docker compose logs -f api` / `docker compose logs -f web`. Shell: `make shell` (api), `make db-shell` (psql).

### Deployment
- Render config: `render.yaml` (Docker deploy for FastAPI). Ensure env vars (`POSTGRES_*`, `LLM_PROVIDER`, `GOOGLE_MODEL`, `JWT_SECRET_KEY`, `FASTAPI_BASE_URL`) are set in Render dashboard. Health check path: `/health`.
- Next.js image served via `web/Dockerfile`; set `FASTAPI_BASE_URL` to the API’s public URL when web is deployed separately.

### Project Overview
- Backend: FastAPI with agent orchestration (LangChain). Agents configured via YAML in `app/agents/configs/`; orchestrator in `app/agents/orchestrator_agent.py`; tools in `app/agents/tools.py`; routers in `app/routers/`.
- Frontend: Next.js 15 (App Router) in `web/app/`; React Query for data fetching; dashboard at `web/app/dashboard/` with chat input (`web/app/components/ChatInput.tsx`) and action log (`web/app/components/ActionLogTable.tsx`). Asset sidebar and summaries via `web/app/api/assets-summary/route.ts` and `web/app/hooks/useAssetSummaries.ts`.
- Database: PostgreSQL (runtime), SQLite in-memory for tests. Models/schemas in `app/models.py` and `app/schemas.py`.

### Security Considerations
- JWT secret (`JWT_SECRET_KEY`) required by FastAPI auth; keep it out of source control. Tokens stored as HTTP-only cookies on the web side.
- LLM provider keys (`GOOGLE_API_KEY`, `OLLAMA_BASE_URL`) must be set per environment; do not commit secrets.
- Internal agent calls use `INTERNAL_API_URL` (defaults to `http://app:8000` in Docker). If you enforce auth on assets/transactions later, ensure tools send proper Authorization headers.

### Code Style Guidelines
- Python: follow FastAPI conventions; tests with pytest. No specific formatter config present—use standard tooling as needed.
- JS/TS: ESLint via Next.js config; TypeScript config in `web/tsconfig.json`; Tailwind config in `web/tailwind.config.ts`.
