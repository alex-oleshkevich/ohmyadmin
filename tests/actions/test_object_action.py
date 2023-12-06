import pathlib
import pytest
from starlette.requests import Request

from ohmyadmin.actions import ObjectAction
from tests.models import Post


def test_object_action_requires_template(http_request: Request) -> None:
    class MyAction(ObjectAction):
        ...

    with pytest.raises(AssertionError, match="template is not defined"):
        page = MyAction()
        page.render(http_request, object())


def test_object_action_renders_template(
    http_request: Request, extra_template_dir: pathlib.Path
) -> None:
    (extra_template_dir / "action.html").write_text("hello {{ object.title }}")

    class MyAction(ObjectAction):
        template = "action.html"

    model = Post(title="world")

    page = MyAction()
    assert str(page.render(http_request, model)) == "hello world"
