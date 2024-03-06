import abc
import typing

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.components.display import DetailView
from ohmyadmin.datasources.datasource import NoObjectError
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import Screen


class DisplayScreen(Screen):
    view_class: DetailView = DetailView
    template = "ohmyadmin/screens/display/page.html"

    @abc.abstractmethod
    async def get_object(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        try:
            model = await self.get_object(request)
        except NoObjectError:
            raise HTTPException(404, "Page not found")

        component = self.view_class(model)
        return render_to_response(
            request,
            self.template,
            {
                "screen": self,
                "model": model,
                "component": component,
                "page_title": self.label,
                "page_description": self.description,
            },
        )
