## 2026-01-29 - Docker Container Running as Root
**Vulnerability:** The Dockerfile was configured to run the application as the root user. This is a critical security risk as it allows an attacker who compromises the application to have full control over the container and potentially escalate privileges to the host.
**Learning:** Default Docker images often run as root unless specified otherwise. It's easy to overlook this when focusing on functionality.
**Prevention:** Always include a user creation step in the Dockerfile (e.g., `useradd`) and switch to that user using the `USER` instruction before the `CMD` or `ENTRYPOINT`. Ensure file permissions are adjusted so the non-root user can access necessary files.

## 2026-05-23 - Auxiliary Dockerfiles Running as Root
**Vulnerability:** Found `Dockerfile.processor` running as root user. While the main `Dockerfile` was secured, auxiliary or secondary Dockerfiles were missed.
**Learning:** Security audits often focus on the main entry point. In microservices or multi-container setups, *all* Dockerfiles must be audited.
**Prevention:** Use a linter like `hadolint` or a policy check to scan all `Dockerfile*` patterns in the repository, not just `Dockerfile`.

## 2026-06-15 - Insecure Path Handling in Model Loading
**Vulnerability:** The `load_model` function in `src/dashboard/app.py` constructed file paths using unsanitized input (`f"models/lstm_{ticker}.keras"`). While the UI constrained the input, the backend function was vulnerable to path traversal if reused or if the UI was bypassed.
**Learning:** Hardcoded allowed lists in UI are insufficient security controls. Backend functions must validate inputs and enforce path confinement.
**Prevention:** Use `pathlib.Path.resolve()` combined with `path.is_relative_to(base_dir)` to ensure that resolved file paths are strictly within the intended directory.

## 2026-02-05 - Sensitive Data Exposure in API Calls and Silent Test Failures
**Vulnerability:** API keys were passed in URL query strings (visible in logs) instead of headers. Additionally, `tests/test_ingest.py` contained nested test functions due to indentation errors, causing pytest to silently skip them.
**Learning:** Transporting secrets in URLs is a common but dangerous anti-pattern. Test suite health (verifying test counts) is a security concern because "passing" suites may hide broken coverage.
**Prevention:** Enforce header-based authentication for APIs. Implement CI checks that alert on significant drops in test counts or use linters that detect unreachable code/nested tests.
