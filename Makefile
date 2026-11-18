up:        ; docker compose up --build -d api worker
test:      ; docker compose run --rm --build test
test-local:; pip install -r requirements-dev.txt && pytest -v
down:      ; docker compose down -v
