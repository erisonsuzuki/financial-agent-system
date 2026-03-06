# Phase 19 Implementation Ticket Checklist

## Ticket 1: DB price cache model + CRUD
- [ ] Add `AssetPriceCache` in `app/models.py` (`ticker`, `price`, `source`, `fetched_at`).
- [ ] Add `normalize_ticker`, `get_cached_price`, and `upsert_cached_price` in `app/crud.py`.
- [ ] Ensure upsert is DB-agnostic (SQLite tests + Postgres runtime).
- [ ] Verify metadata-based table creation works on startup.

Definition of done:
- [ ] Cache row is created/updated for same ticker without duplicates.
- [ ] Ticker keys are canonicalized to uppercase.

## Ticket 2: Market data agent cache integration
- [ ] Update `market_data_agent.get_current_price` signature to support `db` and `force_refresh`.
- [ ] Return `(price, is_stale)` tuple consistently.
- [ ] Implement cache-first behavior (1h TTL) when `force_refresh` is false.
- [ ] Implement stale fallback on provider failure when cached value exists.

Definition of done:
- [ ] Fresh cache avoids provider call.
- [ ] `force_refresh=true` bypasses fresh cache.
- [ ] No-cache + provider failure returns `(None, False)`.

## Ticket 3: API schema + endpoint updates
- [ ] Extend `schemas.AssetPrice` with `fetched_at` and `is_stale`.
- [ ] Extend `schemas.AssetAnalysis` with `fetched_at` and `is_stale`.
- [ ] Update `/assets/{ticker}/price` to support `refresh` and return freshness metadata.
- [ ] Update analysis path to thread `refresh` into price lookup.
- [ ] Ensure endpoint auth dependency is present for protected routes.

Definition of done:
- [ ] 401/404 behavior is explicit and unchanged except refresh behavior.
- [ ] Response shape includes freshness fields whenever price is present.

## Ticket 4: Return metric alignment
- [ ] Keep `financial_return_*` as price-only return.
- [ ] Define `total_return_*` as `financial_return + dividends`.
- [ ] Verify percentage formulas use cost basis denominator.

Definition of done:
- [ ] No duplicate/contradictory semantics between return fields.
- [ ] Backend and frontend use the same formulas.

## Ticket 5: Web assets-summary route updates
- [ ] Update `web/app/api/assets-summary/route.ts` type mapping for new fields.
- [ ] Pass through `refresh=true` query param to backend analysis call.
- [ ] Map nulls safely for missing price/returns.

Definition of done:
- [ ] Route returns `currentPrice`, `plValue`, `plPercent`, `dividends`, `totalReturnValue`, `totalReturnPercent`, `priceFetchedAt`, `isStale`.

## Ticket 6: Sidebar UX updates
- [ ] Update `AssetSidebar` to show price, price-only P/L, dividends, total return, freshness.
- [ ] Add stale indicator UI when `isStale` is true.
- [ ] Add `Refresh prices` action with loading/disabled state.
- [ ] Preserve prior values and show non-blocking message on refresh failure.

Definition of done:
- [ ] Fresh and stale states are visually distinct.
- [ ] Positive/negative/zero return coloring is deterministic.

## Ticket 7: Tests and verification
- [ ] Update `tests/test_market_data_agent.py` for tuple contract and stale logic.
- [ ] Update `tests/test_portfolio_analyzer_agent.py` for return formulas and refresh passthrough.
- [ ] Update `tests/test_assets.py` for endpoint freshness fields + refresh behavior.
- [ ] Update/add web tests for route mapping and refresh passthrough.

Definition of done:
- [ ] All touched test suites pass locally.
- [ ] No regressions in auth and error handling paths.

## Ticket 8: Observability and operational checks
- [ ] Add logs for cache hit/miss, provider failure, stale fallback.
- [ ] Confirm no sensitive values are logged.
- [ ] Confirm no new env vars are required (or update docs if that changes).

Definition of done:
- [ ] Logs are sufficient to debug stale/fetch issues in production.

## Final Release Gate
- [ ] Backend tests pass.
- [ ] Web tests/lint pass.
- [ ] Manual smoke check: refresh flow, stale fallback, and sidebar rendering.
- [ ] Blueprint and implementation checklist are in sync.
