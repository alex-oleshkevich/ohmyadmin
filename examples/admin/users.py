import sqlalchemy as sa
import typing

from examples.models import User
from ohmyadmin.ext.sqla import SQLAlchemyResource
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
from ohmyadmin.projections import Projection
from ohmyadmin.tables import BoolColumn, Column, ImageColumn

#
#
# class DuplicateAction(BatchAction):
#     class ActionForm(Form):
#         count = IntegerField(min_value=1, default=1)
#
#     async def apply(self, request: Request, ids: list, form: Form) -> Response:
#         return self.dismiss('Object has been duplicated.')
#
#
# class ExportAction(Action):
#     title = 'Export users?'
#     message = 'This will export all users matching current table filters.'
#
#     class ActionForm(Form):
#         format = SelectField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xls', 'Excel')])
#         range = RadioField(choices=[('all', 'All'), ('selected', 'Selected'), ('all_matched', 'All matched')])
#
#     async def apply(self, request: Request, form: Form) -> Response:
#         return self.dismiss('Action completed.')


class EditForm(Form):
    first_name = TextField()
    last_name = TextField()
    photo = FileField(upload_to='photos')
    email = EmailField(required=True)
    is_active = CheckboxField(default=True)
    password = HiddenField(default='')


#
# def row_actions(entity: typing.Any) -> typing.Iterable[Component]:
#     yield RowAction(
#         entity,
#         children=[
#             RowAction(entity, action=ExportAction()),
#             RowAction(entity, action=DuplicateAction()),
#             RowAction(entity, action=BulkDeleteAction(), danger=True),
#         ],
#     )
#


class ActiveUsers(Projection):
    columns = [
        Column('full_name', label='Name', link=True),
        BoolColumn('is_active', label='Active'),
    ]

    def apply_filter(self, stmt: sa.sql.Select) -> sa.sql.Select:
        return stmt.filter(User.is_active == True)


class UserResource(SQLAlchemyResource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    form_class = EditForm
    queryset = sa.select(entity_class).order_by(User.id)
    # batch_actions = (DuplicateAction(),)
    # page_actions = (ExportAction(),)
    # row_actions = row_actions
    projections = (ActiveUsers,)
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

    def get_fields(self) -> typing.Iterable[Column]:
        yield Column('id', label='ID')
        yield ImageColumn('photo')
        yield Column(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            sort_by='last_name',
            search_in='last_name',
            link=True,
        )
        yield Column('email', label='Email', searchable=True, sortable=True)
        yield BoolColumn('is_active', label='Active')
