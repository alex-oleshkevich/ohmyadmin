import sqlalchemy as sa
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin.actions import Action, BatchAction, LinkRowAction, ModalAction, ModalRowAction, RowAction, RowActionGroup
from ohmyadmin.ext.sqla import BatchDeleteAction, SQLAlchemyResource
from ohmyadmin.forms import CheckboxField, EmailField, FileField, Form, HiddenField, TextField
from ohmyadmin.projections import Projection
from ohmyadmin.tables import BoolColumn, Column, ImageColumn


class DuplicateActionForm(wtforms.Form):
    count = wtforms.IntegerField()


class DuplicateAction(BatchAction):
    icon = 'copy'
    form_class = DuplicateActionForm

    async def apply(self, request: Request, ids: list, form: Form) -> Response:
        return self.dismiss('Object has been duplicated.')


class DuplicateAction2(DuplicateAction):
    ...


class ExportActionForm(wtforms.Form):
    format = wtforms.SelectField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xls', 'Excel')])
    range = wtforms.RadioField(choices=[('all', 'All'), ('selected', 'Selected'), ('all_matched', 'All matched')])


class ExportAction(ModalAction):
    icon = 'download'
    form_class = ExportActionForm

    async def form_valid(self, request: Request, form: Form) -> Response:
        return self.dismiss('Action completed.')


class EditForm(Form):
    first_name = TextField()
    last_name = TextField()
    photo = FileField(upload_to='photos')
    email = EmailField(required=True)
    is_active = CheckboxField(default=True)
    password = HiddenField(default='')


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
    projections = (ActiveUsers,)

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

    def get_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        yield ModalRowAction(action=DuplicateAction())
        yield RowActionGroup(
            [
                LinkRowAction(url='/', text='Home', icon='home'),
                LinkRowAction(url='/', text='Delete', icon='minus', color='danger'),
                ModalRowAction(action=DuplicateAction()),
                ModalRowAction(action=DuplicateAction2()),
            ]
        )

    def get_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        yield BatchDeleteAction(self.entity_class, pk_column=User.id)
        yield DuplicateAction()

    def get_page_actions(self, request: Request) -> typing.Iterable[Action]:
        yield ExportAction()
