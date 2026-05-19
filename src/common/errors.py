"""어댑터 계층 공통 예외.

외부 시스템(yfinance, webhook, Gemini API)과의 경계에서 발생하는 실패를
의미 단위로 분류한다. 도메인(StockSnapshot, DailyReport)은 네트워크·HTTP를
몰라야 하므로 domain/이 아니라 common/에 둔다 — 어댑터·retry·main이 공유하는
횡단 어휘다.

재시도 가능성은 이 계층에 담지 않는다. NetworkError가 "재시도 가능"이고
ParseError가 "불가능"인 건 사실이지만, ApiResponseError는 status_code에 따라
갈리고(429는 4xx지만 재시도 가능) 그 판정은 정책이라 바뀐다. 정책은
common/retry.py가 갖는다. 이 파일은 "무슨 일이 일어났는가"라는 사실만 담는다.
"""