up: down
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down --volumes --rmi all

logs:
	docker compose logs -f

shell:
	docker compose exec app bash

db-shell:
	docker compose exec db psql -U user -d financialdb

test:
	docker compose exec app pytest
