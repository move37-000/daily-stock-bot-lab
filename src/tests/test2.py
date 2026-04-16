from src.domain import Market, DailyPrice, StockSnapshot

# 미국 종목
nvda = StockSnapshot(
    symbol="NVDA",
    name="NVIDIA Corporation",
    market=Market.US,
    close=135.50,
    change=2.30,
    change_pct=1.73,
    history=[
        DailyPrice("2026-04-14", 132.0, 134.0, 131.0, 133.2, 50000000),
        DailyPrice("2026-04-15", 133.5, 136.0, 133.0, 135.5, 48000000),
    ],
)

print(nvda)
print(nvda.market)        # Market.US
print(nvda.market.value)  # "US"
print(nvda.market == Market.US)  # True

# 한국 종목
tiger = StockSnapshot(
    symbol="471760",
    name="TIGER AI반도체핵심공정",
    market=Market.KR,
    close=12850.0,
    change=150.0,
    change_pct=1.18,
)
# history는 기본값 [] 사용

print(tiger.history)  # []

# 실수 방지 실험: market에 문자열 넣어보기
try:
    wrong = StockSnapshot(
        symbol="AAPL", name="Apple", market="US",  # ← Enum이 아니라 str
        close=200, change=1, change_pct=0.5
    )
    # 런타임에는 통과하지만...
    print(wrong.market == Market.US)  # False (str != Enum)
except Exception as e:
    print(e)