import typing

from starlette.requests import Request

if typing.TYPE_CHECKING:
    from ohmyadmin.screens import Screen


class View:
    ...


class IndexView(View):
    def render(self, request: Request, screen: "Screen", models: typing.Sequence[typing.Any]) -> str:
        raise NotImplementedError("IndexView must implement render()")
