from examples.config import async_session
from examples.models import User
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.filters import StringFilter
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


class UserPage(TablePage):
    label = 'App users'
    datasource = SQLADataSource(User, async_session)
    columns = [
        TableColumn('photo', formatter=AvatarFormatter()),
        TableColumn('first_name'),
        TableColumn('last_name', searchable=True, sortable=True),
        TableColumn('email', searchable=True),
        TableColumn('is_active', sortable=True, formatter=BoolFormatter(as_text=True)),
        TableColumn('created_at', sortable=True, formatter=DateFormatter()),
    ]
    filters = [
        StringFilter('first_name'),
        StringFilter('last_name'),
    ]
