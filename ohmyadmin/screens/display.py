import abc
import typing

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.components import AutoDisplayLayout, DisplayLayoutBuilder
from ohmyadmin.datasources.datasource import NoObjectError
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import Screen
from ohmyadmin.display_fields import DisplayField


class DisplayScreen(Screen):
    fields: typing.Sequence[DisplayField] = tuple()
    layout_class: typing.Type[DisplayLayoutBuilder] = AutoDisplayLayout
    template = "ohmyadmin/screens/display/page.html"

    @abc.abstractmethod
    async def get_object(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        try:
            instance = await self.get_object(request)
        except NoObjectError:
            raise HTTPException(404, "Page not found")

        layout_builder = self.layout_class()
        return render_to_response(
            request,
            self.template,
            {
                "screen": self,
                "model": instance,
                "page_title": self.label,
                "page_description": self.description,
                "layout": layout_builder(request, instance),
            },
        )
