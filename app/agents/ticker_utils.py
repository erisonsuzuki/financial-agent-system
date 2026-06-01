from typing import Iterable


def _looks_like_b3_ticker(ticker: str) -> bool:
    if "." in ticker:
        return False
    return len(ticker) in (5, 6) and ticker[:4].isalpha() and ticker[4:].isdigit()


def ticker_candidates(ticker: str) -> Iterable[str]:
    """
    Builds a list of symbols to try. For Brazilian tickers we also attempt the `.SA` suffix.
    """
    if _looks_like_b3_ticker(ticker):
        yield f"{ticker}.SA"
        yield ticker
        return

    yield ticker
    if "." not in ticker:
        yield f"{ticker}.SA"
