# Implementation Blueprint: Phase 19 - Asset Valuation with P/L and 1h Price Cache

## Overview
Add current price and returns to the dashboard sidebar, backed by yfinance with a 1-hour shared cache persisted in DB. Expose freshness metadata and support user-triggered refresh from authenticated flows.

This revision resolves scope ambiguities from prior drafts:
- Endpoints in this phase are treated as authenticated (`Depends(get_current_user)`) to prevent unauthenticated refresh abuse.
- Return semantics are explicit:
  - `financial_return_*`: price-only return.
  - `total_return_*`: price return plus dividends.
- DB cache is the source of truth for 1h TTL in request paths touched by this phase.

## Implementation Phases

### Phase 1: Persisted price cache (DB)
**Objective**: Store per-ticker price with timestamp for 1h TTL, reusable across processes and restarts.

**Code Proposal**:
```python
# app/models.py (new model)
class AssetPriceCache(Base):
    __tablename__ = "asset_price_cache"
    ticker = Column(String, primary_key=True)  # canonical uppercase ticker
    price = Column(Numeric(10, 2), nullable=False)
    source = Column(String, default="yfinance", nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)

# app/crud.py (helpers)
def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()

def get_cached_price(db, ticker): ...

def upsert_cached_price(db, ticker, price, source):
    # Use DB-agnostic upsert strategy compatible with SQLite tests + Postgres runtime
    # via Session.merge() on PK ticker
    ...
```

**Notes**:
- Follow existing project pattern (`models.Base.metadata.create_all(...)` in `app/main.py`).
- If Alembic is introduced later, add migration for `asset_price_cache`.

**Acceptance Criteria**:
- Cache keys are normalized consistently (e.g., `aapl` and `AAPL` resolve to one row).
- Upsert updates existing rows without duplicate ticker records.
- TTL cutoff uses UTC-aware timestamps.

**Tests**:
- CRUD roundtrip persists price, source, and timestamp.
- Normalization test covers mixed case and whitespace.
- Upsert test verifies overwrite behavior for same ticker.

### Phase 2: Market data agent uses DB cache + force refresh
**Objective**: Integrate DB cache into price fetch with deterministic stale fallback behavior.

**Code Proposal**:
```python
def get_current_price(
    ticker: str,
    db: Session | None = None,
    force_refresh: bool = False,
) -> tuple[Decimal | None, bool]:
    # Returns: (price, is_stale)
    # 1) Canonicalize ticker
    # 2) If db and not force_refresh and cache fresh (< 3600s), return cached (False)
    # 3) Else fetch via yfinance (existing _ticker_candidates)
    # 4) On success, upsert cache and return fresh price (False)
    # 5) On fetch failure, return stale cached price (True) if present; else (None, False)
```

**Notes**:
- For this phase's request paths, DB cache controls freshness. Existing in-memory cache should be bypassed or reduced so TTL behavior is consistent and testable.

**Acceptance Criteria**:
- `force_refresh=True` bypasses fresh cache and attempts provider fetch.
- If provider fails and stale exists, stale is returned with `is_stale=True`.
- If provider fails and no cached value exists, endpoint path can return 404.

**Tests**:
- Fresh cache returns without calling yfinance (mocked).
- Expired cache triggers fetch and updates cache.
- `force_refresh=True` triggers fetch even if cache is fresh.
- Fetch failure returns stale cached value when available.

### Phase 3: API endpoints for price/analysis with refresh and metadata
**Objective**: Surface current price and return metrics with freshness metadata and optional refresh.

**Code Proposal**:
```python
# app/routers/assets.py
@router.get("/{ticker}/price", response_model=schemas.AssetPrice)
def get_asset_price(
    ticker: str,
    refresh: bool = False,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    price, is_stale = market_data_agent.get_current_price(ticker, db=db, force_refresh=refresh)
    if price is None:
        raise HTTPException(status_code=404, detail="Price unavailable")

    cached = crud.get_cached_price(db, ticker)
    return schemas.AssetPrice(
        ticker=ticker.upper(),
        price=price,
        source=cached.source,
        fetched_at=cached.fetched_at,
        is_stale=is_stale,
    )

# schemas.AssetPrice: add fetched_at: datetime and is_stale: bool
# schemas.AssetAnalysis: add fetched_at: datetime | None and is_stale: bool
# portfolio_analyzer_agent.analyze_asset(..., refresh: bool = False): pass refresh through

# Return formulas:
# financial_return_value = (qty * current_price) - (qty * average_price)
# financial_return_percent = financial_return_value / (qty * average_price) * 100
# total_return_value = financial_return_value + total_dividends_received
# total_return_percent = total_return_value / (qty * average_price) * 100
```

