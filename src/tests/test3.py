from src.domain import Market, DailyPrice, StockSnapshot, NewsItem

news1 = NewsItem(
    title="NVIDIA announces new AI chip",
    link="https://example.com/article/1",
    publisher="Reuters",
    time="4월 15일 오후 2시 30분",
)

news2 = NewsItem(
    title="엔비디아 신제품 출시",
    link="https://n.news.naver.com/...",
    time="4월 15일 오후 3시",
)
print(news2.publisher)

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
    news=[news1, news2],
)

print(f"{nvda.symbol} ({nvda.name}): ${nvda.close}")
print(f"전일 대비: {nvda.change_pct:+.2f}%")
print(f"관련 뉴스 {len(nvda.news)}건")
for n in nvda.news:
    # publisher가 없어도 AttributeError 안 남
    label = n.publisher if n.publisher else "출처 미상"
    print(f"  - [{label}] {n.title}")