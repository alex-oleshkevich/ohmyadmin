import abc
import typing

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.datasources.datasource import NoObjectError
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import Screen
from ohmyadmin.views.display import DisplayView


class DisplayScreen(Screen):
    view: DisplayView | None = None
    template = "ohmyadmin/screens/display/page.html"

    @abc.abstractmethod
    async def get_object(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    def get_view(self) -> DisplayView:
        assert self.view, "No view is defined"
        return self.view

    async def dispatch(self, request: Request) -> Response:
        try:
            instance = await self.get_object(request)
        except NoObjectError:
            raise HTTPException(404, "Page not found")

        return render_to_response(
            request,
            self.template,
            {
                "screen": self,
                "model": instance,
                "page_title": self.label,
                "view": self.get_view(),
                "page_description": self.description,
            },
        )
