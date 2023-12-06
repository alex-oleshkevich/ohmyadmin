from starlette.requests import Request

from ohmyadmin.formatters import BadgeFormatter
from ohmyadmin.testing import MarkupSelector


def test_badge(http_request: Request) -> None:
    formatter = BadgeFormatter(color_map={"success": "green"})
    content = formatter.format(http_request, "success")
    selector = MarkupSelector(content)
    assert selector.has_node(".badge.badge-green")
    assert selector.get_text(".badge") == "success"
