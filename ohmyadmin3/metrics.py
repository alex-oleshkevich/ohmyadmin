import typing
from starlette.requests import Request


class Metric:
    columns: int = 3
    rows: int = 1
    template: str = 'ohmyadmin/metrics/stub.html'
    title: str = 'Example Metric'

    async def compute(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    async def render(self, request: Request) -> typing.Any:
        value = await self.compute(request)
        return request.state.admin.render(
            self.template,
            {
                'request': request,
                'title': self.title,
                'value': value,
            },
        )


class StatMetric(Metric):
    template = 'ohmyadmin/metrics/stats.html'


class RenderedMetric:
    def __init__(self, metric: Metric, content: str) -> None:
        self.metric = metric
        self.content = content
