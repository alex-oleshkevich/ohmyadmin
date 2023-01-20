import sqlalchemy as sa
import typing
import wtforms
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin import actions
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.filters import StringFilter
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class ToggleActivationObjectAction(actions.BaseObjectAction):
    label = 'Toggle activation'
    confirmation = 'Change activation state?'

    async def apply(self, request: Request, object_id: str) -> Response:
        model = await request.state.datasource.get(request, object_id)
        model.is_active = not model.is_active
        await request.state.datasource.update(request, model)
        message = 'Activated' if model.is_active else 'Deactivated'
        return actions.response().show_toast(message).refresh_datatable()


class ChangePasswordForm(wtforms.Form):
    password = wtforms.PasswordField(validators=[wtforms.validators.length(min=8), wtforms.validators.data_required()])
    password_confirm = wtforms.PasswordField(
        label='Confirm password', validators=[wtforms.validators.equal_to('password')]
    )


class ChangePasswordObjectAction(actions.BaseFormObjectAction):
    icon = 'password'
    label = 'Change password'
    form_class = ChangePasswordForm

    async def get_form_object(self, request: Request, object_id: str) -> typing.Any:
        return await request.state.datasource.get(request, object_id)

    async def handle(self, request: Request, form: ChangePasswordForm, model: typing.Any) -> Response:
        model.password = pbkdf2_sha256.hash(form.password.data)
        await request.state.datasource.update(request, model)
        return actions.response().show_toast('Password changed.').close_modal()


class UserForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField()
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    is_active = wtforms.BooleanField()


class Users(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    datasource = SQLADataSource(User, sa.select(User).order_by(User.id))
    form_class = UserForm
    columns = [
        TableColumn('photo', formatter=AvatarFormatter()),
        TableColumn('first_name', link=True),
        TableColumn('last_name', searchable=True, sortable=True),
        TableColumn('email', searchable=True),
        TableColumn('is_active', sortable=True, formatter=BoolFormatter(as_text=True)),
        TableColumn('created_at', sortable=True, formatter=DateFormatter()),
    ]
    filters = [
        StringFilter('first_name'),
        StringFilter('last_name'),
    ]
    object_actions = [
        ChangePasswordObjectAction(),
        ToggleActivationObjectAction(),
    ]
