import dataclasses

import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin import actions
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


@dataclasses.dataclass
class Entity:
    id: int
    name: str


class ToastPageAction(actions.BasePageAction):
    label = 'Show toast'

    async def apply(self, request: Request) -> Response:
        return actions.response().show_toast('Clicked')


class ToastWithConfirmationPageAction(ToastPageAction):
    label = 'Confirmation'
    confirmation = 'Please confirm this action'


class ToastForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class ModalPageAction(actions.BaseFormPageAction):
    label = 'In modal'
    form_class = ToastForm

    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        return actions.response().show_toast(f'Name: {form.name.data}').close_modal()


class Actions(TablePage):
    group = 'Misc'
    label = 'Actions demo'
    datasource = InMemoryDataSource(
        Entity,
        [
            Entity(id=1, name='One'),
            Entity(id=2, name='Two')
        ]
    )
    page_actions = [
        actions.Link(label='Link', url='/admin', icon='plus'),
        ToastPageAction(),
        ToastWithConfirmationPageAction(),
        ModalPageAction(),
    ]
    columns = [
        TableColumn('id'),
        TableColumn('name'),
    ]
