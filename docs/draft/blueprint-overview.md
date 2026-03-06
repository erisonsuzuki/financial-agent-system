# Implementation Blueprint: Phase 18 - Asset Valuation with P/L and 1h Price Cache

## Overview
Add current price and P/L (including dividends) to the dashboard sidebar, backed by yfinance price retrieval with a 1-hour shared cache persisted in the DB and a user-triggered refresh. Expose cached price/time via API so the UI can show freshness and allow a force-refresh per asset list.

## Implementation Phases

### Phase 1: Persisted price cache (DB)
**Objective**: Store per-ticker price with timestamp for 1h TTL, enabling reuse across processes and restarts.
**Code Proposal**:
```python
# app/models.py (new model)
class AssetPriceCache(Base):
    __tablename__ = "asset_price_cache"
    ticker = Column(String, primary_key=True)
    price = Column(Numeric(10, 2), nullable=False)
    source = Column(String, default="yfinance", nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)

# app/crud.py (helpers)
def get_cached_price(db, ticker): ...
def upsert_cached_price(db, ticker, price, source): ...
```
**Notes**:
- Follow existing project pattern (`models.Base.metadata.create_all(...)` in `app/main.py`): add the model and let metadata create the table on startup. If later adopting Alembic, add a migration, but default path is metadata-based creation.
```
**Tests**:
- CRUD roundtrip persists price and timestamp.
- TTL logic respects 1h cutoff and refreshes when expired.

### Phase 2: Market data agent uses DB cache + force refresh
**Objective**: Integrate cache into price fetch; allow bypass via flag.
**Code Proposal**:
```python
def get_current_price(ticker: str, db: Session | None = None, force_refresh: bool = False):
    # 1) if not force_refresh and db cache fresh (< 3600s) -> return cached
    # 2) else fetch via yfinance (existing _ticker_candidates)
    # 3) on success, upsert cache record (with db provided)
    # 4) if fetch fails: return stale cached price with an `is_stale=True` marker; if no cache, return None
```
**Tests**:
- Fresh cache returns without calling yfinance (mock).
- Expired cache triggers fetch and updates cache.
- `force_refresh=True` triggers fetch even if fresh.
- Missing/failed fetch returns stale cached price (flagged) when available; otherwise None (404 propagates).

### Phase 3: API endpoints for price/analysis with refresh and metadata
**Objective**: Surface current price and P/L with cache metadata; support optional refresh query param.
**Code Proposal**:
```python
# app/routers/assets.py
@router.get("/{ticker}/price", response_model=schemas.AssetPrice)
def get_asset_price(ticker: str, refresh: bool = False, db=Depends(get_db)):
    price, is_stale = market_data_agent.get_current_price(ticker, db=db, force_refresh=refresh)
    if price is None: raise 404
    cached = crud.get_cached_price(db, ticker)
    return schemas.AssetPrice(
        ticker=ticker,
        price=price,
        source=cached.source,
        fetched_at=cached.fetched_at,
        is_stale=is_stale,
    )

# schemas.AssetPrice -> add datetime fetched_at and boolean is_stale
# schemas.AssetAnalysis -> add fetched_at and is_stale when price present
# portfolio_analyzer_agent.analyze_asset(db, asset, refresh: bool=False) -> thread refresh flag to price getter.
# Returns: price-only P/L where total_return_value = (qty * current_price) - (qty * average_price); dividends are separate fields (not added into total_return).
```
**Tests**:
- `/assets/{ticker}/price` returns price + fetched_at and respects refresh.
- `/assets/{ticker}/analysis` returns current_market_price/value and financial_return including dividends; refresh triggers fetch.
- 401/404 behaviors unchanged.

### Phase 4: Frontend asset summary endpoint includes price/P&L
**Objective**: Extend `/app/api/assets-summary` to include current price, P/L value, P/L %, and fetched_at.
**Code Proposal**:
```ts
// web/app/api/assets-summary/route.ts
type AssetAnalysis = {
  total_quantity: number;
  average_price: string;
  current_market_price: string | null;
  financial_return_value: string | null;  // price-only P/L
  financial_return_percent: string | null;
  total_dividends_received: string;
  total_return_value: string | null;      // (qty * current_price) - (qty * avg_price), dividends NOT included
  total_return_percent: string | null;    // price-only return percent
  fetched_at?: string;
  is_stale?: boolean;
};
return {
  ...,
  currentPrice: analysis.current_market_price ? Number(analysis.current_market_price) : null,
  plValue: analysis.financial_return_value ? Number(...) : null,
  plPercent: analysis.financial_return_percent ? Number(...) : null,
  dividends: Number(analysis.total_dividends_received),
  totalReturnValue: analysis.total_return_value ? Number(...) : null,
  totalReturnPercent: analysis.total_return_percent ? Number(...) : null,
  priceFetchedAt: analysis.fetched_at ?? null,
  isStale: analysis.is_stale ?? false,
};
// Handle refresh query ?refresh=true passthrough.
```
**Tests**:
- Route returns enriched fields and handles 401/analysis errors.
- Refresh query hits backend with `refresh=true`.

### Phase 5: UI updates (sidebar P/L with refresh)
**Objective**: Show current price, P/L value/%, dividends, and freshness; allow force refresh.
**Code Proposal**:
```tsx
// AssetSidebar: show a two-column list: Asset info (name/ticker, units, avg price, fetched_at/stale) and a Total Return column (price-only) with colored background (green for positive, red for negative, neutral for zero/unknown). Dividends can be shown as a smaller line item text, but not used for coloring.
// Add "Refresh prices" button (auth only) that calls /api/assets-summary?refresh=true and revalidates query.
// Style: Total Return column uses background color blocks; fetched_at shown inline.
// Button shows loading/disabled state while refresh in flight.
```
**Tests**:
- Query refresh triggers refetch via React Query (invalidate).
- UI renders values and colors correctly for positive/negative/zero/unknown.
- Button disabled while loading.

## Consolidated Checklist
- [ ] Add DB model; rely on metadata create_all to create `asset_price_cache` (add migration later if Alembic is introduced)
- [ ] Add CRUD helpers and TTL logic (1h) for cached prices
- [ ] Update market data agent to use DB cache and force refresh flag
- [ ] Extend schemas for fetched_at/is_stale metadata and update analysis pipeline (total return = price P/L only; dividends separate)
- [ ] Update assets price/analysis endpoints to accept refresh and return fetched_at
- [ ] Enhance assets-summary API route to include price/P&L/dividends/freshness and refresh passthrough
- [ ] Update AssetSidebar UI for price, P/L (with dividends), coloring, and refresh CTA
- [ ] Add tests (backend: cache logic, endpoints; frontend: route handler)

## Notes
- Data source: yfinance remains the provider.
- Cache policy: 1h TTL; force refresh via query param. If fetch fails and a cached price exists, return it flagged as stale; otherwise return 404. Table creation follows existing pattern (create_all); if migrations are added later, include this table.
- Dividends: show separately; total return is price-only ((qty * current price) - (qty * avg price)).
- Security: endpoints remain auth-protected; ensure no leakage for guest users.
- Performance: avoid N+1 price fetch by using cache and batching analysis sequentially; respect yfinance limits.
