import requests

from src.domain.market import IndexSnapshot
from src.domain.report import DailyReport
from src.domain.stock import StockSnapshot
from src.port.notifier import Notifier


class SlackNotifier(Notifier):
    """Slack webhook 기반 알림 어댑터.

    DailyReport를 Slack Block Kit 페이로드로 변환해 webhook으로 전송한다.
    메시지 본문에는 지수 요약, 환율, 상승/하락 카운트, top gainer/loser를
    포함한다. 시장 뉴스는 HTML 리포트 전용이므로 알림에 포함하지 않는다.

    실패 시 예외를 전파한다 (requests.HTTPError 등). 호출측이 재시도·
    스킵·중단 정책을 결정한다 (Notifier Port 규약).
    """

    def __init__(self, webhook_url: str, timeout: float = 10.0) -> None:
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(self, report: DailyReport, report_url: str | None = None) -> None:
        message = self._build_message(report)
        blocks = self._build_blocks(message, report_url)
        payload = {"text": message, "blocks": blocks}

        response = requests.post(
            self._webhook_url,
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()

    def _build_message(self, report: DailyReport) -> str:
        """Slack mrkdwn 형식 메시지 텍스트 생성."""
        lines = [
            f"📊 *일일 주식 리포트* | {report.date.isoformat()}",
            "",
            "",
            "*시장 지수*",
            "",
            self._format_index_line(report.us_market.primary),
            self._format_index_line(report.us_market.secondary),
            "",
            "",
            f"💵 *{report.exchange_rate.pair}*  "
            f"{report.exchange_rate.formatted_price} "
            f"({report.exchange_rate.formatted_change_pct}%)",
            "",
            "",
            "*오늘의 요약*",
            "",
            f"🇺🇸 {report.us_up_count}↑ {report.us_down_count}↓",
            self._format_top_line(report.top_gainer, report.top_loser),
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_index_line(index: IndexSnapshot) -> str:
        return (
            f"{index.emoji} {index.name}  "
            f"{index.formatted_price} ({index.formatted_change_pct}%)"
        )

    @staticmethod
    def _format_top_line(gainer: StockSnapshot, loser: StockSnapshot) -> str:
        return (
            f"📈 {gainer.symbol} {gainer.change_pct:+.2f}% | "
            f"📉 {loser.symbol} {loser.change_pct:+.2f}%"
        )

    @staticmethod
    def _build_blocks(
        message: str, report_url: str | None
    ) -> list[dict]:
        """Slack Block Kit 구성. report_url이 있으면 버튼 추가."""
        blocks: list[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            }
        ]

        if report_url:
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 전체 리포트 보기",
                                "emoji": True,
                            },
                            "url": report_url,
                            "style": "primary",
                        }
                    ],
                }
            )

        return blocks