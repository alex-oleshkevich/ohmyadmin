import dataclasses

import abc
import typing
import wtforms.validators
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser, UnauthenticatedUser
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_flash import flash

from ohmyadmin.forms import EmailField, Form, HiddenField, PasswordField
from ohmyadmin.i18n import _
from ohmyadmin.menu import MenuItem

SESSION_KEY = '_auth_user_id_'


@dataclasses.dataclass
class UserMenu:
    user_name: str = 'Anonymous'
    avatar: str = ''
    menu: list[MenuItem] = dataclasses.field(default_factory=list)


class LoginForm(Form):
    identity = EmailField(
        label=_('Email'),
        render_kw={'autocomplete': 'email', 'inputmode': 'email'},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    password = PasswordField(
        render_kw={'autocomplete': 'password'},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    next_url = HiddenField()


class UserLike(BaseUser):
    is_anonymous = False

    @abc.abstractmethod
    def get_id(self) -> str:
        ...

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return str(self)


class AnonymousUser(UserLike):
    is_anonymous = True
    display_name = 'Anonymous.'

    def get_id(self) -> str:
        return ''


class BaseAuthPolicy(abc.ABC):
    login_form_class: typing.ClassVar[typing.Type[Form]] = LoginForm

    @abc.abstractmethod
    async def authenticate(self, conn: HTTPConnection, identity: str, password: str) -> UserLike | None:
        ...

    def login(self, conn: HTTPConnection, user: UserLike) -> None:
        conn.session[SESSION_KEY] = user.get_id()

    def logout(self, conn: HTTPConnection) -> None:
        if SESSION_KEY in conn.session:
            del conn.session[SESSION_KEY]

    @abc.abstractmethod
    async def load_user(self, conn: HTTPConnection, user_id: str) -> UserLike | None:
        ...

    def is_authenticated(self, conn: HTTPConnection) -> bool:
        return conn.user.is_authenticated

    def get_login_form_class(self) -> typing.Type[Form]:
        return self.login_form_class

    def get_authentication_backend(self) -> AuthenticationBackend:
        return SessionAuthBackend()

    def get_user_menu(self, conn: HTTPConnection) -> UserMenu:
        return UserMenu(user_name='anon.')


class AnonymousAuthPolicy(BaseAuthPolicy):
    async def authenticate(self, conn: HTTPConnection, identity: str, password: str) -> UserLike | None:
        return None

    async def load_user(self, conn: HTTPConnection, user_id: str) -> UserLike | None:
        return AnonymousUser()


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
        auth_policy: BaseAuthPolicy = conn.state.auth_policy
        user_id = conn.session.get(SESSION_KEY, '')
        if user_id and (user := await auth_policy.load_user(conn, user_id)):
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

        flash(Request(scope)).error(_('You need to be logged in to access this page.'))
        redirect_to = conn.url_for('ohmyadmin_login') + '?next=' + conn.url.path
        response = RedirectResponse(url=redirect_to)
        await response(scope, receive, send)
