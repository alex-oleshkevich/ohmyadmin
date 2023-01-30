import typing
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute

from ohmyadmin.helpers import camel_to_sentence, pluralize


class PageMeta(type):
    def __new__(mcs, name: str, bases: tuple[type], attrs: dict[str, typing.Any], **kwargs: typing.Any) -> type:
        if '__abstract__' not in attrs:
            if not attrs.get('label'):
                clean_label = name.removesuffix('Page').removesuffix('Resource')
                attrs['label'] = camel_to_sentence(clean_label)
            if not attrs.get('label_plural'):
                attrs['label_plural'] = attrs.get('label_plural', pluralize(attrs['label']))
            if not attrs.get('slug'):
                attrs['slug'] = slugify(attrs['label'])
            if not attrs.get('page_title'):
                attrs['page_title'] = attrs['label']

        return type.__new__(mcs, name, bases, attrs, **kwargs)


class BasePage(metaclass=PageMeta):
    slug: str = ''
    label: str = ''
    page_title: str = ''
    label_plural: str = ''
    group: str = ''
    icon: str = ''

    def render_to_response(
        self,
        request: Request,
        template_name: str,
        context: typing.Mapping[str, typing.Any] | None = None,
        headers: typing.Mapping[str, typing.Any] | None = None,
    ) -> Response:
        """Render template into HTTP response."""
        return request.state.admin.render_to_response(request, template_name, context, headers=headers)

    def redirect_to_path(self, request: Request, path_name: str, **path_params: typing.Any) -> RedirectResponse:
        """A shortcut to create RedirectResponse for path name and params."""
        url = request.url_for(path_name, **path_params)
        return RedirectResponse(url, status_code=302)

    def redirect_to(self, url: str | URL) -> RedirectResponse:
        """A shortcut to create RedirectResponse for given URL."""
        return RedirectResponse(url, status_code=302)

    def redirect_to_self(self, request: Request) -> RedirectResponse:
        """A shortcut to create RedirectResponse back to this page."""
        url = request.url_for(self.get_path_name())
        return RedirectResponse(url, status_code=302)

    def as_route(self) -> BaseRoute:  # pragma: no cover
        """Create a route instance for this page."""
        raise NotImplementedError()

    @classmethod
    def get_path_name(cls) -> str:
        """Generate a path name for this page."""
        return f'app.pages.{cls.slug}'

    @classmethod
    def generate_url(cls, request: Request) -> str:
        """Generate absolute URL to this page."""
        return request.url_for(cls.get_path_name())
