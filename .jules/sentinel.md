## 2026-01-29 - Docker Container Running as Root
**Vulnerability:** The Dockerfile was configured to run the application as the root user. This is a critical security risk as it allows an attacker who compromises the application to have full control over the container and potentially escalate privileges to the host.
**Learning:** Default Docker images often run as root unless specified otherwise. It's easy to overlook this when focusing on functionality.
**Prevention:** Always include a user creation step in the Dockerfile (e.g., `useradd`) and switch to that user using the `USER` instruction before the `CMD` or `ENTRYPOINT`. Ensure file permissions are adjusted so the non-root user can access necessary files.
