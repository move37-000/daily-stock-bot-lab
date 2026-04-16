from dataclasses import dataclass


@dataclass(frozen=True)
class NewsItem:
    """뉴스 기사 하나

    종목별 뉴스와 시장 뉴스 모두 이 타입으로 표현한다.
    publisher와 time은 소스에 따라 없을 수 있으므로 빈 문자열을 기본값으로 둔다.

    Attributes:
        title: 뉴스 제목
        link: 원문 URL
        publisher: 언론사명 (없으면 빈 문자열)
        time: 발행 시각 (사람이 읽는 포맷, 예: "4월 15일 오후 2시 30분")
    """
    title: str
    link: str
    publisher: str = ""
    time: str = ""