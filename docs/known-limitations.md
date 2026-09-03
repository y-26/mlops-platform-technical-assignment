# Known Limitations

- Deployment execution is simulated; it does not call Azure ML, AKS or another live model-serving platform.
- Authentication and role-based access control are not implemented. In production, approval and deployment actions should be restricted by role.
- Monitoring metrics are seeded sample data; there is no live metrics ingestion pipeline.
- The automated backend tests use SQLite for speed while Docker Compose runs PostgreSQL.
- The frontend has unit tests but no browser-level end-to-end test suite.
- Retry currently converts the simulated failure into a successful second attempt; a real system would retry the external deployment operation and preserve the external error details.
