import dataclasses
import typing

from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _

ActionVariant = typing.Literal['accent', 'default', 'text', 'danger']


class Action: ...


@dataclasses.dataclass
class LinkAction(Action):
    url: str
    icon: str = ''
    target: typing.Literal['', '_blank'] = ''
    label: str = dataclasses.field(default_factory=lambda: _('Unlabeled'))
    template: str = 'ohmyadmin/actions/link.html'


@dataclasses.dataclass
class EventAction(Action):
    event: str
    icon: str = ''
    trigger_from: str = 'body'
    label: str = dataclasses.field(default_factory=lambda: _('Unlabeled'))
    data: typing.Any = None
    variant: ActionVariant = 'default'
    template: str = 'ohmyadmin/actions/event.html'


@dataclasses.dataclass
class CallFunctionAction(Action):
    function: str
    icon: str = ''
    label: str = dataclasses.field(default_factory=lambda: _('Unlabeled'))
    args: list[typing.Any] = dataclasses.field(default_factory=list)
    variant: ActionVariant = 'default'
    template: str = 'ohmyadmin/actions/call_function.html'


CallbackActionHandler = typing.Callable[[Request], typing.Awaitable[Response]]


@dataclasses.dataclass
class CallbackAction(Action):
    callback: CallbackActionHandler
    icon: str = ''
    request_method: typing.Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] = 'GET'
    label: str = dataclasses.field(default_factory=lambda: _('Unlabeled'))
    variant: ActionVariant = 'default'
    slug: str = ''
    template: str = 'ohmyadmin/actions/callback.html'

    def __post_init__(self):
        self.slug = self.slug or slugify(self.label or str(id(self)))

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)
