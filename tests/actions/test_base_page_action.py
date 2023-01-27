from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import BasePageAction


class MyAction(BasePageAction):  # pragma: no cover
    async def apply(self, request: Request) -> Response:
        return Response('CALLED')


def test_generates_slug(http_request: Request) -> None:
    action = MyAction()
    assert action.slug == 'myaction'


async def test_dispatch(http_request: Request) -> None:
    action = MyAction()
    response = await action.dispatch(http_request)
    assert response.body == b'CALLED'
