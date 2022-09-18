from __future__ import annotations

import dataclasses

import typing

from ohmyadmin.globals import get_current_request

if typing.TYPE_CHECKING:
    from ohmyadmin.dashboards import Dashboard
    from ohmyadmin.pages import Page
    from ohmyadmin.resources import Resource, ResourceAction


@dataclasses.dataclass
class URLSpec:
    url: str | None = None
    path_name: str | None = None
    path_params: dict[str, str | int] | None = None
    resource: typing.Type[Resource] | Resource | None = None
    resource_action: ResourceAction = 'list'
    resource_action_params: dict[str, str | int] | None = None
    dashboard: typing.Type[Dashboard] | Dashboard | None = None
    page: typing.Type[Page] | Page | None = None

    def to_url(self) -> str:
        request = get_current_request()
        if self.url:
            return self.url
        if self.path_name:
            return request.url_for(self.path_name, **(self.path_params or {}))
        if self.resource:
            return request.url_for(
                self.resource.get_route_name(self.resource_action), **(self.resource_action_params or {})
            )
        if self.page:
            return request.url_for(self.page.get_route_name())
        if self.dashboard:
            return request.url_for(self.dashboard.get_route_name())
        raise ValueError('Cannot generate URL.')

    @classmethod
    def to_path_name(cls, path_name: str, path_params: dict[str, str | int] | None = None) -> URLSpec:
        return cls(path_name=path_name, path_params=path_params)

    @classmethod
    def to_resource(
        cls,
        resource: typing.Type[Resource] | Resource,
        action: ResourceAction = 'list',
        path_params: dict[str, str | int] | None = None,
    ) -> URLSpec:
        return cls(resource=resource, resource_action=action, resource_action_params=path_params)

    @classmethod
    def to_page(cls, page: typing.Type[Page] | Page) -> URLSpec:
        return cls(page=page)

    @classmethod
    def to_dashboard(cls, dashboard: typing.Type[Dashboard] | Dashboard) -> URLSpec:
        return cls(dashboard=dashboard)


url_to = URLSpec
