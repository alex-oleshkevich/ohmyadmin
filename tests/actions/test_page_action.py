import pathlib
import pytest
from starlette.requests import Request

from ohmyadmin.actions import PageAction


def test_page_action_requires_template(http_request: Request) -> None:
    class MyAction(PageAction):
        ...

    with pytest.raises(AssertionError, match="template is not defined"):
        page = MyAction()
        page.render(http_request)


def test_page_action_renders_template(
    http_request: Request, extra_template_dir: pathlib.Path
) -> None:
    (extra_template_dir / "action.html").write_text("ACTION")

    class MyAction(PageAction):
        template = "action.html"

    page = MyAction()
    assert page.render(http_request) == "ACTION"
