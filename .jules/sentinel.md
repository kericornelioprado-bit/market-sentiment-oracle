## 2026-01-29 - Docker Container Running as Root
**Vulnerability:** The Dockerfile was configured to run the application as the root user. This is a critical security risk as it allows an attacker who compromises the application to have full control over the container and potentially escalate privileges to the host.
**Learning:** Default Docker images often run as root unless specified otherwise. It's easy to overlook this when focusing on functionality.
**Prevention:** Always include a user creation step in the Dockerfile (e.g., `useradd`) and switch to that user using the `USER` instruction before the `CMD` or `ENTRYPOINT`. Ensure file permissions are adjusted so the non-root user can access necessary files.

## 2026-05-23 - Auxiliary Dockerfiles Running as Root
**Vulnerability:** Found `Dockerfile.processor` running as root user. While the main `Dockerfile` was secured, auxiliary or secondary Dockerfiles were missed.
**Learning:** Security audits often focus on the main entry point. In microservices or multi-container setups, *all* Dockerfiles must be audited.
**Prevention:** Use a linter like `hadolint` or a policy check to scan all `Dockerfile*` patterns in the repository, not just `Dockerfile`.
