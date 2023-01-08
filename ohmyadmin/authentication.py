import dataclasses

import abc
import typing
import wtforms.validators
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser, UnauthenticatedUser
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin.menu import MenuItem

SESSION_KEY = '_auth_user_id_'


@dataclasses.dataclass
class UserMenu:
    user_name: str = ''
    avatar: str = ''
    menu: list[MenuItem] = dataclasses.field(default_factory=list)

    def __iter__(self) -> typing.Iterator[MenuItem]:
        return iter(self.menu)


class LoginForm(wtforms.Form):
    identity = wtforms.EmailField(
        label=_('Email', domain='ohmyadmin'),
        render_kw={'autocomplete': 'email', 'inputmode': 'email'},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    password = wtforms.PasswordField(
        label=_('Password', domain='ohmyadmin'),
        render_kw={'autocomplete': 'password'},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    next_url = wtforms.HiddenField()


class AnonymousUser(UnauthenticatedUser):
    is_anonymous = True
    display_name = _('Anonymous', domain='ohmyadmin')


class BaseAuthPolicy(abc.ABC):
    login_form_class: type[LoginForm] = LoginForm

    @abc.abstractmethod
    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        ...

    @abc.abstractmethod
    async def load_user(self, request: Request, user_id: str) -> BaseUser | None:
        ...

    def login(self, request: Request, user: BaseUser) -> None:
        request.session[SESSION_KEY] = user.identity

    def logout(self, request: Request) -> None:
        if SESSION_KEY in request.session:
            del request.session[SESSION_KEY]

    def is_authenticated(self, request: Request) -> bool:
        return request.user.is_authenticated

    def get_login_form_class(self) -> type[LoginForm]:
        return self.login_form_class

    def get_authentication_backend(self) -> AuthenticationBackend:
        return SessionAuthBackend()

    def get_user_menu(self, request: Request) -> UserMenu:
        return UserMenu(user_name=_('anon.', domain='ohmyadmin'))


class AnonymousAuthPolicy(BaseAuthPolicy):
    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        return None

    async def load_user(self, request: Request, user_id: str) -> BaseUser | None:
        return AnonymousUser()


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request) -> tuple[AuthCredentials, BaseUser] | None:
        auth_policy: BaseAuthPolicy = request.state.admin.auth_policy
        user_id = request.session.get(SESSION_KEY, '')
        if user_id and (user := await auth_policy.load_user(request, user_id)):
            return AuthCredentials(), user
        return AuthCredentials([]), UnauthenticatedUser()


class RequireLoginMiddleware:
    def __init__(self, app: ASGIApp, exclude_paths: list[str]) -> None:
        self.app = app
        self.exclude_paths = exclude_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        conn = HTTPConnection(scope)
        if conn.user.is_authenticated or any([excluded_path in conn.url.path for excluded_path in self.exclude_paths]):
            await self.app(scope, receive, send)
            return

        flash(Request(scope)).error(_('You need to be logged in to access this page.', domain='ohmyadmin'))
        redirect_to = conn.url_for('ohmyadmin.login') + '?next=' + conn.url.path
        response = RedirectResponse(url=redirect_to)
        await response(scope, receive, send)
