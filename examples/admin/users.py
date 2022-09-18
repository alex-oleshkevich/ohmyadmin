import sqlalchemy as sa
import typing
from starlette.requests import Request

from examples.models import User
from ohmyadmin.actions import Action, BatchAction, BulkDeleteAction
from ohmyadmin.components import Component, RowAction
from ohmyadmin.forms import (
    CheckboxField,
    EmailField,
    FileField,
    Form,
    HiddenField,
    IntegerField,
    RadioField,
    SelectField,
    TextField,
)
from ohmyadmin.resources import PkType, Resource
from ohmyadmin.responses import Response
from ohmyadmin.tables import BoolColumn, Column, ImageColumn


class DuplicateAction(BatchAction):
    class ActionForm(Form):
        count = IntegerField(min_value=1, default=1)

    async def apply(self, request: Request, ids: list[PkType], form: Form) -> Response:
        return self.dismiss('Object has been duplicated.')


class ExportAction(Action):
    title = 'Export users?'
    message = 'This will export all users matching current table filters.'

    class ActionForm(Form):
        format = SelectField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xls', 'Excel')])
        range = RadioField(choices=[('all', 'All'), ('selected', 'Selected'), ('all_matched', 'All matched')])

    async def apply(self, request: Request, form: Form) -> Response:
        return self.dismiss('Action completed.')


class EditForm(Form):
    first_name = TextField()
    last_name = TextField()
    photo = FileField(upload_to='photos')
    email = EmailField(required=True)
    is_active = CheckboxField(default=True)
    password = HiddenField(default='')


def row_actions(entity: typing.Any) -> typing.Iterable[Component]:
    yield RowAction(
        entity,
        children=[
            RowAction(entity, action=ExportAction()),
            RowAction(entity, action=DuplicateAction()),
            RowAction(entity, action=BulkDeleteAction(), danger=True),
        ],
    )


class UserResource(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    form_class = EditForm
    queryset = sa.select(entity_class).order_by(User.id)
    batch_actions = (DuplicateAction(),)
    page_actions = (ExportAction(),)
    row_actions = row_actions
    table_columns = [
        Column('id', label='ID'),
        ImageColumn('photo'),
        Column(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            search_in=[User.first_name, User.last_name],
            sort_by=User.last_name,
            link=True,
        ),
        Column('email', label='Email', searchable=True),
        BoolColumn('is_active', label='Active'),
    ]
