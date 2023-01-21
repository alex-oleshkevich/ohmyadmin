import dataclasses

import abc
import typing
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.shortcuts import render_to_response


class Metric(abc.ABC):
    slug: str = ''
    label: str = ''
    size: int = 4

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


@dataclasses.dataclass
class TrendResult:
    current_value: int | float | None = None
    series: list[tuple[str, float]] = dataclasses.field(default_factory=list)


class TrendMetric(Metric):
    template: str = 'ohmyadmin/metrics/trend.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> TrendResult:
        ...

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        return render_to_response(
            request,
            self.template,
            {'value': value, 'metric': self},
        )


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


class PartitionItem(typing.TypedDict):
    color: str
    value: float


@dataclasses.dataclass
class PartitionResult:
    groups: dict[str, PartitionItem] = dataclasses.field(default_factory=dict)

    def add_group(self, label: str, value: float | int, color: str = '') -> None:
        self.groups[label] = {'value': value, 'color': color}

    def __iter__(self) -> typing.Iterator[tuple[str, PartitionItem]]:
        return iter(self.groups.items())


class PartitionMetric(Metric):
    template: str = 'ohmyadmin/metrics/partition.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> PartitionResult:
        ...

    async def dispatch(self, request: Request) -> Response:
        partitions = await self.calculate(request)
        return render_to_response(
            request,
            self.template,
            {
                'partitions': partitions,
                'metric': self,
            },
        )
