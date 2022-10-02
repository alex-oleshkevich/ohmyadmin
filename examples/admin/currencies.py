import sqlalchemy as sa
import wtforms

from examples.models import Currency
from ohmyadmin.globals import get_dbsession
from ohmyadmin.old_forms import Field, Form, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


async def code_is_unique(form: Form, field: Field) -> None:
    if field.data == field.object_data:
        return
    stmt = sa.select(sa.exists(sa.select(Currency).where(Currency.code == field.data)))
    if await get_dbsession().scalar(stmt):
        raise wtforms.ValidationError('Country with this core already exists.')


class EditForm(Form):
    name = TextField(required=True)
    code = TextField(required=True, validators=[code_is_unique])


class CurrencyResource(Resource):
    icon = 'currency'
    entity_class = Currency
    form_class = EditForm
    table_columns = [
        Column('name', searchable=True, sortable=True, link=True),
        Column('code', searchable=True),
    ]