**Acceptance Criteria**:
- `refresh=true` changes behavior only by forcing provider fetch attempt.
- Both endpoints return `fetched_at` and `is_stale` when price is available.
- 401 and 404 semantics are explicit and covered by tests.

**Tests**:
- `tests/test_assets.py`: `/assets/{ticker}/price` includes freshness metadata and honors refresh.
- `tests/test_portfolio_analyzer_agent.py`: verifies return formulas and refresh passthrough.
- `tests/test_market_data_agent.py`: verifies tuple return contract and stale behavior.

### Phase 4: Frontend assets-summary endpoint includes price/returns/freshness
**Objective**: Extend `/app/api/assets-summary` with current price, return fields, and freshness metadata.

**Code Proposal**:
```ts
// web/app/api/assets-summary/route.ts
type AssetAnalysis = {
  total_quantity: number;
  average_price: string;
  current_market_price: string | null;
  financial_return_value: string | null;   // price-only
  financial_return_percent: string | null; // price-only
  total_dividends_received: string;
  total_return_value: string | null;       // price + dividends
  total_return_percent: string | null;     // price + dividends
  fetched_at?: string | null;
  is_stale?: boolean;
};

return {
  ...,
  currentPrice: analysis.current_market_price ? Number(analysis.current_market_price) : null,
  plValue: analysis.financial_return_value ? Number(analysis.financial_return_value) : null,
  plPercent: analysis.financial_return_percent ? Number(analysis.financial_return_percent) : null,
  dividends: Number(analysis.total_dividends_received),
  totalReturnValue: analysis.total_return_value ? Number(analysis.total_return_value) : null,
  totalReturnPercent: analysis.total_return_percent ? Number(analysis.total_return_percent) : null,
  priceFetchedAt: analysis.fetched_at ?? null,
  isStale: analysis.is_stale ?? false,
};
```

**Acceptance Criteria**:
- Null-safe mapping for absent price/returns.
- `refresh=true` is passed through to backend analysis call.
- Type updates are reflected in hook and component usage.

**Tests**:
- Route returns enriched fields and handles 401/analysis errors.
- Refresh query forwards `refresh=true`.
- Update `web/app/hooks/useAssetSummaries.ts` type assertions as needed.

### Phase 5: UI updates (sidebar returns + refresh UX)
**Objective**: Show price, returns, dividends, and freshness with clear stale/failure states.

**Code Proposal**:
```tsx
// AssetSidebar
// - Show current price, price-only P/L, dividends, and total return.
// - Show freshness label with formatted fetched time.
// - If isStale=true, display explicit stale badge/text.
// - Add "Refresh prices" button that calls /api/assets-summary?refresh=true.
// - While refreshing: button disabled + loading state.
// - On refresh failure: keep previous data and show non-blocking error message.
```

**Acceptance Criteria**:
- Positive/negative/zero return color logic is deterministic and documented.
- Stale data is visibly distinguishable from fresh data.
- Refresh failure does not clear existing values.

**Tests**:
- Query refresh triggers refetch/invalidate.
- UI renders fresh vs stale states correctly.
- Button disables during loading and re-enables afterward.
- Error banner/toast appears on refresh failure.

## Observability and Security
- Log cache hits/misses, provider fetch failures, and stale fallbacks in backend service layer.
- Do not log tokens or sensitive user details.
- Keep endpoints protected with existing auth dependencies.
- If abuse is observed, add endpoint rate limiting as follow-up.

## Consolidated Checklist
- [ ] Add `AssetPriceCache` model and metadata-based table creation.
- [ ] Add ticker normalization + DB-agnostic upsert helpers in `app/crud.py`.
- [ ] Update `market_data_agent.get_current_price` to return `(price, is_stale)` with DB-cache-first semantics.
- [ ] Align return semantics (`financial_return_*` price-only, `total_return_*` includes dividends).
- [ ] Update auth-protected `/assets/{ticker}/price` and `/assets/{ticker}/analysis` refresh behavior.
- [ ] Extend schemas with `fetched_at` and `is_stale` and update affected call sites.
- [ ] Update `web/app/api/assets-summary/route.ts` and `web/app/hooks/useAssetSummaries.ts` mappings/types.
- [ ] Update `AssetSidebar` UI for freshness, stale badge, refresh loading/error states.
- [ ] Update tests: `tests/test_market_data_agent.py`, `tests/test_portfolio_analyzer_agent.py`, `tests/test_assets.py`, and relevant web tests.

## Notes
- Data source remains yfinance.
- Cache policy: 1h TTL with explicit `refresh=true` override.
- Stale fallback: return cached value with `is_stale=true` when provider fetch fails; return 404 only when no cached value exists.
- No new env vars are required in this phase.
