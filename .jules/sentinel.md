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

## 2026-02-08 - API Key Exposure in URL Parameters
**Vulnerability:** The `fetch_news` function in `src/data/ingest_news.py` was passing the `NEWS_API_KEY` as a query parameter in the GET request URL. This exposes the API key in proxy logs, browser history, and request logs.
**Learning:** Even when using HTTPS, query parameters are visible in logs. Documentation often shows query parameters as the "easy" way, leading to insecure implementations.
**Prevention:** Always prefer sending API keys and sensitive tokens in HTTP headers (e.g., `X-Api-Key` or `Authorization`) rather than URL query parameters. Use `requests.get(url, headers=...)`.
