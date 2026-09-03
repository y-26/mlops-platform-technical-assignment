.PHONY: up test backend-test frontend-test
up:
	docker compose up --build
test: backend-test frontend-test
backend-test:
	cd backend && pytest --cov=app --cov-report=term-missing
frontend-test:
	cd frontend && npm test

