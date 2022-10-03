import sqlalchemy as sa
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin.actions import Action, BatchAction, LinkRowAction, ModalAction, ModalRowAction, RowAction, RowActionGroup
from ohmyadmin.components import display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.ext.sqla import BatchDeleteAction, SQLAlchemyResource
from ohmyadmin.forms import BooleanField, EmailField, FileField, Form, HiddenField, StringField, Uploader
from ohmyadmin.helpers import media_url_or_redirect
from ohmyadmin.projections import Projection
from ohmyadmin.tables import BoolColumn, Column


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
    queryset = sa.select(entity_class).order_by(User.id)
    projections = (ActiveUsers,)

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('id', label='ID')
        yield DisplayField('photo', component=display.Image(), value_formatter=media_url_or_redirect)
        yield DisplayField(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            sort_by='last_name',
            search_in='last_name',
            link=True,
        )
        yield DisplayField('email', label='Email', searchable=True, sortable=True)
        yield DisplayField('is_active', label='Active', component=display.Boolean())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield StringField(name='first_name')
        yield StringField(name='last_name')
        yield EmailField(name='email', validators=[wtforms.validators.DataRequired()])
        yield FileField(
            name='photo',
            uploader=Uploader(request.state.admin.file_storage, 'photos/{pk}_{prefix}_{file_name}'),
        )
        yield BooleanField(name='is_active')
        yield HiddenField(name='password')

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
