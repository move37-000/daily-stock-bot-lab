from typing import Protocol

from src.domain.market import ExchangeRate


class ExchangeRateFetcher(Protocol):
    """환율 조회 Port

    ExchangeRate는 IndexSnapshot과 별개 타입이므로 Port도 별도로 둔다.
    현재 USD/KRW 하나만 사용하므로 파라미터를 두지 않는다.
    환율 쌍이 늘어나면 fetch(pair) 형태로 확장한다.
    """

    def fetch(self) -> ExchangeRate:
        ...