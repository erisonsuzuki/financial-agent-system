up: down
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down --volumes --rmi all

update-deps:
	docker compose exec --workdir /code/app app poetry update
	
logs:
	docker compose logs -f

shell:
	docker compose exec app bash

db-shell:
	docker compose exec db psql -U user -d financialdb

test:
	docker compose exec app pytest

# Send a query to the registration agent. Usage: make agent-query q="your question"
agent-query:
	@curl -s -X POST http://localhost:8000/agent/query/registration_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Send a query to the management agent
agent-manage:
	@curl -s -X POST http://localhost:8000/agent/query/management_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"
