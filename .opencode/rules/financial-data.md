# Financial Data

- Use `Decimal` in Python and `Numeric` in SQLAlchemy for monetary values and financial calculations. (Financial math must stay precise and use predictable rounding.)
- Assert `Decimal` values as JSON strings in API response tests. (FastAPI serializes decimals as strings to preserve precision.)
