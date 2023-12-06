import abc
import typing
import wtforms as wtforms
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    UnauthenticatedUser,
)
from starlette.requests import HTTPConnection, Request
from starlette_babel import gettext_lazy as _

SESSION_KEY = "_auth_user_id_"


class AdminUser(typing.Protocol):
    display_name: str
    avatar: str


class AnonymousUser(UnauthenticatedUser):
    is_anonymous = True
    display_name = _("Anonymous", domain="ohmyadmin")


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        auth_policy: AuthPolicy = conn.state.ohmyadmin.auth_policy
        user_id = conn.session.get(SESSION_KEY, "")
        if user_id and (user := await auth_policy.load_user(conn, user_id)):
            return AuthCredentials(), user
        return AuthCredentials([]), UnauthenticatedUser()


class LoginForm(wtforms.Form):
    identity = wtforms.EmailField(
        label=_("Email", domain="ohmyadmin"),
        render_kw={"autocomplete": "email", "inputmode": "email"},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    password = wtforms.PasswordField(
        label=_("Password", domain="ohmyadmin"),
        render_kw={"autocomplete": "password"},
        validators=[
            wtforms.validators.data_required(),
        ],
    )
    next_url = wtforms.HiddenField()


class AuthPolicy(abc.ABC):
    login_form_class: type[LoginForm] = LoginForm

    @abc.abstractmethod
    async def authenticate(
        self, request: Request, identity: str, password: str
    ) -> BaseUser | None:  # pragma: nocover
        ...

    @abc.abstractmethod
    async def load_user(
        self, conn: HTTPConnection, user_id: str
    ) -> BaseUser | None:  # pragma: nocover
        ...

    def login(self, request: Request, user: BaseUser) -> None:
        request.session[SESSION_KEY] = user.identity

    def logout(self, request: Request) -> None:
        if SESSION_KEY in request.session:
            del request.session[SESSION_KEY]

    def get_login_form_class(self) -> type[LoginForm]:
        return self.login_form_class

    def get_authentication_backend(self) -> AuthenticationBackend:
        return SessionAuthBackend()


class AnonymousAuthPolicy(AuthPolicy):
    async def authenticate(
        self, request: Request, identity: str, password: str
    ) -> BaseUser | None:
        return None

    async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
        return AnonymousUser()
