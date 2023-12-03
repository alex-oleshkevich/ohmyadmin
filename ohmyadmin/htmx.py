from starlette.requests import Request
from starlette.responses import Response


def is_htmx_request(request: Request) -> bool:
    return 'hx-request' in request.headers


def matches_target(request: Request, target: str) -> bool:
    return request.headers.get('hx-target', '') == target


def push_url(response: Response, url: str) -> Response:
    response.headers['hx-push-url'] = url
    return response
