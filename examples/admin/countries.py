import sqlalchemy as sa
import wtforms

from examples.models import Country
from ohmyadmin.forms import Field, Form, TextField
from ohmyadmin.globals import get_dbsession
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


async def code_is_unique(form: Form, field: Field) -> None:
    if field.data == field.object_data:
        return
    stmt = sa.select(sa.exists(sa.select(Country).where(Country.code == field.data)))
    if await get_dbsession().scalar(stmt):
        raise wtforms.ValidationError('Country with this core already exists.')


class CountryResource(Resource):
    icon = 'map'
    label_plural = 'Countries'
    entity_class = Country
    table_columns = [
        Column('name', searchable=True, sortable=True, link=True),
        Column('code', searchable=True),
    ]
    form_fields = [
        TextField('name', required=True),
        TextField('code', required=True, validators=[code_is_unique]),
    ]
