import abc
import dataclasses
import typing

from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin import colors
from ohmyadmin.metrics.base import Metric
from ohmyadmin.templating import render_to_response


@dataclasses.dataclass
class _ProgressViewModel:
    current_value: float
    target_value: float

    @property
    def percent(self) -> float:
        try:
            return self.current_value * 100 / self.target_value
        except ZeroDivisionError:
            return 0


ProgressColor: typing.TypeAlias = str


class ProgressMetric(Metric):
    color: ProgressColor = colors.COLOR_GREEN
    decimals: int = 0
    template = "ohmyadmin/metrics/progress.html"

    @abc.abstractmethod
    async def calculate(self, request: Request) -> int | float:
        raise NotImplementedError()

    @abc.abstractmethod
    async def calculate_target(self, request: Request) -> int | float:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        current_value = await self.calculate(request)
        target_value = await self.calculate_target(request)

        view_model = _ProgressViewModel(
            current_value=current_value,
            target_value=target_value,
        )
        return render_to_response(request, self.template, {"request": request, "metric": self, "value": view_model})
