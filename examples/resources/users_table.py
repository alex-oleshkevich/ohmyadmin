from starlette.datastructures import URL
from starlette.requests import Request

from examples.models import User
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter, LinkFormatter
from ohmyadmin.views.table import Column, TableView


def user_edit_url(request: Request) -> URL:
    return UsersTable.get_url(request)


class UsersTable(TableView):
    label = 'Users'
    group = 'Other'
    description = 'List all users.'
    datasource = SADataSource(User)
    columns = [
        Column('photo', formatter=AvatarFormatter()),
        Column('first_name', formatter=LinkFormatter(url='/admin')),
        Column('last_name', searchable=True, sortable=True),
        Column('email', searchable=True),
        Column('is_active', sortable=True, formatter=BoolFormatter(as_text=True)),
        Column('created_at', sortable=True, formatter=DateFormatter()),
    ]
