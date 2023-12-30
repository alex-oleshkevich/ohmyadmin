from __future__ import annotations

import abc
import dataclasses
import typing

from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _

from ohmyadmin.colors import ColorGenerator, TailwindColors
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.metrics.base import Metric
from ohmyadmin.templating import render_to_response


class Partition(typing.TypedDict):
    label: str
    value: float
    color: typing.NotRequired[str]


@dataclasses.dataclass
class _PartitionViewModel:
    percent_decimals: int
    series: list[Partition]

    @property
    def total(self) -> float:
        return sum([p["value"] for p in self.series])

    def percent(self, value: float) -> float:
        if self.total == 0:
            return 0
        return round(100 * value / self.total, self.percent_decimals)


class PartitionMetric(Metric):
    colors: typing.Mapping[str, str] | None = None
    labels: typing.Mapping[str, str] | None = None
    show_total: bool = True
    show_percents: bool = True
    show_values: bool = True
    percent_decimals: int = 2
    total_format: str = _("({total} total)", domain="ohmyadmin")

    color_generator: type[ColorGenerator] = TailwindColors
    template = "ohmyadmin/metrics/partition.html"

    @abc.abstractmethod
    async def calculate(self, request: Request) -> list[Partition]:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        value = await self.calculate(request)
        color_generator = self.color_generator()
        labels = self.labels or {}
        colors = self.colors or {}
        view_model = _PartitionViewModel(
            percent_decimals=self.percent_decimals,
            series=[
                {
                    "label": str(labels.get(item["label"], snake_to_sentence(item["label"]))),
                    "color": colors.get(item.get("color", item.get("label", "")), color_generator.next()),
                    "value": item["value"],
                }
                for item in value
            ],
        )
        return render_to_response(request, self.template, {"request": request, "metric": self, "value": view_model})
