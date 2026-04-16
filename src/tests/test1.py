# 인터랙티브 셸에서
from src.domain import DailyPrice

# 정상 생성
price = DailyPrice(
    date="2026-04-16",
    open=100.5,
    high=105.0,
    low=99.5,
    close=103.2,
    volume=1500000
)
print(price)
# DailyPrice(date='2026-04-16', open=100.5, high=105.0, low=99.5, close=103.2, volume=1500000)

# 같은 값으로 만들면 같은 객체로 취급 (__eq__ 자동 생성됨)
price2 = DailyPrice("2026-04-16", 100.5, 105.0, 99.5, 103.2, 1500000)
print(price == price2)  # True

# 수정 시도 → 에러
# price.close = 200
# dataclasses.FrozenInstanceError: cannot assign to field 'close'

# set의 원소로 사용 가능 (frozen=True 덕분에 hashable)
prices = {price, price2}
print(len(prices))  # 1 (같은 값이므로 중복 제거됨)