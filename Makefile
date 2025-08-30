# Build and start the services in detached mode
up:
	docker compose up -d --build

# Stop and remove the services
down:
	docker compose down

# Show logs for all services
logs:
	docker compose logs -f

# Access the application container's shell
shell:
	docker compose exec app bash
