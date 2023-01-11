import abc
import typing
from slugify import slugify
from starlette.datastructures import MultiDict
from starlette.requests import Request
from starlette.responses import Response
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.helpers import LazyURL, camel_to_sentence, resolve_url
from ohmyadmin.shortcuts import render_to_string


class ObjectAction(abc.ABC):
    label: str = ''
    icon: str = ''
    confirmation: str = ''
    template: str = ''
    method: typing.Literal['get', 'post', 'put', 'patch', 'delete']
    dangerous: bool = False

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        return render_to_string(request, self.template, {'action': self})

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...


class Link(ObjectAction):
    template = 'ohmyadmin/object_actions/object_action_link.html'

    def __init__(self, label: str, url: str | LazyURL, icon: str = '', dangerous: bool = False) -> None:
        self.url = url
        self.icon = icon
        self.label = label
        self.dangerous = dangerous

    def resolve(self, request: Request) -> str:
        return resolve_url(request, self.url)

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError('Link action cannot be dispatched.')


class Dispatch(ObjectAction):
    template = 'ohmyadmin/object_actions/object_action_dispatch.html'

    def __init__(
        self,
        label: str,
        callback: typing.Callable[[Request], typing.Awaitable[Response]],
        icon: str = '',
        dangerous: bool = False,
        confirmation: str = '',
        slug: str = '',
        method: typing.Literal['get', 'post', 'patch', 'put', 'delete'] = 'get',
    ) -> None:
        self.method = method
        self.callback = callback
        self.slug = slug or slugify(camel_to_sentence(callback.__name__))
        self.icon = icon or self.icon
        self.label = label or self.label
        self.dangerous = dangerous or self.dangerous
        self.confirmation = confirmation or self.confirmation

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.append('_action', self.slug)
        params.setlist('_ids', [obj.id])  # FIXME: .id must not be hardcoded
        menu_link = request.url.replace(query=urlencode(params.multi_items()))
        return render_to_string(request, self.template, {'action': self, 'object': obj, 'menu_link': menu_link})

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)
