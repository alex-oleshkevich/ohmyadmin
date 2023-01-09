import typing

from markupsafe import Markup
from starlette.requests import Request

from ohmyadmin.shortcuts import render_to_string
from ohmyadmin.views.base import IndexView


class GridView(IndexView):

    def render(self, request: Request, objects: list[typing.Any]) -> str:
        return Markup(render_to_string(request, 'ohmyadmin/views/grid.html', {'table': self, 'objects': objects}))
