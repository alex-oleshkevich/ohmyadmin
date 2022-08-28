from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from ohmyadmin.app import OhMyAdmin

# class UserTable(TableView):
#     id = 'users'
#     columns = [
#         Column('id', label='ID'),
#         Column('first_name', label='First name', sortable=True, searchable=True),
#         Column('last_name', label='Last name', sortable=True, searchable=True),
#         Column('email', label='Email', searchable=True),
#         Column('active', label='Active'),
#     ]
#     row_actions = [
#         Action.link('Edit', '/admin/edit'),
#         Action.link('View', '/admin/view'),
#         Action.confirm('Delete', '/admin/delete', dangerous=True),
#     ]
#     batch_actions = [
#         BatchAction('bulk_delete', 'Delete', confirmation='Do you want to delete all these items?', dangerous=True),
#     ]
from ohmyadmin.nav import MenuItem


def index_view(request: Request) -> Response:
    url = request.url_for('welcome')
    return Response(f'<a href="{url}">admin</a>')


class Admin(OhMyAdmin):
    def build_main_menu(self, request: Request) -> list[MenuItem]:
        return []


app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', Admin()),
    ],
    middleware=[
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
)
