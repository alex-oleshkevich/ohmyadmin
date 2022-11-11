import typing
from slugify import slugify
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route, Router

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.metrics import Metric
from ohmyadmin.templating import TemplateResponse, admin_context


class DashboardMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Dashboard':
            attrs['slug'] = attrs.get('slug', slugify(camel_to_sentence(name.removesuffix('Dashboard'))))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Dashboard')))
            attrs['route_name'] = 'ohmyadmin_dashboard_' + attrs['slug']

        return super().__new__(cls, name, bases, attrs)


class Dashboard(Router, metaclass=DashboardMeta):
    slug: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    group: typing.ClassVar[str] = 'Dashboards'
    icon: typing.ClassVar[str] = ''
    metrics: typing.ClassVar[typing.Iterable[Metric] | None] = None
    template = 'ohmyadmin/dashboard.html'

    def __init__(self) -> None:
        super().__init__(routes=list(self.get_routes()))

    def get_metrics(self) -> typing.Iterable[Metric]:
        yield from self.metrics or []

    @classmethod
    def url_name(cls, sub_route: str = '') -> str:
        sub_route = f'.{sub_route}' if sub_route else ''
        return f'ohmyadmin.{cls.slug}{sub_route}'

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        yield Route('/', self.dispatch, name=self.url_name())
        yield Route('/metrics', self.metric_view, name=self.url_name('metrics'))

    async def dispatch(self, request: Request) -> Response:
        metrics = list(self.get_metrics())
        return TemplateResponse(
            self.template,
            {
                'request': request,
                'dashboard': self,
                'metrics': metrics,
                'page_title': self.label,
                **admin_context(request),
            },
        )

    async def metric_view(self, request: Request) -> Response:
        metric_id = request.query_params.get('_metric', '')
        metrics = {metric.slug: metric for metric in self.get_metrics()}
        metric = metrics.get(metric_id)
        if not metric:
            raise HTTPException(404, 'Metric does not exists.')
        return await metric.dispatch(request)
