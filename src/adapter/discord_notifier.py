import requests

from src.domain.market import IndexSnapshot
from src.domain.report import DailyReport
from src.domain.stock import StockSnapshot
from src.port.notifier import Notifier


class DiscordNotifier(Notifier):
    """Discord webhook 기반 알림 어댑터.

    DailyReport를 Discord Embed 페이로드로 변환해 webhook으로 전송한다.
    Slack 어댑터와 메시지 본문 구성은 유사하지만 마크다운 문법
    (**bold**, 백틱 코드), 리포트 링크 표현(마크다운 링크),
    페이로드 구조(embeds)가 다르다.

    실패 시 예외를 전파한다 (requests.HTTPError 등). 호출측이 재시도·
    스킵·중단 정책을 결정한다 (Notifier Port 규약).
    """

    _EMBED_COLOR = 0x5865F2  # Discord brand blue

    def __init__(self, webhook_url: str, timeout: float = 10.0) -> None:
        if not webhook_url:
            raise ValueError("Discord webhook_url이 비어있음.")
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(self, report: DailyReport, report_url: str | None = None) -> None:
        embed = {
            "title": "📈 일일 주식 리포트",
            "description": self._build_description(report, report_url),
            "color": self._EMBED_COLOR,
            "footer": {"text": f"Daily Stock Bot • {report.date.isoformat()}"},
        }
        payload = {"embeds": [embed]}

        response = requests.post(
            self._webhook_url,
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()

    def _build_description(
        self, report: DailyReport, report_url: str | None
    ) -> str:
        """Discord Embed description 생성 (markdown 형식)."""
        lines = [
            "**🇺🇸 US Market**",
            self._format_index_line(report.us_market.primary),
            self._format_index_line(report.us_market.secondary),
            "",
            "**💵 USD/KRW**",
            f"{report.exchange_rate.formatted_price} "
            f"({report.exchange_rate.formatted_change_pct}%)",
            "",
            "**📊 오늘의 요약**",
            f"🇺🇸 {report.us_up_count}↑ {report.us_down_count}↓",
            self._format_top_line(report.top_gainer, report.top_loser),
        ]

        if report_url:
            lines.append("")
            lines.append(f"[📊 **전체 리포트 보기**]({report_url})")

        return "\n".join(lines)

    @staticmethod
    def _format_index_line(index: IndexSnapshot) -> str:
        """백틱으로 가격 강조 (Discord markdown)."""
        return (
            f"{index.emoji} {index.name} "
            f"`{index.formatted_price}` ({index.formatted_change_pct}%)"
        )

    @staticmethod
    def _format_top_line(gainer: StockSnapshot, loser: StockSnapshot) -> str:
        return (
            f"📈 {gainer.symbol} `{gainer.change_pct:+.2f}%` │ "
            f"📉 {loser.symbol} `{loser.change_pct:+.2f}%`"
        )