import dataclasses

import abc
import typing
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.shortcuts import render_to_response


class CardError(Exception):
    ...


class UndefinedCardError(CardError):
    ...


class Card(abc.ABC):
    slug: str = ''
    label: str = ''
    size: int = 4

    def __init__(self) -> None:
        self.slug = self.slug or slugify(self.__class__.__name__)
        self.label = self.label or camel_to_sentence(self.__class__.__name__)

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:  # pragma: no cover
        ...

    def resolve_url(self, request: Request) -> URL:
        return request.url.include_query_params(_metric=self.slug)


class ValueMetric(Card):
    template: str = 'ohmyadmin/metrics/value.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> str:  # pragma: no cover
        ...

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        return render_to_response(request, self.template, {'value': value, 'metric': self})


@dataclasses.dataclass
class TrendResult:
    current_value: int | float | None = None
    series: list[tuple[str, float]] = dataclasses.field(default_factory=list)


class TrendMetric(Card):
    template: str = 'ohmyadmin/metrics/trend.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> TrendResult:  # pragma: no cover
        ...

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        return render_to_response(
            request,
            self.template,
            {'value': value, 'metric': self},
        )


class ProgressMetric(Card):
    """
    Renders progress bar metric.

    Useful for displaying the progresses.
    """

    target: int = 100
    progress_color: str = 'green'
    template: str = 'ohmyadmin/metrics/progress.html'

    async def get_target(self, request: Request) -> int:
        """
        The value you attempt to reach.

        Examples: 100 percents, or 1000 users
        """
        return self.target

    @abc.abstractmethod
    async def calculate(self, request: Request) -> float | int:  # pragma: no cover
        """
        Calculate the current value.

        This value is used against the target to calculate percentage.
        """

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
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

    def __iter__(self) -> typing.Iterator[tuple[str, PartitionItem]]:
        return iter(self.groups.items())


class PartitionMetric(Card):
    """Renders a pie chart."""

    template: str = 'ohmyadmin/metrics/partition.html'

    @abc.abstractmethod
    async def calculate(self, request: Request) -> PartitionResult:  # pragma: no cover
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
