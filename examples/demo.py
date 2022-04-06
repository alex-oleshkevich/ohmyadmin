from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.request import AdminRequest


class MyAdmin(OhMyAdmin):
    def get_user_menu(self, request: AdminRequest) -> UserMenu:
        return UserMenu(
            'Alex Oleshkevich',
            [MenuItem('Log out', '/admin/logout', icon='logout')],
            photo=(
                'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-1.2.1'
                '&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=3&w=256&h=256&q=80'
            ),
        )


def index_view(request: Request) -> Response:
    url = request.url_for('admin:welcome')
    return Response(f'<a href="{url}">admin</a>')


app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', MyAdmin(), name='oma'),
    ],
)
