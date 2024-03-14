from __future__ import annotations

import functools
import typing

from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.helpers import snake_to_sentence


def default_value_getter(obj: typing.Any, attr: str) -> typing.Any:
    return getattr(obj, attr)


ValueGetter: typing.TypeAlias = typing.Callable[[typing.Any], typing.Any]
ResourceActionLink: typing.TypeAlias = typing.Literal["view", "edit"]


class DisplayField:
    def __init__(
        self,
        name: str,
        label: str | None = None,
        value_getter: ValueGetter | None = None,
        default_if_none: str = "-",
        link: bool = False,
        link_to: ResourceActionLink = "edit",
    ) -> None:
        self.name = name
        self.link = link
        self.link_to = link_to
        self.default_if_none = default_if_none
        self.label = label or snake_to_sentence(name)
        self.value_getter = value_getter or functools.partial(default_value_getter, attr=name)

    def get_field_value(self, request: Request, obj: typing.Any) -> str:
        obj_value = self.get_value(obj)
        if obj_value is None:
            return self.default_if_none

        return self.format_value(request, obj_value)

    def get_value(self, obj: typing.Any) -> typing.Any:
        return self.value_getter(obj)

    def format_value(self, request: Request, value: typing.Any) -> str:
        return self.formatter(request, value)

    def get_link_url(self, request: Request, obj: typing.Any) -> URL:
        resource = request.state.resource
        object_id = resource.datasource.get_pk(obj)
        if callable(self.link_to):
            return self.link_to(request, obj)

        if self.link_to == "edit":
            return request.url_for(resource.get_edit_route_name(), object_id=object_id)
        return request.url_for(resource.get_display_route_name(), object_id=object_id)
