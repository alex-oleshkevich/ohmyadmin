import sqlalchemy as sa
from starlette.requests import Request

from examples.models import User
from ohmyadmin.actions import ActionResponse
from ohmyadmin.batch_actions import BatchAction
from ohmyadmin.forms import CheckboxField, EmailField, FileField, Form, HiddenField, IntegerField, TextField
from ohmyadmin.resources import PkType, Resource
from ohmyadmin.tables import BoolColumn, Column, ImageColumn


class DuplicateAction(BatchAction):
    class ActionForm(Form):
        count = IntegerField(min_value=1, default=1)

    async def apply(self, request: Request, ids: list[PkType], form: Form) -> ActionResponse:
        return self.respond().redirect_to_resource(UserResource).with_success('User has been scheduled for export.')


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
    table_actions = []
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
