import abc
import dataclasses
import typing

from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin import formatters
from ohmyadmin.metrics.base import Metric
from ohmyadmin.templating import render_to_response


@dataclasses.dataclass
class _ValueViewModel:
    value: str


ValueValue: typing.TypeAlias = typing.Any  # anything with __str__ is ok


class ValueMetric(Metric):
    formatter: formatters.BaseFormatter = formatters.StringFormatter()
    template = "ohmyadmin/metrics/value.html"

    @abc.abstractmethod
    async def calculate(self, request: Request) -> ValueValue:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        view_model = _ValueViewModel(value=self.formatter.format(request, value))
        return render_to_response(request, self.template, {"request": request, "metric": self, "value": view_model})
