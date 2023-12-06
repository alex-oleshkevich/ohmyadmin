from starlette.requests import Request

from ohmyadmin.formatters import StringFormatter


def test_string_formatter(http_request: Request) -> None:
    formatter = StringFormatter()
    assert formatter.format(http_request, "text") == "text"
