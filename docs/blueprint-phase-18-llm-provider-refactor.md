# Blueprint Phase 18: LLM Provider Refactor (Groq Primary + Nemotron Fallback)

## Task
Refactor LLM provider wiring to use Groq as the primary provider and NVIDIA Nemotron as the fallback. Replace Google/Ollama references. Use env vars:

- GROQ_API_KEY
- GROQ_MODEL
- NVIDIA_API_KEY
- NVIDIA_MODEL
- LLM_PROVIDER (groq | nvidia)
- LLM_FALLBACK_PROVIDER (default: nvidia)

## Proposed Plan (Initial)
1. Add Groq and NVIDIA LangChain dependencies.
2. Replace provider wiring in `app/agents/orchestrator_agent.py` with a provider registry and fallback logic.
3. Update `app/agents/config_loader.py` to resolve model names by provider.
4. Update `app/agents/configs/*.yaml` to use a neutral model placeholder.
5. Update `.env.sample`, `README.md`, `AGENTS.md`, `render.yaml`, and `docker-compose.yml` for new envs.
6. Add tests for provider selection and fallback behavior.

## Revised Plan (After Self-Review)

### 1) Provider Wiring and Fallback (Core)
- **Define provider registry** in `app/agents/orchestrator_agent.py` mapping `groq` and `nvidia` to their LangChain chat models.
- **Implement fallback around execution**, not only LLM creation. Use `with_fallbacks()` on the runnable/tool-calling pipeline or wrap `agent_executor.invoke()` in try/except that retries with fallback on transient failures.
- **Fallback criteria**: timeouts, 429s, 5xx, and connection errors trigger retry; validation errors do not.

### 2) Model Placeholder Strategy (Config Alignment)
- Replace `${GOOGLE_MODEL}` in all `app/agents/configs/*.yaml` with `${LLM_MODEL}`.
- Update `app/agents/config_loader.py` to resolve `${LLM_MODEL}` by provider:
  - `groq` -> `GROQ_MODEL`
  - `nvidia` -> `NVIDIA_MODEL`

### 3) Dependencies and Env Contract
- Add provider SDKs in `app/pyproject.toml` (confirm correct packages):
  - `langchain-groq`
  - `langchain-nvidia-ai-endpoints`
- Verify any required base URL or additional envs for NVIDIA SDK and document them if needed.

### 4) Docs and Deployment
- Update `.env.sample`, `README.md`, `AGENTS.md`, and `render.yaml` with Groq/NVIDIA defaults and `LLM_FALLBACK_PROVIDER`.
- Update `docker-compose.yml` only if env defaults are used there.

### 5) Tests
- Add unit tests for config loader model resolution based on `LLM_PROVIDER`.
- Add unit tests for fallback behavior (mock Groq failure; assert NVIDIA path used).

## Risks and Mitigations
- **Fallback integration risk**: If fallback is only on LLM creation, tool-calling failures will not trigger failover. Mitigate by wrapping execution.
- **SDK mismatch**: Wrong package or class name may break runtime. Mitigate by verifying LangChain provider packages and pin versions if needed.
- **Config drift**: Missing updates in YAMLs or docs can reintroduce Google/Ollama assumptions. Mitigate by sweeping configs and docs in the same change set.

## Acceptance Criteria
- `LLM_PROVIDER=groq` uses Groq by default.
- If Groq fails with transient errors, NVIDIA Nemotron is used automatically.
- Agent configs no longer reference Google/Ollama model envs.
- Docs and `.env.sample` reflect Groq/NVIDIA only.
- Tests cover model resolution and fallback behavior.

## Consolidated Execution Checklist
- [x] Confirm Groq/NVIDIA LangChain packages and add to `app/pyproject.toml`.
- [x] Implement provider registry and fallback around execution in `app/agents/orchestrator_agent.py`.
- [x] Update model placeholder resolution in `app/agents/config_loader.py`.
- [x] Replace `${GOOGLE_MODEL}` with `${LLM_MODEL}` in `app/agents/configs/*.yaml`.
- [x] Update `.env.sample`, `README.md`, `AGENTS.md`, and `render.yaml` for Groq/NVIDIA envs.
- [x] Add tests for model resolution and fallback behavior.
