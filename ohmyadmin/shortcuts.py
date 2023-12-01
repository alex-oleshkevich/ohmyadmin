from starlette.requests import Request

from ohmyadmin.app import OhMyAdmin


def get_app(request: Request) -> OhMyAdmin:
    return request.state.ohmyadmin
