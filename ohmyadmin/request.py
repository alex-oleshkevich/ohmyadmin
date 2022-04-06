from __future__ import annotations

import typing
from starlette.requests import Request

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin


class AdminRequest(Request):
    admin: OhMyAdmin

    @classmethod
    def from_starlette(cls, request: Request, admin: OhMyAdmin) -> AdminRequest:
        admin_request = AdminRequest(scope=request.scope, receive=request.receive, send=request._send)
        admin_request.admin = admin
        return admin_request
