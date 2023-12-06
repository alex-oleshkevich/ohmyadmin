import pathlib
from starlette.requests import Request

from ohmyadmin.formatters import BaseFormatter


def test_renders_template(
    http_request: Request, extra_template_dir: pathlib.Path
) -> None:
    (extra_template_dir / "custom.html").write_text("FORMATTED")

    class MyFormatter(BaseFormatter):
        template = "custom.html"

    formatter = MyFormatter()
    assert formatter.format(http_request, "") == "FORMATTED"


def test_base_formatter_is_callable(http_request: Request) -> None:
    class MyFormatter(BaseFormatter):
        def format(self, request: Request, value: str) -> str:
            return "FORMATTED"

    formatter = MyFormatter()
    assert formatter(http_request, "") == "FORMATTED"
