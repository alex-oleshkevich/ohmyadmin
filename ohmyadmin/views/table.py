from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import View


class TableView(View):
    template = 'ohmyadmin/views/table/table.html'

    def dispatch(self, request: Request) -> Response:
        return render_to_response(request, self.template, {
            'page_title': self.label,
        })
