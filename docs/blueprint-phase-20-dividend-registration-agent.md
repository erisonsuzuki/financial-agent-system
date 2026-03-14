# Implementation Blueprint: Phase 20 - Dividend Registration Agent Support

## Overview
Add dividend registration support to the existing `registration_agent` by introducing a `register_dividend` tool that uses `/assets/` and `/dividends/`.

The goal is to make dividend requests deterministic, with clear amount rules, consistent errors, and optional refresh-time sync.

## Core Decisions
- **Canonical amount field**: Use `amount_per_share` (`schemas.DividendCreate`).
- **Total amount conversion**: If `total_amount` is provided, require `share_count` and compute `amount_per_share = total_amount / share_count`.
- **Validation**: Reject requests with both `amount_per_share` and `total_amount`, or with non-positive numeric values.
- **Fallback**: If no amount is provided, fetch the latest per-share dividend from yfinance.
- **Asset resolution**: Lookup by `/assets/?ticker=...`; never auto-create assets.
- **Routing scope**: Keep handling in `registration_agent`.

## Phase 1 - `register_dividend` Tool
**Objective**: Add a robust tool in `app/agents/tools.py`.

**Code Snippet**:
```python
# app/agents/tools.py
@tool
def register_dividend(
    ticker: str,
    amount_per_share: Decimal | None = None,
    total_amount: Decimal | None = None,
    share_count: Decimal | None = None,
    payment_date: date | None = None,
) -> dict:
    """Return {"status": "success|error", "message": str, "data": dict | None}."""
```

**Behavior**:
1. Validate inputs.
2. Resolve `asset_id` from ticker.
3. Compute `amount_per_share` if needed.
4. If still missing, use yfinance latest dividend.
5. Build payload for `/dividends/` and submit.
6. Return a consistent result format: `status`, `message`, optional `data`.

**Rules**:
- `payment_date` precedence: explicit input > yfinance date (if fallback used) > `date.today()`.
- Use existing HTTP helper patterns and call `response.raise_for_status()` on API requests.
- Share ticker normalization through a common helper reused by tools and market-data logic.
- Handle empty yfinance history with a clear error.

**Acceptance**:
- Registers with direct `amount_per_share`.
- Registers with computed `amount_per_share` from `total_amount` + `share_count`.
- Returns explicit validation errors for bad/ambiguous input.
- Returns explicit error when asset is missing.
- Uses yfinance fallback when amount is missing and data exists.
- Returns explicit error when fallback data does not exist.

**Tests**:
- Direct amount success.
- Computed amount success.
- Missing `share_count` error.
- Missing asset error.
- Both amount fields provided error.
- Yfinance fallback success and empty-history error.
- Deterministic precision/rounding for computed values.

## Phase 2 - Agent Wiring (Config + Routing)
**Objective**: Ensure dividend requests consistently trigger registration behavior.

**Code Snippets**:
```yaml
# app/agents/configs/registration_agent.yaml
tools:
  - register_asset_position
  - register_dividend

prompt_template: |
  ...
  For dividends, call register_dividend with:
  - amount_per_share, or
  - total_amount + share_count
  If total_amount is provided without share_count, ask for share_count.
  If the request is dividend-only, do not call register_asset_position.
```

```python
# app/agents/tools.py
keywords["registration_agent"].extend([
    "dividend", "dividends", "distribution", "cash distribution", "jcp"
])
```

**Changes**:
- Add `register_dividend` to `app/agents/configs/registration_agent.yaml`.
- Update prompt rules:
  - prefer `amount_per_share`;
  - allow `total_amount + share_count` conversion;
  - ask for `share_count` when missing;
  - do not call `register_asset_position` for dividend-only requests.
- Extend registration keywords in `classify_agent_request` for dividend phrasing.

**Acceptance**:
- Dividend intents route to `registration_agent`.
- Agent produces tool calls instead of generic fallback text.

**Tests**:
- English routing matrix:
  - dividend registration phrases -> `registration_agent`;
  - analysis-only phrases -> `analysis_agent`.

## Phase 3 - Refresh-Time Dividend Sync (Optional)
**Objective**: Sync latest yfinance dividend during refresh flows.

**Code Snippet**:
```python
# app/agents/portfolio_analyzer_agent.py
if refresh:
    sync_latest_dividend_for_ticker(ticker)

# app/crud.py
def get_latest_dividend_for_asset(db: Session, asset_id: int) -> Dividend | None:
    return (
        db.query(Dividend)
        .filter(Dividend.asset_id == asset_id)
        .order_by(Dividend.payment_date.desc(), Dividend.id.desc())
        .first()
    )
```

**Algorithm**:
1. During `portfolio_analyzer_agent.analyze_asset(..., refresh=True)`, fetch latest yfinance per-share dividend for the ticker.
2. Fetch latest stored dividend for the asset (`payment_date DESC, id DESC`) and same-date record if present.
3. Apply policy:
   - newer external date -> insert new dividend;
   - same date and different amount -> update existing same-date row;
   - same date and same amount -> skip.

**Rules**:
- No duplicate rows for the same `payment_date`.
- If yfinance has no dividend history, skip without error.
- Quantize amounts consistently (for example, 4 decimals) before comparisons/writes.

**Tests**:
- Inserts when external dividend is newer.
- Updates when same date has changed amount.
- Skips when same date and amount already exist.
- Skips safely when no yfinance dividend exists.

## Phase 4 - Documentation
**Objective**: Keep docs aligned with capability changes.

**Required**:
- Update relevant capability docs under `docs/`.
- Record exact doc files changed in the PR checklist.
- No `.env.sample` changes expected.

## Implementation Checklist
- [ ] Implement `register_dividend` in `app/agents/tools.py`.
- [ ] Add tool to `app/agents/configs/registration_agent.yaml` and update prompt guidance.
- [ ] Extend routing keywords and add routing tests.
- [ ] Add tool tests for happy paths, validation errors, fallback, and precision.
- [ ] Implement optional refresh-time sync with update-vs-insert dedupe policy.
- [ ] Update docs and list exact updated doc files in the PR.

## Success Criteria
- A request like "register a 200 BRL dividend for HGCR11" either registers correctly or asks for missing `share_count`.
- Tool errors are explicit and user-friendly.
- Test coverage includes success, validation failures, fallback behavior, and sync idempotency.
