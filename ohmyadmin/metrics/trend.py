import abc
import dataclasses
import decimal
import typing

from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin import colors
from ohmyadmin.metrics.base import Metric
from ohmyadmin.templating import render_to_response


class TrendValue(typing.TypedDict):
    label: str
    value: int | float


@dataclasses.dataclass
class _TrendViewModel:
    current_value: str
    series: list[TrendValue]


class TrendMetric(Metric):
    show_current_value: bool = False
    show_ticks: bool = False
    show_grid: bool = False
    show_tooltip: bool = True
    color: str = colors.COLOR_SKY
    background_color: str = colors.COLOR_SKY_LIGHT

    template = "ohmyadmin/metrics/trend.html"

    async def calculate_current_value(self, request: Request) -> int | float | decimal.Decimal | str:
        raise NotImplementedError()

    @abc.abstractmethod
    async def calculate(self, request: Request) -> list[TrendValue]:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        series = await self.calculate(request)
        current_value: float | int | decimal.Decimal = 0
        if self.show_current_value:
            current_value = await self.calculate_current_value(request)

        view_model = _TrendViewModel(
            series=series,
            current_value=str(current_value),
        )
        return render_to_response(request, self.template, {"request": request, "metric": self, "value": view_model})
