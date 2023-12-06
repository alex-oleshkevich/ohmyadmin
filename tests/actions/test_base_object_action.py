from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import BaseObjectAction
from tests.conftest import RequestFactory


class MyAction(BaseObjectAction):  # pragma: no cover
    async def apply(self, request: Request, object_id: str) -> Response:
        return Response(f"CALLED: {object_id}")


def test_generates_slug(http_request: Request) -> None:
    action = MyAction()
    assert action.slug == "myaction"


async def test_dispatch(request_f: RequestFactory) -> None:
    request = request_f(query_string="_ids=1")
    action = MyAction()
    response = await action.dispatch(request)
    assert response.body == b"CALLED: 1"


async def test_dispatch_requires_object_id(request_f: RequestFactory) -> None:
    request = request_f()
    action = MyAction()
    response = await action.dispatch(request)
    assert "No object selected." in response.headers["hx-trigger"]
