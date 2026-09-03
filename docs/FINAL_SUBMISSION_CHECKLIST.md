# Final Submission Checklist

Before sending the repository:

- [ ] Replace `[Your Name]` and repository placeholders in the submission email draft.
- [ ] Push the project using meaningful commits rather than one large generated commit.
- [ ] Run `docker compose up --build` on your laptop and verify all three containers become healthy.
- [ ] Open the Angular UI at `http://localhost:4200`.
- [ ] Open Swagger at `http://localhost:8000/docs`.
- [ ] Run backend tests from `backend`: `pytest --cov=app --cov-report=term-missing`.
- [ ] Run frontend tests: `npm test`.
- [ ] Run frontend build: `npm run build`.
- [ ] Test an unapproved production deployment and confirm HTTP 409.
- [ ] Test a successful deployment, simulated failure, retry and rollback.
- [ ] Capture 2–4 screenshots of the running UI and place them in `docs/screenshots/`.
- [ ] Confirm `.env`, virtual environments, caches, `node_modules`, database files and coverage files are not committed.
- [ ] Read `docs/PROJECT_WALKTHROUGH.md` and be able to explain each section without reading from it.
