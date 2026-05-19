up:
	docker compose up -d --build

up-dev:
	docker compose --profile dev up -d --build
	
down:
	docker compose down

down-dev:
	docker compose --profile dev down

clean:
	docker compose down --volumes --rmi all

update-deps:
	docker compose exec --workdir /code/app api poetry update
	
logs:
	docker compose logs -f

shell:
	docker compose exec api bash

db-shell:
	docker compose exec db psql -U user -d financialdb

# Usage: make test file=tests/test_example.py
test:
	@if [ -n "$(file)" ]; then \
		docker compose exec api pytest -- "$(file)"; \
	else \
		docker compose exec api pytest; \
	fi

api-audit:
	docker compose exec --workdir /code/app api poetry run pip-audit

web-test:
	npm run test --prefix web

web-audit:
	docker compose run --rm -e NODE_ENV=development -v $(PWD)/web:/app -v web_node_modules:/app/node_modules -w /app web sh -lc "npm install --include=dev && npm audit --audit-level=high"

audit: api-audit web-audit

# Check current DB revision vs Alembic head
migrate-check:
	@docker compose exec api sh -lc 'cd /code/app && echo "Current:" && alembic -c alembic.ini current || true; echo "Head:" && alembic -c alembic.ini heads'

# Run migrations only when DB is behind head
migrate:
	@docker compose exec api sh -lc 'cd /code/app && python scripts/migrate.py'

# Explicitly stamp current schema at head (for legacy DBs already matching schema)
migrate-stamp:
	@docker compose exec api sh -lc 'cd /code/app && ALLOW_ALEMBIC_STAMP=1 python scripts/migrate.py'

web-dev:
	npm run dev --prefix web

# Send a query to the registration agent. Usage: make agent-query q="your question"
agent-register:
	@curl -s -X POST http://localhost:8000/agent/query/registration_agent \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer $(AUTH_TOKEN)" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Send a query to the management agent
agent-manage:
	@curl -s -X POST http://localhost:8000/agent/query/management_agent \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer $(AUTH_TOKEN)" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Send a query to the analysis agent
agent-analyze:
	@curl -s -X POST http://localhost:8000/agent/query/analysis_agent \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer $(AUTH_TOKEN)" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Debug agent queries to see raw output
agent-debug:
	@curl -X POST http://localhost:8000/agent/query/management_agent \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer $(AUTH_TOKEN)" \
	-d '{"question": "$(q)"}'
