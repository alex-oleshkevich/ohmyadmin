from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.request import AdminRequest


def user_menu_config(request: AdminRequest, user_menu: UserMenu) -> None:
    user_menu.name = 'Alex Oleshkevich'
    user_menu.photo = (
        'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-1.2.1'
        '&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=3&w=256&h=256&q=80'
    )
    user_menu.items.append(MenuItem('My profile', '/'))


def index_view(request: Request) -> Response:
    url = request.url_for('oma:welcome')
    return Response(f'<a href="{url}">admin</a>')


app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', OhMyAdmin(user_menu_config=user_menu_config), name='oma'),
    ],
)
