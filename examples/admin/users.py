import sqlalchemy as sa
from starlette.requests import Request

from examples.models import User
from ohmyadmin.actions import Action, BatchAction
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
from ohmyadmin.structures import URLSpec
from ohmyadmin.tables import BoolColumn, Column, ImageColumn


class DuplicateAction(BatchAction):
    class ActionForm(Form):
        count = IntegerField(min_value=1, default=1)

    async def apply(self, request: Request, ids: list[PkType], form: Form) -> Response:
        return Response.empty().hx_redirect(URLSpec.to_resource(UserResource))


class ExportAction(Action):
    title = 'Export users?'
    message = 'This will export all users matching current table filters.'

    class ActionForm(Form):
        format = SelectField(
            choices=[
                ('csv', 'CSV'),
                ('json', 'JSON'),
                ('xls', 'Excel'),
            ]
        )
        range = RadioField(
            choices=[
                ('all', 'All'),
                ('selected', 'Selected'),
                ('all_matched', 'All matched'),
            ]
        )

    async def apply(self, request: Request, form: Form) -> Response:
        return self.dismiss('Action completed.')


class EditForm(Form):
    first_name = TextField()
    last_name = TextField()
    photo = FileField(upload_to='photos')
    email = EmailField(required=True)
    is_active = CheckboxField(default=True)
    password = HiddenField(default='')


class UserResource(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    form_class = EditForm
    queryset = sa.select(entity_class).order_by(User.id)
    batch_actions = (DuplicateAction(),)
    table_actions = (ExportAction(),)
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
