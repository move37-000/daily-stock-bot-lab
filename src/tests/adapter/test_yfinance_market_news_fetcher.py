"""YFinanceMarketNewsFetcher 어댑터 단위 테스트.

§7.9 격리 책임 검증이 이 파일의 핵심 목적이다.

이 어댑터의 약속은 "어떤 일이 있어도 raise하지 않는다"이다.
- yfinance 자체가 네트워크 실패로 예외를 던지거나
- parse_yfinance_news가 내부 버그(yfinance API 변경 등)로 예외를 던져도
main.py까지 전파되지 않고 빈 리스트로 격리되어야 한다.

이 격리가 무너지면 시장 뉴스(보조 정보) 실패가 리포트 본체 전송을 막는다.
parse_yfinance_news 자체는 자체 격리를 하지 않는다(§7.9 결정).
그 책임이 호출측 어댑터로 위임됐다는 약속을 이 테스트가 보증한다.
"""
from src.adapter.yfinance_market_news_fetcher import YFinanceMarketNewsFetcher


class TestNormalPath:
    """정상 경로: parse 결과를 그대로 전달."""

    def test_정상_NewsItem_리스트_반환(self, mocker, sample_news_item):
        """parse_yfinance_news 결과를 어댑터가 가공 없이 그대로 반환.

        parse 함수 자체의 동작(yfinance 응답 → NewsItem 변환)은
        test_yfinance_fetcher.py가 ticker.news를 직접 mock해 검증한다.
        여기는 "전달"만 확인한다.
        """
        mocker.patch("src.adapter.yfinance_market_news_fetcher.yf.Ticker")
        mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.parse_yfinance_news",
            return_value=[sample_news_item, sample_news_item],
        )

        result = YFinanceMarketNewsFetcher(symbol="^GSPC", news_limit=3).fetch()

        assert result == [sample_news_item, sample_news_item]


class TestIsolationGuarantee:
    """§7.9 격리 약속: 어떤 예외도 raise되지 않고 []로 흡수."""

    def test_yf_Ticker_생성자_예외시_빈리스트(self, mocker):
        """1번 격리 지점: yf.Ticker(...) 호출 자체가 실패.

        네트워크 끊김, yfinance 라이브러리 내부 변경 등의 시나리오.
        """
        mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.yf.Ticker",
            side_effect=ConnectionError("network down"),
        )

        result = YFinanceMarketNewsFetcher().fetch()

        assert result == []

    def test_parse_yfinance_news_예외시_빈리스트(self, mocker):
        """§7.9 핵심: 2번 격리 지점 — parse 함수 내부 실패.

        parse_yfinance_news는 try/except가 없어 KeyError·AttributeError 등이
        그대로 raise된다. 이 책임을 호출측 어댑터가 진다는 게 §7.9 결정.
        이 테스트가 그 책임의 회로 검증.
        """
        mocker.patch("src.adapter.yfinance_market_news_fetcher.yf.Ticker")
        mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.parse_yfinance_news",
            side_effect=AttributeError("yfinance internal change"),
        )

        result = YFinanceMarketNewsFetcher().fetch()

        assert result == []

    def test_범용_Exception에도_격리(self, mocker):
        """경계 검증: catch가 `except Exception`이라는 약속의 폭 확인.

        구체 타입(ConnectionError, AttributeError) 외에 일반 Exception에도
        동작하는지. 어댑터 코드가 `except ConnectionError`로 좁혀지면
        이 테스트가 깨지면서 격리 약속 축소가 즉시 드러난다.
        """
        mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.yf.Ticker",
            side_effect=Exception("unexpected from yfinance"),
        )

        result = YFinanceMarketNewsFetcher().fetch()

        assert result == []


class TestConstructorParameters:
    """생성자 인자가 호출에 정확히 전달되는지."""

    def test_symbol이_yf_Ticker에_전달(self, mocker):
        mock_ticker = mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.yf.Ticker",
        )
        mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.parse_yfinance_news",
            return_value=[],
        )

        YFinanceMarketNewsFetcher(symbol="^DJI").fetch()

        mock_ticker.assert_called_once_with("^DJI")

    def test_news_limit이_parse에_전달(self, mocker):
        mocker.patch("src.adapter.yfinance_market_news_fetcher.yf.Ticker")
        mock_parse = mocker.patch(
            "src.adapter.yfinance_market_news_fetcher.parse_yfinance_news",
            return_value=[],
        )

        YFinanceMarketNewsFetcher(news_limit=5).fetch()

        # parse_yfinance_news(ticker, limit) — 두 번째 위치 인자가 limit.
        # 첫 인자는 mock이라 값 검증 생략.
        args, _ = mock_parse.call_args
        assert args[1] == 5