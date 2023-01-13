import sqlalchemy as sa
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin import display
from ohmyadmin.actions import Action, BatchAction, LinkRowAction, ModalAction, ModalRowAction, RowAction, RowActionGroup
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import BatchDeleteAction, SQLAlchemyResource
from ohmyadmin.forms import AsyncForm, AvatarField, ImageType, Uploader
from ohmyadmin.helpers import media_url_or_redirect
from ohmyadmin.projections import DefaultProjection, Projection


class DuplicateActionForm(wtforms.Form):
    count = wtforms.IntegerField()


class DuplicateAction(BatchAction):
    icon = 'copy'
    form_class = DuplicateActionForm

    async def apply(self, request: Request, ids: list, form: AsyncForm) -> Response:
        return self.dismiss('Object has been duplicated.')


class DuplicateAction2(DuplicateAction):
    ...


class ExportActionForm(wtforms.Form):
    format = wtforms.SelectField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xls', 'Excel')])
    range = wtforms.RadioField(choices=[('all', 'All'), ('selected', 'Selected'), ('all_matched', 'All matched')])


class ExportAction(ModalAction):
    icon = 'download'
    form_class = ExportActionForm

    async def form_valid(self, request: Request, form: AsyncForm) -> Response:
        return self.dismiss('Action completed.')


class ActiveUsers(Projection):
    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        return query.filter(User.is_active == True)


class DisabledUsers(Projection):
    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        return query.filter(User.is_active == False)


class UserResource(SQLAlchemyResource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    queryset = sa.select(entity_class).order_by(User.id)

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('id', label='ID')
        yield DisplayField('photo', component=display.Image(url_generator=media_url_or_redirect))
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
        yield wtforms.StringField(name='first_name')
        yield wtforms.StringField(name='last_name')
        yield wtforms.EmailField(name='email', validators=[wtforms.validators.DataRequired()])
        yield wtforms.BooleanField(name='is_active')
        yield AvatarField(
            name='photo',
            validators=[ImageType(['image/jpeg'])],
            uploader=Uploader(request.state.admin.file_storage, 'photos/{pk}_{prefix}_{file_name}'),
        )
        yield wtforms.HiddenField(name='password')

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

    def get_projections(self, request: Request) -> typing.Iterable[Projection]:
        yield DefaultProjection(self.get_queryset(request), 'All Users')
        yield ActiveUsers()
        yield DisabledUsers()
