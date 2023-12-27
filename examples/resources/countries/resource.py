import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import Country
from ohmyadmin import actions
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.htmx import response
from ohmyadmin.resources.resource import ResourceView
from ohmyadmin.views.table import Column


async def show_toast_callback(request: Request) -> Response:
    return response().toast("Clicked!")


class CountryForm(wtforms.Form):
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CountriesResource(ResourceView):
    label = "Country"
    group = "Shop"
    datasource = SADataSource(Country)
    form_class = CountryForm
    page_actions = [
        actions.CallbackAction("Show toast", callback=show_toast_callback),
    ]
    columns = [
        Column("code", searchable=True),
        Column("name", searchable=True, sortable=True),
    ]
