import pathlib
import typing
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.metrics import StatMetric
from ohmyadmin.resources import Resource
from ohmyadmin.routing import route
from ohmyadmin.tools import Tool


def user_menu_config(request: Request, user_menu: UserMenu) -> None:
    user_menu.name = 'Alex Oleshkevich'
    user_menu.photo = (
        'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-1.2.1'
        '&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=3&w=256&h=256&q=80'
    )
    user_menu.items.append(MenuItem('My profile', url='/'))


def index_view(request: Request) -> Response:
    url = request.url_for('welcome')
    return Response(f'<a href="{url}">admin</a>')


class FileManager(Tool):
    title = 'File Manager'
    icon = 'file'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')

    @route('/create')
    async def create_file_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/create_file.html')

    @route('/delete')
    async def delete_file_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/delete_file.html')


class Backup(Tool):
    title = 'Back ups'
    icon = 'database-export'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')


class Calendar(Tool):
    title = 'Calendar'
    icon = 'calendar'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'calendar.html')


class Photos(Tool):
    title = 'Photos'
    icon = 'photo'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'photos.html')


class NewUsersMetric(StatMetric):
    title = 'New users'

    async def compute(self, request: Request) -> typing.Any:
        return 42


class NewBirdsMetric(StatMetric):
    title = 'New birds'

    async def compute(self, request: Request) -> typing.Any:
        return 2


class ObservationTrendMetric(StatMetric):
    title = 'Observation Trend'
    columns = 6

    async def compute(self, request: Request) -> typing.Any:
        return 2


class OverviewDashboard(Dashboard):
    title = 'Overview'
    icon = 'dashboard'
    metrics = [NewUsersMetric, NewBirdsMetric, ObservationTrendMetric]


class UserResource(Resource):
    title = 'User'
    icon = 'users'


class OrdersResource(Resource):
    title = 'Order'
    icon = 'list'


class FalimiesResource(Resource):
    title = 'Family'
    icon = 'list'


class SpeciesResource(Resource):
    title = 'Specie'
    icon = 'feather'


this_dir = pathlib.Path(__file__).parent
admin = OhMyAdmin(
    user_menu_config=user_menu_config,
    template_dirs=[this_dir / 'templates'],
    tools=[Backup, FileManager, Calendar, Photos],
    dashboards=[OverviewDashboard],
    resources=[UserResource, OrdersResource, FalimiesResource, SpeciesResource],
)

app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', admin),
    ],
)
