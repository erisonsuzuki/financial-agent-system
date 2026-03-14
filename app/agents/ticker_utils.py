from typing import Iterable


def ticker_candidates(ticker: str) -> Iterable[str]:
    """
    Builds a list of symbols to try. For Brazilian tickers we also attempt the `.SA` suffix.
    """
    yield ticker
    if "." not in ticker:
        yield f"{ticker}.SA"
