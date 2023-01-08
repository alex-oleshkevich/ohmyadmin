import abc
import inspect
import typing
from slugify import slugify
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Route
from starlette.types import Receive, Scope, Send

from ohmyadmin.helpers import camel_to_sentence, pluralize


class PageMeta(type):
    def __new__(mcs, name: str, bases: tuple[type], attrs: dict[str, typing.Any], **kwargs: typing.Any) -> type:
        if not attrs.get('label'):
            clean_label = name.removesuffix('Page').removesuffix('Resource')
            attrs['slug'] = slugify(clean_label)
            attrs['label'] = camel_to_sentence(clean_label)
            attrs['label_plural'] = attrs.get('label_plural', pluralize(attrs['label']))

        return type.__new__(mcs, name, bases, attrs, **kwargs)


class BasePage(metaclass=PageMeta):
    slug: str = ''
    label: str = ''
    label_plural: str = ''
    group: str = ''
    icon: str = ''

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

    @abc.abstractmethod
    def as_route(cls) -> BaseRoute:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def get_path_name(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(cls.get_path_name())


class Page(BasePage):
    template: typing.ClassVar[str] = 'ohmyadmin/pages/blank.html'

    async def get(self, request: Request) -> Response:
        return self.render_to_response(request, self.template, {'page_title': self.label})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        method = request.method.lower()
        if handler := getattr(self, method, None):
            response = (
                await handler(request)
                if inspect.iscoroutinefunction(handler)
                else await run_in_threadpool(handler, request)
            )
            await response(scope, receive, send)
            return
        raise HTTPException(405, 'Method Not Allowed')

    def as_route(self) -> BaseRoute:
        methods: list[str] = []
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if hasattr(self, method.lower()):
                methods.append(method)

        return Route(f'/{self.slug}', self, methods=methods, name=self.get_path_name())

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.pages.{cls.slug}'
