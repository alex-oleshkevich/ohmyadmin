import abc
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette_babel import gettext_lazy as _

from ohmyadmin import actions, layouts
from ohmyadmin.forms import create_form, validate_on_submit
from ohmyadmin.pages.base import BasePage

_F = typing.TypeVar('_F', bound=wtforms.Form)


class FormPage(BasePage):
    """This page renders HTML form."""

    __abstract__ = True

    form_class: type[wtforms.Form]
    form_actions: typing.Sequence[actions.Submit | actions.Link] | None = None
    template: typing.ClassVar[str] = 'ohmyadmin/pages/form.html'

    def get_form_actions(self, request: Request) -> typing.Sequence[actions.Submit | actions.Link]:
        return self.form_actions or [
            actions.Submit(label=_('Submit', domain='ohmyadmin'), variant='accent'),
        ]

    async def get_form_object(self, request: Request) -> typing.Any:
        return None

    async def create_form(self, request: Request, model: typing.Any) -> wtforms.Form:
        return await create_form(request, self.form_class, obj=model)

    def build_form_layout(self, request: Request, form: wtforms.Form) -> layouts.Layout:
        return layouts.Card([layouts.StackedForm([layouts.Input(field) for field in form])])

    async def dispatch(self, request: Request) -> Response:
        model = await self.get_form_object(request)
        form = await self.create_form(request, model)
        if await validate_on_submit(request, form):
            return await self.handle_submit(request, form, model)

        form_layout = self.build_form_layout(request, form)
        form_actions = self.get_form_actions(request)
        return self.render_to_response(
            request,
            self.template,
            {'form': form, 'page_title': self.page_title, 'form_layout': form_layout, 'form_actions': form_actions},
        )

    @abc.abstractmethod
    async def handle_submit(
        self, request: Request, form: wtforms.Form, model: typing.Any
    ) -> Response:  # pragma: no cover
        ...

    def as_route(self) -> BaseRoute:
        return Route(f'/{self.slug}', self.dispatch, methods=['GET', 'POST'], name=self.get_path_name())
