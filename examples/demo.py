import pathlib
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.request import AdminRequest
from ohmyadmin.routing import route
from ohmyadmin.tools import Tool


def user_menu_config(request: AdminRequest, user_menu: UserMenu) -> None:
    user_menu.name = 'Alex Oleshkevich'
    user_menu.photo = (
        'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-1.2.1'
        '&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=3&w=256&h=256&q=80'
    )
    user_menu.items.append(MenuItem('My profile', url='/'))


def index_view(request: Request) -> Response:
    url = request.url_for('oma:welcome')
    return Response(f'<a href="{url}">admin</a>')


class FileManager(Tool):
    title = 'File Manager'
    icon = 'file'

    async def index_view(self, request: AdminRequest) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')

    @route('/create')
    async def create_file_view(self, request: AdminRequest) -> Response:
        return self.admin.render_to_response(request, 'file_manager/create_file.html')

    @route('/delete')
    async def delete_file_view(self, request: AdminRequest) -> Response:
        return self.admin.render_to_response(request, 'file_manager/delete_file.html')


class Backup(Tool):
    title = 'Back ups'
    icon = 'database-export'

    async def index_view(self, request: AdminRequest) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')


class OverviewDashboard(Dashboard):
    title = 'Overview'
    icon = 'dashboard'


this_dir = pathlib.Path(__file__).parent
admin = OhMyAdmin(
    user_menu_config=user_menu_config,
    template_dirs=[this_dir / 'templates'],
    dashboards=[
        OverviewDashboard,
    ],
    tools=[
        Backup,
        FileManager,
    ],
)

app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', admin, name='oma'),
    ],
)
