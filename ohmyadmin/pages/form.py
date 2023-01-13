import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import actions
from ohmyadmin.forms import create_form, validate_on_submit
from ohmyadmin.pages.page import Page

_F = typing.TypeVar('_F', bound=wtforms.Form)


class FormPage(Page):
    __abstract__ = True

    form_class: type[wtforms.Form]
    form_actions: list[type[actions.Submit | actions.Link]] | None = None
    success_message: str = _('{object} has been submitted.', domain='ohmyadmin')
    template: typing.ClassVar[str] = 'ohmyadmin/pages/form.html'

    def get_form_actions(self, request: Request) -> list[actions.Submit | actions.Link]:
        return self.form_actions or []

    async def create_form(self, request: Request) -> wtforms.Form:
        return await create_form(request, self.form_class)

    async def handler(self, request: Request) -> Response:
        form = await self.create_form(request)
        if await validate_on_submit(request, form):
            return await self.handle_submit(request, form)

        form_actions = self.get_form_actions(request)
        return self.render_to_response(
            request, self.template, {'form': form, 'page_title': self.page_title, 'form_actions': form_actions}
        )

    async def handle_submit(self, request: Request, form: wtforms.Form) -> Response:
        flash(request).success(self.success_message.format(object='form'))
        return self.redirect_to_self(request)

    def as_route(self) -> BaseRoute:
        return Route(f'/{self.slug}', self, methods=['GET', 'POST'], name=self.get_path_name())
