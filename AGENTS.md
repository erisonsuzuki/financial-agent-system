# AGENTS.md

## Purpose
- This file guides agentic coding tools working in this repo.
- Prefer existing conventions over introducing new ones.
- Keep instructions practical and repository-specific.

## Repo map
- Backend (FastAPI) lives in `app/`; Poetry manages dependencies in `app/pyproject.toml`.
- Frontend (Next.js App Router) lives in `web/`.
- Agent configs are YAML in `app/agents/configs/`.
- Agent orchestration is in `app/agents/orchestrator_agent.py` and tools in `app/agents/tools.py`.
- Routers are in `app/routers/` (agent endpoints in `app/routers/agent.py`).
- Web dashboard and components are in `web/app/`.

## Build, lint, test commands
- Full stack (Docker Compose): `make up` (builds API, Web, Postgres).
- Stop/clean containers: `make down` / `make clean`.
- Logs: `make logs` (or `docker compose logs -f api` / `docker compose logs -f web`).
- API shell: `make shell` (container bash).
- DB shell: `make db-shell` (psql).
- Update API deps: `make update-deps` (runs `poetry update` in container).
- Audit deps: `make audit` (runs `pip-audit` and `npm audit`).

### API (FastAPI)
- Run tests in container: `make test` (runs `docker compose exec api pytest`).
- Run a single test file: `docker compose exec api pytest tests/test_<name>.py`.
- Run a single test by name: `docker compose exec api pytest tests/test_<name>.py -k "<filter>"`.
- Debugging: `docker compose exec api bash`, then run `pytest` directly.

### Web (Next.js)
- Dev server: `npm run dev --prefix web` (or `make web-dev`).
- Lint: `npm run lint --prefix web` (Next ESLint rules).
- Build: `npm run build --prefix web`.
- Tests: `npm run test --prefix web` (Vitest run).
- Single test file: `npm run test --prefix web -- path/to/test.spec.tsx`.
- Single test by name: `npm run test --prefix web -- -t "test name"`.

## Agent command shortcuts
- Registration agent: `make agent-register q="..."`.
- Management agent: `make agent-manage q="..."`.
- Analysis agent: `make agent-analyze q="..."`.
- Debug raw agent output: `make agent-debug q="..."`.

## Environment and secrets
- API expects: `LLM_PROVIDER`, `LLM_FALLBACK_PROVIDER`, `GROQ_MODEL`, `GROQ_API_KEY`, `NVIDIA_MODEL`, `NVIDIA_API_KEY`, `JWT_SECRET_KEY`, `INTERNAL_API_URL`, and Postgres creds.
- Web uses `FASTAPI_BASE_URL` to point to the API.
- Never commit secrets or real tokens.

## Docker notes
- Compose file: `docker-compose.yml`.
- Containers: `api`, `web`, `db`.
- Ports: API `8000:8000`, Web `3000:3000`, Postgres internal only.
- Postgres data persists via `postgres_data` volume.
- Health checks: API `/health`, Postgres `pg_isready`.

## Local URLs
- API: `http://localhost:8000`.
- Web: `http://localhost:3000`.

## Change checklist
- Update docs in `docs/` when workflows, env vars, or endpoints change.
- Keep `.env.sample` in sync with new variables.
- Add/adjust tests when modifying tools, routers, or agent configs.
- Mock external services to keep tests hermetic.

## Code style guidelines

### Python (FastAPI, SQLAlchemy, Pydantic)
- Formatting: 4-space indents; keep lines readable; no formatter enforced.
- Imports: standard library, third-party, then local `app.*` imports.
- Naming: classes in `PascalCase`, functions/variables in `snake_case`, constants in `UPPER_SNAKE_CASE`.
- Typing: use explicit types for public functions; prefer `str | None` unions; keep return types clear.
- Error handling: raise `HTTPException` with explicit `status_code`; avoid bare `except` unless wrapping with context.
- JSON/IO: validate or guard against malformed inputs; default safely if parsing fails (see router JSON parsing pattern).
- DB models: keep SQLAlchemy models in `app/models.py`; use `relationship` and `back_populates` consistently.
- Schemas: use Pydantic `BaseModel` with `ConfigDict(from_attributes=True)` when mapping ORM objects.
- Logging: use module `logger` instead of print for service code.

### API patterns
- Router functions should be small and delegate heavy logic to `crud` or service modules.
- Favor dependency injection via `Depends` for DB sessions and authentication.
- Keep response models explicit in route decorators.
- Validate external calls; mock external services in tests.

### Data access and models
- Runtime DB is Postgres; tests use in-memory SQLite.
- SQLAlchemy models live in `app/models.py`.
- Pydantic schemas live in `app/schemas.py`.
- CRUD helpers live in `app/crud.py` (keep DB logic out of routers).

### Tests (pytest)
- Tests live under `tests/`.
- Tests use in-memory SQLite; avoid relying on Postgres in tests.
- Mock external services (HTTP, LLM) with `respx` or fixtures.
- Prefer clear Arrange/Act/Assert blocks; keep test names descriptive.

### TypeScript / React / Next.js
- Formatting: 2-space indent, semicolons, double quotes (match existing files).
- Imports: React/Next first, third-party next, then local; use `import type` for type-only imports.
- Paths: use `@/` alias per `web/tsconfig.json` when importing from `web/app`.
- Naming: components in `PascalCase`, hooks in `useSomething`, local vars in `camelCase`.
- Types: use `interface` for props, `type` for data shapes; keep exported types explicit.
- Client components: include `"use client"` at the top when using hooks/state.
- Data fetching: guard `res.ok` and handle `401` explicitly; return typed JSON.
- Error handling: throw user-friendly errors from hooks; render fallback UI for empty states.

### Web app structure
- App Router pages and routes live in `web/app/`.
- API routes live under `web/app/api/`.
- Shared UI components live in `web/app/components/`.
- Data hooks live in `web/app/hooks/`.
- Shared types live in `web/app/types/`.

### React Query usage
- Use `useQuery` for fetches; key on auth state where relevant.
- Include `credentials: "include"` when calling API routes that use cookies.
- Prefer `cache: "no-store"` for API routes that should not be cached.
- Provide friendly error messages for empty or error states.

### Styling (Tailwind)
- Keep Tailwind class lists readable; prefer semantic grouping (layout, spacing, color, state).
- Use existing color palette (slate, emerald, sky) unless a change is intentional.
- Avoid inline styles unless necessary.

## Deployment notes
- Render config: `render.yaml` (Docker deploy for API).
- Health check path: `/health`.
- If adding env vars, update `.env.sample` and docs.

## Repository hygiene
- Do not reformat entire files without reason; match surrounding style.
- Keep diffs minimal and scoped to the request.
- Avoid committing `.env` or secrets.

## Security checklist
- Do not log or commit secrets.
- Validate user input before storing or executing.
- Keep auth flows in `app/dependencies.py` and use `Depends` for protected routes.
- Use `HTTPException` for auth failures and clear status codes.
