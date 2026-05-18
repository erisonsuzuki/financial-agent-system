# Implementation Blueprint: Phase 21 - Priority 1 Security and Multi-user Isolation

## Overview
Implement Priority 1 from `local/architecture_analysis.md` with a user-owned data model, authenticated financial and agent endpoints, and context-aware agent tools.

This phase hardens the current architecture to prevent cross-user data access, removes runtime schema mutation, and standardizes database migrations with Alembic.

## Final Decisions
- **Ownership model**: User-owned assets scoped by portfolio (`portfolio_id`), with per-portfolio ticker uniqueness.
- **Direct agent endpoint transition**: Short transition. Keep `/agent/query/{agent_name}` temporarily, require auth immediately, and migrate callers to `/agent/query/router` before removal.
- **Tool execution model**: Enforce a context contract (`user_id`, `portfolio_id`, `db_session`) for all portfolio-changing/reading tools.

## Implementation Phases

### Phase 1: Alembic foundation and runtime DDL removal
**Objective**: Make migrations the single source of schema truth.

**Code Proposal**:
```python
# app/main.py
# Remove startup schema mutation and startup DDL/data-fix logic:
# - models.Base.metadata.create_all(bind=engine)
# - ensure_dividend_uniqueness_constraint(...)
```

```text
# New files
alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/<revision>_phase21_priority1_baseline.py
```

**Acceptance Criteria**:
- App startup no longer creates or mutates DB schema.
- `alembic upgrade head` succeeds on a clean DB.

**Tests**:
- Migration smoke test for clean upgrade.
- App startup test to confirm no runtime DDL behavior.

### Phase 2: Ownership schema (user-owned assets + portfolio scope)
**Objective**: Introduce hard ownership boundaries at the data layer.

**Code Proposal**:
```python
# app/models.py (conceptual)
class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="Default")

class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_assets_portfolio_ticker"),
    )
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)

class Transaction(Base):
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)

class Dividend(Base):
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
```

**Migration/Backfill Plan**:
1. Add `portfolios` and nullable ownership columns.
2. Create a legacy owner user + default portfolio.
3. Backfill existing rows to legacy portfolio.
4. Validate no NULL ownership rows remain.
5. Enforce NOT NULL, FKs, and new scoped uniqueness.

**Acceptance Criteria**:
- Same ticker can exist in different portfolios.
- Ownership fields are non-null after migration.
- Existing data is preserved and assigned to a valid owner.

**Tests**:
- Model/CRUD tests for scoped uniqueness.
- Migration test for backfill correctness.

### Phase 3: Scoped CRUD and auth enforcement
**Objective**: Ensure all financial operations are authenticated and ownership-filtered.

**Code Proposal**:
```python
# app/routers/assets.py (pattern)
@router.get("/")
def list_assets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    portfolio = crud.get_or_create_default_portfolio(db, user_id=current_user.id)
    return crud.get_assets(db, portfolio_id=portfolio.id)
```

**Changes**:
- Add `get_current_user` to all financial routes:
  - `app/routers/assets.py`
  - `app/routers/transactions.py`
  - `app/routers/dividends.py`
- Update `app/crud.py` methods to require scope (`portfolio_id`) for read/write/delete.
- Enforce ownership checks before returning or mutating rows.

**Acceptance Criteria**:
- Unauthenticated calls return `401`.
- User A cannot read/update/delete user B data.

**Tests**:
- Update endpoint tests for `401` and cross-user isolation.
- Verify nested routes also enforce ownership (`/assets/{asset_id}/transactions`, etc.).

### Phase 4: Agent endpoint transition (short)
**Objective**: Secure direct agent endpoint immediately while preserving short-term compatibility.

**Changes**:
- Protect `/agent/query/{agent_name}` with `Depends(get_current_user)`.
- Keep endpoint functional for transition period.
- Add warning in logs and docs that route is transitional; preferred route is `/agent/query/router`.

**Acceptance Criteria**:
- Direct endpoint requires auth now.
- Existing authenticated callers continue working.

**Tests**:
- `401` without token on direct and router endpoints.
- Success path with valid token on direct endpoint during transition.

### Phase 5: Tool context contract and internal HTTP removal
**Objective**: Make tools run with explicit user context and no self-HTTP dependency for core portfolio operations.

**Context Contract**:
```python
# app/agents/tool_context.py
@dataclass
class ToolContext:
    user_id: int
    portfolio_id: int
    db_session: Session
```

**Wiring Proposal**:
1. `app/routers/agent.py` authenticates user, resolves active portfolio, creates `ToolContext`.
2. Orchestrator invocation receives and propagates `ToolContext`.
3. Tools consume context and call scoped CRUD directly.
4. Missing context raises controlled error (no global fallback).

**Changes**:
- Refactor `app/agents/tools.py` to replace internal `httpx` calls for assets/transactions/dividends with direct CRUD + DB session.
- Keep output contract stable (`status`, `message`, optional `data`).

**Acceptance Criteria**:
- Tool execution is scoped to the request user/portfolio.
- Tool calls fail fast when context is absent.
- No internal unauthenticated self-calls for core portfolio operations.

**Tests**:
- Tool unit tests for with-context success and missing-context failure.
- Agent endpoint integration test validating scoped tool effects.

### Phase 6: Documentation and operations alignment
**Objective**: Keep workflows and docs aligned with secure behavior.

**Required Updates**:
- `README.md`:
  - auth requirement for financial and agent endpoints;
  - direct endpoint marked transitional.
- `.env.sample`:
  - remove/deprecate `INTERNAL_API_URL` if no longer required by tools.
- `Makefile`:
  - update `agent-*` commands to authenticated flow.

**Acceptance Criteria**:
- Docs and dev commands reflect actual auth and routing behavior.

## Test Strategy (Must-pass)
- Backend auth matrix:
  - `401` for unauthenticated `/assets`, `/transactions`, `/dividends`, `/agent/query/{agent_name}`, `/agent/query/router`.
- Isolation matrix:
  - user A cannot access user B assets/transactions/dividends.
- Transition matrix:
  - direct endpoint still works with auth during short transition.
- Tool matrix:
  - missing `ToolContext` fails predictably;
  - valid context only affects scoped portfolio data.
- Migration matrix:
  - `alembic upgrade head` on clean DB;
  - backfill path for legacy rows.

## Execution Checklist
- [ ] Add Alembic scaffolding and baseline migration.
- [ ] Remove runtime schema mutation and startup DDL fixes from `app/main.py`.
- [ ] Implement `Portfolio` and ownership FKs/constraints in `app/models.py`.
- [ ] Add backfill migration for legacy data and enforce NOT NULL ownership constraints.
- [ ] Refactor CRUD to require and enforce `portfolio_id` scope.
- [ ] Add auth dependencies to all financial endpoints.
- [ ] Protect `/agent/query/{agent_name}` and mark as transitional.
- [ ] Implement `ToolContext` contract and orchestrator/tool wiring.
- [ ] Refactor tools off internal HTTP calls for core portfolio operations.
- [ ] Update tests for auth, isolation, transition, tools, and migration behavior.
- [ ] Update `README.md`, `.env.sample`, and `Makefile` for new behavior.

## Definition of Done
- All Priority 1 architecture requirements are implemented with user-owned asset scoping.
- No financial or agent query endpoint is publicly accessible without authentication.
- Cross-user data leakage tests pass for assets, transactions, dividends, and agent flows.
- Tool execution is context-scoped and fails safely without required context.
- Alembic is the canonical migration path and startup performs no runtime schema mutation.
- Docs and developer commands are updated and accurate.
