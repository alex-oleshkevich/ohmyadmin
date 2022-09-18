import typing
from slugify import slugify
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import BaseRoute, Route, Router

from ohmyadmin.helpers import camel_to_sentence, render_to_response
from ohmyadmin.metrics import Metric
from ohmyadmin.responses import Response


class DashboardMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Page':
            attrs['id'] = attrs.get('id', slugify(name.removesuffix('Dashboard')))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Dashboard')))
            attrs['route_name'] = 'ohmyadmin_dashboard_' + attrs['id']

        return super().__new__(cls, name, bases, attrs)


class Dashboard(Router, metaclass=DashboardMeta):
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    icon: typing.ClassVar[str] = ''
    metrics: typing.ClassVar[typing.Iterable[Metric] | None] = None
    template = 'ohmyadmin/dashboard.html'

    def __init__(self) -> None:
        super().__init__(routes=list(self.get_routes()))

    def get_metrics(self) -> typing.Iterable[Metric]:
        yield from self.metrics or []

    @classmethod
    def get_route_name(cls, sub_route: str = '') -> str:
        sub_route = f'_{sub_route}' if sub_route else ''
        return f'ohmyadmin_{cls.id}{sub_route}'

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        yield Route('/', self.dispatch, name=self.get_route_name())
        yield Route('/metrics/{metric_id}', self.metric_view, name=self.get_route_name('metric'))

    async def dispatch(self, request: Request) -> Response:
        metric_urls = [
            request.url_for(self.get_route_name('metric'), metric_id=metric.id) for metric in self.get_metrics()
        ]
        return render_to_response(
            request,
            self.template,
            {'request': request, 'page': self, 'page_title': self.label, 'metric_urls': metric_urls},
        )

    async def metric_view(self, request: Request) -> Response:
        metric_id = request.path_params['metric_id']
        metric = next((metric for metric in self.get_metrics() if metric.id == metric_id))
        if not metric:
            raise HTTPException(404, 'Metric does not exists.')
        return await metric.dispatch(request)
