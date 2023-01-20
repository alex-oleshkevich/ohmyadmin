import abc
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.shortcuts import render_to_response


class Metric(abc.ABC):
    slug: str = ''
    label: str = ''
    size: int = 3

    def __init__(self) -> None:
        self.slug = self.slug or slugify(self.__class__.__name__)
        self.label = self.label or camel_to_sentence(self.__class__.__name__)

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...

    def resolve_url(self, request: Request) -> URL:
        return request.url.include_query_params(_metric=self.slug)

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request)


class ValueMetric(Metric):
    template: str = 'ohmyadmin/metrics/value.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> str:
        ...

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        return render_to_response(request, self.template, {'value': value, 'metric': self})


class ProgressMetric(Metric):
    target: int = 100
    progress_color: str = 'green'
    template: str = 'ohmyadmin/metrics/progress.html'

    async def get_target(self, request: Request) -> int:
        return self.target

    @abc.abstractmethod
    async def current_value(self, request: Request) -> float | int:
        ...

    async def dispatch(self, request: Request) -> Response:
        value = await self.current_value(request)
        target = await self.get_target(request)
        percent = f'{value * 100 / target:.0f}'
        return render_to_response(
            request,
            self.template,
            {
                'value': value,
                'target': target,
                'percent': percent,
                'metric': self,
            },
        )
