import abc
import typing
from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.templating import TemplateResponse


class MetricMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Metric':
            attrs['slug'] = attrs.get('slug', slugify(name.removesuffix('Metric')))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Metric')))

        return super().__new__(cls, name, bases, attrs)


class Metric(metaclass=MetricMeta):
    slug: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    template: str = ''
    refresh_every: int | None = None

    async def get_value(self, request: Request) -> dict[str, typing.Any]:
        return {}

    async def dispatch(self, request: Request) -> Response:
        return TemplateResponse(
            self.template,
            {
                'request': request,
                'metric': self,
                'refresh_every': self.refresh_every,
                **(await self.get_value(request)),
            },
        )


class ValueMetric(Metric):
    template = 'ohmyadmin/metrics/value.html'
    colspan: int = 4
    value_prefix: str = ''
    value_suffix: str = ''
    round: int | None = None

    @abc.abstractmethod
    async def calculate(self, request: Request) -> int:
        raise NotImplementedError()

    async def get_value(self, request: Request) -> dict[str, typing.Any]:
        value = await self.calculate(request)
        value = value or 0
        return {'value': value}
