import json
import typing

from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

ToastCategory = typing.Literal["error", "success"]
R = typing.TypeVar("R", bound=Response)


def is_htmx_request(request: Request) -> bool:
    return "hx-request" in request.headers


def matches_target(request: Request, target: str) -> bool:
    return request.headers.get("hx-target", "") == target


def push_url(response: R, url: str | URL) -> R:
    response.headers["hx-push-url"] = str(url)
    return response


def redirect(response: R, url: str | URL) -> R:
    response.headers["hx-redirect"] = str(url)
    return response


def location(response: R, url: str | URL) -> R:
    response.headers["hx-location"] = str(url)
    return response


def trigger(response: R, event: str, data: typing.Any = None) -> R:
    triggers = json.loads(response.headers.get("hx-trigger", "{}"))
    triggers[event] = data
    response.headers["hx-trigger"] = json.dumps(triggers)
    return response


def close_modal(response: R) -> R:
    return trigger(response, "modals-close")


def refresh(response: R) -> R:
    """Refresh table items."""
    return trigger(response, "refresh")


def toast(response: R, message: str, category: ToastCategory = "success") -> R:
    return trigger(response, "toast", {"message": message, "category": category})


class HXResponse(Response):
    def toast(self, message: str, category: ToastCategory = "success") -> typing.Self:
        return toast(self, str(message), category)

    def close_modal(self) -> typing.Self:
        return close_modal(self)

    def refresh(self) -> typing.Self:
        return refresh(self)

    def redirect(self, url: str | URL) -> typing.Self:
        return redirect(self, url)

    def push_url(self, url: str | URL) -> typing.Self:
        return push_url(self, url)

    def location(self, url: str | URL) -> typing.Self:
        return location(self, url)


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
