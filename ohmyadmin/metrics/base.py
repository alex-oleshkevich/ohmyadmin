import abc
import typing

import slugify
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette.types import Receive, Scope, Send

from ohmyadmin.templating import render_to_response

MetricSize: typing.TypeAlias = typing.Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


class Metric(abc.ABC):
    label: str = ""
    update_interval: float = 0
    size: MetricSize = 4
    template: str = ""

    def __init__(self) -> None:
        self.label = self.label or self.__class__.__name__

    @property
    def slug(self) -> str:
        return slugify.slugify(self.label)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        return render_to_response(request, self.template, {"request": request, "metric": self, "value": value})

    @abc.abstractmethod
    async def calculate(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    def get_url_name(self, url_name_prefix: str) -> str:
        return url_name_prefix + ".metric." + self.slug

    def get_route(self, url_name_prefix: str) -> BaseRoute:
        return Route("/" + self.slug, self, name=self.get_url_name(url_name_prefix))
