import json
import typing
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response

ToastCategory = typing.Literal['error', 'success']
R = typing.TypeVar('R', bound=Response)


def is_htmx_request(request: Request) -> bool:
    return 'hx-request' in request.headers


def matches_target(request: Request, target: str) -> bool:
    return request.headers.get('hx-target', '') == target


def push_url(response: R, url: str) -> R:
    response.headers['hx-push-url'] = url
    return response


def trigger(response: R, event: str, data: typing.Any = None) -> R:
    triggers = json.loads(response.headers.get('hx-trigger', '{}'))
    triggers[event] = data
    response.headers['hx-trigger'] = json.dumps(triggers)
    return response


def close_modal(response: R) -> R:
    return trigger(response, 'modals-close')


def toast(response: R, message: str, category: ToastCategory = 'success') -> R:
    return trigger(response, 'toast', {'message': message, 'category': category})


class HXResponse(Response):
    def toast(self, message: str, category: ToastCategory = 'success') -> typing.Self:
        return toast(self, message, category)

    def close_modal(self) -> typing.Self:
        return close_modal(self)


def response(
    status_code: int = 204,
    headers: typing.Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> HXResponse:
    return HXResponse(
        status_code=status_code,
        headers=headers,
        media_type=media_type,
        background=background,
    )
