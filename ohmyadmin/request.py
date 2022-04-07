from __future__ import annotations

import typing
from starlette.requests import Request

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin


class AdminRequest(Request):
    @classmethod
    def from_starlette(cls, request: Request) -> AdminRequest:
        return AdminRequest(scope=request.scope, receive=request.receive, send=request._send)

    @property
    def admin(self) -> OhMyAdmin:
        return self.scope['ohmyadmin']

    def url_for(self, name: str, **path_params: typing.Any) -> str:
        return super().url_for(self.path_name(name), **path_params)

    def path_name(self, path_name: str) -> str:
        return f'{self.admin.app_name}:{path_name}'
