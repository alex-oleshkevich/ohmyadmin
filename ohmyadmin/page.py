import typing
from slugify import slugify
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.helpers import camel_to_sentence, pluralize


class PageMeta(type):
    def __new__(mcs, name: str, bases: tuple[type], attrs: dict[str, typing.Any], **kwargs: typing.Any) -> type:
        if not attrs.get('label'):
            attrs['slug'] = slugify(name.removesuffix('Page'))
            attrs['label'] = camel_to_sentence(name.removesuffix('Page'))
            attrs['label_plural'] = attrs.get('label_plural', pluralize(attrs['label']))

        return type.__new__(mcs, name, bases, attrs, **kwargs)


class BasePage(metaclass=PageMeta):
    slug: str = ''
    label: str = ''
    label_plural: str = ''
    group: str = ''
    icon: str = ''

    @classmethod
    def get_path_name(cls) -> str:
        raise NotImplementedError()

    def render_to_response(
        self,
        request: Request,
        template_name: str,
        context: typing.Mapping[str, typing.Any] | None = None,
    ) -> Response:
        return request.state.admin.render_to_response(request, template_name, context)

    def redirect_to_path(self, request: Request, path_name: str, **path_params: typing.Any) -> RedirectResponse:
        url = request.url_for(path_name, **path_params)
        return RedirectResponse(url, status_code=302)

    def redirect_to_self(self, request: Request) -> RedirectResponse:
        url = request.url_for(self.get_path_name())
        return RedirectResponse(url, status_code=302)

    @classmethod
    def as_route(cls) -> BaseRoute:
        raise NotImplementedError()

    @classmethod
    def generate_url(cls, request: Request) -> str:
        raise NotImplementedError()


class Page(HTTPEndpoint, BasePage):
    template: typing.ClassVar[str] = 'ohmyadmin/pages/blank.html'

    async def get(self, request: Request) -> Response:
        return self.render_to_response(request, self.template, {'page_title': self.label})

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.pages.{cls.slug}'

    @classmethod
    def as_route(cls) -> BaseRoute:
        methods: list[str] = []
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if hasattr(cls, method.lower()):
                methods.append(method)

        return Route(f'/{cls.slug}', cls, methods=methods, name=cls.get_path_name())

    @classmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(f'ohmyadmin.pages.{cls.slug}')
