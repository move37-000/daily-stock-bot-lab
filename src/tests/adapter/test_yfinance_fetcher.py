"""YFinanceFetcher 어댑터 단위 테스트.

검증 책임:
1. 정상 경로 (단·다종목)
2. 단종목 실패 격리 (스킵, 예외 번역, 나머지 종목 반환)
3. 전종목 실패 시 상위로 raise (현재 RuntimeError — 코드 의도 확인 필요)
4. 뉴스 격리 (§7.9 StockFetcher 측면 — news=[]로 흡수, 스냅샷은 정상)
5. parse_yfinance_news 정상 동작 (ticker.news mock으로 간접 검증)

이 파일은 모든 어댑터 테스트 중 mock 셋업이 가장 복잡하므로
DataFrame과 yfinance 뉴스 dict 생성 헬퍼를 분리했다. 각 테스트가
중요한 차이만 짚을 수 있도록.
"""