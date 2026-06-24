# Portfolio Safety

- Resolve authenticated financial endpoints through `get_current_portfolio` and pass `portfolio_id` into CRUD calls. (Portfolio ownership is the isolation boundary; skipping it risks cross-user access.)
- Set and reset a real `ToolContext` around portfolio-reading or portfolio-writing agent execution and tool tests. (Agent tools depend on request-scoped user, portfolio, and DB session state and fail fast without it.)
- Keep portfolio agent tools on scoped CRUD calls instead of internal self-HTTP requests. (The security model relies on in-process portfolio context, not unauthenticated loopback calls.)
