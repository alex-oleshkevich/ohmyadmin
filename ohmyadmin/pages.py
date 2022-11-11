import typing
from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route, Router

from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.templating import TemplateResponse, admin_context


class PageMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Page':
            attrs['id'] = attrs.get('id', slugify(name.removesuffix('Page')))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Page')))

        return super().__new__(cls, name, bases, attrs)


class Page(Router, metaclass=PageMeta):
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    group: typing.ClassVar[str] = 'Pages'
    icon: typing.ClassVar[str] = ''
    template: typing.ClassVar[str] = 'ohmyadmin/page.html'

    def __init__(self) -> None:
        super().__init__(routes=list(self.get_routes()))

    @classmethod
    def url_name(cls, sub_page: str = '') -> str:
        sub_page = f'_{sub_page}' if sub_page else ''
        return f'ohmyadmin_pages_{cls.id}{sub_page}'

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        yield Route('/', self.dispatch, name=self.url_name())

    async def get_template_context(self, request: Request) -> dict[str, typing.Any]:
        return {**admin_context(request)}

    async def dispatch(self, request: Request) -> Response:
        context = await self.get_template_context(request)
        return TemplateResponse(self.template, {'request': request, 'page': self, 'page_title': self.label, **context})
