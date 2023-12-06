import json
from starlette.requests import Request

from ohmyadmin.actions import ActionResponse


def test_action_response_toast() -> None:
    response = ActionResponse().show_toast("Message", "error")
    assert json.loads(response.headers["hx-trigger"]) == {
        "toast": {"message": "Message", "category": "error"}
    }


def test_action_response_redirect(http_request: Request) -> None:
    response = ActionResponse().redirect(http_request, "/")
    assert response.headers["hx-redirect"] == "/"


def test_action_response_refresh(http_request: Request) -> None:
    response = ActionResponse().refresh()
    assert response.headers["hx-refresh"] == "true"


def test_action_refresh_datatable() -> None:
    response = ActionResponse().refresh_datatable()
    assert json.loads(response.headers["hx-trigger"]) == {"refresh-datatable": ""}


def test_action_close_modal() -> None:
    response = ActionResponse().close_modal()
    assert json.loads(response.headers["hx-trigger"]) == {"modals.close": ""}


def test_action_trigger() -> None:
    response = ActionResponse().trigger("myevent", "mypayload")
    assert json.loads(response.headers["hx-trigger"]) == {"myevent": "mypayload"}
