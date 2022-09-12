import abc
from starlette.requests import Request

from ohmyadmin.helpers import render_to_string


class Metric:
    template: str = ''

    async def render(self, request: Request) -> str:
        return render_to_string(self.template, {})


class CountMetric(Metric):
    label: str = 'Counter'
    template = 'ohmyadmin/metrics/counter.html'
    cols: int = 4
    value_prefix: str = ''
    value_suffix: str = ''
    round: int | None = None

    @abc.abstractmethod
    async def calculate(self, request: Request) -> int:
        raise NotImplementedError()

    async def render(self, request: Request) -> str:
        value = await self.calculate(request)
        value = value or 0
        return render_to_string(self.template, {'metric': self, 'value': value})
