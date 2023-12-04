from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin.actions import actions
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter, LinkFormatter
from ohmyadmin.htmx import response
from ohmyadmin.views.table import Column, TableView


def user_edit_url(request: Request) -> URL:
    return UsersTable.get_url(request)


async def show_toast_callback(request: Request) -> Response:
    return response().toast('Clicked!')


class UsersTable(TableView):
    label = 'Users'
    group = 'Other'
    description = 'List all users.'
    datasource = SADataSource(User)
    actions = [
        actions.LinkAction(url='/admin', label='To Main page'),
        actions.CallFunctionAction(function='alert', args=['kek'], label='Show alert'),
        actions.EventAction(event='refresh', variant='text', label='Refresh data'),
        actions.CallbackAction(show_toast_callback, label='Show toast', variant='danger'),
    ]
    columns = [
        Column('photo', formatter=AvatarFormatter()),
        Column('first_name', formatter=LinkFormatter(url='/admin')),
        Column('last_name', searchable=True, sortable=True),
        Column('email', searchable=True),
        Column('is_active', sortable=True, formatter=BoolFormatter(as_text=True)),
        Column('created_at', sortable=True, formatter=DateFormatter()),
    ]
