from src.domain import Market, IndexSnapshot, MarketOverview, ExchangeRate

# 개별 지수
sp500 = IndexSnapshot(name="sp500", price=5234.56, change=15.23, change_pct=0.29)
nasdaq = IndexSnapshot(name="nasdaq", price=16789.12, change=-23.45, change_pct=-0.14)

# property 동작 확인
print(sp500.formatted_price)        # "5,234.56"
print(sp500.formatted_change_pct)   # "+0.29"
print(sp500.emoji)                   # "🟢"
print(sp500.is_up)                   # True

print(nasdaq.emoji)                  # "🔴"

# 시장 전체
us_market = MarketOverview(
    market=Market.US,
    primary=sp500,
    secondary=nasdaq,
)

# 통일된 접근
print(us_market.primary.name)        # "sp500"
print(us_market.primary.formatted_price)
print(us_market.secondary.formatted_price)

# 환율
usd_krw = ExchangeRate(pair="USD/KRW", price=1340.50, change=2.30, change_pct=0.17)
print(f"{usd_krw.pair}: {usd_krw.formatted_price}")  # "USD/KRW: 1,340.50"