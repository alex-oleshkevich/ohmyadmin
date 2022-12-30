import sqlalchemy as sa
import typing
import wtforms
from starlette.requests import Request

from examples.models import Currency
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource
from ohmyadmin.forms import AsyncForm
from ohmyadmin.globals import get_dbsession


async def code_is_unique(form: AsyncForm, field: wtforms.Field) -> None:
    if field.data == field.object_data:
        return
    stmt = sa.select(sa.exists(sa.select(Currency).where(Currency.code == field.data)))
    if await get_dbsession().scalar(stmt):
        raise wtforms.ValidationError('Country with this core already exists.')


class CurrencyResource(SQLAlchemyResource):
    icon = 'currency'
    entity_class = Currency

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('name', searchable=True, sortable=True, link=True)
        yield DisplayField('code', searchable=True)

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield wtforms.StringField(name='name', validators=[wtforms.validators.data_required()])
        yield wtforms.StringField(name='code', validators=[code_is_unique, wtforms.validators.data_required()])
